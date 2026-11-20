#!/usr/bin/env python3
"""Set up SirHurt in one pass: exclusions, repair, runtimes, Roblox build, launch stack.

Automates stages 1-3 of https://sirhurt.pages.dev/guide/:

* scans the folder you started it from and the folder the exe lives in for a
  SirHurt archive, moves it into the install folder (validated to be outside
  OneDrive and Program Files), adds a Windows Defender exclusion for that
  folder, then extracts the archive - a gofile download is the SirHurt folder
  itself while a Box share wraps it in another zip, which is unpacked too;
* runs the system-repair chain (SFC, then DISM CheckHealth/ScanHealth/RestoreHealth);
* installs both Visual C++ redistributables and the .NET Framework 4.8.1 web
  installer;
* resolves the published Windows build through Roblox's deployment API, then
  downloads `rbxPkgManifest.txt` and every package it lists from Roblox's CDN
  and unpacks them into %LOCALAPPDATA%\\Roblox\\Versions\\version-<hash> - the
  same walk RDD does at /rdd/, so the client SirHurt injects into is the
  latest build without a separate version manager (`--roblox-version` pins one,
  `--roblox-channel` follows a non-LIVE channel);
* downloads the SirHurt Cleaner (the standalone CLI zip the Sirstrap releases
  publish) and can run it from the same pass (`--run-cleaner`), answering `y` to
  every prompt so old Roblox/SirHurt files and stored login data are gone before
  the install;
* otherwise SirHurt needs the single-use link you get from sirhurt.net after
  logging in - a gofile.io folder or a Box share;
* turns off "Launch at startup" and "Minimize to tray when closed" in Roblox's
  %LOCALAPPDATA%\\Roblox\\LocalStorage\\appStorage.json.

Started with no switches from a console it first asks six yes/no questions (repair,
exclusion, Roblox build, Cleaner, Roblox settings, reboot) and prints the resulting plan;
`--no-survey` keeps the defaults and any stage switch skips the questions. When the
SirHurt archive isn't found it offers a rescan loop instead of giving up, and the
end of a run writes `<install folder>\\README.txt` with the next steps before it
optionally schedules a 60-second reboot.

The install folder defaults to SirHurt inside Downloads, then Desktop, then
Documents - the first one Windows reports as not synced to OneDrive - so it is
easy to find. When the script isn't already elevated it re-launches itself
through the UAC prompt before doing anything.

Only the public download link is handled - no credentials are read or stored.
Requires Python 3.10+ and builds with Nuitka (see build.ps1 next to this file).
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
import zipfile
from pathlib import Path

__version__ = "1.2.0"

# The Cleaner is only published inside the Sirstrap releases; this endpoint
# always answers with the newest SirHurt.Cleaner.CLI.zip, so no tag lookup.
CLEANER_URL = "https://www.sirstrap.com/releases/download.php?file=SirHurt.Cleaner.CLI.zip"
CLEANER_ASSET = "SirHurt.Cleaner.CLI.zip"
CLEANER_FOLDER = "cleaner"
# Roblox deployment download, mirroring RDD (/rdd/): the settings API reports the
# build that is actually published, the CDN serves its manifest and packages.
ROBLOX_SETTINGS_API = "https://clientsettingscdn.roblox.com"
ROBLOX_CDN = "https://setup-aws.rbxcdn.com"
ROBLOX_BINARY_TYPE = "WindowsPlayer"
ROBLOX_DEFAULT_CHANNEL = "LIVE"
ROBLOX_MANIFEST_SUFFIX = "-rbxPkgManifest.txt"
# RobloxApp.zip unpacks into the version folder itself; every other package stays
# the zip the client reads, which is the split RDD uses too.
ROBLOX_UNPACKED_PACKAGES = frozenset({"RobloxApp.zip"})
ROBLOX_PLAYER_EXE = "RobloxPlayerBeta.exe"
ROBLOX_APP_SETTINGS = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    "<Settings>\n"
    "    <ContentFolder>content</ContentFolder>\n"
    "    <BaseUrl>http://www.roblox.com</BaseUrl>\n"
    "</Settings>\n"
)
# name, md5, compressed size, uncompressed size
MANIFEST_ENTRY_LINES = 4
# The thank-you page (DOTNET481_PAGE) is HTML; its "download manually" link is
# this fwlink, which resolves to NDP481-Web.exe.
DOTNET481_PAGE = "https://dotnet.microsoft.com/en-us/download/dotnet-framework/thank-you/net481-web-installer"
DOTNET481_WEB_INSTALLER = "https://go.microsoft.com/fwlink/?LinkId=2203304"
RUNTIMES = (
    ("vc_redist.x86.exe", "https://aka.ms/vc14/vc_redist.x86.exe", ("/install", "/quiet", "/norestart")),
    ("vc_redist.x64.exe", "https://aka.ms/vc14/vc_redist.x64.exe", ("/install", "/quiet", "/norestart")),
    ("NDP481-Web.exe", DOTNET481_WEB_INSTALLER, ("/q", "/norestart")),
)
RUNTIME_OK_CODES = frozenset({0, 1638, 3010})
REPAIR_CHAIN = (
    ("SFC scan", "sfc.exe", ("/scannow",)),
    ("DISM CheckHealth", "dism.exe", ("/Online", "/Cleanup-Image", "/CheckHealth")),
    ("DISM ScanHealth", "dism.exe", ("/Online", "/Cleanup-Image", "/ScanHealth")),
    ("DISM RestoreHealth", "dism.exe", ("/Online", "/Cleanup-Image", "/RestoreHealth")),
)
ROBLOX_STORAGE_PARTS = ("Roblox", "LocalStorage", "appStorage.json")
ROBLOX_VERSIONS_PARTS = ("Roblox", "Versions")
ROBLOX_SETTINGS = {"LaunchAtStartup": "false", "MinimizeToTray": "false"}
# Install-folder parents, in order of preference. Resolved through the shell so
# a OneDrive folder-redirect is visible rather than guessed at.
FOLDERID_DOWNLOADS = "{374DE290-123F-4565-9164-39C4925E467B}"
FOLDERID_DESKTOP = "{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}"
FOLDERID_DOCUMENTS = "{FDD39AD0-238F-46AF-ADB4-6C85480369C7}"
PREFERRED_INSTALL_PARENTS = (FOLDERID_DOWNLOADS, FOLDERID_DESKTOP, FOLDERID_DOCUMENTS)
PARENT_FALLBACK_NAMES = {
    FOLDERID_DOWNLOADS: "Downloads",
    FOLDERID_DESKTOP: "Desktop",
    FOLDERID_DOCUMENTS: "Documents",
}
ONEDRIVE_ENV_VARS = ("OneDrive", "OneDriveConsumer", "OneDriveCommercial")
INSTALL_FOLDER_NAME = "SirHurt"
GOFILE_RE = re.compile(r"^https?://(?:www\.)?gofile\.io/d/([A-Za-z0-9]{6,})$", re.I)
BOX_RE = re.compile(r"^https?://(?:www\.)?app\.box\.com/s/([A-Za-z0-9]{8,})$", re.I)
ARCHIVE_SUFFIXES = (".zip", ".7z", ".rar")
USER_AGENT = "SirHurtSetup/1.0 (+https://sirhurt.pages.dev)"

GOFILE_API = "https://api.gofile.io"
HTTP_TIMEOUT = 30
WINDOWS_24H2_BUILD = 26100
CHUNK_SIZE = 1 << 16


class SetupError(RuntimeError):
    """A failure the user can act on; reported without a traceback."""


def info(message: str) -> None:
    print(message, flush=True)


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr, flush=True)


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #


def http_bytes(url: str, data: bytes | None = None, headers: dict[str, str] | None = None) -> bytes:
    request_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(
        url,
        data=data,
        headers=request_headers,
        method="POST" if data is not None else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise SetupError(f"HTTP {exc.code} from {url}") from exc
    except urllib.error.URLError as exc:
        raise SetupError(f"cannot reach {url}: {exc.reason}") from exc
    except (TimeoutError, OSError) as exc:
        raise SetupError(f"network error talking to {url}: {exc}") from exc


def http_json(url: str, data: bytes | None = None, headers: dict[str, str] | None = None) -> object:
    raw = http_bytes(url, data, headers)
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SetupError(f"malformed JSON from {url}") from exc


def http_text(url: str) -> str:
    return http_bytes(url).decode("utf-8", "replace")


def download(url: str, destination: Path) -> None:
    """Stream url into destination, writing through a .part file."""
    if not url:
        raise SetupError("the download URL was empty")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
            expected = int(response.headers.get("Content-Length") or 0)
            written = 0
            with open(partial, "wb") as handle:
                while True:
                    chunk = response.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    handle.write(chunk)
                    written += len(chunk)
        if expected and written != expected:
            raise SetupError(f"incomplete download from {url}: {written} of {expected} bytes")
        os.replace(partial, destination)
    except SetupError:
        partial.unlink(missing_ok=True)
        raise
    except urllib.error.HTTPError as exc:
        partial.unlink(missing_ok=True)
        raise SetupError(f"HTTP {exc.code} from {url}") from exc
    except urllib.error.URLError as exc:
        partial.unlink(missing_ok=True)
        raise SetupError(f"cannot reach {url}: {exc.reason}") from exc
    except (TimeoutError, OSError) as exc:
        partial.unlink(missing_ok=True)
        raise SetupError(f"network error downloading {url}: {exc}") from exc
    except BaseException:
        partial.unlink(missing_ok=True)
        raise


# --------------------------------------------------------------------------- #
# Archives
# --------------------------------------------------------------------------- #


def safe_extract_zip(archive: Path, destination: Path) -> None:
    """Extract archive into destination, refusing absolute, .., and symlink entries."""
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            name = member.filename.replace("\\", "/")
            parts = [part for part in name.split("/") if part not in ("", ".")]
            if name.startswith("/") or (len(name) > 1 and name[1] == ":"):
                raise SetupError(f"refusing absolute path {member.filename!r} in {archive.name}")
            if any(part == ".." for part in parts):
                raise SetupError(f"refusing path with '..' in {archive.name}: {member.filename!r}")
            if member.is_dir():
                (root.joinpath(*parts) if parts else root).mkdir(parents=True, exist_ok=True)
                continue
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                warn(f"skipping symlink {member.filename!r} in {archive.name}")
                continue
            target = root.joinpath(*parts) if parts else root
            if root not in target.resolve().parents and target.resolve() != root:
                raise SetupError(f"refusing to write outside {root}: {member.filename!r}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(member) as source, open(target, "wb") as sink:
                shutil.copyfileobj(source, sink)


def copy_into(source: Path, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    if source.parent.resolve() == folder.resolve():
        return source
    destination = folder / source.name
    shutil.copy2(source, destination)
    return destination


# --------------------------------------------------------------------------- #
# Preflight and target folder
# --------------------------------------------------------------------------- #


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        return False


def windows_build() -> int | None:
    get_version = getattr(sys, "getwindowsversion", None)
    if get_version is None:
        return None
    try:
        return int(get_version().build)
    except (AttributeError, OSError):
        return None


def preflight() -> None:
    if not sys.platform.startswith("win"):
        raise SetupError("this script only runs on Windows")
    if not is_admin():
        warn(
            "not running as Administrator - the exclusion, SFC and DISM stages will refuse "
            "to run until you elevate"
        )
    build = windows_build()
    if build is not None and build < WINDOWS_24H2_BUILD:
        warn(
            f"Windows build {build} detected; the guide targets Windows 11 24H2 "
            f"(build {WINDOWS_24H2_BUILD}) or newer"
        )


def require_admin(reason: str) -> None:
    if not is_admin():
        raise SetupError(
            f"run this script as Administrator to {reason} (or skip that stage)"
        )


def relaunch_target() -> Path:
    """The executable the user actually launched - not Nuitka's %TEMP% payload."""
    if not is_compiled():
        return Path(sys.executable)
    for candidate in (os.environ.get("NUITKA_ONEFILE_BINARY"), sys.argv[0], sys.executable):
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        try:
            if path.is_file() and not is_unpack_folder(path.parent):
                return path.resolve()
        except OSError:
            continue
    return Path(sys.executable)


def elevate(argv: list[str]) -> bool:
    """Relaunch this script/exe elevated through UAC; True when that copy started."""
    executable = relaunch_target()
    arguments = list(argv) if is_compiled() else [str(Path(__file__).resolve()), *argv]
    parameters = subprocess.list2cmdline([*arguments, "--elevated"])
    try:
        shell_execute = ctypes.windll.shell32.ShellExecuteW  # type: ignore[attr-defined]
        result = shell_execute(None, "runas", str(executable), parameters, str(Path.cwd()), 1)
    except (AttributeError, OSError) as exc:
        warn(f"cannot request Administrator rights: {exc}")
        return False
    if result <= 32:
        detail = "the UAC prompt was declined" if result == 5 else f"ShellExecuteW returned {result}"
        warn(f"could not start {executable.name} elevated: {detail}")
        return False
    return True


def should_elevate(argv: list[str]) -> bool:
    if not sys.platform.startswith("win") or is_admin() or "--elevated" in argv:
        return False
    # Help, version and dry runs write nothing, so they don't need the prompt.
    return not any(flag in argv for flag in ("-h", "--help", "--version", "--dry-run"))


class _GUID(ctypes.Structure):
    _fields_ = (
        ("Data1", ctypes.c_uint32),
        ("Data2", ctypes.c_uint16),
        ("Data3", ctypes.c_uint16),
        ("Data4", ctypes.c_ubyte * 8),
    )


def known_folder(folder_id: str) -> Path | None:
    """Resolve a shell KNOWNFOLDERID, so OneDrive redirections show up as-is."""
    if not sys.platform.startswith("win"):
        return None
    try:
        guid = _GUID.from_buffer_copy(uuid.UUID(folder_id).bytes_le)
        path = ctypes.c_wchar_p()
        result = ctypes.windll.shell32.SHGetKnownFolderPath(  # type: ignore[attr-defined]
            ctypes.byref(guid), 0, None, ctypes.byref(path)
        )
    except (AttributeError, OSError, ValueError):
        return None
    if result != 0 or not path.value:
        return None
    try:
        return Path(path.value)
    finally:
        ctypes.windll.ole32.CoTaskMemFree(ctypes.cast(path, ctypes.c_void_p))  # type: ignore[attr-defined]


def is_onedrive_path(candidate: Path) -> bool:
    cased = os.path.normcase(os.path.abspath(candidate))
    roots = [Path.home() / "OneDrive"]
    for key in ONEDRIVE_ENV_VARS:
        value = os.environ.get(key)
        if value:
            roots.append(Path(value))
    for root in roots:
        root_cased = os.path.normcase(os.path.abspath(root))
        if cased == root_cased or cased.startswith(root_cased + os.sep):
            return True
    return any(part.lower().startswith("onedrive") for part in candidate.parts)


def default_target() -> Path:
    """SirHurt under Downloads, Desktop or Documents - whichever isn't OneDrive."""
    for folder_id in PREFERRED_INSTALL_PARENTS:
        parent = known_folder(folder_id) or (Path.home() / PARENT_FALLBACK_NAMES[folder_id])
        if is_onedrive_path(parent):
            warn(f"skipping {parent} - it is synced to OneDrive")
            continue
        return parent / INSTALL_FOLDER_NAME
    return Path.home() / INSTALL_FOLDER_NAME


def protected_roots() -> list[Path]:
    roots: list[Path] = []
    for key in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"):
        value = os.environ.get(key)
        if value:
            roots.append(Path(value))
    drive = os.environ.get("SystemDrive", "C:")
    roots.append(Path(f"{drive}\\Program Files"))
    roots.append(Path(f"{drive}\\Program Files (x86)"))
    return roots


def validate_target(target: Path) -> None:
    candidate = Path(os.path.abspath(target.expanduser()))
    cased = os.path.normcase(str(candidate))
    if is_onedrive_path(candidate):
        raise SetupError(f"refusing to install into a OneDrive-synced folder: {candidate}")
    for root in protected_roots():
        root_cased = os.path.normcase(os.path.abspath(root))
        if cased == root_cased or cased.startswith(root_cased + os.sep):
            raise SetupError(f"refusing to install into a protected system folder: {candidate}")


def resolve_target(raw: str | None, *, dry_run: bool) -> Path:
    if raw:
        target = Path(raw).expanduser()
    else:
        default = default_target()
        if dry_run:
            target = default
        else:
            answer = input(f"Where should SirHurt live? [default: {default}]: ").strip().strip('"')
            target = Path(answer).expanduser() if answer else default
    validate_target(target)
    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)
    info(f"target folder: {target}")
    return target


# --------------------------------------------------------------------------- #
# Survey
# --------------------------------------------------------------------------- #

SURVEY_QUESTIONS = (
    ("repair", "do you want to run system corruption scans?", False),
    ("exclusions", "do you want to add an exclusion for the sirhurt folder?", True),
    (
        "roblox_build",
        "do you want to download the latest Roblox build into %LOCALAPPDATA%\\Roblox\\Versions?",
        True,
    ),
    (
        "cleaner",
        "do you want to download and clean current sirhurt configuration(s) via sirhurt cleaner?",
        True,
    ),
    (
        "roblox_settings",
        "do you want to turn off launch at start and minimize to tray to avoid possible injection issues?",
        True,
    ),
    ("reboot", "do you want to automatically reboot your PC?", False),
)
SURVEY_OPTOUT_FLAGS = frozenset({
    "--skip-roblox-build",
    "--roblox-version",
    "--roblox-channel",
    "--skip-sirhurt",
    "--skip-exclusions",
    "--skip-repair",
    "--skip-runtimes",
    "--skip-roblox-settings",
    "--run-cleaner",
    "--reboot",
    "--no-survey",
    "--dry-run",
})


def has_stage_flag(argv: list[str]) -> bool:
    """True when argv already chooses stages, so the survey must not run."""
    return any(argument.split("=", 1)[0] in SURVEY_OPTOUT_FLAGS for argument in argv)


def should_survey(argv: list[str]) -> bool:
    return not has_stage_flag(argv) and sys.stdin is not None and sys.stdin.isatty()


def ask_yes_no(question: str, default: bool) -> bool:
    suffix = "Y/n" if default else "y/N"
    while True:
        try:
            raw = input(f"{question} {suffix}: ").strip().lower()
        except EOFError:
            return default
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        info("  please answer y or n")


def apply_survey(args: argparse.Namespace) -> None:
    info("\nAnswer six questions to pick the stages (--help lists every switch).")
    answers = {key: ask_yes_no(question, default) for key, question, default in SURVEY_QUESTIONS}
    args.skip_repair = not answers["repair"]
    args.skip_exclusions = not answers["exclusions"]
    args.skip_roblox_build = not answers["roblox_build"]
    args.skip_roblox_settings = not answers["roblox_settings"]
    args.run_cleaner = answers["cleaner"]
    args.reboot = answers["reboot"]


def survey_plan(args: argparse.Namespace) -> str:
    stages = []
    if not args.skip_exclusions:
        stages.append("exclusion")
    if not args.skip_repair:
        stages.append("repair")
    if not args.skip_runtimes:
        stages.append("runtimes")
    if not args.skip_roblox_build:
        stages.append("roblox build")
    if args.run_cleaner:
        stages.append("cleaner")
    if not args.skip_sirhurt:
        stages.append("sirhurt")
    if not args.skip_roblox_settings:
        stages.append("roblox settings")
    if args.reboot:
        stages.append("reboot")
    return ", ".join(stages) or "nothing"


# --------------------------------------------------------------------------- #
# Local SirHurt archive, Defender exclusion, repair, runtimes
# --------------------------------------------------------------------------- #


def is_compiled() -> bool:
    return "__compiled__" in globals() or bool(getattr(sys, "frozen", False))


def is_unpack_folder(folder: Path) -> bool:
    """True for Nuitka/PyInstaller onefile scratch dirs (%TEMP%\\onefile_*, %TEMP%\\_MEI*)."""
    return any(part.lower().startswith(("onefile_", "_mei")) for part in folder.parts)


def script_directory() -> Path:
    """Where the exe (or script) really lives - onefile extracts itself to %TEMP%."""
    if not is_compiled():
        return Path(__file__).resolve().parent
    candidates = (os.environ.get("NUITKA_ONEFILE_BINARY"), sys.argv[0], sys.executable)
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        try:
            if path.is_file() and not is_unpack_folder(path.parent):
                return path.resolve().parent
        except OSError:
            continue
    return Path.cwd()


def search_directories() -> list[Path]:
    """Folders to look for the archive in: where you are, then where the exe is."""
    folders: list[Path] = []
    for folder in (Path.cwd(), script_directory()):
        try:
            resolved = folder.resolve()
        except OSError:
            continue
        if resolved not in folders:
            folders.append(resolved)
    return folders


def find_local_archive(folders: list[Path]) -> Path | None:
    """Newest archive in any of folders whose name mentions SirHurt."""
    found: list[tuple[float, Path]] = []
    for folder in folders:
        try:
            entries = list(folder.iterdir())
        except OSError as exc:
            warn(f"cannot scan {folder}: {exc}")
            continue
        for entry in entries:
            if not entry.is_file() or entry.suffix.lower() not in ARCHIVE_SUFFIXES:
                continue
            if "sirhurt" not in entry.name.lower():
                continue
            try:
                found.append((entry.stat().st_mtime, entry))
            except OSError:
                continue
    if not found:
        return None
    found.sort(key=lambda item: item[0], reverse=True)
    for _, extra in found[1:]:
        info(f"  ignoring {extra.name} (using the newest archive, {found[0][1].name})")
    return found[0][1]


def prompt_for_archive(folders: list[Path]) -> Path | None:
    """Ask for the SirHurt archive; Enter rescans, 's' skips SirHurt."""
    info("\nSirHurt isn't detected in the current folder or next to the executable.")
    info(f"  looked in: {', '.join(str(folder) for folder in folders)}")
    info("  move it to the same folder as the executable, or paste the direct path.")
    info("  download it from https://sirhurt.net/login/download.php if you don't have it yet.")
    while True:
        try:
            raw = input("archive path (Enter = look again, 's' = skip SirHurt): ").strip()
        except EOFError:
            return None
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
            raw = raw[1:-1].strip()
        if not raw:
            found = find_local_archive(folders)
            if found is not None:
                info(f"  found {found}")
                return found
            info(f"  still nothing in {', '.join(str(folder) for folder in folders)}")
            continue
        if raw.lower() in ("s", "skip"):
            info("  skipping SirHurt - everything else still runs")
            return None
        candidate = Path(raw).expanduser()
        if candidate.is_dir():
            found = find_local_archive([candidate])
            if found is not None:
                info(f"  found {found}")
                return found
            info(f"  no SirHurt .zip/.7z/.rar in {candidate}")
            continue
        if candidate.is_file():
            return candidate
        info(f"  not a file: {candidate}")


def adopt_local_archive(archive: Path, target: Path, *, dry_run: bool) -> None:
    """Move a SirHurt archive out of the script folder and extract it into target."""
    downloads = target / "downloads"
    info(f"\n[SirHurt] local archive {archive}")
    info(f"  secluded folder: {target}")
    info(f"  target: {target / 'sirhurt'}")
    if dry_run:
        info(f"  would move it to {downloads} and extract it")
        return
    downloads.mkdir(parents=True, exist_ok=True)
    if archive.parent.resolve() == downloads.resolve():
        destination = archive
    else:
        destination = downloads / archive.name
        try:
            shutil.move(str(archive), str(destination))
        except OSError as exc:
            raise SetupError(f"cannot move {archive} to {destination}: {exc}") from exc
        info(f"  moved to {destination}")
    extract_sirhurt(destination, target)


def powershell(script: str, *, timeout: float | None = 120) -> subprocess.CompletedProcess[str]:
    shell = shutil.which("powershell") or shutil.which("pwsh")
    if shell is None:
        raise SetupError("PowerShell was not found; set the exclusion up by hand")
    try:
        return subprocess.run(
            [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise SetupError("PowerShell timed out") from exc
    except OSError as exc:
        raise SetupError(f"cannot run PowerShell: {exc}") from exc


def same_folder(left: str, right: Path) -> bool:
    def normalise(value: str) -> str:
        return os.path.normcase(os.path.abspath(value)).rstrip("\\/")

    return normalise(left) == normalise(str(right))


def defender_exclusions() -> list[str]:
    result = powershell("@((Get-MpPreference).ExclusionPath) | ForEach-Object { $_ }")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip() or f"exit code {result.returncode}"
        raise SetupError(detail)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def add_defender_exclusion(folder: Path, *, dry_run: bool) -> bool:
    """Add the exclusion; True when it is (or would be) in place."""
    info(f"\n[Exclusion] {folder}")
    if dry_run:
        info("  would add a Windows Defender folder exclusion")
        return True
    require_admin("add the Defender exclusion")
    try:
        if any(same_folder(entry, folder) for entry in defender_exclusions()):
            info("  already excluded")
            return True
    except SetupError as exc:
        warn(f"cannot read Defender's exclusion list ({exc}); trying to add it anyway")
    quoted = str(folder).replace("'", "''")
    result = powershell(f"Add-MpPreference -ExclusionPath '{quoted}' -ErrorAction Stop")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip() or f"exit code {result.returncode}"
        warn(f"could not add the exclusion ({detail}); add {folder} in Windows Security by hand")
        return False
    try:
        verified = any(same_folder(entry, folder) for entry in defender_exclusions())
    except SetupError:
        verified = False
    info("  added and verified" if verified else "  added (Windows Security may take a moment to list it)")
    return verified


def repair_system_files(*, dry_run: bool) -> bool:
    """Run SFC and DISM; True only when a tool asked for a reboot."""
    info("\n[Repair] Windows component store")
    info("  this is the slow part - SFC and DISM each take several minutes")
    for name, executable, arguments in REPAIR_CHAIN:
        info(f"  ==> {name}: {executable} {' '.join(arguments)}")
    if dry_run:
        return False
    require_admin("run SFC and DISM")
    needs_reboot = False
    for name, executable, arguments in REPAIR_CHAIN:
        try:
            result = subprocess.run([executable, *arguments], check=False)
        except OSError as exc:
            raise SetupError(f"cannot run {executable}: {exc}") from exc
        if result.returncode == 3010:
            needs_reboot = True
        elif result.returncode != 0:
            raise SetupError(
                f"{name} failed with exit code {result.returncode}; "
                "repair the component store before installing SirHurt"
            )
    info(
        "  repair chain finished; reboot before the first launch"
        if needs_reboot
        else "  repair chain finished (no reboot needed)"
    )
    return needs_reboot


def install_runtimes(*, dry_run: bool) -> bool:
    """Install VC++ and .NET; True only when an installer asked for a reboot."""
    info("\n[Runtimes] Visual C++ x86, Visual C++ x64, .NET Framework 4.8.1")
    for name, url, arguments in RUNTIMES:
        info(f"  {name}: {url} {' '.join(arguments)}")
    if dry_run:
        return False
    codes: list[int] = []
    with tempfile.TemporaryDirectory(prefix="sirhurt-runtimes-") as scratch:
        for name, url, arguments in RUNTIMES:
            info(f"\n  {name}: downloading")
            installer = Path(scratch) / name
            download(url, installer)
            info(f"  {name}: installing ({' '.join(arguments)})")
            try:
                result = subprocess.run([str(installer), *arguments], check=False)
            except OSError as exc:
                raise SetupError(f"cannot run {name}: {exc}") from exc
            codes.append(result.returncode)
            if result.returncode == 1638:
                info("    a newer version is already installed")
            elif result.returncode == 3010:
                warn(f"    {name} installed; it needs a reboot to finish")
            elif result.returncode not in RUNTIME_OK_CODES:
                raise SetupError(f"{name} failed with exit code {result.returncode}")
    needs_reboot = 3010 in codes
    if needs_reboot:
        info("  runtimes installed; reboot before the first launch")
    elif all(code == 1638 for code in codes):
        info("  runtimes already up to date (no reboot needed)")
    else:
        info("  runtimes installed (no reboot needed)")
    return needs_reboot


# --------------------------------------------------------------------------- #
# Roblox deployment (what RDD does, without the browser)
# --------------------------------------------------------------------------- #


def roblox_versions_root() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise SetupError("LOCALAPPDATA is not set; cannot find Roblox's Versions folder")
    return Path(local).joinpath(*ROBLOX_VERSIONS_PARTS)


def resolve_roblox_version(channel: str) -> str:
    """The published WindowsPlayer build - the hash RDD resolves before downloading.

    Roblox's settings API reports the build that is actually on the CDN; the
    CDN's own version file can point at one that is staged but not yet served.
    """
    name = channel.strip() or ROBLOX_DEFAULT_CHANNEL
    url = f"{ROBLOX_SETTINGS_API}/v2/client-version/{ROBLOX_BINARY_TYPE}"
    if name.upper() not in ("LIVE", "PRODUCTION"):
        url += f"/channel/{urllib.parse.quote(name, safe='')}"
    payload = http_json(url)
    if not isinstance(payload, dict):
        raise SetupError(f"unexpected response from {url}")
    version = str(payload.get("clientVersionUpload") or "").strip().lower()
    if not version:
        raise SetupError(f"{url} reported no clientVersionUpload")
    return version if version.startswith("version-") else f"version-{version}"


def parse_pkg_manifest(body: str) -> list[tuple[str, str, int]]:
    """(name, md5, compressed size) for every package in an rbxPkgManifest v0."""
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    if not lines or lines[0] != "v0":
        raise SetupError(
            f"unrecognised rbxPkgManifest header: {lines[0] if lines else '(empty response)'}"
        )
    packages: list[tuple[str, str, int]] = []
    for start in range(1, len(lines) - MANIFEST_ENTRY_LINES + 1, MANIFEST_ENTRY_LINES):
        name, md5 = lines[start], lines[start + 1].lower()
        # RobloxPlayerInstaller.exe is listed too; only the zips are packages.
        if not name.lower().endswith(".zip"):
            continue
        try:
            size = int(lines[start + 2])
        except ValueError:
            size = 0
        packages.append((name, md5, size))
    if not any(name in ROBLOX_UNPACKED_PACKAGES for name, _, _ in packages):
        raise SetupError("rbxPkgManifest lists no RobloxApp.zip - the deployment layout changed")
    return packages


def verify_package(path: Path, md5: str, size: int) -> None:
    """The manifest carries the md5 and the compressed size of every package."""
    actual = path.stat().st_size
    if size and actual != size:
        raise SetupError(f"{path.name} is {actual} bytes; the manifest lists {size}")
    digest = hashlib.md5(usedforsecurity=False)  # md5 is what the manifest publishes
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    if digest.hexdigest() != md5:
        raise SetupError(f"{path.name} failed verification (md5 {digest.hexdigest()} != {md5})")


def install_roblox_build(
    versions_root: Path,
    *,
    version: str | None,
    channel: str,
    dry_run: bool,
) -> Path:
    """Unpack the latest (or pinned) deployment into Versions\\version-<hash>."""
    resolved = (version or "").strip().lower() or resolve_roblox_version(channel)
    if not resolved.startswith("version-"):
        resolved = f"version-{resolved}"
    destination = versions_root / resolved
    manifest_url = f"{ROBLOX_CDN}/{resolved}{ROBLOX_MANIFEST_SUFFIX}"
    info(f"\n[Roblox build] {resolved}")
    info(f"  build:  {ROBLOX_BINARY_TYPE} on {channel.strip() or ROBLOX_DEFAULT_CHANNEL}")
    info(f"  cdn:    {manifest_url}")
    info(f"  target: {destination}")
    if (destination / ROBLOX_PLAYER_EXE).is_file():
        info(f"  already installed ({ROBLOX_PLAYER_EXE} is there); leaving it alone")
        return destination
    try:
        packages = parse_pkg_manifest(http_text(manifest_url))
    except SetupError as exc:
        raise SetupError(
            f"cannot read the manifest for {resolved} ({exc}) - the build may not be "
            "published on that channel yet; retry, or drop --roblox-version"
        ) from exc
    total = sum(size for _, _, size in packages)
    info(f"  packages: {len(packages)} ({total / (1 << 20):.1f} MiB)")
    if dry_run:
        for name, _, size in packages:
            info(f"  would download {name} ({size / (1 << 20):.1f} MiB)")
        info(f"  would unpack RobloxApp.zip into {destination} and keep the rest zipped")
        return destination
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sirhurt-roblox-") as scratch:
        for index, (name, md5, size) in enumerate(packages, start=1):
            info(f"  [{index}/{len(packages)}] {name} ({size / (1 << 20):.1f} MiB)")
            blob = Path(scratch) / name
            download(f"{ROBLOX_CDN}/{resolved}-{name}", blob)
            verify_package(blob, md5, size)
            if name in ROBLOX_UNPACKED_PACKAGES:
                safe_extract_zip(blob, destination)
            else:
                shutil.copy2(blob, destination / name)
    (destination / "AppSettings.xml").write_text(ROBLOX_APP_SETTINGS, encoding="utf-8")
    if not (destination / ROBLOX_PLAYER_EXE).is_file():
        raise SetupError(f"{destination} has no {ROBLOX_PLAYER_EXE} - the deployment layout changed")
    info(f"  installed {ROBLOX_PLAYER_EXE} into {destination}")
    return destination


# --------------------------------------------------------------------------- #
# SirHurt Cleaner
# --------------------------------------------------------------------------- #


def cleaner_executable(target: Path) -> Path | None:
    folder = target / CLEANER_FOLDER
    if not folder.is_dir():
        return None
    for executable in sorted(folder.rglob("*.exe")):
        if "cleaner" in executable.name.lower():
            return executable
    return None


def install_cleaner(target: Path, *, dry_run: bool) -> None:
    """Fetch the standalone Cleaner zip and unpack it into <target>\\cleaner."""
    if cleaner_executable(target) is not None:
        return
    destination = target / CLEANER_FOLDER
    info(f"\n[Cleaner] {CLEANER_ASSET}")
    info(f"  url:    {CLEANER_URL}")
    info(f"  target: {destination}")
    if dry_run:
        return
    with tempfile.TemporaryDirectory(prefix="sirhurt-setup-") as scratch:
        archive = Path(scratch) / CLEANER_ASSET
        download(CLEANER_URL, archive)
        if not zipfile.is_zipfile(archive):
            raise SetupError(
                f"{CLEANER_ASSET} did not download as a zip archive - "
                "the release layout may have changed"
            )
        safe_extract_zip(archive, destination)
    executables = sorted(path.name for path in destination.rglob("*.exe"))
    info(f"  extracted: {', '.join(executables) if executables else '(no .exe found)'}")


def run_sirhurt_cleaner(target: Path, *, dry_run: bool) -> None:
    """Run SirHurt Cleaner non-interactively: 'y' to every prompt, per the guide."""
    info("\n[Cleaner] SirHurt / Roblox leftovers")
    executable = cleaner_executable(target)
    if executable is None:
        if dry_run:
            info(f"  would run the Cleaner from {target / CLEANER_FOLDER} (downloaded if missing)")
            return
        raise SetupError(f"SirHurt Cleaner isn't in {target / CLEANER_FOLDER}")
    if dry_run:
        info(f"  would run {executable} (deletes Roblox/SirHurt configs and stored login data)")
        return
    require_admin("run the SirHurt Cleaner")
    info(f"  {executable}")
    info("  answering y to every prompt; stored SirHurt login data is deleted")
    try:
        # stdin is a pipe, so the Cleaner's own prompts take these answers and its
        # "Press any key to exit" is skipped (Console.IsInputRedirected).
        result = subprocess.run(
            [str(executable)], input="y\n" * 8, text=True, cwd=str(executable.parent), check=False
        )
    except OSError as exc:
        raise SetupError(f"cannot run {executable}: {exc}") from exc
    if result.returncode != 0:
        warn(f"SirHurt Cleaner exited with code {result.returncode}; some leftovers may remain")


# --------------------------------------------------------------------------- #
# SirHurt link
# --------------------------------------------------------------------------- #


def classify_link(raw: str) -> tuple[str, str, str]:
    url = raw.strip().strip('"')
    match = GOFILE_RE.match(url)
    if match:
        return "gofile", match.group(1), url
    match = BOX_RE.match(url)
    if match:
        return "box", match.group(1), url
    raise SetupError(
        "unrecognised link - expected https://gofile.io/d/XXXXXX or https://app.box.com/s/XXXXXX"
    )


def resolve_sirhurt_link(explicit: str | None, *, dry_run: bool) -> tuple[str, str, str] | None:
    if explicit:
        return classify_link(explicit)
    if dry_run:
        info("\n[SirHurt] no --link given; you'd be prompted for the sirhurt.net download link at run time")
        return None
    while True:
        raw = input(
            "\nPaste your SirHurt download link from sirhurt.net/login/download.php\n"
            "(gofile.io/d/... or app.box.com/s/..., or 'q' to cancel): "
        )
        if raw.strip().lower() == "q":
            info("cancelled - the Roblox build is installed, SirHurt was skipped")
            return None
        try:
            return classify_link(raw)
        except SetupError as exc:
            info(f"  {exc}")


def gofile_guest_token() -> str:
    payload = http_json(f"{GOFILE_API}/accounts", data=b"", headers={"Content-Type": "application/json"})
    if not isinstance(payload, dict) or payload.get("status") != "ok":
        raise SetupError("gofile refused a guest account")
    token = (payload.get("data") or {}).get("token")
    if not token:
        raise SetupError("gofile returned no guest token")
    return str(token)


def gofile_contents(folder_id: str, token: str, password: str | None = None) -> dict:
    query = {"token": token}
    if password is not None:
        query["password"] = hashlib.sha256(password.encode("utf-8")).hexdigest()
    payload = http_json(f"{GOFILE_API}/contents/{folder_id}?{urllib.parse.urlencode(query)}")
    if not isinstance(payload, dict):
        raise SetupError("gofile returned an unexpected response")
    return payload


def gofile_download(folder_id: str, downloads: Path) -> Path:
    token = gofile_guest_token()
    payload = gofile_contents(folder_id, token)
    if payload.get("status") == "error-password":
        password = input("  this gofile link is password protected. Password: ")
        payload = gofile_contents(folder_id, token, password=password)
    status = payload.get("status")
    if status != "ok":
        raise SetupError(f"gofile returned {status or 'an unknown status'}")
    children = (payload.get("data") or {}).get("children") or {}
    candidates = [
        child
        for child in children.values()
        if isinstance(child, dict) and str(child.get("name") or "").lower().endswith(ARCHIVE_SUFFIXES)
    ]
    if not candidates:
        raise SetupError("that gofile folder contains no .zip, .7z or .rar file")
    best = max(candidates, key=lambda child: int(child.get("size") or 0))
    name = Path(str(best.get("name") or "sirhurt.zip")).name
    destination = downloads / name
    info(f"  downloading {name} ...")
    download(str(best.get("link") or ""), destination)
    return destination


def download_scan_folders() -> list[Path]:
    """Where a browser might have saved the archive, honouring folder redirection."""
    folders: list[Path] = []
    for folder_id, fallback in (
        (FOLDERID_DOWNLOADS, "Downloads"),
        (FOLDERID_DESKTOP, "Desktop"),
    ):
        resolved = known_folder(folder_id) or (Path.home() / fallback)
        if resolved not in folders:
            folders.append(resolved)
    return folders


def newest_archive(started: float) -> Path | None:
    found: list[tuple[float, Path]] = []
    for folder in download_scan_folders():
        if not folder.is_dir():
            continue
        try:
            entries = list(folder.iterdir())
        except OSError:
            continue
        for entry in entries:
            if not entry.is_file() or not entry.name.lower().endswith(ARCHIVE_SUFFIXES):
                continue
            try:
                modified = entry.stat().st_mtime
            except OSError:
                continue
            if modified + 1 < started:
                continue
            found.append((modified, entry))
    return max(found, key=lambda item: item[0])[1] if found else None


def browser_handoff(url: str, downloads: Path, reason: str) -> Path:
    warn(f"{reason}; handing the download to your browser")
    started = time.time()
    webbrowser.open(url)
    info("  download the archive in your browser, then come back here")
    for _ in range(3):
        answer = input(
            "  press Enter once it has finished, or paste the archive's full path: "
        ).strip().strip('"')
        if answer:
            candidate = Path(answer).expanduser()
            if candidate.is_file():
                return copy_into(candidate, downloads)
            info(f"  not a file: {candidate}")
            continue
        found = newest_archive(started)
        if found is not None:
            info(f"  found {found}")
            return copy_into(found, downloads)
        info("  no new archive in Downloads or Desktop yet - wait for it to finish, then press Enter again")
    raise SetupError(
        "couldn't find a downloaded archive; download it manually and extract it into "
        "<SirHurt folder>\\sirhurt"
    )


def unpack_nested_archives(destination: Path, *, depth: int = 2) -> None:
    """Unpack zips inside the archive until a bootstrapper .exe shows up.

    A gofile download is the SirHurt folder itself (bootstrapper at the top);
    a Box share wraps that folder - and the same zip - one level down, so the
    nested copy is unpacked next to itself to leave the same usable layout.
    """
    seen: set[Path] = set()
    for _ in range(depth):
        if any(destination.rglob("*.exe")):
            return
        nested = sorted(path for path in destination.rglob("*.zip") if zipfile.is_zipfile(path))
        if not nested:
            return
        for archive in nested:
            if archive in seen:
                continue
            info(f"  unpacking nested {archive.relative_to(destination).as_posix()}")
            safe_extract_zip(archive, archive.parent)
            seen.add(archive)


def extract_sirhurt(archive: Path, target: Path) -> Path | None:
    """Extract archive into <target>/sirhurt; the .exe found there, or None."""
    destination = target / "sirhurt"
    if archive.suffix.lower() == ".zip" and zipfile.is_zipfile(archive):
        safe_extract_zip(archive, destination)
        unpack_nested_archives(destination)
        executables = sorted(path.relative_to(destination).as_posix() for path in destination.rglob("*.exe"))
        suffix = f" ({', '.join(executables)})" if executables else ""
        info(f"  extracted to {destination}{suffix}")
        return next(destination.rglob("*.exe"), None)
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(archive, destination / archive.name)
    info(f"  {archive.name} isn't a zip; copied it to {destination}")
    info(f"  extract it manually with 7-Zip or WinRAR into {destination}")
    return None


def install_sirhurt(target: Path, link: tuple[str, str, str]) -> None:
    kind, identifier, url = link
    downloads = target / "downloads"
    info(f"\n[SirHurt] {kind} link {identifier}")
    info(f"  url:    {url}")
    info(f"  target: {target / 'sirhurt'}")
    if kind == "gofile":
        try:
            archive = gofile_download(identifier, downloads)
        except SetupError as exc:
            archive = browser_handoff(url, downloads, f"gofile download failed ({exc})")
    else:
        archive = browser_handoff(url, downloads, "Box shares have no unauthenticated download API")
    extract_sirhurt(archive, target)


# --------------------------------------------------------------------------- #
# Roblox settings (appStorage.json)
# --------------------------------------------------------------------------- #


def roblox_storage_path() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise SetupError("LOCALAPPDATA is not set; cannot find Roblox's appStorage.json")
    return Path(local).joinpath(*ROBLOX_STORAGE_PARTS)


ROBLOX_PROCESSES = ("RobloxPlayerBeta.exe", "RobloxCrashHandler.exe")


def running_roblox_processes() -> list[str]:
    found: list[str] = []
    for name in ROBLOX_PROCESSES:
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {name}", "/NH", "/FO", "CSV"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if name.lower() in (result.stdout or "").lower():
            found.append(name)
    return found


def roblox_running() -> bool:
    return bool(running_roblox_processes())


def close_roblox() -> bool:
    """Kill the Roblox processes and wait for them to disappear."""
    for name in running_roblox_processes():
        try:
            subprocess.run(
                ["taskkill", "/IM", name, "/F"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
    for _ in range(20):
        if not roblox_running():
            return True
        time.sleep(0.5)
    return not roblox_running()


def configure_roblox_settings(*, dry_run: bool) -> None:
    """Force "Launch at startup" and "Minimize to tray when closed" off."""
    path = roblox_storage_path()
    info(f"\n[Roblox] {path}")
    settings: dict[str, object] = {}
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SetupError(f"cannot read {path}: {exc}") from exc
        if not isinstance(loaded, dict):
            raise SetupError(f"{path} does not contain a JSON object")
        settings = loaded
    else:
        action = "would create" if dry_run else "creating"
        info(f"  no appStorage.json yet - {action} one with both settings off")

    first_launch = str(settings.get("IsFirstLaunchAfterInstall", "")).lower() == "true"
    if first_launch:
        warn(
            "Roblox has not completed a first launch on this profile yet - it rewrites "
            "appStorage.json on start, so re-run this stage after opening Roblox once"
        )

    changed = False
    for key, disabled in ROBLOX_SETTINGS.items():
        current = settings.get(key)
        # Roblox stores these as the strings "true"/"false"; keep that shape. A
        # boolean or a number from another writer is replaced, not inverted.
        desired: str = disabled
        if current == desired:
            info(f"  {key}: already {disabled}")
            continue
        if isinstance(current, str):
            info(f"  {key}: {current!r} -> {desired!r}")
        else:
            info(f"  {key}: {current!r} (non-string) -> {desired!r}")
        settings[key] = desired
        changed = True
    if not changed:
        return
    if dry_run:
        info("  would save appStorage.json")
        return

    # Roblox writes its in-memory settings back when the client exits, so a
    # running client would silently undo this change.
    if roblox_running():
        if sys.stdin is not None and sys.stdin.isatty():
            answer = ask_yes_no(
                "Roblox is running; close it now so it cannot write the old values back?", True
            )
            if not answer or not close_roblox():
                raise SetupError("Roblox is still running - close it and run the setup again")
            info("  Roblox closed")
        else:
            raise SetupError("Roblox is running - close it and run the setup again")

    backup = path.with_name(path.name + ".bak")
    partial = path.with_name(path.name + ".part")
    created_backup = False
    try:
        if path.is_file() and not backup.exists():
            shutil.copy2(path, backup)
            created_backup = True
        partial.write_text(json.dumps(settings, separators=(",", ":")), encoding="utf-8")
        os.replace(partial, path)
    except OSError as exc:
        partial.unlink(missing_ok=True)
        raise SetupError(f"cannot write {path}: {exc}") from exc

    try:
        written = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SetupError(f"wrote {path} but cannot read it back: {exc}") from exc
    if not isinstance(written, dict):
        raise SetupError(f"wrote {path} but it no longer contains a JSON object")
    still_on = [
        key for key in ROBLOX_SETTINGS
        if str(written.get(key, "")).strip().lower() != "false"
    ]
    if still_on:
        raise SetupError(f"{path} still reports {', '.join(still_on)} as enabled")
    if first_launch:
        info(
            "  saved, but Roblox rewrites this file on its next start - "
            "re-run this stage after opening Roblox once"
        )
    elif created_backup:
        info(f"  saved and verified (backup: {backup.name})")
    elif backup.exists():
        info(f"  saved and verified (kept existing backup: {backup.name})")
    else:
        info("  saved and verified")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="SixSirhurtUnretardifier9000Pro",
        description=(
            "Prepare Windows, install the latest Roblox build into Versions, then download "
            "SirHurt into one folder (stages 1-3)."
        ),
        epilog="Guide: https://sirhurt.pages.dev/guide/",
    )
    parser.add_argument(
        "--dir",
        metavar="PATH",
        help=(
            "install folder (default: SirHurt under Downloads, Desktop or Documents - "
            "whichever isn't synced to OneDrive)"
        ),
    )
    parser.add_argument("--link", metavar="URL", help="SirHurt download link (gofile.io or app.box.com)")
    parser.add_argument(
        "--archive",
        metavar="PATH",
        help="SirHurt archive to use instead of scanning this script's folder",
    )
    parser.add_argument(
        "--no-local-archive",
        action="store_true",
        help="ignore any SirHurt archive sitting next to this script",
    )
    parser.add_argument(
        "--skip-roblox-build",
        action="store_true",
        help="don't download a Roblox deployment into %%LOCALAPPDATA%%\\Roblox\\Versions",
    )
    parser.add_argument(
        "--roblox-version",
        metavar="HASH",
        help="Roblox build to install instead of the latest one (version-xxxxxxxxxxxx)",
    )
    parser.add_argument(
        "--roblox-channel",
        metavar="NAME",
        default=ROBLOX_DEFAULT_CHANNEL,
        help=f"Roblox channel to resolve the build on (default: {ROBLOX_DEFAULT_CHANNEL})",
    )
    parser.add_argument("--skip-sirhurt", action="store_true", help="don't install SirHurt")
    parser.add_argument("--skip-exclusions", action="store_true", help="don't add the Defender exclusion")
    parser.add_argument("--skip-repair", action="store_true", help="don't run SFC and DISM")
    parser.add_argument("--skip-runtimes", action="store_true", help="don't install VC++ and .NET")
    parser.add_argument(
        "--skip-roblox-settings",
        action="store_true",
        help="don't touch Roblox's appStorage.json",
    )
    parser.add_argument(
        "--run-cleaner",
        action="store_true",
        help="run SirHurt Cleaner (deletes Roblox/SirHurt configs, including stored SirHurt login data)",
    )
    parser.add_argument(
        "--reboot",
        action="store_true",
        help="restart Windows when the run finishes (60-second delay; cancel with 'shutdown /a')",
    )
    parser.add_argument(
        "--no-survey",
        action="store_true",
        help="don't ask the setup questions; use the defaults (everything except the cleaner and reboot)",
    )
    parser.add_argument("--dry-run", action="store_true", help="resolve everything and print it, write nothing")
    parser.add_argument("--version", action="version", version=f"SirHurt Setup {__version__}")
    parser.add_argument("--elevated", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args(argv)


NEXT_STEPS = """SirHurt setup - next steps
==========================

1. Restart Windows if the setup asked for it (the runtimes register at boot).
2. Open Roblox and join any game - injection needs a loaded game client.
3. Wait 5-10 seconds after the game finishes loading.
4. Run the SirHurt bootstrapper ("SirHurt V5.exe") as Administrator - it is in
   the "sirhurt" folder, or one subfolder down if the archive came from a Box
   share (right-click -> Run as administrator, then accept the UAC prompt).
5. In the bootstrapper, click Inject once and log in. Do not click Inject a second time.
6. Test with a small script such as Infinite Yield before using your own scripts.

The cleaner (if you ran it) deleted stored SirHurt login data, so you will need to
log in again on the first injection.

Guide:           https://sirhurt.pages.dev/guide/injection/
Troubleshooting: https://sirhurt.pages.dev/guide/troubleshooting/
Downgrade:       https://sirhurt.pages.dev/guide/downgrade/
Roblox builds:   https://sirhurt.pages.dev/rdd/
Discord:         https://discord.gg/sirhurt
"""


def write_next_steps(target: Path) -> None:
    path = target / "README.txt"
    try:
        path.write_text(NEXT_STEPS, encoding="utf-8")
    except OSError as exc:
        warn(f"cannot write {path}: {exc}")


def schedule_reboot(*, dry_run: bool) -> None:
    info("\n[Reboot] Windows restarts in 60 seconds - run 'shutdown /a' to cancel")
    if dry_run:
        return
    try:
        result = subprocess.run(
            ["shutdown", "/r", "/t", "60", "/c", "SirHurt Setup finished - restarting"],
            check=False,
        )
    except OSError as exc:
        warn(f"cannot schedule the reboot: {exc}; restart Windows yourself")
        return
    if result.returncode != 0:
        warn(f"shutdown returned {result.returncode}; restart Windows yourself")


def pause_before_exit() -> None:
    if sys.stdin is None or not sys.stdin.isatty():
        return
    try:
        input("\nPress Enter to close ...")
    except (EOFError, KeyboardInterrupt):
        pass


def summarize(
    target: Path,
    *,
    reboot_expected: bool,
    cleaned: bool,
    bootstrapper: Path | None,
    exclusion_ok: bool | None,
    roblox_build: Path | None,
) -> None:
    info("\nDone. Layout:")
    for entry in sorted(target.iterdir(), key=lambda path: path.name.lower()):
        info(f"  {entry.name}{os.sep if entry.is_dir() else ''}")
    if reboot_expected:
        info("\nReboot before continuing - the runtimes register themselves at boot.")
    if cleaned:
        info("\nThe cleaner removed stored SirHurt data - you'll need to log in again.")
    if (target / "README.txt").is_file():
        info(f"Next steps are also in {target / 'README.txt'}.")
    if exclusion_ok is False:
        info(
            f"\nThe Defender exclusion was not confirmed - add {target} in Windows Security by hand."
        )
    if roblox_build is not None:
        info(f"\nRoblox build in place: {roblox_build}")
        info("  launch the game through Roblox as usual - that folder holds the client SirHurt injects into")
    else:
        info("\nNo Roblox build was installed - grab one from https://sirhurt.pages.dev/rdd/")
        info(f"and extract it into {roblox_versions_root()} as version-<hash>.")
    if bootstrapper is not None:
        info("Next: stage 4 of the guide - launch Roblox, join a game, then run the SirHurt loader")
        info("      as Administrator: https://sirhurt.pages.dev/guide/injection/")
    else:
        info("\nSirHurt itself wasn't installed - get it from https://sirhurt.net/login/download.php")
        info(f"and extract it into {target / 'sirhurt'}, then run its bootstrapper as Administrator.")
        info(f"  no .exe under {target / 'sirhurt'} - extract the archive you downloaded into that folder")


def run(args: argparse.Namespace, *, survey: bool) -> int:
    preflight()
    if args.link:
        classify_link(args.link)  # fail fast on a malformed --link
    if survey:
        apply_survey(args)
        info(f"plan: {survey_plan(args)}")
        info("  Ctrl+C cancels.")
    if (
        args.skip_roblox_build
        and args.skip_sirhurt
        and args.skip_exclusions
        and args.skip_repair
        and args.skip_runtimes
        and args.skip_roblox_settings
        and not args.run_cleaner
        and not args.reboot
    ):
        raise SetupError("nothing to do: every stage was skipped and --reboot was not given")
    if args.dry_run and not is_admin() and (
        not args.skip_exclusions or not args.skip_repair or args.run_cleaner
    ):
        warn(
            "the real run needs Administrator for those stages; the dry run cannot show that failure"
        )
    target = resolve_target(args.dir, dry_run=args.dry_run)
    # adopt_local_archive moves the archive into <target>/downloads before the
    # later stages run, so an aborted run must not lose sight of it.
    folders = search_directories()
    downloads = target / "downloads"
    if downloads.is_dir() and downloads not in folders:
        folders.append(downloads)

    local_archive: Path | None = None
    if not args.skip_sirhurt and not args.link:
        if args.archive:
            local_archive = Path(args.archive).expanduser()
            if not local_archive.is_file():
                raise SetupError(f"no such archive: {local_archive}")
        elif not args.no_local_archive:
            local_archive = find_local_archive(folders)
            if local_archive is None:
                searched = " or ".join(str(folder) for folder in folders)
                if args.dry_run:
                    warn(f"no SirHurt archive found in {searched}")
                else:
                    local_archive = prompt_for_archive(folders)
                    if local_archive is None:
                        # 's' (or end of input) skips SirHurt - no link prompt.
                        args.skip_sirhurt = True

    exclusion_ok: bool | None = None
    if not args.skip_exclusions:
        exclusion_ok = add_defender_exclusion(target, dry_run=args.dry_run)
    if local_archive is not None:
        adopt_local_archive(local_archive, target, dry_run=args.dry_run)
    repair_needs_reboot = False
    if not args.skip_repair:
        repair_needs_reboot = repair_system_files(dry_run=args.dry_run)
    runtimes_need_reboot = False
    if not args.skip_runtimes:
        runtimes_need_reboot = install_runtimes(dry_run=args.dry_run)
    roblox_build: Path | None = None
    if not args.skip_roblox_build:
        roblox_build = install_roblox_build(
            roblox_versions_root(),
            version=args.roblox_version,
            channel=args.roblox_channel,
            dry_run=args.dry_run,
        )
    if args.run_cleaner:
        # The Cleaner is its own download; install_cleaner returns early when it
        # is already in <target>\cleaner.
        install_cleaner(target, dry_run=args.dry_run)
        run_sirhurt_cleaner(target, dry_run=args.dry_run)
    if not args.skip_sirhurt and local_archive is None:
        link = resolve_sirhurt_link(args.link, dry_run=args.dry_run)
        if link is not None:
            if args.dry_run:
                kind, identifier, url = link
                info(f"\n[SirHurt] {kind} link {identifier}")
                info(f"  url:    {url}")
                info(f"  target: {target / 'sirhurt'}")
            else:
                install_sirhurt(target, link)
    if not args.skip_roblox_settings:
        configure_roblox_settings(dry_run=args.dry_run)
    if args.dry_run:
        if args.reboot:
            schedule_reboot(dry_run=True)
        info("\ndry run: nothing was written")
    else:
        if not args.skip_sirhurt:
            write_next_steps(target)
        sirhurt_folder = target / "sirhurt"
        bootstrapper = (
            next(sirhurt_folder.rglob("*.exe"), None) if sirhurt_folder.is_dir() else None
        )
        summarize(
            target,
            reboot_expected=repair_needs_reboot or runtimes_need_reboot,
            cleaned=args.run_cleaner,
            bootstrapper=bootstrapper,
            exclusion_ok=exclusion_ok,
            roblox_build=roblox_build,
        )
        if args.reboot:
            schedule_reboot(dry_run=False)
        else:
            pause_before_exit()
    return 0


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if should_elevate(raw):
        if elevate(raw):
            print(
                "relaunching as Administrator ... (this process exits 0 once the UAC prompt is "
                "answered; the elevated copy does the work)",
                file=sys.stderr,
            )
            return 0
        print(
            "error: this setup needs Administrator rights - accept the UAC prompt, or run it "
            "from an elevated prompt",
            file=sys.stderr,
        )
        return 1
    args = parse_args(raw)
    try:
        return run(args, survey=should_survey(raw))
    except KeyboardInterrupt:
        print("\ncancelled", file=sys.stderr)
        return 130
    except SetupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        pause_before_exit()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
