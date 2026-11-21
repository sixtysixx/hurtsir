# SixSirhurtUnretardifier9000Pro

[![Setup exe](https://github.com/sixtysixx/hurtsir/actions/workflows/setup-exe.yml/badge.svg)](https://github.com/sixtysixx/hurtsir/actions/workflows/setup-exe.yml)

One-shot Windows setup for SirHurt that automates stages 1-3 of
<https://sirhurt.pages.dev/guide/>.

Download the latest build from
<https://github.com/sixtysixx/hurtsir/releases/latest>, or build it yourself with
`build.ps1` (see [Build it](#build-it)).

## What it does

- scans the folder you started it from and the folder the exe lives in for a SirHurt
  archive, moves it into the install folder, and extracts it - the gofile download is the
  SirHurt folder itself, while a Box share wraps that folder one level down, so a zip
  found inside the archive is unpacked too;
- adds a Windows Defender folder exclusion for the install folder;
- optionally runs the system-repair chain (SFC, then DISM
  CheckHealth/ScanHealth/RestoreHealth);
- installs both Visual C++ redistributables and the .NET Framework 4.8.1 web installer;
- optionally resolves the published Windows build through Roblox's deployment API and
  unpacks it into `%LOCALAPPDATA%\Roblox\Versions\version-<hash>` - the same
  `rbxPkgManifest.txt` walk [RDD](https://sirhurt.pages.dev/rdd/) does, so the client
  SirHurt injects into is the latest build without a separate version manager;
- downloads the SirHurt Cleaner and runs it on every pass, before anything is installed, so old
  Roblox/SirHurt files and stored login data are gone first (`--skip-cleaner` leaves them alone);
- optionally turns off "Launch at startup" and "Minimize to tray when closed" in Roblox's
  `appStorage.json` - it offers to close a running Roblox first (the client writes its
  in-memory settings back on exit) and re-reads the file afterwards to confirm the change;
- optionally schedules a reboot in 15 seconds (the runtimes register themselves at boot);
- writes `README.txt` with the next steps into the install folder (when SirHurt is
  installed).

## Before you run it

- Windows 11 24H2 or newer - check with `winver` (`build 26100+`).
- Administrator rights: the exe re-launches itself through the UAC prompt on start.
- The SirHurt archive from <https://sirhurt.net/login/download.php>
- Around 2 GB of free space.
- Keep the install folder out of OneDrive and out of `C:\Program Files` - the setup
  refuses those locations on purpose.

## Run it

Double-click the exe and accept the UAC prompt. With no switches it asks six questions
before touching anything and then prints the resulting plan:

| Question                                                                                         | Default |
| ------------------------------------------------------------------------------------------------ | ------- |
| do you want to run system corruption scans?                                                      | `n`     |
| do you want to add an exclusion for the sirhurt folder?                                          | `y`     |
| do you want to download the latest Roblox build into `%LOCALAPPDATA%\Roblox\Versions`?           | `y`     |
| do you want to download and clean current sirhurt configuration(s) via sirhurt cleaner?          | `y`     |
| do you want to turn off launch at start and minimize to tray to avoid possible injection issues? | `y`     |
| do you want to automatically reboot your PC?                                                     | `n`     |

Enter accepts the default, `y`/`n` answers explicitly. `Ctrl+C` cancels.

Two escape hatches:

- `--help` lists every switch;
- `--no-survey` skips the questions and uses the defaults (everything except the Cleaner
  and the reboot).

The questions are skipped whenever you pass a stage switch, `--dry-run` or `--no-survey`;
`--dir`, `--link` and `--archive` do not skip them.

If no SirHurt archive is found, the setup asks for a path instead of giving up: paste a
file or folder path, press Enter to scan the same folders again, or type `s` to skip
SirHurt entirely (every other stage still runs, and no download link is requested).

## Switches

| Switch                   | Meaning                                                                                                      |
| ------------------------ | ------------------------------------------------------------------------------------------------------------ |
| `--dir PATH`             | install folder (default: SirHurt under Downloads, Desktop or Documents - whichever isn't synced to OneDrive) |
| `--link URL`             | SirHurt download link (gofile.io or app.box.com)                                                             |
| `--archive PATH`         | SirHurt archive to use instead of scanning this script's folder                                              |
| `--no-local-archive`     | ignore any SirHurt archive sitting next to this script                                                       |
| `--skip-roblox-build`    | don't download a Roblox deployment into `%LOCALAPPDATA%\Roblox\Versions`                                     |
| `--roblox-version HASH`  | Roblox build to install instead of the latest one (`version-xxxxxxxxxxxx`)                                   |
| `--roblox-channel NAME`  | Roblox channel to resolve the build on (default: `LIVE`)                                                     |
| `--skip-sirhurt`         | don't install SirHurt                                                                                        |
| `--skip-exclusions`      | don't add the Defender exclusion                                                                             |
| `--skip-repair`          | don't run SFC and DISM                                                                                       |
| `--skip-runtimes`        | don't install VC++ and .NET                                                                                  |
| `--skip-roblox-settings` | don't touch Roblox's appStorage.json                                                                         |
| `--skip-cleaner`         | don't run the SirHurt Cleaner (it deletes Roblox/SirHurt configs, including stored SirHurt login data)       |
| `--reboot`               | restart Windows when the run finishes (15-second delay; cancel with `shutdown /a`)                           |
| `--no-survey`            | don't ask the setup questions; use the defaults (everything except the reboot)                               |
| `--dry-run`              | resolve everything and print it, write nothing                                                               |
| `--version`              | print the version                                                                                            |

## What it changes

Inside the install folder:

| Path         | Content                                                                                                                                                                                                    |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sirhurt\`   | the extracted SirHurt archive (or the gofile/Box download) - a gofile download puts the bootstrapper (`SirHurt V5.exe`) at the top, a Box download keeps it one subfolder down (`sirhurt\SirHurt V5 Web\`) |
| `cleaner\`   | SirHurt Cleaner                                                                                                                                                                                            |
| `downloads\` | the archive it moved into the install folder                                                                                                                                                               |
| `README.txt` | the next steps, written whenever SirHurt is installed                                                                                                                                                      |

Outside the install folder:

- a Windows Defender folder exclusion for the install folder;
- `%LOCALAPPDATA%\Roblox\Versions\version-<hash>` - the deployment's packages unpacked where the
  client expects them, same as RDD: `RobloxApp.zip` and `WebView2.zip` into the version folder
  (`RobloxPlayerBeta.exe`, `RobloxPlayerBeta.dll`, `RobloxCrashHandler.exe`, `COPYRIGHT.txt`,
  `WebView2Loader.dll`), `shaders.zip` into `shaders\`, `ssl.zip` into `ssl\`, the content packages
  into `content\`, `PlatformContent\pc\...` and `ExtraContent\...`, and
  `WebView2RuntimeInstaller.zip` into `WebView2RuntimeInstaller\`, plus `AppSettings.xml`; every
  package is checked against the md5 and size in the manifest, packages already in place are
  skipped, and stale root zips from older layouts are removed;
- `%LOCALAPPDATA%\Roblox\LocalStorage\appStorage.json` - `LaunchAtStartup` and
  `MinimizeToTray` set to `false`, with the original kept as `appStorage.json.bak`;
- the Cleaner, which now runs before the Roblox build is installed, deletes Roblox and SirHurt
  leftovers: `%LOCALAPPDATA%\Roblox`,
  `%APPDATA%\sirhurt`, `%APPDATA%\Sirstrap`, the Roblox and SirHurt folders under
  `Program Files`/`Program Files (x86)`, the `sirhurta.dat`/`sirhurtp.dat`/`Sirstrap.ini`
  configuration files, `rsTrust`, and the `Roblox Corporation`, `Roblox` and `Asshurt`
  registry keys - **including stored SirHurt login data**;
- `--reboot` schedules `shutdown /r /t 15`.

## Next steps

1. Restart Windows if the setup asked for it (the runtimes register at boot).
2. Open Roblox and join any game - injection needs a loaded game client. If SirHurt reports an
   unsupported version, install the build it wants into `%LOCALAPPDATA%\Roblox\Versions` (the
   [Downgrade Tutorial](https://sirhurt.pages.dev/guide/downgrade/) covers it) and start
   `RobloxPlayerBeta.exe` from that folder instead of the Start-menu shortcut.
3. Wait 5-10 seconds after the game finishes loading.
4. Run the SirHurt Legacy UI (`SirHurt V5 (Legacy Ui).exe`) as Administrator - it is in the
   `sirhurt` folder, or one subfolder down if the archive came from a Box share
   (right-click, then Run as administrator, and accept the UAC prompt).
5. If SirHurt says an update is available click **Yes** to let it update.
6. Test with a small script such as Infinite Yield before using your own scripts.

The cleaner (unless you skipped it) deleted stored SirHurt login data, so you will need to log in
again on the first injection.

- Guide: <https://sirhurt.pages.dev/guide/injection/>
- Troubleshooting: <https://sirhurt.pages.dev/guide/troubleshooting/>
- Downgrade: <https://sirhurt.pages.dev/guide/downgrade/>
- Roblox builds: <https://sirhurt.pages.dev/rdd/>
- Discord: <https://discord.gg/sirhurt>

## Build it

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

The script builds `setup.py` with Nuitka, using the repository `.venv` when it exists, and
writes `build\SixSirhurtUnretardifier9000Pro.exe`.

## Releases

`.github/workflows/setup-exe.yml` builds on every push to `main` that touches the tool and on all
pull requests, but only publishes a release when one of these is true:

- a tag matching `v*` or `[0-9]*` is pushed (`git tag v1.2.0 && git push origin v1.2.0`);
- a push to `main` bumps `__version__` in `setup.py` - the release is `v<version>`, and it is
  skipped when that release already exists, so ordinary pushes stay artifact-only;
- a GitHub release is published with the **Release** event;
- **Actions → Setup exe → Run workflow** is started with a tag in the `release` input.

The release job uploads `SixSirhurtUnretardifier9000Pro.exe` and `SHA256SUMS.txt`; if the release
already exists it uploads with `--clobber` instead of failing. A plain push to `main` never
publishes anything.
