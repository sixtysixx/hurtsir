---
layout: base.njk
title: UNOFFICIAL SirHurt Troubleshooting Guide
---

# UNOFFICIAL SirHurt Troubleshooting Guide

**PLEASE read the guide and follow it step by step ( dont just skim through it pls :3 )**
<br>

<div class="embed">

### Quick Start

1. Disable your AV(antivirus) temporarily.
2. Create a dedicated folder and exclude it from your AV.
3. Place **Sirstrap**, **SirHurt Cleaner**, and **SirHurt** inside it. (DO NOT EXTRACT ANYTHING YET)
4. Install both **VC Redist x86/x64** and the latest **.NET SDK**.
5. Run the **SirHurt Cleaner** — press `Y` for all prompts. - See step 4
6. Remove any leftover SirHurt folders (yes this includes any old sirhurt zips or folders).
7. **Restart your PC.**
8. Open Roblox.
9. Extract Sirhurt (**7-Zip** preferred).
10. Run the Bootstrapper as **Administrator**.
11. Attempt to inject, then login.
12. Execute a test script (e.g. **Infinite Yield**).

</div>

<div class="embed">

### Checklist

- Disabled Roblox's `Minimize to tray when closed` setting.
- Moved SirHurt into a dedicated folder excluded from your AV.
- **Using a custom OS (like Atlas OS)?** Don't, these suck ass.
- On Windows **24H2** or above.
- Waited **5-10 seconds** before injecting, or toggled autoinject on/off.

</div>

<div class="embed">

### 1. System Repairs (SFC & DISM) - Classic Microslop response for literally nothing related to system corruption

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

5. Driver Updater - Finds and installs any outdated or missing drivers, **_OPTIONAL_** but recommended in most cases.

   [https://sourceforge.net/projects/snappy-driver-installer-origin/](https://sourceforge.net/projects/snappy-driver-installer-origin/)
   - Click `Download latest release`, extract the archive and run the `SDIO_auto` batch script.
   - Choose to `Index This PC Only`. Turn on `Expert Mode`.
   - Toggle the following ON in the first menu: "Not installed, Newer, Better matches"
   - Toggle the following ON in the second menu "Not Installed"
   - Toggle ON "Show only best" in the last menu.
   - Click "Select all" and Install any missing or outdated drivers.
   - I would 100% recommend a recovery point.

**Restart your PC after these commands finish.**

</div>

<div class="embed">

### 2. Required Installations

Install **both x86 and x64** versions.

#### Visual C++ Redistributables

- [VC Redist x86](https://aka.ms/vc14/vc_redist.x86.exe)
- [VC Redist x64](https://aka.ms/vc14/vc_redist.x64.exe)

- If these links become outdated, find the latest versions on [Microsoft's site](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-supported-redistributable-version).

#### .NET SDK & Runtimes

- [SDK x64](https://dotnet.microsoft.com/en-us/download/dotnet/thank-you/sdk-10.0.301-windows-x64-installer) | [SDK x86](https://dotnet.microsoft.com/en-us/download/dotnet/thank-you/sdk-10.0.301-windows-x86-installer)

  **RESTART your PC after installing these.**
- If these links become outdated, find the latest versions on [Microsoft's site](https://dotnet.microsoft.com/en-us/download).
- Click `Download .NET SDK x64` as well as under the dropdow menu `Download .NET SDK x86`

</div>

<div class="embed">

### 3. Setup & Tools

1. **Antivirus Exclusion:**
   - Disable your AV temporarily.
   - Create a dedicated folder (`C:\Users\whateveryourusernameis\Downloads\sirhurtian_utils` - You can name it whatever).
   - Add this folder to your AV's **Exclusion/Whitelist** list. (often windows defender and/or malwarebytes)
2. **Sirstrap (Sirhurt's Recommended Launcher):**
   - [Download Sirstrap](https://massimopaganigh.github.io/Sirstrap/)
   - Extract the archive and run the executable
3. **SirHurt:**
   - Download directly from the official [SirHurt](https://sirhurt.net/) site. If using the Box link, click **top right** on the starting page, otherwise it might not start the download. Recommended to use Gofile.
   - Place it in your excluded folder and use **7-Zip** or **WinRAR** to extract; the default Windows extractor can cause extraction errors.
   - Once extracted, open roblox and join a game. It should automatically use sirstrap for launching
   - After roblox is open and youre in a game, open the extracted folder and run the bootstrapper (only necessary to run bootstrapper if there is a roblox update or sirhurt pushes an update)
   - Press initialize / inject & wait for the bottom left indicator to turn green, then execute your script(s)

</div>

<div class="embed">

### 4. SirHurt Cleaner

If you are still having issues, use the [SirHurt Cleaner](https://massimopaganigh.github.io/Sirstrap/) (Bundled with Sirstrap).

- Press `Y` + `Enter` for all prompts.
- Remove any leftover SirHurt folders after running it.
- Then restart your PC and retry injection.
- _This WILL clear your auth data, so youll need to log in again._

</div>

<div class="embed">

### 5. Troubleshooting Steps

Follow the following steps if injection fails:

1. **Window Version Check:** Ensure you are on Windows **24H2** or higher.
2. **Roblox Settings:**
   - Disable Roblox's `Minimize to tray when closed` setting.
   - Temporarily disable Voice Chat on your account (unlikely, but can cause issues)
3. **Launching:**
   - Open Roblox via **Sirstrap** and join a simple game (baseplate or default starting game).
   - Run the SirHurt Bootstrapper as **Administrator**. Verify `sirhurt.dll` exists in the folder.
4. **Injection:**
   - Use the "Kill Processes" button in the UI after the bootstrapper fetches everything.
   - Open Roblox again and join a game.
   - Wait **5-10 seconds** before clicking Inject (or toggle autoinject on/off).
   - Click **Inject**. Youll be prompted to log in.
   - **Do NOT** click Inject again after logging in; it will handle the rest automatically.
   - Execute a test script (e.g. **Infinite Yield**) to confirm it works.

</div>
<div class="embed">

> **Recommended Version (as of 7/4/2026):** `version-1a951716f19e4638`

<h4>Downgrade tutorial - Manual</h4>
<video controls width="100%">
  <source src="https://r2.e-z.host/a466cf7c-0034-4d68-80d8-1c7ad54cf3c3/1co3ngj3.mp4" type="video/mp4">
</video>
<h4>Downgrade tutorial #2 - Using Sirstrap (Easier & Multi-instance support)</h4>
<video controls width="100%">
  <source src="https://r2.e-z.host/a466cf7c-0034-4d68-80d8-1c7ad54cf3c3/fu6yfecw.mp4" type="video/mp4">
</video>

</div>
^_^ UNOFFICIAL Guide - Made by <a href="https://discord.com/users/1045933816260350032">SYX</a> ^_^
