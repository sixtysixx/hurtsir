import os, sys, subprocess, ctypes, json

VERSION = "1.0.0"
# 1. Automatic Requirements Installation
def install_reqs():
    try:
        import textual
    except ImportError as e:
        import traceback
        traceback.print_exc()
        print(f"ImportError details: {e}")
        print("Installing Textual TUI framework...")
        import shutil
        commands = [
            ["uv", "pip", "install", "textual"],
            [sys.executable, "-m", "pip", "install", "textual"],
            [sys.executable, "-m", "ensurepip", "--default-pip"],
        ]
        success = False
        for cmd in commands:
            try:
                if cmd[0] == "uv" and not shutil.which("uv"):
                    continue
                subprocess.check_call(cmd)
                if cmd[-1] == "--default-pip":
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "textual"])
                success = True
                break
            except Exception:
                continue
        if not success:
            print("Error: Failed to install 'textual'. Please install it manually.", file=sys.stderr)
            sys.exit(1)
        os.execv(sys.executable, ['python'] + sys.argv)

# 2. Self-Elevation
def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

if __name__ == "__main__":
    if not is_admin():
        script = os.path.abspath(sys.argv[0])
        params = f'"{script}"'
        if len(sys.argv) > 1:
            params += " " + " ".join(f'"{arg}"' for arg in sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, os.getcwd(), 1)
        sys.exit()
    install_reqs()

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, RichLog, ContentSwitcher
from textual.containers import Container
from textual.binding import Binding
from textual.screen import ModalScreen


class UpdateModal(ModalScreen):
    CSS = """
    UpdateModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }
    
    #dialog {
        layout: vertical;
        padding: 1 2;
        width: 50;
        height: auto;
        border: thick #4A0072;
        background: #111111;
        color: #ffffff;
    }
    
    #question {
        text-align: center;
        margin-bottom: 1;
        height: auto;
    }
    
    #buttons {
        layout: horizontal;
        height: auto;
        align: center middle;
        width: 100%;
    }
    
    #buttons Button {
        width: 15;
        margin: 0 1;
    }
    """
    
    def __init__(self, remote_version: str, remote_content: str):
        super().__init__()
        self.remote_version = remote_version
        self.remote_content = remote_content
        
    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Static(f"[bold]Update Available[/bold]\n\nA new version ({self.remote_version}) of Roblox Monitor is available. Would you like to update now?", id="question")
            with Container(id="buttons"):
                yield Button("Yes", variant="success", id="yes")
                yield Button("No", variant="error", id="no")
                
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            self.dismiss(True)
        else:
            self.dismiss(False)
class RobloxManager(App):
    CSS = """
    Screen {
        background: #000000;
        color: #ffffff;
        layout: vertical;
    }
    
    #banner {
        text-align: center;
        width: 100%;
        padding: 1 0;
        border-bottom: double #4A0072;
        background: #000000;
        height: auto;
    }
    
    #pane-container {
        layout: grid;
        grid-size: 2 1;
        grid-columns: 1fr 2fr;
        height: 1fr;
    }
    
    #left-pane {
        border-right: double #4A0072;
        padding: 0 2;
        align: center middle;
        height: 100%;
        background: #000000;
    }
    
    #right-pane {
        padding: 0 2;
        height: 100%;
        background: #000000;
    }
    
    #status_text {
        text-align: center;
        margin: 0 0 1 0;
        padding: 1;
        border: round #ffffff;
        height: auto;
        background: #000000;
        color: #ffffff;
    }
    
    Button {
        width: 100%;
        margin: 0 0 1 0;
        background: #111111;
        color: #ffffff;
        border: tall #ffffff;
    }
    
    Button:focus {
        background: #4A0072;  /* Dark violet */
        color: #ffffff;
        border: tall #ffffff;
        text-style: bold;
    }
    
    Button.success, Button.error, Button.primary, Button.default {
        background: #111111;
        color: #ffffff;
        border: tall #ffffff;
    }
    
    Button.success:focus, Button.error:focus, Button.primary:focus, Button.default:focus {
        background: #4A0072;
        color: #ffffff;
        border: tall #ffffff;
        text-style: bold;
    }
    
    Button.success:hover, Button.error:hover, Button.primary:hover, Button.default:hover, Button:hover {
        background: #222222;
        color: #ffffff;
        border: tall #ffffff;
    }
    
    RichLog {
        border: round #ffffff;
        background: #000000;
        color: #ffffff;
        height: 1fr;
        margin-top: 1;
    }
    
    Header {
        background: #000000;
        color: #ffffff;
        border-bottom: solid #4A0072;
    }
    
    Footer {
        background: #000000;
        color: #ffffff;
        border-top: solid #4A0072;
    }
    """

    BINDINGS = [
        Binding("up", "focus_previous", "Focus Previous", show=False),
        Binding("down", "focus_next", "Focus Next", show=False),
        Binding("left", "focus_previous", "Focus Previous", show=False),
        Binding("right", "focus_next", "Focus Next", show=False),
        Binding("w", "focus_previous", "Focus Previous", show=False),
        Binding("s", "focus_next", "Focus Next", show=False),
        Binding("a", "focus_previous", "Focus Previous", show=False),
        Binding("d", "focus_next", "Focus Next", show=False),
        Binding("1", "press_register", "Register", show=False),
        Binding("2", "press_copy", "Copy Logs", show=False),
        Binding("3", "press_clean", "Clean Logs", show=False),
        Binding("4", "press_exit", "Exit", show=False),
        Binding("5", "press_back", "Back", show=False),
    ]

    def action_press_register(self) -> None:
        current_menu = self.query_one("#menu_switcher", ContentSwitcher).current
        if current_menu == "main_menu":
            self.query_one("#goto_task", Button).press()
        elif current_menu == "task_menu":
            self.query_one("#start_task", Button).press()
        elif current_menu == "logs_menu":
            self.query_one("#clean_logs", Button).press()

    def action_press_copy(self) -> None:
        current_menu = self.query_one("#menu_switcher", ContentSwitcher).current
        if current_menu == "main_menu":
            self.query_one("#goto_logs", Button).press()
        elif current_menu == "task_menu":
            self.query_one("#stop_task", Button).press()
        elif current_menu == "logs_menu":
            self.query_one("#copy_logs", Button).press()

    def action_press_clean(self) -> None:
        current_menu = self.query_one("#menu_switcher", ContentSwitcher).current
        if current_menu == "main_menu":
            self.exit()
        elif current_menu == "task_menu":
            self.query_one("#register_task", Button).press()
        elif current_menu == "logs_menu":
            self.query_one("#toggle_logging", Button).press()

    def action_press_exit(self) -> None:
        current_menu = self.query_one("#menu_switcher", ContentSwitcher).current
        if current_menu == "task_menu":
            self.query_one("#deregister_task", Button).press()
        elif current_menu == "logs_menu":
            self.query_one("#menu_switcher", ContentSwitcher).current = "main_menu"

    def action_press_back(self) -> None:
        current_menu = self.query_one("#menu_switcher", ContentSwitcher).current
        if current_menu == "task_menu":
            self.query_one("#menu_switcher", ContentSwitcher).current = "main_menu"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            "[bold #4A0072]\n" +
            "  ███████╗██╗██╗  ██╗\n" +
            "  ██╔════╝██║╚██╗██╔╝\n" +
            "  ███████╗██║ ╚███╔╝ \n" +
            "  ╚════██║██║ ██╔██╗ \n" +
            "  ███████║██║██╔╝ ██╗\n" +
            "  ╚══════╝╚═╝╚═╝  ╚═╝\n" +
            "    R O B L O X   M O N I T O R[/bold #4A0072]",
            id="banner"
        )
        with Container(id="pane-container"):
            with Container(id="left-pane"):
                yield Static("Monitor Task: [bold yellow]CHECKING...[/bold yellow]", id="status_text")
                with ContentSwitcher(initial="main_menu", id="menu_switcher"):
                    with Container(id="main_menu"):
                        yield Button("[1] Task Management", id="goto_task", variant="primary")
                        yield Button("[2] Log Management", id="goto_logs", variant="primary")
                        yield Button("[3] Exit", id="exit", variant="default")
                    with Container(id="task_menu"):
                        yield Button("[1] Start Task", id="start_task", variant="success")
                        yield Button("[2] Stop Task", id="stop_task", variant="error")
                        yield Button("[3] Register Task", id="register_task", variant="success")
                        yield Button("[4] Deregister Task", id="deregister_task", variant="error")
                        yield Button("[5] Back", id="back_to_main_task", variant="default")
                    with Container(id="logs_menu"):
                        yield Button("[1] Clear Logs", id="clean_logs", variant="default")
                        yield Button("[2] Copy Logs", id="copy_logs", variant="primary")
                        yield Button("[3] Toggle Logging", id="toggle_logging", variant="success")
                        yield Button("[4] Back", id="back_to_main_logs", variant="default")
            with Container(id="right-pane"):
                yield Static("Real-time Monitor Logs:")
                yield RichLog(highlight=True, markup=True, wrap=True)
        yield Footer()

    def on_mount(self) -> None:
        self.log_file = r"C:\ProgramData\RobloxMonitor\monitor.log"
        self.last_pos = 0
        self.logging_enabled = True
        
        # Ensure log file exists so that monitoring is active immediately
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            if not os.path.exists(self.log_file):
                with open(self.log_file, "w", encoding="utf-8") as f:
                    pass
        except:
            pass
        
        # Load config
        config_path = r"C:\ProgramData\RobloxMonitor\config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.logging_enabled = config.get("logging", True)
            except:
                pass
        
        self.update_logging_button()
        self.update_status()
        self.update_logs()
        self.set_interval(1.0, self.update_logs)
        self.set_interval(3.0, self.update_status)
        
        # Check for updates in background
        self.run_worker(self.check_for_updates, thread=True)

    def update_logging_button(self) -> None:
        btn = self.query_one("#toggle_logging", Button)
        if self.logging_enabled:
            btn.label = "[3] Stop Logging"
            btn.variant = "error"
        else:
            btn.label = "[3] Activate Logging"
            btn.variant = "success"

    def write_config(self) -> None:
        try:
            os.makedirs(r"C:\ProgramData\RobloxMonitor", exist_ok=True)
            with open(r"C:\ProgramData\RobloxMonitor\config.json", "w", encoding="utf-8") as f:
                json.dump({"logging": self.logging_enabled}, f)
        except:
            pass

    def update_status(self) -> None:
        try:
            res = subprocess.run(
                ["schtasks", "/query", "/tn", "RobloxConfigMonitor"],
                capture_output=True,
                text=True,
                check=False
            )
            status_widget = self.query_one("#status_text", Static)
            if "RobloxConfigMonitor" in res.stdout:
                running = False
                pid_file = r"C:\ProgramData\RobloxMonitor\monitor.pid"
                if os.path.exists(pid_file):
                    try:
                        with open(pid_file, "r") as f:
                            pid = int(f.read().strip())
                        tasklist_res = subprocess.run(
                            ["tasklist", "/FI", f"PID eq {pid}"],
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        if str(pid) in tasklist_res.stdout:
                            running = True
                    except:
                        pass
                
                if running:
                    status_widget.update("Monitor Task: [bold green]REGISTERED (RUNNING)[/bold green]")
                else:
                    status_widget.update("Monitor Task: [bold yellow]REGISTERED (STOPPED)[/bold yellow]")
            else:
                status_widget.update("Monitor Task: [bold red]NOT REGISTERED[/bold red]")
        except Exception:
            pass

    def update_logs(self) -> None:
        if not os.path.exists(self.log_file):
            return
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                f.seek(self.last_pos)
                new_data = f.read()
                self.last_pos = f.tell()
                if new_data:
                    log_widget = self.query_one(RichLog)
                    log_widget.write(new_data)
        except Exception:
            pass

    def write_local_log(self, msg: str) -> None:
        import datetime
        formatted_msg = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n"
        if self.logging_enabled:
            try:
                os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(formatted_msg)
            except:
                pass
            self.update_logs()
        else:
            try:
                log_widget = self.query_one(RichLog)
                log_widget.write(formatted_msg)
            except:
                pass

    def check_for_updates(self) -> None:
        import urllib.request
        import re
        url = "https://raw.githubusercontent.com/sixtysixx/hurtsir/refs/heads/main/robloxMonitor/rblx.py"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                remote_content = response.read().decode('utf-8')
        except:
            return
            
        match = re.search(r'VERSION\s*=\s*"([^"]+)"', remote_content)
        if not match:
            return
        remote_version = match.group(1)
        
        if remote_version != VERSION:
            self.call_after_refresh(self.show_update_modal, remote_version, remote_content)

    def show_update_modal(self, remote_version: str, remote_content: str) -> None:
        def modal_callback(update_approved: bool) -> None:
            if update_approved:
                self.perform_update(remote_content)
        self.push_screen(UpdateModal(remote_version, remote_content), modal_callback)

    def perform_update(self, new_code: str) -> None:
        try:
            self.write_local_log("Downloading and applying update...")
            script_path = os.path.abspath(sys.argv[0])
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(new_code)
            self.write_local_log("Update applied. Restarting application...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            self.write_local_log(f"Failed to apply update: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit":
            self.exit()
            
        # Navigation
        elif event.button.id == "goto_task":
            self.query_one("#menu_switcher", ContentSwitcher).current = "task_menu"
        elif event.button.id == "goto_logs":
            self.query_one("#menu_switcher", ContentSwitcher).current = "logs_menu"
        elif event.button.id in ("back_to_main_task", "back_to_main_logs"):
            self.query_one("#menu_switcher", ContentSwitcher).current = "main_menu"
            
        # Task sub-menu
        elif event.button.id == "start_task":
            # Check if task is registered
            res = subprocess.run(
                ["schtasks", "/query", "/tn", "RobloxConfigMonitor"],
                capture_output=True,
                text=True,
                check=False
            )
            if "RobloxConfigMonitor" not in res.stdout:
                self.notify("Warning: Task is not registered. Please register the task first.", title="Error", severity="error")
                self.write_local_log("Warning: Cannot start task because it is not registered. Please register the task first.")
                return
            subprocess.run(["schtasks", "/run", "/tn", "RobloxConfigMonitor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.update_status()
            self.write_local_log("Task start requested.")
        elif event.button.id == "stop_task":
            pid_file = r"C:\ProgramData\RobloxMonitor\monitor.pid"
            if os.path.exists(pid_file):
                try:
                    with open(pid_file, "r") as f:
                        pid = int(f.read().strip())
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    os.remove(pid_file)
                    self.write_local_log("Task stopped.")
                except Exception as e:
                    self.write_local_log(f"Failed to stop task process: {e}")
            else:
                self.write_local_log("No active process ID found.")
            self.update_status()
        elif event.button.id == "register_task":
            os.makedirs(r"C:\ProgramData\RobloxMonitor", exist_ok=True)
            with open(r"C:\ProgramData\RobloxMonitor\monitor.ps1", "w", encoding="utf-8") as f:
                f.write(monitor_code)
            self.write_config()
            cmd = f'schtasks /create /tn "RobloxConfigMonitor" /sc onstart /ru SYSTEM /rl highest /tr "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File \\"C:\\ProgramData\\RobloxMonitor\\monitor.ps1\\"" /f'
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["schtasks", "/run", "/tn", "RobloxConfigMonitor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.update_status()
            self.write_local_log("Task registered under SYSTEM and started.")
        elif event.button.id == "deregister_task":
            pid_file = r"C:\ProgramData\RobloxMonitor\monitor.pid"
            if os.path.exists(pid_file):
                try:
                    with open(pid_file, "r") as f:
                        pid = int(f.read().strip())
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    os.remove(pid_file)
                except:
                    pass
            subprocess.run(["schtasks", "/delete", "/tn", "RobloxConfigMonitor", "/f"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.update_status()
            self.write_local_log("Task deregistered.")
            
        # Logs sub-menu
        elif event.button.id == "clean_logs":
            if os.path.exists(self.log_file):
                try:
                    with open(self.log_file, "w", encoding="utf-8") as f:
                        f.write("")
                except:
                    pass
            self.last_pos = 0
            self.query_one(RichLog).clear()
            self.write_local_log("Logs cleared by user.")
        elif event.button.id == "copy_logs":
            logs_content = ""
            if os.path.exists(self.log_file):
                try:
                    with open(self.log_file, "r", encoding="utf-8") as f:
                        logs_content = f.read()
                except Exception as e:
                    self.write_local_log(f"Error reading logs: {e}")
            if logs_content:
                try:
                    subprocess.run("clip", input=logs_content, text=True, check=True)
                    self.write_local_log("Logs copied to clipboard.")
                except Exception as e:
                    self.write_local_log(f"Failed to copy logs to clipboard: {e}")
            else:
                self.write_local_log("No logs available to copy.")
        elif event.button.id == "toggle_logging":
            self.logging_enabled = not self.logging_enabled
            self.write_config()
            self.update_logging_button()
            status = "enabled" if self.logging_enabled else "disabled"
            self.write_local_log(f"Logging has been {status}.")

if __name__ == "__main__":

    monitor_code = r"""$log_file = "C:\ProgramData\RobloxMonitor\monitor.log"
$pid_file = "C:\ProgramData\RobloxMonitor\monitor.pid"
$config_path = "C:\ProgramData\RobloxMonitor\config.json"

function log-msg($msg) {
    $logging_enabled = $true
    if (Test-Path $config_path) {
        try {
            $config = Get-Content -Raw -Path $config_path | ConvertFrom-Json
            if ($config.logging -eq $false) {
                $logging_enabled = $false
            }
        } catch {}
    }
    if ($logging_enabled) {
        $time = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        "[$time] $msg" | Out-File -FilePath $log_file -Append -Encoding utf8
    }
}

# Write PID
$PID | Out-File -FilePath $pid_file -Encoding ascii

# Read initial config for start log
$logging_enabled = $true
if (Test-Path $config_path) {
    try {
        $config = Get-Content -Raw -Path $config_path | ConvertFrom-Json
        if ($config.logging -eq $false) {
            $logging_enabled = $false
        }
    } catch {}
}
if ($logging_enabled) {
    log-msg "Roblox Monitor Service started (PID: $PID)"
}

while ($true) {
    $logging_enabled = $true
    if (Test-Path $config_path) {
        try {
            $config = Get-Content -Raw -Path $config_path | ConvertFrom-Json
            if ($config.logging -eq $false) {
                $logging_enabled = $false
            }
        } catch {}
    }
    if (Test-Path "C:\Users") {
        try {
            $users = Get-ChildItem "C:\Users"
            foreach ($user in $users) {
                $target = "C:\Users\$($user.Name)\AppData\Local\Roblox\LocalStorage\appStorage.json"
                if (Test-Path $target) {
                    $size = (Get-Item $target).Length
                    if ($size -gt 0) {
                        $content = Get-Content -Raw -Path $target | ConvertFrom-Json
                        $changed = $false
                        if ($content.LaunchAtStartup -ne "false") {
                            $content.LaunchAtStartup = "false"
                            $changed = $true
                        }
                        if ($content.MinimizeToTray -ne "false") {
                            $content.MinimizeToTray = "false"
                            $changed = $true
                        }
                        if ($changed) {
                            $json = $content | ConvertTo-Json -Compress
                            [System.IO.File]::WriteAllText($target, $json)
                            if ($logging_enabled) {
                                log-msg "Disabled LaunchAtStartup / MinimizeToTray in $target"
                            }
                        }
                    } else {
                        $json = '{"LaunchAtStartup":"false","MinimizeToTray":"false"}'
                        [System.IO.File]::WriteAllText($target, $json)
                        if ($logging_enabled) {
                            log-msg "Initialized empty appStorage.json in $target"
                        }
                    }
                } else {
                    $appdata_local = "C:\Users\$($user.Name)\AppData\Local"
                    if (Test-Path $appdata_local) {
                        $roblox_dir = Join-Path $appdata_local "Roblox"
                        $local_storage_dir = Join-Path $roblox_dir "LocalStorage"
                        if (!(Test-Path $local_storage_dir)) {
                            New-Item -ItemType Directory -Force -Path $local_storage_dir | Out-Null
                        }
                        $json = '{"LaunchAtStartup":"false","MinimizeToTray":"false"}'
                        [System.IO.File]::WriteAllText($target, $json)
                        if ($logging_enabled) {
                            log-msg "Created Roblox LocalStorage directory and appStorage.json with disabled startup/tray in $target"
                        }
                    }
                }
            }
        } catch {
            # Ignore errors
        }
    }
    Start-Sleep -Seconds 10
}
"""
    
    # Setup directory and files
    os.makedirs(r"C:\ProgramData\RobloxMonitor", exist_ok=True)
    with open(r"C:\ProgramData\RobloxMonitor\monitor.ps1", "w", encoding="utf-8") as f: f.write(monitor_code)
    
    # Ensure log file exists so that monitoring is active immediately
    log_file_path = r"C:\ProgramData\RobloxMonitor\monitor.log"
    if not os.path.exists(log_file_path):
        try:
            with open(log_file_path, "w", encoding="utf-8") as f:
                pass
        except:
            pass
    
    # Set console size on Windows
    if sys.platform == "win32":
        os.system("mode con: cols=120 lines=45")
    # Run TUI
    RobloxManager().run()