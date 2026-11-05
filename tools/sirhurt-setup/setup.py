#!/usr/bin/env python3
"""Download Sirstrap and SirHurt into one folder.

Partially automates stage 3 of https://sirhurt.pages.dev/guide/:
Sirstrap is fetched from its own releases (no account needed), SirHurt needs the
single-use link you get from sirhurt.net after logging in, and that link is a
gofile.io folder or a Box share.

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
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
import zipfile
from pathlib import Path

__version__ = "1.0.0"

SIRSTRAP_RELEASES_API = "https://codeberg.org/api/v1/repos/Sirstrap/Sirstrap/releases?limit=20"
SIRSTRAP_DOWNLOAD_BASE = "https://sirstrap.com/releases"
SIRSTRAP_FALLBACK_TAG = "v10.12.7.4-beta"
SIRSTRAP_ASSETS = (("Sirstrap.UI.zip", "sirstrap"), ("SirHurt.Cleaner.CLI.zip", "cleaner"))
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
            "not running as Administrator - downloading and extracting works, but the SirHurt "
            "loader itself has to run elevated (stage 4 of the guide)"
        )
    build = windows_build()
    if build is not None and build < WINDOWS_24H2_BUILD:
        warn(
            f"Windows build {build} detected; the guide targets Windows 11 24H2 "
            f"(build {WINDOWS_24H2_BUILD}) or newer"
        )


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
    for part in candidate.parts:
        if part.lower().startswith("onedrive"):
            raise SetupError(f"refusing to install into a OneDrive-synced folder: {candidate}")
    for root in protected_roots():
        root_cased = os.path.normcase(os.path.abspath(root))
        if cased == root_cased or cased.startswith(root_cased + os.sep):
            raise SetupError(f"refusing to install into a protected system folder: {candidate}")


def resolve_target(raw: str | None, *, dry_run: bool) -> Path:
    default = Path.home() / "SirHurt"
    if raw:
        target = Path(raw).expanduser()
    elif dry_run:
        target = default
    else:
        answer = input(f"Where should SirHurt live? [default: {default}]: ").strip().strip('"')
        target = Path(answer).expanduser() if answer else default
    validate_target(target)
    if dry_run:
        info(f"target folder: {target}")
    else:
        target.mkdir(parents=True, exist_ok=True)
        info(f"target folder: {target}")
    return target


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
    for asset, subfolder in SIRSTRAP_ASSETS:
        url = f"{SIRSTRAP_DOWNLOAD_BASE}/{tag}/{asset}"
        destination = target / subfolder
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


def newest_archive(started: float) -> Path | None:
    found: list[tuple[float, Path]] = []
    for folder in (Path.home() / "Downloads", Path.home() / "Desktop"):
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
    return max(found)[1] if found else None


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
# CLI
# --------------------------------------------------------------------------- #


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="SirHurt-Setup",
        description="Download Sirstrap and SirHurt into one folder (stage 3 of the guide).",
        epilog="Guide: https://sirhurt.pages.dev/guide/install/",
    )
    parser.add_argument(
        "--dir",
        metavar="PATH",
        default=str(Path.home() / "SirHurt"),
        help="install folder (default: %(default)s)",
    )
    parser.add_argument("--link", metavar="URL", help="SirHurt download link (gofile.io or app.box.com)")
    parser.add_argument("--skip-sirstrap", action="store_true", help="don't download Sirstrap or the Cleaner")
    parser.add_argument("--skip-sirhurt", action="store_true", help="don't download SirHurt")
    parser.add_argument("--dry-run", action="store_true", help="resolve everything and print it, write nothing")
    parser.add_argument("--version", action="version", version=f"SirHurt Setup {__version__}")
    return parser.parse_args(argv)


def summarize(target: Path) -> None:
    info("\nDone. Layout:")
    for entry in sorted(target.iterdir(), key=lambda path: path.name.lower()):
        info(f"  {entry.name}{os.sep if entry.is_dir() else ''}")
    info("\nNext: stage 4 of the guide - launch Roblox, join a game, then run the SirHurt loader")
    info("      as Administrator: https://sirhurt.pages.dev/guide/injection/")


def run(args: argparse.Namespace) -> int:
    if args.skip_sirstrap and args.skip_sirhurt:
        raise SetupError("nothing to do: both --skip-sirstrap and --skip-sirhurt were given")
    preflight()
    if args.link:
        classify_link(args.link)  # fail fast on a malformed --link
    target = resolve_target(args.dir, dry_run=args.dry_run)
    if not args.skip_sirstrap:
        tag = resolve_sirstrap_tag()
        info(f"Sirstrap release: {tag}")
        install_sirstrap(target, tag, dry_run=args.dry_run)
    if not args.skip_sirhurt:
        link = resolve_sirhurt_link(args.link, dry_run=args.dry_run)
        if link is not None:
            if args.dry_run:
                kind, identifier, url = link
                info(f"\n[SirHurt] {kind} link {identifier}")
                info(f"  url:    {url}")
                info(f"  target: {target / 'sirhurt'}")
            else:
                install_sirhurt(target, link)
    if args.dry_run:
        info("\ndry run: nothing was written")
    else:
        summarize(target)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
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
