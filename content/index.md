---
layout: base.njk
title: SirHurt Troubleshooting Guide
---

# SirHurt Troubleshooting Guide

**PLEASE read this guide carefully and follow it step-by-step.**

<div class="embed">

### Quick Start Summary
1. **Prepare:** Disable AV, create an excluded folder, and install prerequisites (VC Redist, .NET).
2. **Clean:** Run the SirHurt Cleaner to remove old files.
3. **Configure:** Disable "Launch on Startup" and "Minimize to tray" in Roblox.
4. **Launch:** Open Roblox, then run the SirHurt Bootstrapper as Administrator.
5. **Inject:** Join a game, wait 5-10 seconds, and inject.

*See the detailed sections below for instructions on each step.*

</div>

<div class="embed">

### 1. Preparation & Prerequisites
Before installing, ensure your environment is ready:

*   **Antivirus:** Disable your AV temporarily and add your dedicated SirHurt folder to your **Exclusion/Whitelist**.
*   **System Files:** Run the following in an **Administrator PowerShell** to fix potential corruption:
    ```cmd
    try { sfc /scannow; DISM /Online /Cleanup-Image /CheckHealth; DISM /Online /Cleanup-Image /ScanHealth; DISM /Online /Cleanup-Image /RestoreHealth; Write-Host -ForegroundColor Green "SUCCESS: System repair chain executed successfully." } catch { Write-Host -ForegroundColor Red "ERROR: System repair chain failed: $_" }
    ```
*   **Required Installations:** Install both x86 and x64 versions of:
    *   [Visual C++ Redistributables](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-supported-redistributable-version)
    *   [.NET SDK](https://dotnet.microsoft.com/en-us/download)
    *   *RESTART YOUR PC after these installations.*

</div>

<div class="embed">

### 2. Setup & Configuration
1. **Sirstrap:** [Download Sirstrap](https://github.com/i-nagap/Sirstrap/releases/), extract, and run.
2. **SirHurt:** Download from the official [SirHurt](https://sirhurt.net/) site. Use **7-Zip** or **WinRAR** to extract into your excluded folder.
3. **Roblox Settings:** Open Roblox settings and disable **"Launch on startup"** and **"Minimize to tray when closed"**. Close and reopen Roblox to apply.
4. **SirHurt Cleaner:** If issues persist, run the [SirHurt Cleaner](https://github.com/i-nagap/Sirstrap/releases/) (bundled with Sirstrap). Press `Y` + `Enter` for all prompts. *Note: This will clear your auth data.*

</div>

<div class="embed">

### 3. Execution & Injection
1. **Launch:** Open Roblox via **Sirstrap** and join a game.
2. **Bootstrapper:** Run the SirHurt Bootstrapper as **Administrator**.
3. **Inject:**
   - Wait **5-10 seconds** after joining a game.
   - Click **Inject**.
   - Log in when prompted. **Do NOT** click Inject again after logging in; it handles the rest automatically.
   - Execute a test script (e.g., **Infinite Yield**) to confirm it works.

</div>

<div class="embed">

### 4. Troubleshooting
If injection fails:
1. **Windows Version:** Ensure you are on Windows **24H2** or higher.
2. **Roblox Settings:** Double-check that "Minimize to tray when closed" and "Launch on Startup" are disabled.
3. **Process Management:** Use the "Kill Processes" button in the UI if the bootstrapper hangs.

</div>

<div class="embed">

### 5. Downgrade Tutorial
> **Recommended Version (as of 8/22/2026):** [version-ce0bcd0fbd484804](https://sirhurt.net/downgradetutorial.php?version=version-ce0bcd0fbd484804)

<video controls width="100%">
  <source src="https://r2.e-z.host/a466cf7c-0034-4d68-80d8-1c7ad54cf3c3/1co3ngj3.mp4" type="video/mp4">
</video>

</div>

Guide - Made by <a href="https://discord.com/users/1045933816260350032">SIX</a> - See an issue? Let me know!
