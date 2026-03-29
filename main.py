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
from datetime import datetime

# --- Dependency Bootstrap ---
def check_deps():
    """
    Handles dependencies. In a compiled EXE environment, we assume 
    dependencies are already bundled via Nuitka/PyInstaller.
    """
    try:
        import questionary
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
    except ImportError:
        # If running from source, attempt to install
        if not hasattr(sys, 'frozen'):
            print("[*] Initializing environment and installing UI dependencies...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "questionary", "rich", "requests"])
                os.execv(sys.executable, [sys.executable] + sys.argv)
            except Exception as e:
                print(f"[!] Failed to install dependencies: {e}")
                sys.exit(1)
        else:
            print("[!] Critical Error: Dependencies missing in compiled executable.")
            sys.exit(1)

# Only run dependency check if not being imported or analyzed by a compiler
if __name__ == "__main__" and not hasattr(sys, 'frozen'):
    check_deps()

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import questionary

console = Console()

# --- Configuration ---
if hasattr(sys, 'frozen'):
    # When running as an EXE, sys.executable is the path to the EXE
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    APP_PATH = os.path.abspath(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_PATH = os.path.abspath(__file__)

LOG_FILE = os.path.join(BASE_DIR, "troubleshoot_log.txt")

CONFIG = {
    "WORK_DIR": BASE_DIR,
    "RUNTIMES": {
        "VC_X64": "https://aka.ms/vs/17/release/vc_redist.x64.exe",
        "VC_X86": "https://aka.ms/vs/17/release/vc_redist.x86.exe",
        "DOTNET": "https://dotnet.microsoft.com/download/dotnet/scripts/v1/dotnet-install.ps1" 
    },
    "DOWNLOAD_URL": "https://sirhurt.net/login/download.php"
}

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
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
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

def download_file(url, dest):
    r = requests.get(url, stream=True)
    with open(dest, 'wb') as f:
        for data in r.iter_content(chunk_size=4096):
            f.write(data)

def set_run_once():
    """Sets the EXE or script to run once after the next reboot."""
    log_event("Setting RunOnce registry key.")
    key_path = r"Software\Microsoft\Windows\CurrentVersion\RunOnce"
    try:
        # Important: RunOnce requires specific quoting for arguments
        if hasattr(sys, 'frozen'):
            # Path to EXE + Argument
            cmd = f'"{APP_PATH}" --post-restart'
        else:
            # Path to Python Interpreter + Script Path + Argument
            cmd = f'"{sys.executable}" "{APP_PATH}" --post-restart'
            
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
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
    # /r = restart, /f = force apps to close, /t 0 = immediate
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
            console.print(f"\n[yellow][!] No response for {timeout}s. Continuing automatically...[/yellow]")
            return True
        time.sleep(0.5)
    return result[0]

# --- Integrated Cleaner Logic ---
def run_integrated_cleaner(auto_confirm=False):
    console.print(Panel("[bold magenta]INTEGRATED CLEANER[/bold magenta]\nTargeting all known Roblox, SirHurt, and Account traces...", title="Cleaning"))
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
        os.path.join(local_app_data, "Roblox", "logs")
    ]

    file_targets = [
        os.path.join(user_profile, "AppData", "LocalLow", "rbxcsettings.rbx"),
        os.path.join(local_app_data, "Roblox", "GlobalBasicSettings_13.xml"),
        os.path.join(local_app_data, "Roblox", "RobloxCookies.dat"),
        os.path.join(local_app_data, "Roblox", "frm.cfg"),
        os.path.join(local_app_data, "Roblox", "AnalysticsSettings.xml")
    ]

    wildcard_targets = [
        os.path.join(temp_dir, "RBX-*.log"),
        os.path.join(local_app_data, "Microsoft", "CLR_v4.0_32", "UsageLogs", "*"),
        os.path.join(local_app_data, "Microsoft", "CLR_v4.0", "UsageLogs", "*"),
        os.path.join(system_root, "Temp", "*"),
        # Added targets for SirHurt V5 / Web folders and zips in working directory
        os.path.join(BASE_DIR, "Sirhurt V5"),
        os.path.join(BASE_DIR, "Sirhurt V5 Web"),
        os.path.join(BASE_DIR, "Sirhurt V5.zip"),
        os.path.join(BASE_DIR, "Sirhurt V5 Web.zip")
    ]

    for target in dir_targets:
        if os.path.exists(target):
            try:
                should_delete = True if auto_confirm else questionary.confirm(f"Delete folder: {target}?").ask()
                if should_delete:
                    log_event(f"Deleting directory: {target}")
                    shutil.rmtree(target, ignore_errors=True)
                    if os.path.exists(target):
                        subprocess.run(f'rd /s /q "{target}"', shell=True, capture_output=True)
            except Exception as e:
                log_event(f"Error cleaning directory {target}: {e}")

    for target in file_targets:
        if os.path.exists(target):
            try:
                log_event(f"Deleting file: {target}")
                os.remove(target)
            except Exception as e:
                log_event(f"Error deleting file {target}: {e}")

    for pattern in wildcard_targets:
        for target in glob.glob(pattern):
            try:
                if os.path.isfile(target):
                    log_event(f"Deleting wildcard file: {target}")
                    os.remove(target)
                elif os.path.isdir(target):
                    log_event(f"Deleting wildcard directory: {target}")
                    shutil.rmtree(target, ignore_errors=True)
            except Exception as e:
                log_event(f"Error cleaning wildcard item {target}: {e}")

    local_temp = os.path.join(local_app_data, "Temp")
    if os.path.exists(local_temp):
        log_event("Cleaning Local Temp contents")
        for item in os.listdir(local_temp):
            item_path = os.path.join(local_temp, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                else:
                    os.remove(item_path)
            except:
                pass

    console.print("[cyan][*] Resetting Network Configuration...[/cyan]")
    log_event("Performing network reset.")
    subprocess.run("ipconfig /flushdns", shell=True, capture_output=True)
    subprocess.run("netsh winsock reset", shell=True, capture_output=True)

    console.print("[bold green]✓ Cleanup Finished.[/bold green]")

# --- Core Logic ---
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

def install_runtimes(audit_results):
    if all(audit_results.values()):
        console.print("[green]All runtimes already installed![/green]")
        return

    log_event("Starting runtime installation.")
    console.print(Panel("[bold yellow]Missing Runtimes Detected[/bold yellow]\nDownloading and installing requirements.", title="Auto-Installer"))
    
    temp_dir = os.path.join(CONFIG["WORK_DIR"], "temp_runtimes")
    os.makedirs(temp_dir, exist_ok=True)

    vc_to_install = []
    if not audit_results["vc64"]: vc_to_install.append(("VC++ x64", CONFIG["RUNTIMES"]["VC_X64"], "vc_redist_x64.exe"))
    if not audit_results["vc86"]: vc_to_install.append(("VC++ x86", CONFIG["RUNTIMES"]["VC_X86"], "vc_redist_x86.exe"))

    for name, url, filename in vc_to_install:
        dest = os.path.join(temp_dir, filename)
        console.print(f"[*] Downloading {name}...")
        download_file(url, dest)
        console.print(f"[*] Installing {name}... (Quiet mode)")
        subprocess.run([dest, "/q", "/norestart"], check=False)

    if not audit_results["dotnet"]:
        console.print("[*] Installing .NET SDK via Microsoft Install Script...")
        script_path = os.path.join(temp_dir, "dotnet-install.ps1")
        download_file(CONFIG["RUNTIMES"]["DOTNET"], script_path)
        subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path, "-Channel", "8.0", "-Runtime", "dotnet"], check=False)

def run_fix_sequence():
    if not is_admin():
        elevate_to_admin()

    log_event("Starting Full Fix sequence.")
    with console.status("[bold cyan]Applying Security Exclusions...", spinner="dots"):
        subprocess.run(["powershell", "-Command", f"Add-MpPreference -ExclusionPath '{CONFIG['WORK_DIR']}'"], capture_output=True)

    os.chdir(CONFIG["WORK_DIR"])

    console.print(Panel("[bold cyan]PHASE 1: PREPARATION[/bold cyan]\nThe script will now begin the deep clean and prepare for reboot.", title="Step 1"))
    
    with console.status("[bold red]Nuking processes...", spinner="dots"):
        procs = [
            "RobloxPlayerBeta.exe", 
            "RobloxPlayerLauncher.exe", 
            "SirHurt.exe",
            "Sirstrap.exe",
            "Bloxstrap.exe",
            "Fishstrap.exe",
            "Voidstrap.exe"
        ]
        for p in procs:
            log_event(f"Killing process: {p}")
            subprocess.run(f"taskkill /F /IM {p} /T", shell=True, capture_output=True)
        time.sleep(2)

    run_integrated_cleaner(auto_confirm=True)

    console.print(Panel("[bold green]CLEANUP COMPLETE[/bold green]\nI will now set the script to auto-start once after the reboot.", title="System Setup"))
    
    if set_run_once():
        log_event("Troubleshooting complete, awaiting reboot.")
        if timed_confirm("Mandatory reboot required. Restart now?"):
            restart_pc()
        else:
            console.print("[yellow]Please restart manually. The script will resume on login.[/yellow]")
    else:
        console.print("[bold red]Critical Error: Failed to set the post-restart trigger.[/bold red]")
        log_event("Failed fix: Post-restart trigger could not be set.")

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

def main():
    # Check if we are starting up after a restart
    # We check sys.argv for the flag
    is_post_restart = "--post-restart" in sys.argv

    if not is_admin():
        elevate_to_admin()

    log_event(f"Script session started. Post-restart: {is_post_restart}")
    
    if is_post_restart:
        show_post_restart_instructions()
        sys.exit()

    while True:
        console.clear()
        console.print(Panel.fit(f" [bold blue]SirHurt Awesome Sauce Troubleshooting Script[/bold blue] \n [small white]Location: {CONFIG['WORK_DIR']}[/small white]"))
        results = system_audit()
        
        choice = questionary.select(
            "Main Menu:",
            choices=[
                "Run Full Fix (Automated + Reboot)",
                "Install Missing Runtimes (.NET/VC++)",
                "Clean Account Traces & Roblox Cache",
                "Open Troubleshooting Log",
                "Exit"
            ]
        ).ask()

        if choice == "Run Full Fix (Automated + Reboot)":
            run_fix_sequence()
            break
        elif choice == "Install Missing Runtimes (.NET/VC++)":
            install_runtimes(results)
            questionary.press_any_key_to_continue("Press any key to refresh audit...").ask()
        elif choice == "Clean Account Traces & Roblox Cache":
            run_integrated_cleaner(auto_confirm=False)
            questionary.press_any_key_to_continue("Cleaning finished. Press any key...").ask()
        elif choice == "Open Troubleshooting Log":
            if os.path.exists(LOG_FILE):
                os.startfile(LOG_FILE)
            else:
                console.print("[yellow]Log file not found yet.[/yellow]")
                time.sleep(1)
        else:
            log_event("Script session ended by user.")
            break

if __name__ == "__main__":
    main()