# UNOFFICIAL SirHurt Troubleshooting Guide

This guide provides comprehensive steps to resolve common issues with SirHurt injection and execution. **PLEASE read the guide and follow it step by step (DONT just fucking skim through it)**

---

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

5. Driver Updater - Finds and installs any outdated or missing drivers, ***OPTIONAL*** but recommended in most cases.

   ```
   https://sourceforge.net/projects/snappy-driver-installer-origin/
   - Click `Download latest release`, extract the archive and run the `SDIO_auto` batch script.
   - Choose to `Index This PC Only'. Turn on `Expert Mode`
   - Toggle the following ON in the first menu: "Not installed, Newer, Better matches"
   - Toggle the following ON in the second menu "Not Installed"
   - Toggle ON "Show only best" in the last menu.
   - Click "Select all" and Install any missing or outdated drivers.
   - I would 100% recommend a recovery point.
   ```

**Restart your PC after these commands finish.**

---

### 2. Required Installations

Install **both x86 and x64** versions.

#### Visual C++ (CPP) Redistributables

- [VC Redist x86](https://aka.ms/vc14/vc_redist.x86.exe)
- [VC Redist x64](https://aka.ms/vc14/vc_redist.x64.exe)

#### .NET SDK & Runtimes

- [SDK x64](https://dotnet.microsoft.com/en-us/download/dotnet/thank-you/sdk-10.0.203-windows-x64-installer) | [SDK x86](https://dotnet.microsoft.com/en-us/download/dotnet/thank-you/sdk-10.0.203-windows-x86-installer)

 **RESTART your PC after installing these.**

---

### 3. Setup & Tools

1. **Antivirus Exclusion:**
   - Disable your AV temporarily.
   - Create a dedicated folder (`C:\Users\whateveryourusernameis\Downloads\sirhurtian_utils` - You can name it whatever).
   - Add this folder to your AV's **Exclusion/Whitelist** list. (often windows defender and/or malwarebytes)
2. **Sirstrap (Sirhurt's Recommended Launcher):**
   - [Download Sirstrap](https://massimopaganigh.github.io/Sirstrap/)
   - Sirstrap is less customizable, but is recommended for testing purposes with sirhurt.
3. **SirHurt Bootstrapper:**
   - Download directly from the official SirHurt site.
   - Use **7-Zip** or **WinRAR** to extract files; the default Windows extractor can cause extraction errors alongside AV.

---

### 4. SirHurt Cleaner

If you are still having issues, use the [SirHurt Cleaner](https://massimopaganigh.github.io/Sirstrap/) (Bundled with Sirstrap).

- Press `Y` + `Enter` for all prompts. Then restart your PC and retry injection.
- _This WILL clear your app login data, so youll need to log in again- UNLESS youre using a browser._

---

### 5. Troubleshooting Steps

Follow the following steps if injection fails:

1. **Window Version Check:** Ensure you are on Windows **24H2** or higher.
2. **Roblox Settings:**
   - Disable Roblox's `Minimize to tray when closed` setting.
   - Temporarily disable Voice Chat on your account (unlikely, but can cause issues)
3. **Launching:**
   - Open Roblox via **Voidstrap/Sirstrap** and join a simple game (baseplate or default starting game).
   - Run the SirHurt Bootstrapper as **Administrator**. Verify `sirhurt.dll` exists in the folder.
4. **Injection:**
   - Use the "Kill Processes" button in the UI after the bootstrapper fetches everything.
   - Open Roblox again and join a game.
   - Click **Inject**. Youll be prompted to log in.
   - **Do NOT** click Inject again after logging in; it will handle the rest automatically.

---

Might as well put [the discord troubleshooting guide](https://r2.e-z.host/a466cf7c-0034-4d68-80d8-1c7ad54cf3c3/80laz55n.png) in here as well. *Should* be pinned in the #support channel. Might make a video later on for users. Eh, who knows.
