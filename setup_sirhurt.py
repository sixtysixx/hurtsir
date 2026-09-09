#!/usr/bin/env python3
# ============================================================================
#  SirHurt One-Click Setup (Python port of setup_sirhurt.ps1)
#
#  What it does, in order:
#    1. Installs Visual C++ Redistributables (x64 + x86)      - silent
#    2. Installs .NET SDK 10.0.400 (x64 + x86)                - silent
#    3. Downloads + silently installs 7-Zip
#    4. Sets MinimizeToTray / LaunchAtStartup = false in
#       %localappdata%\Roblox\localStorage\appStorage.json
#    5. Creates the dedicated SirHurt folder, adds it to the
#       antivirus (Windows Defender) exclusions, then downloads the SirHurt
#       archive from the gofile distribution link (headless browser, or a
#       manual-download watcher as fallback) and extracts it with 7-Zip
#    6. --post-logon mode: enforces Roblox startup values, relaunches the
#       Roblox client, then runs the SirHurt Bootstrapper elevated
#
#  Run with:  right-click -> "Run with Python"   (it self-elevates)
#            or: python setup_sirhurt.py            (full setup)
#            or: python setup_sirhurt.py --post-logon   (after logon phase)
#            or: python setup_sirhurt.py --skip-gofile  (manual download)
# ============================================================================

import argparse
import base64
import ctypes
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

IS_WINDOWS = os.name == "nt"

# Folder where SirHurt is extracted and excluded from AV
SIRHURT_DIR = Path(os.environ.get("USERPROFILE", Path.home())) / "Downloads" / "sirhurt_utils"
# .NET SDK version to install (both architectures)
DOTNET_VERSION = "10.0.400"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36")

TMP = Path(tempfile.gettempdir()) / "sirhurt_setup"
LOG_FILE = Path(tempfile.gettempdir()) / "sirhurt_setup.log"


# ----------------------------------------------------------------------------
# logging - the elevated window closes on exit, so keep a transcript the
# user can check afterwards if something goes wrong.
# ----------------------------------------------------------------------------
_log_fh = open(LOG_FILE, "a", encoding="utf-8")


def _log(msg: str) -> None:
    _log_fh.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")
    _log_fh.flush()


def step(m: str) -> None:
    print(f"\n=== {m} ===", flush=True)
    _log(f"STEP: {m}")


def ok(m: str) -> None:
    print(f"  [OK] {m}", flush=True)
    _log(f"OK: {m}")


def warn(m: str) -> None:
    print(f"  [!]  {m}", flush=True)
    _log(f"WARN: {m}")


# ----------------------------------------------------------------------------
# 0. Self-elevate to Administrator (needed for installers + AV exclusions)
# ----------------------------------------------------------------------------
def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def self_elevate() -> None:
    if is_admin():
        return
    print("Requesting administrator privileges...")
    if getattr(sys, "frozen", False):
        # Running as a compiled exe (Nuitka/PyInstaller): relaunch the exe
        # itself, preserving its arguments (--post-logon etc.).
        target = sys.executable
        params = subprocess.list2cmdline(sys.argv[1:])
    else:
        # Running from source: relaunch python with this script.
        target = sys.executable
        params = subprocess.list2cmdline([os.path.abspath(sys.argv[0])])
    ret = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", target, params, None, 1  # SW_SHOWNORMAL
    )
    if ret <= 32:
        print(f"Elevation was cancelled or failed (code {ret}).")
    sys.exit(0)


def get_file(url: str, out: Path) -> Path:
    """Download `url` to `out` unless it already exists (like Get-File)."""
    if out.exists():
        return out
    print(f"  Downloading {url}", flush=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req) as resp, open(out, "wb") as fh:
            shutil.copyfileobj(resp, fh)
    except Exception as exc:
        warn(f"Direct download failed ({exc}); trying BITS fallback...")
        # PowerShell fallback: Start-BitsTransfer (resumable, Windows-native)
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command",
             f"Start-BitsTransfer -Source '{url}' -Destination '{out}'"],
            check=True,
        )
    return out


def run_installer(exe: Path, args: list) -> int:
    """Run an installer and wait, returning its exit code."""
    proc = subprocess.run([str(exe), *args])
    return proc.returncode


# ----------------------------------------------------------------------------
# 1-2. Shared installer logic (VC++ Redistributables / .NET SDK)
# ----------------------------------------------------------------------------
def install_exes(downloads: dict) -> None:
    for name, url in downloads.items():
        exe = get_file(url, TMP / name)
        print(f"  Installing {name} ...", flush=True)
        code = run_installer(exe, ["/install", "/quiet", "/norestart"])
        # 0 = installed, 1638 = newer already installed, 4000 = installed,
        # reboot required
        if code in (0, 1638, 4000):
            ok(f"{name} finished (exit {code})")
        else:
            warn(f"{name} exited with code {code}")


def step_vc_redist() -> None:
    step("Step 1/7 - Visual C++ Redistributables (x64 + x86)")
    install_exes({
        "vc_redist.x64.exe": "https://aka.ms/vc14/vc_redist.x64.exe",
        "vc_redist.x86.exe": "https://aka.ms/vc14/vc_redist.x86.exe",
    })


def step_dotnet() -> None:
    step(f"Step 2/7 - .NET SDK {DOTNET_VERSION} (x64 + x86)")
    base = f"https://builds.dotnet.microsoft.com/dotnet/Sdk/{DOTNET_VERSION}"
    install_exes({
        f"dotnet-sdk-win-x64.exe": f"{base}/dotnet-sdk-{DOTNET_VERSION}-win-x64.exe",
        f"dotnet-sdk-win-x86.exe": f"{base}/dotnet-sdk-{DOTNET_VERSION}-win-x86.exe",
    })


# ----------------------------------------------------------------------------
# 3. 7-Zip (silent install)
# ----------------------------------------------------------------------------
def step_sevenzip() -> Path | None:
    step("Step 3/7 - 7-Zip (silent install)")
    seven_zip = Path(os.environ["ProgramFiles"]) / "7-Zip" / "7z.exe"
    if seven_zip.exists():
        ok("7-Zip already installed")
        return seven_zip

    installer = get_file(
        "https://github.com/ip7z/7zip/releases/download/26.03/7z2603-x64.exe",
        TMP / "7z2603-x64.exe",
    )
    print("  Installing 7-Zip ...", flush=True)
    subprocess.run([str(installer), "/S"], check=False)
    if seven_zip.exists():
        ok("7-Zip installed")
        return seven_zip
    warn("7-Zip not found at default path; extraction will fall back to "
         "Expand-Archive")
    return None


# ----------------------------------------------------------------------------
# 4. Roblox appStorage.json - disable MinimizeToTray / LaunchAtStartup
# ----------------------------------------------------------------------------
def enforce_roblox_startup_values(kill_roblox: bool = False) -> None:
    """Set MinimizeToTray / LaunchAtStartup = false in Roblox's
    appStorage.json (case-insensitive keys, value types preserved)."""
    if kill_roblox:
        # Roblox rewrites localStorage on exit, so kill it before editing
        subprocess.run(["taskkill", "/F", "/IM", "RobloxPlayerBeta.exe"],
                       capture_output=True, check=False)
        subprocess.run(["taskkill", "/F", "/IM", "RobloxCrashHandler.exe"],
                       capture_output=True, check=False)

    app_storage = (Path(os.environ["LOCALAPPDATA"])
                   / "Roblox" / "localStorage" / "appStorage.json")
    if not app_storage.exists():
        warn("appStorage.json not found (Roblox may not be installed yet).")
        warn("Re-run this script, or disable the settings manually in Roblox.")
        return


    try:
        shutil.copy2(app_storage, app_storage.with_suffix(".json.bak"))
        data = json.loads(app_storage.read_text(encoding="utf-8-sig"))

        for key in ("MinimizeToTray", "LaunchAtStartup"):
            # Roblox JSON is case-insensitive at the app level; match any case
            existing = next((k for k in data if k.lower() == key.lower()), None)
            if existing is not None:
                # preserve the original value type (Roblox stores strings)
                if isinstance(data[existing], str):
                    data[existing] = "false"
                else:
                    data[existing] = False
            else:
                data[key] = False

        # compact JSON, matching ConvertTo-Json -Compress
        app_storage.write_text(
            json.dumps(data, separators=(",", ":")), encoding="utf-8")
        ok("appStorage.json updated (backup at appStorage.json.bak)")
    except Exception as exc:
        warn(f"Failed to edit appStorage.json: {exc}")
        warn('Disable "Minimize to tray" and "Launch on startup" manually '
             "in Roblox settings.")


def step_roblox_storage() -> None:
    step("Step 4/7 - Roblox: disable MinimizeToTray & LaunchAtStartup")
    enforce_roblox_startup_values(kill_roblox=True)


# ----------------------------------------------------------------------------
# 5. SirHurt: excluded folder -> AV exclusion -> download -> extract
# ----------------------------------------------------------------------------
def add_defender_exclusions() -> None:
    try:
        ps = lambda cmd: subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", cmd],
            capture_output=True, check=False)

        res = ps(f"(Get-MpPreference).ExclusionPath")
        existing = str(SIRHURT_DIR).lower() in (res.stdout or b"").decode(
            errors="replace").lower()
        if existing:
            ok("Defender exclusion already present")
        else:
            res2 = ps(f"Add-MpPreference -ExclusionPath "
                      f"'{SIRHURT_DIR}'")
            if res2.returncode == 0:
                ok(f"Defender exclusion added for: {SIRHURT_DIR}")
            else:
                raise RuntimeError("Add-MpPreference returned "
                                   f"{res2.returncode}")

        for proc_name in ("SirHurt.exe", "Bootstrapper.exe"):
            ps(f"Add-MpPreference -ExclusionProcess '{proc_name}' "
               f"-ErrorAction SilentlyContinue")
    except Exception:
        warn("Could not add Windows Defender exclusions (third-party AV?).")
        warn(f"Add {SIRHURT_DIR} to your AV exclusion/whitelist MANUALLY, "
             "then press Enter.")
        input("Press Enter once the AV exclusion is in place")


# ----------------------------------------------------------------------------
# 5a. Automated gofile download (headless browser; falls back to the
#     manual watcher below if Playwright/Chromium is unavailable)
# ----------------------------------------------------------------------------
GOFILE_CODE = "RE0cXfkA"   # official SirHurt V5 distribution share


def try_gofile_download(dest: Path, skip: bool = False) -> Path | None:
    """Download the SirHurt archive from the gofile share via a headless
    Chromium. Returns the path on success, None on failure
    (caller falls back to the manual watcher)."""
    if skip:
        return None
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        warn("Playwright not installed - falling back to manual download.")
        return None

    dl_dir = dest.parent / ".gofile_dl_tmp"
    dl_dir.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            launch_kwargs = dict(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            try:
                browser = p.chromium.launch(**launch_kwargs)
            except Exception:
                # No bundled Chromium - drive the installed system Chrome.
                browser = p.chromium.launch(channel="chrome", **launch_kwargs)
            ctx = browser.new_context(accept_downloads=True, user_agent=UA)
            page = ctx.new_page()
            page.goto(f"https://gofile.io/d/{GOFILE_CODE}",
                      wait_until="domcontentloaded", timeout=120_000)
            btn = page.locator('button[data-action="download"]')
            btn.first.wait_for(state="visible", timeout=120_000)
            btn.first.scroll_into_view_if_needed()
            with page.expect_download(timeout=600_000) as dl_info:
                btn.first.click()
            tmp_path = dl_info.value.path()
            shutil.move(str(tmp_path), dest)
            ctx.close()
        ok(f"Downloaded from gofile: {dest.name} "
           f"({dest.stat().st_size / 1048576:.1f} MB)")
        return dest
    except Exception as exc:
        warn(f"gofile auto-download failed ({exc}) - falling back to "
             "manual download.")
        return None
    finally:
        shutil.rmtree(dl_dir, ignore_errors=True)


def find_sirhurt_archive(watch_start: datetime) -> Path | None:
    """Newest zip/rar/7z in Downloads / Desktop / Documents (top level only).

    Prefer files with 'sirhurt' in the name; otherwise only accept archives
    that appeared AFTER the watcher started (skips old unrelated downloads).
    """
    candidates: list[Path] = []
    for sub in ("Downloads", "Desktop", "Documents"):
        d = Path(os.environ.get("USERPROFILE", Path.home())) / sub
        if not d.is_dir():
            continue
        for p in d.iterdir():
            if not p.is_file() or p.suffix.lower() not in (".zip", ".rar", ".7z"):
                continue
            if re.search("sirhurt", p.name, re.IGNORECASE) or \
                    datetime.fromtimestamp(p.stat().st_ctime) > watch_start:
                candidates.append(p)

    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def wait_for_archive(sirhurt_dir: Path) -> Path:
    print("", flush=True)
    print("  ACTION REQUIRED - download SirHurt manually:")
    print("    1. The official site is opening in your browser.")
    print("    2. Save the SirHurt archive (zip/rar/7z) anywhere in")
    print("       Downloads, Desktop or Documents.")
    print(f"    3. It will be detected automatically and moved to {sirhurt_dir}")

    os.startfile("https://sirhurt.net/login/download.php")

    print("  Watching Downloads / Desktop / Documents for the archive "
          "(5 s interval)...", flush=True)
    watch_start = datetime.now()
    while True:
        time.sleep(5)
        found = find_sirhurt_archive(watch_start)
        if not found:
            continue
        # Give the browser time to finish writing, then require a stable size
        # across two checks so we never move a half-downloaded file.
        size1 = found.stat().st_size
        time.sleep(3)
        found2 = find_sirhurt_archive(watch_start)
        if found2 and str(found2) == str(found) and found2.stat().st_size == size1:
            archive = sirhurt_dir / "SirHurt V5.zip"
            shutil.move(str(found), archive)
            ok(f"Detected and moved: {found.name} -> {archive}")
            return archive


def extract_archive(path: Path, dest: Path, seven_zip: Path | None) -> bool:
    """Extract with 7-Zip when available, falling back to zipfile
    / Expand-Archive."""
    if seven_zip and seven_zip.exists():
        res = subprocess.run(
            [str(seven_zip), "x", str(path), f"-o{dest}", "-y",
             "-bso0", "-bsp0"],
            capture_output=True, check=False)
        return res.returncode == 0

    # Built-in fallback (only handles .zip)
    if path.suffix.lower() == ".zip":
        try:
            with zipfile.ZipFile(path) as zf:
                zf.extractall(dest)
            return True
        except Exception as exc:
            warn(f"zipfile extraction failed ({exc})")
            return False

    # Last resort: PowerShell Expand-Archive (zip only, rar/7z unsupported)
    try:
        res = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command",
             f"Expand-Archive -LiteralPath '{path}' "
             f"-DestinationPath '{dest}' -Force"],
            capture_output=True, check=False)
        if res.returncode == 0:
            return True
        warn(f"Expand-Archive failed "
             f"({res.stderr.decode(errors='replace').strip()})")
    except Exception as exc:
        warn(f"Expand-Archive failed ({exc})")
    return False


def step_sirhurt(seven_zip: Path | None, skip_gofile: bool = False) -> Path:
    step("Step 5/7 - SirHurt folder, AV exclusion, download & extract")

    SIRHURT_DIR.mkdir(parents=True, exist_ok=True)
    ok(f"Dedicated folder ready: {SIRHURT_DIR}")

    add_defender_exclusions()

    # Automated gofile download first; reuse an existing complete archive;
    # manual watcher as last resort.
    archive = SIRHURT_DIR / "SirHurt V5.zip"
    if archive.exists() and archive.stat().st_size > 100_000_000:
        ok(f"Existing archive found: {archive}")
    else:
        archive = (try_gofile_download(archive, skip=skip_gofile)
                   or wait_for_archive(SIRHURT_DIR))

    # SirHurt V5 web zip is DOUBLE zipped: the downloaded archive contains
    # "sirhurt v5.zip", which itself holds the actual files. Extract both
    # layers.
    extract_dir = SIRHURT_DIR / "SirHurt"
    extract_dir.mkdir(parents=True, exist_ok=True)

    if extract_archive(archive, extract_dir, seven_zip):
        ok(f"Extracted outer archive to: {extract_dir}")

        # Layer 2: find the inner "sirhurt v5.zip" and extract it in place
        inners = [p for p in extract_dir.rglob("*.zip") if p.is_file()]
        if inners:
            inner = max(inners, key=lambda p: p.stat().st_size)
            inner_dest = inner.parent
            if extract_archive(inner, inner_dest, seven_zip):
                try:
                    inner.unlink()
                except OSError:
                    pass
            else:
                warn(f"Failed to extract inner zip: {inner} - extract it "
                     "manually")
        else:
            print("  No inner zip found (single-layer archive) - continuing.",
                  flush=True)
    else:
        warn(f"Extraction failed - extract {archive} manually with "
             f"7-Zip/WinRAR into {extract_dir}")
    return extract_dir


# ----------------------------------------------------------------------------
# 6. One-shot scheduled task: open the game page in the default browser
#    automatically at next logon (after the restart below)
# ----------------------------------------------------------------------------
GAME_URL = "https://www.roblox.com/games/189707/Natural-Disaster-Survival"
TASK_NAME = "OpenRobloxGamePageOnce"


def step_register_task() -> None:
    step("Step 6/7 - Register post-logon task")

    # If this script runs as a compiled exe (Nuitka), the task invokes the
    # exe itself with --post-logon; otherwise fall back to opening the
    # game page in the default browser.
    me = Path(sys.argv[0]).resolve()
    if me.suffix.lower() == ".exe" and me.exists():
        task_exe, task_args = me, "--post-logon"
        desc = "SirHurt post-logon phase (Roblox + bootstrapper)"
    else:
        open_cmd = (
            f"Start-Process '{GAME_URL}'; "
            f"Unregister-ScheduledTask -TaskName '{TASK_NAME}' -Confirm:$false"
        )
        encoded = base64.b64encode(open_cmd.encode("utf-16-le")).decode("ascii")
        task_exe = "powershell.exe"
        task_args = f"-NoProfile -WindowStyle Hidden -EncodedCommand {encoded}"
        desc = "Opens the Roblox game page once after logon"

    # Build the task with PowerShell's ScheduledTasks module (same cmdlets
    # the original script used) - executed via -EncodedCommand so quoting
    # stays safe.
    ps_setup = (
        f"$action  = New-ScheduledTaskAction -Execute '{task_exe}' "
        f"-Argument '{task_args}'; "
        f"$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME; "
        f"$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries "
        f"-DontStopIfGoingOnBatteries -ExecutionTimeLimit "
        f"(New-TimeSpan -Minutes 15); "
        f"Register-ScheduledTask -TaskName '{TASK_NAME}' -Action $action "
        f"-Trigger $trigger -Settings $settings -Description "
        f"'{desc}' -Force"
    )
    encoded_setup = base64.b64encode(
        ps_setup.encode("utf-16-le")).decode("ascii")

    res = subprocess.run(
        ["powershell.exe", "-NoProfile", "-EncodedCommand", encoded_setup],
        capture_output=True, check=False)
    if res.returncode != 0:
        warn(f"Failed to register scheduled task: "
             f"{res.stderr.decode(errors='replace').strip()}")
        return
    ok(f"Task '{TASK_NAME}' registered (runs once at next logon, then is "
       "removed)")


# ----------------------------------------------------------------------------
# 7. Automatic restart
# ----------------------------------------------------------------------------
def step_restart(extract_dir: Path) -> None:
    step("Step 7/7 - Restarting automatically")
    print("  The PC will RESTART in 15 seconds - save your work!")
    print(f"  After logon the default browser opens: {GAME_URL}")

    # /g restarts AND re-opens signed-in apps; /a aborts if the user needs
    # to cancel
    subprocess.run(
        ["shutdown.exe", "/g", "/t", "15", "/c",
         "SirHurt setup finished - restarting to complete installation"],
        check=False)



# ----------------------------------------------------------------------------
# 8. Post-logon phase (run by the scheduled task / compiled exe
#    --post-logon): game page -> Roblox install -> startup values ->
#    relaunch Roblox -> elevate the SirHurt Bootstrapper
# ----------------------------------------------------------------------------
ROBLOX_DL_URL = "https://www.roblox.com/download/client?os=win"


def roblox_running() -> bool:
    res = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq RobloxPlayerBeta.exe", "/NH"],
        capture_output=True, text=True, check=False)
    return "RobloxPlayerBeta" in (res.stdout or "")


def wait_for_roblox_close(timeout_s: int = 600) -> None:
    print("  Waiting for Roblox to close (so it flushes localStorage)...",
          flush=True)
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if not roblox_running():
            return
        time.sleep(5)
    warn("Roblox still running after timeout - killing it.")
    subprocess.run(["taskkill", "/F", "/IM", "RobloxPlayerBeta.exe"],
                   capture_output=True, check=False)


def launch_bootstrapper(extract_dir: Path) -> None:
    bootstrappers = list(Path(extract_dir).rglob("Bootstrapper.exe")) + \
        list(Path(extract_dir).rglob("SirHurt*.exe"))
    bootstrappers = [b for b in bootstrappers if b.is_file()]
    if not bootstrappers:
        warn(f"No Bootstrapper found in {extract_dir} - start it manually.")
        return
    boot = max(bootstrappers, key=lambda p: p.stat().st_size)
    print(f"  Launching {boot.name} as Administrator...", flush=True)
    ret = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", str(boot), None, str(boot.parent), 1)
    if ret <= 32:
        warn(f"Could not elevate {boot.name} (code {ret}) - start it "
             "manually as Administrator.")
    else:
        ok(f"Bootstrapper launched: {boot}")


def run_post_logon() -> None:
    step("Post-logon phase - Roblox install + SirHurt bootstrapper")
    extract_dir = SIRHURT_DIR / "SirHurt"

    # 1. Open the game page so the user can log in while Roblox installs
    print(f"  Opening {GAME_URL} in the default browser...", flush=True)
    os.startfile(GAME_URL)

    # 2. Roblox client: silent install (the launcher installs by itself)
    if not roblox_running():
        launcher = get_file(ROBLOX_DL_URL, TMP / "RobloxPlayerLauncher.exe")
        print("  Installing Roblox (silent)...", flush=True)
        run_installer(launcher, [])

    # 3. Enforce startup values (Roblox rewrites localStorage on exit)
    enforce_roblox_startup_values()

    # 4. Wait until the user joined a game / Roblox is up, then relaunch
    #    Roblox fresh so the enforced values take effect, then elevate
    #    the Bootstrapper while Roblox is open.
    wait_for_roblox_close()
    time.sleep(3)
    # locate the newest RobloxPlayerBeta.exe under %LOCALAPPDATA%\Roblox
    betas = list((Path(os.environ["LOCALAPPDATA"]) / "Roblox")
                 .rglob("RobloxPlayerBeta.exe"))
    if betas:
        beta_exe = max(betas, key=lambda p: p.stat().st_mtime)
        os.startfile(str(beta_exe))
        ok(f"Roblox launched: {beta_exe}")
    else:
        warn("RobloxPlayerBeta.exe not found - start Roblox manually.")

    time.sleep(10)  # give Roblox a moment to open
    launch_bootstrapper(extract_dir)

    step("POST-LOGON DONE")
    print("""
  Roblox is running with startup values enforced.
  The SirHurt Bootstrapper was launched elevated - wait 5-10 seconds
  in-game, then press Inject and log in.
""")


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------
def main() -> None:
    if not IS_WINDOWS:
        print("This script must run on Windows.")
        sys.exit(1)

    ap = argparse.ArgumentParser(
        description="SirHurt one-click setup "
        "(VC++, .NET, 7-Zip, Roblox config, download & extract SirHurt)")
    ap.add_argument("--post-logon", action="store_true",
                    help="run the post-logon phase (Roblox install, "
                    "startup values, bootstrapper) and exit")
    ap.add_argument("--skip-gofile", action="store_true",
                    help="skip the automated gofile download and watch "
                    "for a manual download instead")
    args = ap.parse_args()

    # argparse handled --help/-h above (no UAC prompt) - safe to test flags
    if args.post_logon:
        self_elevate()  # exits if not elevated yet
        run_post_logon()
        return

    self_elevate()  # exits if not elevated yet

    print("", flush=True)
    print(f"SirHurt setup starting - log: {LOG_FILE}", flush=True)

    TMP.mkdir(parents=True, exist_ok=True)
    extract_dir = SIRHURT_DIR / "SirHurt"  # fallback if step 5 fails early

    # All of steps 1-5 are best-effort: a failure here is reported but must
    # NEVER prevent steps 6-7 (scheduled task + restart) from running.
    seven_zip = None
    try:
        step_vc_redist()
        step_dotnet()
        seven_zip = step_sevenzip()
        step_roblox_storage()
        extract_dir = step_sirhurt(seven_zip,
                                   skip_gofile=args.skip_gofile)
    except Exception as exc:
        print("", flush=True)
        warn(f"Setup step failed: {exc}")
        warn("Continuing anyway - the restart and post-logon task still run.")
        warn(f"Full log: {LOG_FILE}")

    step_register_task()
    step_restart(extract_dir)

    step("ALL DONE")
    print(f"""
  Summary
  -------
  - VC++ Redistributables (x64 + x86)    : installed
  - .NET SDK {DOTNET_VERSION} (x64 + x86)  : installed
  - 7-Zip                                : installed
  - Roblox MinimizeToTray/LaunchAtStartup: disabled (backup written)
  - SirHurt folder (AV-excluded)         : {SIRHURT_DIR}
  - SirHurt extracted to                 : {extract_dir}
  - Post-logon task                      : registered (one-shot)
  - Restart                              : in 15 seconds

  AFTER THE RESTART (all automatic)
  ---------------------------------
  1. Log in - the default browser opens {GAME_URL} by itself.
  2. Open Roblox via Sirstrap and join a game.
  3. Run the SirHurt Bootstrapper from {extract_dir} as Administrator.
  4. Wait 5-10 seconds in-game, then press Inject and log in.
""")


if __name__ == "__main__":
    main()
