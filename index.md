# UNOFFICIAL SirHurt Troubleshooting Guide

woah super swag notice: this isnt sirhurts official troubleshooting guide, nor automatic troubleshooter, this was made by [syx](https://discord.com/users/1045933816260350032)  <br>
(im gonna regret putting my dsc here lol) <br>
disclaimer or something: im not responsable for any misuse, malfunction to ur device, or literally anything ig lol

## Quick Links

- [**Download SyxSirHurtTroubleshooter.exe**](https://github.com/sixtysixx/hurtsir/raw/main/SyxSirHurtTroubleshooter.exe) (Automated Troubleshooting Tool)
- [**View Raw main.py Source**](https://raw.githubusercontent.com/sixtysixx/hurtsir/main/main.py)
- [**View Github Repo**](https://github.com/sixtysixx/hurtsir/)

---

### Manual Troubleshooting Guid

- Ensure you are on Windows version **24H2** or above.
- Restart PC and retry injection
- Wait 5-10 seconds before injecting, or toggle **Autoinject** on/off.
- Temporarily disable voice chat functionality on your account.
- Disable ROBLOX's `minimize to tray when closed` setting
- Move sirhurt into a dedicated folder, and exclude that folder from your AV (antivirus)
- Open roblox and join a simple game, such as a baseplate or default game
- Run bootstrapper as admin, waiting for it to download everything (make sure sirhurt.dll exists, if not- rerun bootstrapper as admin)
- Kill processes (bottom right button)
- Open roblox again and join a game
- Attempt to inject
- Youll be prompted to login, so proceed with that
- After login, do NOT press inject, it will automatically inject after
- If that works, have fun with sirhurt fr, rerun bootstrapper as admin every time you want to open sirhurt.

---

### Required Installations

Install both x86 and x64 versions of the following:

#### Visual C++ (cpp) Redistributables

- [vc_redist.x86.exe](https://aka.ms/vc14/vc_redist.x86.exe)
- [vc_redist.x64.exe](https://aka.ms/vc14/vc_redist.x64.exe)

#### .NET SDK (10.0.201)

- [dotnet-sdk-win-x64.exe](https://builds.dotnet.microsoft.com/dotnet/Sdk/10.0.201/dotnet-sdk-10.0.201-win-x64.exe)
- [dotnet-sdk-win-x86.exe](https://builds.dotnet.microsoft.com/dotnet/Sdk/10.0.201/dotnet-sdk-10.0.201-win-x86.exe)

---

### Setup & Tools

1. **Antivirus:** Disable your AV. Create a dedicated folder and **exclude it** from scans.
2. **Download Utilities:** Place these inside your excluded folder:
   - [Sirhurt Cleaner](https://github.com/massimopaganigh/sirhurt.cleaner)
   - [Sirstrap](https://github.com/massimopaganigh/Sirstrap) (CLI is recommended for easier config- Can use others (*whatever*strap) if they allow to manually set roblox build.).
3. **Sirhurt:** Download sirhurt directly from the official downloads page. If using box link click top right on the starting page, otherwise it likely wont download.
   > **Note:** Use **7-Zip** or **WinRAR** for extraction. The default Windows extractor can cause issues.

---

### Execution Steps for Beta Roblox Clients

1. **Run Sirstrap:** Wait for Roblox to download and open, then close it.
2. **Run Sirhurt Cleaner:** Press `Y` + `Enter` for all prompts (including auth data—you will need to log in again during injection).
3. **Restart PC.**
4. **Open Sirstrap Roblox Instance.**
5. **Run Bootstrapper:** Wait for it to finish downloading everything.
6. **Kill Roblox Instances.**
7. **Reopen Sirstrap:** (Via web or program).
8. **Inject:** Log in when prompted. Do **not** manually inject again afterward; it will auto-inject after the login is successful.
