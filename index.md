### SirHurt Troubleshooting Guide

* **Windows Version:** Ensure you are on **24H2** or above.
* **Restart:** Have you tried restarting your PC?
* **Timing:** Wait 5-10 seconds before injecting, or toggle **Autoinject** on/off.
* **Fresh Install:** Redownload the `.zip` from the Sirhurt website if the bootstrapper isn't working.

---

### Required Installations

Install both x86 and x64 versions of the following:

#### Visual C++ Redistributables

* [vc_redist.x86.exe](https://aka.ms/vc14/vc_redist.x86.exe)
* [vc_redist.x64.exe](https://aka.ms/vc14/vc_redist.x64.exe)

#### .NET SDK (10.0.201)

* [dotnet-sdk-win-x64.exe](https://builds.dotnet.microsoft.com/dotnet/Sdk/10.0.201/dotnet-sdk-10.0.201-win-x64.exe)
* [dotnet-sdk-win-x86.exe](https://builds.dotnet.microsoft.com/dotnet/Sdk/10.0.201/dotnet-sdk-10.0.201-win-x86.exe)

---

### Setup & Tools

1. **Antivirus:** Disable your AV. Create a dedicated folder and **exclude it** from scans.
2. **Download Utilities:** Place these inside your excluded folder:
    * [Sirhurt Cleaner](https://github.com/massimopaganigh/sirhurt.cleaner)
    * [Sirstrap](https://github.com/massimopaganigh/Sirstrap) (UI or CLI works; CLI is recommended).
3. **Sirhurt:** Download this directly from the official downloads page.
    > **Note:** Use **7-Zip** or **WinRAR** for extraction. The default Windows extractor can cause issues.

---

### Execution Steps

1. **Run Sirstrap:** Wait for Roblox to download and open, then close it.
2. **Run Sirhurt Cleaner:** Press `Y` + `Enter` for all prompts (including auth data—you will need to log in again during injection).
3. **Restart PC.**
4. **Open Sirstrap Roblox Instance.**
5. **Run Bootstrapper:** Wait for it to finish downloading everything.
6. **Kill Roblox Instances.**
7. **Reopen Sirstrap:** (Via web or program).
8. **Inject:** Log in when prompted. Do **not** manually inject again afterward; it will auto-inject after the login is successful.
