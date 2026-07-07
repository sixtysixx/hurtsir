---
layout: base.njk
title: UNOFFICIAL SirHurt Troubleshooting Guide
---

# UNOFFICIAL SirHurt Troubleshooting Guide

**PLEASE read the guide and follow it step by step (dont just skim through it pls :3)**
<br>

<div class="embed">

### Quick Start

1. Disable your AV (antivirus) temporarily.
2. Create a dedicated folder and exclude it from your AV.
3. Place **Sirstrap**, **SirHurt Cleaner**, and **SirHurt** inside it (DO NOT EXTRACT ANYTHING YET).
4. Install both **VC Redist x86/x64** and the latest **.NET SDK**.
5. Run the **SirHurt Cleaner** — press `Y` for all prompts (see Section 5).
6. Remove any leftover SirHurt folders (including old ZIPs/folders).
7. **Restart your PC.**
8. Open Roblox.
9. Disable Roblox's launch on startup & minimize to tray settings (see Section 4).
10. Close and reopen Roblox.
11. Extract SirHurt (**7-Zip** preferred).
12. Run the Bootstrapper as **Administrator**.
13. Attempt to inject, then login.
14. Execute a test script (e.g. **Infinite Yield**).

</div>

<div class="embed">

### Checklist

- Disabled Roblox's `Minimize to tray when closed` setting.
- Moved SirHurt into a dedicated folder excluded from your AV.
- **Using a custom OS (like Atlas OS)?** (these suck ass, please dont)
- On Windows **24H2** or above.
- Waited **5-10 seconds** before injecting, or toggled autoinject on/off.

</div>

<div class="embed">

### 1. System Repairs (SFC & DISM)

Run these commands in an **Administrator PowerShell** or **Command Prompt**:

1. **SFC Scan:** Fixes corrupted system files.
   ```cmd
   sfc /scannow
   ```

2. **DISM Health Check:** Checks for component store corruption.
   ```cmd
   DISM /Online /Cleanup-Image /CheckHealth
   ```

3. **DISM Scan Health:** Scans the Windows image for corruption.
   ```cmd
   DISM /Online /Cleanup-Image /ScanHealth
   ```

4. **DISM Restore Health:** Repairs the Windows image using Windows Update.
   ```cmd
   DISM /Online /Cleanup-Image /RestoreHealth
   ```

5. **Driver Updater:** Finds and installs any outdated or missing drivers (**OPTIONAL** but recommended).
   [Snappy Driver Installer Origin (SDIO)](https://sourceforge.net/projects/snappy-driver-installer-origin/)
   - Click `Download latest release`, extract the archive and run the `SDIO_auto` batch script.
   - Choose to `Index This PC Only`. Turn on `Expert Mode`.
   - Toggle the following ON in the first menu: "Not installed, Newer, Better matches".
   - Toggle the following ON in the second menu: "Not Installed".
   - Toggle ON "Show only best" in the last menu.
   - Click "Select all" and install any missing or outdated drivers.
   - *It is highly recommended to create a system recovery point first.*

**Restart your PC after these commands finish.**

</div>

<div class="embed">

### 2. Required Installations

Install **both x86 and x64** versions of the following prerequisites.

#### Visual C++ Redistributables
- [VC Redist x86](https://aka.ms/vc14/vc_redist.x86.exe)
- [VC Redist x64](https://aka.ms/vc14/vc_redist.x64.exe)
*If these links become outdated, find the latest versions on [Microsoft's site](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-supported-redistributable-version).*

#### .NET SDK & Runtimes
- [SDK x64](https://dotnet.microsoft.com/en-us/download/dotnet/thank-you/sdk-10.0.301-windows-x64-installer) | [SDK x86](https://dotnet.microsoft.com/en-us/download/dotnet/thank-you/sdk-10.0.301-windows-x86-installer)

**RESTART your PC after installing these.**
*If these links become outdated, find the latest versions on [Microsoft's site](https://dotnet.microsoft.com/en-us/download).*
*Click `Download .NET SDK x64` as well as `Download .NET SDK x86` from the dropdown menu.*

</div>

<div class="embed">

### 3. Setup & Exclusions

1. **Antivirus Exclusion:**
   - Disable your AV temporarily.
   - Create a dedicated folder (e.g. `C:\Users\whateveryourusernameis\Downloads\sirhurtian_utils`).
   - Add this folder to your AV's **Exclusion / Whitelist** (e.g. Windows Defender, Malwarebytes).

2. **Sirstrap (SirHurt's Recommended Launcher):**
   - [Download Sirstrap](https://massimopaganigh.github.io/Sirstrap/)
   - Extract the archive and run the executable.

3. **SirHurt:**
   - Download directly from the official [SirHurt](https://sirhurt.net/) site. If using the Box link, click **top right** on the starting page, otherwise it might not start the download (recommended to use Gofile).
   - Place it in your excluded folder and use **7-Zip** or **WinRAR** to extract; the default Windows extractor can cause extraction errors.
   - Once extracted, open Roblox and join a game. It should automatically use Sirstrap for launching.
   - After Roblox is open and you are in a game, open the extracted folder and run the bootstrapper (only necessary to run the bootstrapper if there is a Roblox update or SirHurt pushes an update).
   - Press initialize / inject & wait for the bottom-left indicator to turn green, then execute your script(s).

</div>

<div class="embed">

### 4. Roblox Configuration & Monitor

Roblox frequently re-enables **"Launch on Startup"** and **"Minimize to tray when closed"** settings, which can cause injection failures. You can disable these manually or use the automated background monitor.

#### Option A: Manual Configuration
- Open Roblox settings.
- Disable **Launch on startup** and **Minimize to tray when closed**.
- Close and reopen Roblox to apply.

#### Option B: Automated Roblox Config Monitor
You can use the background **Roblox Config Monitor** service to automatically keep these settings disabled for all Windows users.

1. **Download the Script:**
   - Download the **[rblx.py](https://raw.githubusercontent.com/sixtysixx/hurtsir/refs/heads/main/robloxMonitor/rblx.py)** script directly and place it in a folder (e.g., `robloxMonitor`).

2. **Install Prerequisites:**
   - Install **Python (v3.8+)** or **[uv](https://astral.sh/uv)** (recommended fast Python installer).
   - Ensure Python is added to your system's PATH during installation.

3. **Run the Manager Tool:**
   - Open Command Prompt or PowerShell as **Administrator**.
   - Navigate to the directory containing `rblx.py`:
     ```cmd
     cd robloxMonitor
     ```
   - Start the manager:
     - **With uv:** `uv run rblx.py`
     - **With standard Python:** `python rblx.py` (The script will automatically attempt to install the required `textual` package if missing).

4. **Register the Service:**
   - Accept the UAC administrator prompt if it appears.
   - In the Textual TUI interface, go to **Task Management** (or press `1`).
   - Select **Register Task**. This registers a persistent Windows Scheduled Task (`RobloxConfigMonitor`) running silently under the SYSTEM account.
   - You can start, stop, view real-time logs, or deregister/remove the service directly within this interface.

</div>

<div class="embed">

### 5. SirHurt Cleaner

If you are still having issues, use the [SirHurt Cleaner](https://massimopaganigh.github.io/Sirstrap/) (bundled with Sirstrap).

- Press `Y` + `Enter` for all prompts.
- Remove any leftover SirHurt folders after running it.
- Restart your PC and retry injection.
- *This WILL clear your auth data, so you will need to log in again.*

</div>

<div class="embed">

### 6. Troubleshooting Steps

Follow these steps if injection fails:

1. **Windows Version Check:** Ensure you are on Windows **24H2** or higher.
2. **Roblox Settings:** Ensure "Minimize to tray when closed" and "Launch on Startup" are disabled (see Section 4).
3. **Voice Chat:** Temporarily disable Voice Chat on your account (unlikely, but can sometimes cause issues).
4. **Launching:**
   - Open Roblox via **Sirstrap** and join a simple game (baseplate or default starting game).
   - Run the SirHurt Bootstrapper as **Administrator**.
5. **Injection:**
   - Use the "Kill Processes" button in the UI after the bootstrapper fetches everything.
   - Open Roblox again and join a game.
   - Wait **5-10 seconds** before clicking Inject (or toggle autoinject on/off).
   - Click **Inject**. You will be prompted to log in.
   - **Do NOT** click Inject again after logging in; it will handle the rest automatically.
   - Execute a test script (e.g. **Infinite Yield**) to confirm it works.

</div>

<div class="embed">

> **Recommended Version (as of 7/7/2026):** `version-90f2fddd3b244ff6 (LIVE)`

#### Downgrade Tutorial - Manual
<video controls width="100%">
  <source src="https://r2.e-z.host/a466cf7c-0034-4d68-80d8-1c7ad54cf3c3/1co3ngj3.mp4" type="video/mp4">
</video>

#### Downgrade Tutorial #2 - Using Sirstrap (Easier & Multi-instance support)
<video controls width="100%">
  <source src="https://r2.e-z.host/a466cf7c-0034-4d68-80d8-1c7ad54cf3c3/fu6yfecw.mp4" type="video/mp4">
</video>

</div>

^_^ UNOFFICIAL Guide - Made by <a href="https://discord.com/users/1045933816260350032">SYX</a> ^_^
