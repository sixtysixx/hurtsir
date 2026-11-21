"""Unit tests for the pure helpers in setup.py.

Run from the repo root:

    python -m unittest discover -s tools/sirhurt-setup -p "test_*.py" -v

Nothing here touches the network, the registry or a Roblox install; the helpers
under test are the ones that decide what gets downloaded, where it is unpacked
and whether the bytes match the manifest.
"""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import setup  # noqa: E402


def manifest_body(*packages: tuple[str, str, int]) -> str:
    lines = ["v0"]
    for name, md5, size in packages:
        lines += [name, md5, str(size), str(size * 4)]
    return "\n".join(lines) + "\n"


class ParsePkgManifestTests(unittest.TestCase):
    def test_keeps_zips_and_lowercases_md5(self) -> None:
        body = manifest_body(
            ("RobloxApp.zip", "ABCDEF", 1000),
            ("WebView2.zip", "0123", 42),
            ("RobloxPlayerInstaller.exe", "FFFF", 9),
        )
        self.assertEqual(
            setup.parse_pkg_manifest(body),
            [("RobloxApp.zip", "abcdef", 1000), ("WebView2.zip", "0123", 42)],
        )

    def test_rejects_unknown_header(self) -> None:
        with self.assertRaises(setup.SetupError):
            setup.parse_pkg_manifest("v1\nRobloxApp.zip\nabc\n1\n2\n")

    def test_rejects_empty_body(self) -> None:
        with self.assertRaises(setup.SetupError):
            setup.parse_pkg_manifest("")

    def test_requires_roblox_app(self) -> None:
        with self.assertRaises(setup.SetupError):
            setup.parse_pkg_manifest(manifest_body(("WebView2.zip", "abc", 5)))

    def test_unparsable_size_becomes_zero(self) -> None:
        body = "v0\nRobloxApp.zip\nabc\nnot-a-number\n4\n"
        self.assertEqual(setup.parse_pkg_manifest(body), [("RobloxApp.zip", "abc", 0)])

    def test_skips_blank_lines(self) -> None:
        body = "\n".join(["", "v0", "", "RobloxApp.zip", "abc", "7", "28", ""])
        self.assertEqual(setup.parse_pkg_manifest(body), [("RobloxApp.zip", "abc", 7)])


class VerifyPackageTests(unittest.TestCase):
    def setUp(self) -> None:
        handle = tempfile.NamedTemporaryFile(delete=False)
        handle.write(b"roblox package payload")
        handle.close()
        self.path = Path(handle.name)
        self.addCleanup(self.path.unlink)
        self.md5 = hashlib.md5(self.path.read_bytes()).hexdigest()
        self.size = self.path.stat().st_size

    def test_accepts_matching_md5_and_size(self) -> None:
        setup.verify_package(self.path, self.md5, self.size)

    def test_accepts_missing_size(self) -> None:
        setup.verify_package(self.path, self.md5, 0)

    def test_rejects_wrong_size(self) -> None:
        with self.assertRaises(setup.SetupError) as caught:
            setup.verify_package(self.path, self.md5, self.size + 1)
        self.assertIn("bytes", str(caught.exception))

    def test_rejects_wrong_md5(self) -> None:
        with self.assertRaises(setup.SetupError) as caught:
            setup.verify_package(self.path, "0" * 32, self.size)
        self.assertIn("failed verification", str(caught.exception))


class PackageTargetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.destination = Path("C:/Roblox/Versions/version-abc")

    def test_subfolder_packages(self) -> None:
        self.assertEqual(
            setup.package_target(self.destination, "content-avatar.zip"),
            self.destination / "content/avatar/",
        )

    def test_root_packages_stay_in_version_folder(self) -> None:
        self.assertEqual(setup.package_target(self.destination, "WebView2.zip"), self.destination)

    def test_every_manifest_package_has_a_root(self) -> None:
        self.assertIn("RobloxApp.zip", setup.ROBLOX_PACKAGE_ROOTS)
        for name in setup.ROBLOX_PACKAGE_ROOTS:
            with self.subTest(package=name):
                setup.package_target(self.destination, name)


class PackagePresentTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.destination = Path(folder.name)

    def test_root_package_needs_all_markers(self) -> None:
        (self.destination / "RobloxPlayerBeta.exe").touch()
        self.assertFalse(setup.package_present(self.destination, "RobloxApp.zip"))
        (self.destination / "RobloxPlayerBeta.dll").touch()
        self.assertTrue(setup.package_present(self.destination, "RobloxApp.zip"))

    def test_webview_loader_marker(self) -> None:
        self.assertFalse(setup.package_present(self.destination, "WebView2.zip"))
        (self.destination / "WebView2Loader.dll").touch()
        self.assertTrue(setup.package_present(self.destination, "WebView2.zip"))

    def test_subfolder_package_needs_a_file(self) -> None:
        folder = self.destination / "shaders"
        folder.mkdir()
        self.assertFalse(setup.package_present(self.destination, "shaders.zip"))
        (folder / "shader.pack").touch()
        self.assertTrue(setup.package_present(self.destination, "shaders.zip"))

    def test_unmapped_package_is_a_zip_on_disk(self) -> None:
        self.assertFalse(setup.package_present(self.destination, "mystery.zip"))
        (self.destination / "mystery.zip").touch()
        self.assertTrue(setup.package_present(self.destination, "mystery.zip"))


class ClassifyLinkTests(unittest.TestCase):
    def test_gofile(self) -> None:
        self.assertEqual(
            setup.classify_link("https://gofile.io/d/AbC123"),
            ("gofile", "AbC123", "https://gofile.io/d/AbC123"),
        )

    def test_gofile_with_www_and_quotes(self) -> None:
        self.assertEqual(
            setup.classify_link('  "https://www.gofile.io/d/abc123def"  ')[:2],
            ("gofile", "abc123def"),
        )

    def test_box(self) -> None:
        self.assertEqual(
            setup.classify_link("https://app.box.com/s/abcdefgh1234")[:2],
            ("box", "abcdefgh1234"),
        )

    def test_rejects_other_hosts(self) -> None:
        for raw in (
            "https://example.com/d/abc123",
            "https://gofile.io/d/abc",  # too short
            "https://app.box.com/s/short",
            "",
        ):
            with self.subTest(link=raw), self.assertRaises(setup.SetupError):
                setup.classify_link(raw)


class ShouldElevateTests(unittest.TestCase):
    def test_never_when_already_elevated_or_read_only(self) -> None:
        with mock.patch.object(setup.sys, "platform", "win32"), mock.patch.object(
            setup, "is_admin", return_value=False
        ):
            self.assertFalse(setup.should_elevate(["--elevated"]))
            self.assertFalse(setup.should_elevate(["--version"]))
            self.assertFalse(setup.should_elevate(["dry", "--dry-run"]))
            self.assertTrue(setup.should_elevate([]))

    def test_never_when_admin(self) -> None:
        with mock.patch.object(setup.sys, "platform", "win32"), mock.patch.object(
            setup, "is_admin", return_value=True
        ):
            self.assertFalse(setup.should_elevate([]))

    def test_never_off_windows(self) -> None:
        with mock.patch.object(setup.sys, "platform", "linux"):
            self.assertFalse(setup.should_elevate([]))


class TargetValidationTests(unittest.TestCase):
    def test_onedrive_parts_are_detected(self) -> None:
        self.assertTrue(setup.is_onedrive_path(Path("C:/Users/someone/OneDrive/SirHurt")))
        self.assertTrue(setup.is_onedrive_path(Path("C:/OneDrive - Contoso/SirHurt")))
        self.assertFalse(setup.is_onedrive_path(Path("C:/Users/someone/Downloads/SirHurt")))

    def test_rejects_onedrive_target(self) -> None:
        with mock.patch.object(setup, "is_onedrive_path", return_value=True):
            with self.assertRaises(setup.SetupError):
                setup.validate_target(Path("C:/Users/someone/OneDrive/SirHurt"))

    @unittest.skipUnless(sys.platform.startswith("win"), "protected roots are Windows paths")
    def test_rejects_program_files(self) -> None:
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        with mock.patch.object(setup, "is_onedrive_path", return_value=False):
            with self.assertRaises(setup.SetupError):
                setup.validate_target(Path(program_files) / "SirHurt")

    def test_accepts_an_ordinary_folder(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            setup.validate_target(Path(folder) / setup.INSTALL_FOLDER_NAME)


class ConstantsTests(unittest.TestCase):
    def test_version_is_a_tag_friendly_string(self) -> None:
        self.assertRegex(setup.__version__, r"^\d+\.\d+\.\d+$")

    def test_runtime_exit_codes(self) -> None:
        self.assertIn(3010, setup.RUNTIME_OK_CODES)  # reboot required, still success

    def test_manifest_entry_width(self) -> None:
        self.assertEqual(setup.MANIFEST_ENTRY_LINES, 4)


if __name__ == "__main__":
    unittest.main()
