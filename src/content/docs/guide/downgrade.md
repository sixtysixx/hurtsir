---
title: Downgrade Tutorial
description: Download a specific Roblox build and put it in the Roblox Versions folder for compatibility with SirHurt.
---

:::Caution
**Recommended Version (as of 11/12/2026):** [version-4ea8e85481e34f46 (latest, no need to downgrade unless youre on beta)](https://sirhurt.net/downgradetutorial.php?version=version-4ea8e85481e34f46)
:::

SirHurt injects into the Roblox build that is installed on your machine, so a downgrade is a
folder swap: the build lives in `%LOCALAPPDATA%\Roblox\Versions\version-<hash>`, and that folder
is what the bootstrapper attaches to. There is nothing else to install.

## Steps

1. Take the build hash SirHurt currently supports - the caution above, or the announcements
   channel in our [Discord](https://discord.gg/sirhurt).
2. Head to the [Downgrade Thingamabob 6000](/rdd/) and download it. **Download Previous Version**
   tracks the current downgrade target, **Download Latest Version** grabs the newest published
   build. Either way you get `version-<hash>.zip`.
3. Fully close Roblox, including the tray icon - a running client keeps the old build alive.
4. Open `%LOCALAPPDATA%\Roblox\Versions` in Explorer. Paste the path into the address bar;
   `AppData` is hidden by default.
5. Make a folder named after the build and extract the zip into it, so you end up with
   `Versions\version-<hash>\RobloxPlayerBeta.exe`, `WebView2Loader.dll`, `AppSettings.xml` and the
   `content\`, `PlatformContent\`, `ExtraContent\`, `shaders\` and `ssl\` folders beside them.
   The zip has no wrapper folder, so create `version-<hash>` yourself and extract into it with
   **7-Zip** or **WinRAR**. Keep the packages where the zip puts them - a `WebView2Loader.dll` left
   inside `WebView2.zip` makes Roblox fail with "Failed to load library".
6. Start `RobloxPlayerBeta.exe` from inside that folder rather than the Start-menu shortcut. The
   shortcut runs Roblox's updater, which pulls the newest build back over the one you installed.
7. Join a game, wait 5-10 seconds for the client to finish loading, then inject from the
   bootstrapper. Do not click **Inject** a second time.

The setup tool does steps 2-5 for you: it resolves the published build, downloads every package
and unpacks it into `Versions\version-<hash>` (`--roblox-version version-<hash>` pins a specific
one, `--roblox-channel` follows a non-`LIVE` channel).

<br>

<video controls src="https://r2.e-z.host/a466cf7c-0034-4d68-80d8-1c7ad54cf3c3/f9i7okia.mp4" title="awesome sauce video"></video>
