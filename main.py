import os
import requests
import zipfile
import io
import subprocess
import time
import sys
import winreg
import ctypes
import threading
import shutil
import glob
import json
from datetime import datetime
import urllib3

# --- SSL Error Suppression ---
# Essential for troubleshooters running on systems with broken root certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Optimized Imports for Nuitka ---
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    import questionary
except ImportError:
    pass

console = Console()

# --- Configuration ---
IS_FROZEN = hasattr(sys, "frozen")
if IS_FROZEN:
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    APP_PATH = os.path.abspath(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_PATH = os.path.abspath(__file__)

LOG_FILE = os.path.join(BASE_DIR, "troubleshoot_log.txt")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

CONFIG = {
    "WORK_DIR": BASE_DIR,
    "RUNTIMES": {
        "VC_X64": "https://aka.ms/vc14/vc_redist.x64.exe",
        "VC_X86": "https://aka.ms/vc14/vc_redist.x86.exe",
        "DOTNET": "https://builds.dotnet.microsoft.com/dotnet/Sdk/10.0.201/dotnet-sdk-10.0.201-win-x64.exe",
    },
    "DOWNLOAD_URL": "https://sirhurt.net/login/download.php",
}

# --- Settings Management ---
DEFAULT_SETTINGS = {
    "quiet_install": True,
    "apply_24h2_patch": True
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
        except:
            return DEFAULT_SETTINGS
    return DEFAULT_SETTINGS

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        log_event(f"Failed to save settings: {e}")

APP_SETTINGS = load_settings()

# --- Utility Functions ---
def log_event(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except:
        pass


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def elevate_to_admin():
    if not is_admin():
        console.print("[yellow][*] Requesting Administrator permissions...[/yellow]")
        log_event("Requesting UAC elevation.")
        params = " ".join(sys.argv)
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1
        )
        sys.exit()


def check_runtime(registry_path):
    try:
        winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path)
        return True
    except FileNotFoundError:
        try:
            wow_path = registry_path.replace("SOFTWARE\\", "SOFTWARE\\WOW6432Node\\")
            winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, wow_path)
            return True
        except FileNotFoundError:
            return False


def download_file(url, dest, timeout=180):
    """
    Downloads a file with a robust fallback for SSL/Certificate bundle issues
    common in compiled Python environments.
    """
    headers = {"User-Agent": "Sentinel/1.0"}
    
    try:
        # Standard attempt
        r = requests.get(url, stream=True, allow_redirects=True, timeout=timeout, headers=headers)
    except (requests.exceptions.SSLError, OSError) as e:
        # Fallback for "Could not find a suitable TLS CA certificate bundle"
        log_event(f"SSL/Cert Error encountered: {e}. Retrying without verification...")
        r = requests.get(url, stream=True, allow_redirects=True, timeout=timeout, headers=headers, verify=False)
    
    r.raise_for_status()
    with open(dest, "wb") as f:
        for data in r.iter_content(chunk_size=8192):
            f.write(data)


def set_run_once():
    log_event("Setting RunOnce registry key.")
    key_path = r"Software\Microsoft\Windows\CurrentVersion\RunOnce"
    try:
        if IS_FROZEN:
            cmd = f'"{APP_PATH}" --post-restart'
        else:
            cmd = f'"{sys.executable}" "{APP_PATH}" --post-restart'

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "SirHurtTroubleshooter", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        log_event(f"RunOnce successfully set: {cmd}")
        return True
    except Exception as e:
        log_event(f"Failed to set RunOnce: {e}")
        console.print(f"[bold red][!] Registry Error: {e}[/bold red]")
        return False


def restart_pc():
    log_event("User initiated system restart.")
    console.print("[bold red][!] Restarting PC in 5 seconds...[/bold red]")
    time.sleep(5)
    os.system("shutdown /r /f /t 0")


def timed_confirm(message, timeout=60):
    result = [None]

    def get_input():
        result[0] = questionary.confirm(message).ask()

    thread = threading.Thread(target=get_input)
    thread.daemon = True
    thread.start()

    start_time = time.time()
    while thread.is_alive():
        if time.time() - start_time > timeout:
            console.print(
                f"\n[yellow][!] No response for {timeout}s. Continuing automatically...[/yellow]"
            )
            return True
        time.sleep(0.5)
    return result[0]


# --- Logic Components ---

def disable_startup_tasks():
    """Removes Roblox from the Windows Startup registry keys."""
    log_event("Disabling Roblox startup tasks.")
    startup_paths = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run")
    ]
    
    for hkey, path in startup_paths:
        try:
            key = winreg.OpenKey(hkey, path, 0, winreg.KEY_ALL_ACCESS)
            # Iterate through values to find Roblox related entries
            idx = 0
            while True:
                try:
                    val_name, val_data, _ = winreg.EnumValue(key, idx)
                    if "roblox" in val_name.lower() or "roblox" in val_data.lower():
                        winreg.DeleteValue(key, val_name)
                        log_event(f"Removed startup entry: {val_name} from {path}")
                        # Don't increment idx since we deleted the current one
                        continue
                    idx += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception as e:
            # Common to fail on HKLM if permissions are weird, just log it
            log_event(f"Startup clean error on {path}: {e}")

def run_integrated_cleaner(auto_confirm=False, step_num="4"):
    console.print(Panel("[bold magenta]CLEANER[/bold magenta]\nTargeting all known Roblox, SirHurt, and Account traces...", title=f"Step {step_num}"))
    log_event("Starting integrated cleaner.")
    
    app_data = os.environ.get("APPDATA")
    local_app_data = os.environ.get("LOCALAPPDATA")
    user_profile = os.environ.get("USERPROFILE")
    temp_dir = os.environ.get("TEMP")
    system_root = os.environ.get("SystemRoot", "C:\\Windows")

    dir_targets = [
        os.path.join(app_data, "SirHurt"),
        os.path.join(app_data, "Roblox"),
        os.path.join(local_app_data, "SirHurt"),
        os.path.join(local_app_data, "Roblox"),
        os.path.join(local_app_data, "Roblox", "LocalStorage"),
        os.path.join(local_app_data, "Roblox", "logs"),
    ]

    file_targets = [
        os.path.join(user_profile, "AppData", "LocalLow", "rbxcsettings.rbx"),
        os.path.join(local_app_data, "Roblox", "GlobalBasicSettings_13.xml"),
        os.path.join(local_app_data, "Roblox", "RobloxCookies.dat"),
        os.path.join(local_app_data, "Roblox", "frm.cfg"),
        os.path.join(local_app_data, "Roblox", "AnalysticsSettings.xml"),
    ]

    wildcard_targets = [
        os.path.join(temp_dir, "RBX-*.log"),
        os.path.join(local_app_data, "Microsoft", "CLR_v4.0_32", "UsageLogs", "*"),
        os.path.join(local_app_data, "Microsoft", "CLR_v4.0", "UsageLogs", "*"),
        os.path.join(system_root, "Temp", "*"),
        os.path.join(BASE_DIR, "Sirhurt V5"),
        os.path.join(BASE_DIR, "Sirhurt V5 Web"),
        os.path.join(BASE_DIR, "Sirhurt V5.zip"),
        os.path.join(BASE_DIR, "Sirhurt V5 Web.zip"),
    ]

    for target in dir_targets:
        if os.path.exists(target):
            try:
                should_delete = True if auto_confirm else questionary.confirm(f"Delete folder: {target}?").ask()
                if should_delete:
                    shutil.rmtree(target, ignore_errors=True)
                    if os.path.exists(target):
                        subprocess.run(f'rd /s /q "{target}"', shell=True, capture_output=True)
            except Exception as e:
                log_event(f"Error cleaning directory {target}: {e}")

    for target in file_targets:
        if os.path.exists(target):
            try:
                os.remove(target)
            except Exception as e:
                log_event(f"Error deleting file {target}: {e}")

    for pattern in wildcard_targets:
        for target in glob.glob(pattern):
            try:
                if os.path.isfile(target):
                    os.remove(target)
                elif os.path.isdir(target):
                    shutil.rmtree(target, ignore_errors=True)
            except Exception as e:
                log_event(f"Error cleaning wildcard item {target}: {e}")

    local_temp = os.path.join(local_app_data, "Temp")
    if os.path.exists(local_temp):
        for item in os.listdir(local_temp):
            item_path = os.path.join(local_temp, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                else:
                    os.remove(item_path)
            except:
                pass

    subprocess.run("ipconfig /flushdns", shell=True, capture_output=True)
    subprocess.run("netsh winsock reset", shell=True, capture_output=True)


def fix_dpi_scaling():
    """Forces high-DPI scaling override for Roblox to fix drawing library offsets."""
    log_event("Executing DPI Scaling Fix.")
    local_app_data = os.environ.get("LOCALAPPDATA")
    versions_path = os.path.join(local_app_data, "Roblox", "Versions")
    
    if not os.path.exists(versions_path):
        return

    try:
        for folder in os.listdir(versions_path):
            exe_path = os.path.join(versions_path, folder, "RobloxPlayerBeta.exe")
            if os.path.exists(exe_path):
                key_path = r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"
                key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, exe_path, 0, winreg.REG_SZ, "~ HIGHDPIAWARE")
                winreg.CloseKey(key)
    except Exception as e:
        log_event(f"DPI Fix Error: {e}")


def force_24h2_update():
    """Applies registry patches to force Windows Update to target 24H2."""
    if not APP_SETTINGS.get("apply_24h2_patch"):
        log_event("Skipping 24H2 update patch per settings.")
        return

    log_event("Executing Force 24H2 Update Registry Patch.")
    try:
        path = r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate"
        key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "ProductVersion", 0, winreg.REG_SZ, "Windows 11")
        winreg.SetValueEx(key, "TargetReleaseVersionInfo", 0, winreg.REG_SZ, "24H2")
        winreg.SetValueEx(key, "TargetReleaseVersion", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
    except Exception as e:
        log_event(f"24H2 Force Update Error: {e}")


def install_runtimes(force_all=True, step_num="5"):
    log_event(f"Starting runtime installation sequence. Force all: {force_all}")
    
    mode_text = "quiet mode" if APP_SETTINGS['quiet_install'] else "visible mode"
    console.print(Panel(f"[bold yellow]RUNTIME MANAGER[/bold yellow]\nForce reinstalling libraries (VC++ & .NET 10 SDK) in {mode_text}.", title=f"Step {step_num}"))

    temp_dir = os.path.join(CONFIG["WORK_DIR"], "temp_runtimes")
    os.makedirs(temp_dir, exist_ok=True)

    vc_args = ["/repair", "/quiet", "/norestart"] if APP_SETTINGS['quiet_install'] else ["/repair"]
    dotnet_args = ["/install", "/quiet", "/norestart"] if APP_SETTINGS['quiet_install'] else ["/install"]

    runtime_tasks = [
        ("VC++ x64", CONFIG["RUNTIMES"]["VC_X64"], "vc_redist_x64.exe", vc_args),
        ("VC++ x86", CONFIG["RUNTIMES"]["VC_X86"], "vc_redist_x86.exe", vc_args),
        (".NET 10.0 SDK", CONFIG["RUNTIMES"]["DOTNET"], "dotnet_sdk_installer.exe", dotnet_args)
    ]

    for name, url, filename, args in runtime_tasks:
        dest = os.path.join(temp_dir, filename)
        try:
            console.print(f"[*] Downloading {name}...")
            download_file(url, dest)
            console.print(f"[*] Executing {name}... ({'Quiet' if APP_SETTINGS['quiet_install'] else 'Interactive'})")
            subprocess.run([dest] + args, capture_output=APP_SETTINGS['quiet_install'], timeout=900)
        except Exception as e:
            log_event(f"Failed to manage {name}: {e}")
            console.print(f"[bold red][!] Error with {name}: {e}[/bold red]")


# --- Combined Ultimate Fix ---

def run_ultimate_fix():
    if not is_admin():
        elevate_to_admin()

    log_event("Starting AIO.")
    
    # 1. Security Exclusions
    with console.status("[bold cyan]Step 1: Applying Security Exclusions...", spinner="dots"):
        subprocess.run(["powershell", "-Command", f"Add-MpPreference -ExclusionPath '{CONFIG['WORK_DIR']}'"], capture_output=True)
    console.print("[green][+] Security exclusions applied.[/green]")

    # 2. DPI, OS Patches & Startup Cleanup
    with console.status("[bold cyan]Step 2: Applying Compatibility, DPI & Startup Patches...", spinner="dots"):
        fix_dpi_scaling()
        force_24h2_update()
        disable_startup_tasks() # Integrated here
    console.print("[green][+] Screen scaling, 24H2 update, and Startup tasks patched.[/green]")

    # 3. Kill Processes
    with console.status("[bold red]Step 3: Nuking active processes...", spinner="dots"):
        procs = ["RobloxPlayerBeta.exe", "RobloxPlayerLauncher.exe", "SirHurt.exe", "Sirstrap.exe", "Bloxstrap.exe", "Fishstrap.exe", "Voidstrap.exe"]
        for p in procs:
            subprocess.run(f"taskkill /F /IM {p} /T", shell=True, capture_output=True)
        time.sleep(2)
    console.print("[green][+] Environment cleared of ghost processes.[/green]")

    # 4. Integrated Cleaner
    run_integrated_cleaner(auto_confirm=True, step_num="4")
    console.print("[green][+] Account traces, cache, and old versions cleared.[/green]")

    # 5. Runtime Reinstall
    install_runtimes(force_all=True, step_num="5")
    console.print("[green][+] All library dependencies reinstalled.[/green]")

    # 6. Set RunOnce & Finish
    console.print(Panel("[bold green] AIO FIX COMPLETE[/bold green]\nI will now set the script to auto-start once after the reboot.", title="System Setup"))
    
    if set_run_once():
        log_event("Troubleshooting complete, awaiting reboot.")
        if timed_confirm("Mandatory reboot required to apply library and OS changes. Restart now?"):
            restart_pc()
        else:
            console.print("[yellow]Please restart manually. The script will resume on login.[/yellow]")
    else:
        console.print("[bold red]Critical Error: Failed to set the post-restart trigger.[/bold red]")


def system_audit():
    table = Table(title="System Requirements Audit", border_style="bright_blue")
    table.add_column("Requirement", style="cyan")
    table.add_column("Status", justify="right")

    build = sys.getwindowsversion().build
    win_status = "[bold green]PASS[/bold green]" if build >= 26100 else "[bold yellow]OLD (24H2 Reqd)[/bold yellow]"
    table.add_row("Windows Build (24H2+)", win_status)

    v64 = check_runtime(r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64")
    v86 = check_runtime(r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x86")
    table.add_row("VC++ 2015-2022 x64", "[bold green]OK[/bold green]" if v64 else "[bold red]MISSING[/bold red]")
    table.add_row("VC++ 2015-2022 x86", "[bold green]OK[/bold green]" if v86 else "[bold red]MISSING[/bold red]")

    try:
        subprocess.check_output(["dotnet", "--version"], stderr=subprocess.STDOUT)
        table.add_row(".NET SDK", "[bold green]OK[/bold green]")
        dotnet_missing = False
    except:
        table.add_row(".NET SDK", "[bold red]MISSING[/bold red]")
        dotnet_missing = True

    console.print(table)
    return {"vc64": v64, "vc86": v86, "dotnet": not dotnet_missing}


def show_post_restart_instructions():
    console.clear()
    console.print(Panel.fit(
        f"[bold cyan]POST-RESTART INSTRUCTIONS[/bold cyan]\n\n"
        f"1. Download SirHurt: [bold white]{CONFIG['DOWNLOAD_URL']}[/bold white]\n"
        f"2. [bold yellow]EXTRACT[/bold yellow] the ZIP using 7zip or WinRAR (Windows default can fail).\n"
        f"3. Right-click the Bootstrapper and [bold red]RUN AS ADMINISTRATOR[/bold red].\n\n"
        f"The environment is now clean. Happy exploiting!",
        title="Final Steps",
        border_style="green"
    ))
    log_event("Post-restart instructions displayed.")
    input("\nPress Enter to finish and exit...")

def show_settings_menu():
    global APP_SETTINGS
    while True:
        console.clear()
        console.print(Panel.fit("[bold cyan]SCRIPT SETTINGS[/bold cyan]\nConfigure how the troubleshooter behaves."))
        
        q_status = "[ON]" if APP_SETTINGS['quiet_install'] else "[OFF]"
        p_status = "[ON]" if APP_SETTINGS['apply_24h2_patch'] else "[OFF]"

        choice = questionary.select(
            "Settings:",
            choices=[
                f"Toggle Quiet Runtime Installation (Current: {q_status})",
                f"Toggle 24H2 Update Patch (Current: {p_status})",
                "Back to Main Menu"
            ]
        ).ask()

        if choice.startswith("Toggle Quiet"):
            APP_SETTINGS['quiet_install'] = not APP_SETTINGS['quiet_install']
            save_settings(APP_SETTINGS)
        elif choice.startswith("Toggle 24H2"):
            APP_SETTINGS['apply_24h2_patch'] = not APP_SETTINGS['apply_24h2_patch']
            save_settings(APP_SETTINGS)
        else:
            break

def main():
    if not is_admin():
        elevate_to_admin()

    is_post_restart = "--post-restart" in sys.argv
    log_event(f"Script session started. Post-restart: {is_post_restart}")
    
    if is_post_restart:
        show_post_restart_instructions()
        sys.exit()

    while True:
        console.clear()
        console.print(Panel.fit(f" [bold blue]SirHurt Awesome Sauce Swag Troubleshooting[/bold blue] \n [small white]Location: {CONFIG['WORK_DIR']}[/small white]"))
        system_audit()
        
        choice = questionary.select(
            "Main Menu:",
            choices=[
                "Run Full Fix (NEEDS REBOOT)",
                "Force Reinstall Runtimes Only",
                "Force Clean Cache & Traces Only",
                "Open Troubleshooting Log",
                "Settings",
                "Exit"
            ]
        ).ask()

        if choice == "Run Full Fix (NEEDS REBOOT)":
            run_ultimate_fix()
            break
        elif choice == "Force Reinstall Runtimes Only":
            install_runtimes(force_all=True, step_num="1")
            questionary.press_any_key_to_continue("Press any key to return to menu...").ask()
        elif choice == "Force Clean Cache & Traces Only":
            run_integrated_cleaner(auto_confirm=False, step_num="1")
            questionary.press_any_key_to_continue("Cleaning finished. Press any key...").ask()
        elif choice == "Open Troubleshooting Log":
            if os.path.exists(LOG_FILE):
                os.startfile(LOG_FILE)
            else:
                console.print("[yellow]Log file not found yet.[/yellow]")
                time.sleep(1)
        elif choice == "Settings":
            show_settings_menu()
        else:
            log_event("Script session ended by user.")
            break


if __name__ == "__main__":
    main()