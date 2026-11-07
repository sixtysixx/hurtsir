#!/usr/bin/env python3
"""Set up SirHurt in one pass: exclusions, repair, runtimes, launch stack.

Automates stages 1-3 of https://sirhurt.pages.dev/guide/:

* scans the folder you started it from and the folder the exe lives in for a
  SirHurt archive, moves it into the install folder (validated to be outside
  OneDrive and Program Files), adds a Windows Defender exclusion for that
  folder, then extracts the archive;
* runs the system-repair chain (SFC, then DISM CheckHealth/ScanHealth/RestoreHealth);
* installs both Visual C++ redistributables and the .NET Framework 4.8.1 web
  installer;
* downloads Sirstrap's UI, Cleaner and CLI builds from their own releases;
* otherwise SirHurt needs the single-use link you get from sirhurt.net after
  logging in - a gofile.io folder or a Box share;
* turns off "Launch at startup" and "Minimize to tray when closed" in Roblox's
  %LOCALAPPDATA%\\Roblox\\LocalStorage\\appStorage.json.

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

__version__ = "1.1.0"

SIRSTRAP_RELEASES_API = "https://codeberg.org/api/v1/repos/Sirstrap/Sirstrap/releases?limit=20"
SIRSTRAP_DOWNLOAD_BASE = "https://sirstrap.com/releases"
SIRSTRAP_FALLBACK_TAG = "v10.12.7.4-beta"
SIRSTRAP_ASSETS = (("Sirstrap.UI.zip", "sirstrap"), ("SirHurt.Cleaner.CLI.zip", "cleaner"))
SIRSTRAP_CLI_URL = "https://www.sirstrap.com/releases/download.php?file=Sirstrap.CLI.zip"
SIRSTRAP_CLI_ASSET = "Sirstrap.CLI.zip"
SIRSTRAP_CLI_FOLDER = "sirstrap-cli"
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


def http_json(url: str, data: bytes | None = None, headers: dict[str, str] | None = None) -> object:
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
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raise SetupError(f"HTTP {exc.code} from {url}") from exc
    except urllib.error.URLError as exc:
        raise SetupError(f"cannot reach {url}: {exc.reason}") from exc
    except (TimeoutError, OSError) as exc:
        raise SetupError(f"network error talking to {url}: {exc}") from exc
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SetupError(f"malformed JSON from {url}") from exc


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


def elevate(argv: list[str]) -> bool:
    """Relaunch this script/exe elevated through UAC; True when that copy started."""
    if getattr(sys, "frozen", False):
        arguments = list(argv)
    else:
        arguments = [str(Path(__file__).resolve()), *argv]
    parameters = subprocess.list2cmdline([*arguments, "--elevated"])
    try:
        shell_execute = ctypes.windll.shell32.ShellExecuteW  # type: ignore[attr-defined]
        result = shell_execute(None, "runas", sys.executable, parameters, str(Path.cwd()), 1)
    except (AttributeError, OSError) as exc:
        warn(f"cannot request Administrator rights: {exc}")
        return False
    if result <= 32:
        warn("the Administrator request was refused (UAC prompt declined)")
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
# Local SirHurt archive, Defender exclusion, repair, runtimes
# --------------------------------------------------------------------------- #


def is_compiled() -> bool:
    return "__compiled__" in globals() or bool(getattr(sys, "frozen", False))


def is_unpack_folder(folder: Path) -> bool:
    """True for Nuitka/PyInstaller onefile scratch dirs under %TEMP%."""
    try:
        cased = os.path.normcase(os.path.abspath(folder))
        temp = os.path.normcase(os.path.abspath(tempfile.gettempdir()))
    except OSError:
        return False
    if cased == temp or cased.startswith(temp + os.sep):
        return True
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


def add_defender_exclusion(folder: Path, *, dry_run: bool) -> None:
    info(f"\n[Exclusion] {folder}")
    if dry_run:
        info("  would add a Windows Defender folder exclusion")
        return
    require_admin("add the Defender exclusion")
    try:
        if any(same_folder(entry, folder) for entry in defender_exclusions()):
            info("  already excluded")
            return
    except SetupError as exc:
        warn(f"cannot read Defender's exclusion list ({exc}); trying to add it anyway")
    quoted = str(folder).replace("'", "''")
    result = powershell(f"Add-MpPreference -ExclusionPath '{quoted}' -ErrorAction Stop")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip() or f"exit code {result.returncode}"
        warn(f"could not add the exclusion ({detail}); add {folder} in Windows Security by hand")
        return
    try:
        verified = any(same_folder(entry, folder) for entry in defender_exclusions())
    except SetupError:
        verified = False
    info("  added and verified" if verified else "  added (Windows Security may take a moment to list it)")


def repair_system_files(*, dry_run: bool) -> None:
    info("\n[Repair] Windows component store")
    info("  this is the slow part - SFC and DISM each take several minutes")
    for name, executable, arguments in REPAIR_CHAIN:
        info(f"  ==> {name}: {executable} {' '.join(arguments)}")
    if dry_run:
        return
    require_admin("run SFC and DISM")
    for name, executable, arguments in REPAIR_CHAIN:
        try:
            result = subprocess.run([executable, *arguments], check=False)
        except OSError as exc:
            raise SetupError(f"cannot run {executable}: {exc}") from exc
        if result.returncode not in (0, 3010):
            raise SetupError(
                f"{name} failed with exit code {result.returncode}; "
                "repair the component store before installing SirHurt"
            )
    info("  repair chain finished; reboot before the first launch")


def install_runtimes(*, dry_run: bool) -> None:
    info("\n[Runtimes] Visual C++ x86, Visual C++ x64, .NET Framework 4.8.1")
    for name, url, arguments in RUNTIMES:
        info(f"  {name}: {url} {' '.join(arguments)}")
    if dry_run:
        return
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
            if result.returncode == 1638:
                info("    a newer version is already installed")
            elif result.returncode == 3010:
                warn(f"    {name} installed; it needs a reboot to finish")
            elif result.returncode not in RUNTIME_OK_CODES:
                raise SetupError(f"{name} failed with exit code {result.returncode}")
    info("  runtimes installed; reboot before the first launch")


# --------------------------------------------------------------------------- #
# Sirstrap
# --------------------------------------------------------------------------- #


def resolve_sirstrap_tag() -> str:
    try:
        releases = http_json(SIRSTRAP_RELEASES_API)
    except SetupError as exc:
        warn(f"cannot read the Sirstrap release API ({exc}); using {SIRSTRAP_FALLBACK_TAG}")
        return SIRSTRAP_FALLBACK_TAG
    if not isinstance(releases, list):
        warn(f"unexpected Sirstrap release API response; using {SIRSTRAP_FALLBACK_TAG}")
        return SIRSTRAP_FALLBACK_TAG
    for release in releases:
        if not isinstance(release, dict) or release.get("draft"):
            continue
        for asset in release.get("assets") or ():
            if not isinstance(asset, dict):
                continue
            name = str(asset.get("name") or "").lower()
            if name.startswith("sirstrap.ui") and name.endswith(".zip"):
                tag = str(release.get("tag_name") or "")
                if tag:
                    return tag
    warn(f"no Sirstrap.UI.zip found in the last 20 releases; using {SIRSTRAP_FALLBACK_TAG}")
    return SIRSTRAP_FALLBACK_TAG


def install_sirstrap(target: Path, tag: str, *, dry_run: bool) -> None:
    jobs = [
        (f"{SIRSTRAP_DOWNLOAD_BASE}/{tag}/{asset}", asset, target / subfolder)
        for asset, subfolder in SIRSTRAP_ASSETS
    ]
    # The CLI build is served from sirstrap.com's latest-release endpoint rather
    # than a tag path, and ships only Sirstrap.exe - keep it out of sirstrap/.
    jobs.append((SIRSTRAP_CLI_URL, SIRSTRAP_CLI_ASSET, target / SIRSTRAP_CLI_FOLDER))
    for url, asset, destination in jobs:
        info(f"\n[Sirstrap] {asset}")
        info(f"  url:    {url}")
        info(f"  target: {destination}")
        if dry_run:
            continue
        with tempfile.TemporaryDirectory(prefix="sirhurt-setup-") as scratch:
            archive = Path(scratch) / asset
            download(url, archive)
            if not zipfile.is_zipfile(archive):
                raise SetupError(
                    f"{asset} did not download as a zip archive - the release layout may have changed"
                )
            safe_extract_zip(archive, destination)
        executables = sorted(path.name for path in destination.rglob("*.exe"))
        info(f"  extracted: {', '.join(executables) if executables else '(no .exe found)'}")


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
            info("cancelled - Sirstrap is installed, SirHurt was skipped")
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


def extract_sirhurt(archive: Path, target: Path) -> None:
    destination = target / "sirhurt"
    if archive.suffix.lower() == ".zip" and zipfile.is_zipfile(archive):
        safe_extract_zip(archive, destination)
        executables = sorted(path.relative_to(destination).as_posix() for path in destination.rglob("*.exe"))
        suffix = f" ({', '.join(executables)})" if executables else ""
        info(f"  extracted to {destination}{suffix}")
        return
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(archive, destination / archive.name)
    info(f"  {archive.name} isn't a zip; copied it to {destination}")
    info(f"  extract it manually with 7-Zip or WinRAR into {destination}")


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


def roblox_running() -> bool:
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq RobloxPlayerBeta.exe", "/NH"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return "RobloxPlayerBeta" in (result.stdout or "")


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

    changed = False
    for key, disabled in ROBLOX_SETTINGS.items():
        current = settings.get(key)
        # Roblox stores these as the strings "true"/"false"; keep that shape.
        desired: object = disabled if isinstance(current, str) or current is None else not bool(current)
        if current == desired:
            info(f"  {key}: already {disabled}")
            continue
        info(f"  {key}: {current!r} -> {desired!r}")
        settings[key] = desired
        changed = True
    if not changed:
        return
    if dry_run:
        info("  would save appStorage.json")
        return
    if roblox_running():
        warn("Roblox is running - close it, or it may write these settings back when it exits")
    backup = path.with_name(path.name + ".bak")
    partial = path.with_name(path.name + ".part")
    try:
        if path.is_file() and not backup.exists():
            shutil.copy2(path, backup)
        partial.write_text(json.dumps(settings, separators=(",", ":")), encoding="utf-8")
        os.replace(partial, path)
    except OSError as exc:
        partial.unlink(missing_ok=True)
        raise SetupError(f"cannot write {path}: {exc}") from exc
    info(f"  saved{' (backup: ' + backup.name + ')' if backup.exists() else ''}")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="SirHurt-Setup",
        description="Prepare Windows, then download Sirstrap and SirHurt into one folder (stages 1-3).",
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
        "--skip-sirstrap",
        action="store_true",
        help="don't download Sirstrap (UI, Cleaner or CLI)",
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
    parser.add_argument("--dry-run", action="store_true", help="resolve everything and print it, write nothing")
    parser.add_argument("--version", action="version", version=f"SirHurt Setup {__version__}")
    parser.add_argument("--elevated", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def summarize(target: Path, *, reboot_expected: bool) -> None:
    info("\nDone. Layout:")
    for entry in sorted(target.iterdir(), key=lambda path: path.name.lower()):
        info(f"  {entry.name}{os.sep if entry.is_dir() else ''}")
    if reboot_expected:
        info("\nReboot before continuing - the runtimes register themselves at boot.")
    info("Next: stage 4 of the guide - launch Roblox, join a game, then run the SirHurt loader")
    info("      as Administrator: https://sirhurt.pages.dev/guide/injection/")


def run(args: argparse.Namespace) -> int:
    if (
        args.skip_sirstrap
        and args.skip_sirhurt
        and args.skip_exclusions
        and args.skip_repair
        and args.skip_runtimes
        and args.skip_roblox_settings
    ):
        raise SetupError("nothing to do: every stage was skipped")
    preflight()
    if args.link:
        classify_link(args.link)  # fail fast on a malformed --link
    target = resolve_target(args.dir, dry_run=args.dry_run)

    local_archive: Path | None = None
    if not args.skip_sirhurt:
        if args.archive:
            local_archive = Path(args.archive).expanduser()
            if not local_archive.is_file():
                raise SetupError(f"no such archive: {local_archive}")
        elif not args.no_local_archive:
            folders = search_directories()
            local_archive = find_local_archive(folders)
            if local_archive is None:
                searched = " or ".join(str(folder) for folder in folders)
                warn(f"no SirHurt archive found in {searched}")
                info(
                    "  Download the archive from https://sirhurt.net/login/download.php and put\n"
                    f"  it next to the setup executable ({folders[-1]}), then run this again.\n"
                    "  You can paste the download link instead if you prefer."
                )

    if not args.skip_exclusions:
        add_defender_exclusion(target, dry_run=args.dry_run)
    if local_archive is not None:
        adopt_local_archive(local_archive, target, dry_run=args.dry_run)
    if not args.skip_repair:
        repair_system_files(dry_run=args.dry_run)
    if not args.skip_runtimes:
        install_runtimes(dry_run=args.dry_run)
    if not args.skip_sirstrap:
        tag = resolve_sirstrap_tag()
        info(f"\nSirstrap release: {tag}")
        install_sirstrap(target, tag, dry_run=args.dry_run)
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
        info("\ndry run: nothing was written")
    else:
        summarize(target, reboot_expected=not (args.skip_repair and args.skip_runtimes))
    return 0


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if should_elevate(raw):
        if elevate(raw):
            print("relaunching as Administrator ...", file=sys.stderr)
            return 0
        print(
            "error: this setup needs Administrator rights - accept the UAC prompt, or run it "
            "from an elevated prompt",
            file=sys.stderr,
        )
        return 1
    args = parse_args(raw)
    try:
        return run(args)
    except KeyboardInterrupt:
        print("\ncancelled", file=sys.stderr)
        return 130
    except SetupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
