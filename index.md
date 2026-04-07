# UNOFFICIAL SirHurt Troubleshooting Guide

This guide provides comprehensive steps to resolve common issues with SirHurt injection and execution. Please read the guide and follow step by step (dont just fucking skim through it)

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

5. **Missing Drivers** Finds and installs any outdated or missing drivers

   ```
   https://sourceforge.net/projects/snappy-driver-installer-origin/
   - Click `Download latest release`, extract and run the automatic batch script, Index 'This PC Only', Install any missing or outdated drivers. I would 100% recommend a recovery point.
   ```

**Restart your PC after these commands finish.**

---

### 2. Required Installations

Install **both x86 and x64** versions.

#### Visual C++ (CPP) Redistributables

- [VC Redist x86](https://aka.ms/vc14/vc_redist.x86.exe)
- [VC Redist x64](https://aka.ms/vc14/vc_redist.x64.exe)

#### .NET SDK & Runtimes (v10.0.201)

- [SDK x64](https://builds.dotnet.microsoft.com/dotnet/Sdk/10.0.201/dotnet-sdk-10.0.201-win-x64.exe) | [SDK x86](https://builds.dotnet.microsoft.com/dotnet/Sdk/10.0.201/dotnet-sdk-10.0.201-win-x86.exe)
- [Runtime x64](https://dotnet.microsoft.com/en-us/download/dotnet/thank-you/runtime-10.0.5-windows-x64-installer) | [Runtime x86](https://dotnet.microsoft.com/en-us/download/dotnet/thank-you/runtime-10.0.5-windows-x86-installer)
- [Desktop Runtime x64](https://dotnet.microsoft.com/en-us/download/dotnet/thank-you/runtime-desktop-10.0.5-windows-x64-installer) | [Desktop Runtime x86](https://dotnet.microsoft.com/en-us/download/dotnet/thank-you/runtime-desktop-10.0.5-windows-x86-installer)

**Restart your PC after installing these.**

---

### 3. Setup & Tools

Proper environment setup is critical to prevent your Antivirus (AV) from deleting essential files.

1. **Antivirus Exclusion:**
   - Disable your AV temporarily.
   - Create a dedicated folder (`C:\Users\whateveryourusernameis\Downloads\sirhurtian_utils` - You can name it whatever).
   - Add this folder to your AV's **Exclusion/Whitelist** list. (often windows defender and/or malwarebytes)
2. **Voidstrap (UNOFFICIAL Recommended Launcher):**
   - [Download Voidstrap](https://github.com/voidstrap/Voidstrap)
   - Voidstrap is a modern alternative to Sirstrap that allows for better configuration and Roblox build management.
3. **Sirstrap (Sirhurt's Recommended Launcher):**
   - [Download Sirstrap](https://github.com/massimopaganigh/Sirstrap)
   - Sirstrap is less customizable, but is recommended for testing purposes with sirhurt.
4. **SirHurt Bootstrapper:**
   - Download directly from the official SirHurt site.
   - Use **7-Zip** or **WinRAR** to extract files; the default Windows extractor can cause extraction errors alongside AV.

---

### 4. SirHurt Cleaner

If you are still having issues, use the [SirHurt Cleaner](https://github.com/massimopaganigh/Sirstrap) (Bundled with Sirstrap utilities).

- Press `Y` + `Enter` for all prompts. Then restart your PC and retry injection.
- _This WILL clear your login data, so youll need to log in again._

---

### 5. Troubleshooting Steps

Follow this exact sequence if injection fails:

1. **Window Version Check:** Ensure you are on Windows **24H2** or higher.
2. **Preparation:**
   - Disable Roblox's `Minimize to tray when closed` setting.
   - Temporarily disable Voice Chat on your account (unlikely, but can cause issues)
3. **Launch Sequence:**
   - Open Roblox via **Voidstrap/Sirstrap** and join a simple game (baseplate or default starting game).
   - Run the SirHurt Bootstrapper as **Administrator**. Verify `sirhurt.dll` exists in the folder.
4. **Injection:**
   - Use the "Kill Processes" button in the UI after the bootstrapper fetches everything.
   - Open Roblox again and join a game.
   - Click **Inject**. Youll be prompted to log in.
   - **Do NOT** click Inject again after logging in; it will handle the rest automatically.
