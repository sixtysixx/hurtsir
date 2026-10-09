from __future__ import annotations

from dataclasses import dataclass

DOCS = "https://sirhurt.pages.dev"
DISCORD = "https://discord.gg/sirhurt"
PHRASE_WEIGHT = 3
DEFAULT_MIN_SCORE = 3


@dataclass(frozen=True, slots=True)
class FaqEntry:
    id: str
    title: str
    phrases: tuple[str, ...]
    keywords: tuple[str, ...]
    answer: str
    min_score: int = DEFAULT_MIN_SCORE


FAQ: tuple[FaqEntry, ...] = (
    FaqEntry(
        id="unsupported-version",
        title="Unsupported version / version check fails",
        phrases=(
            "unsupported version",
            "version check fails",
            "not supported version",
            "version not supported",
            "outdated version",
            "how do i downgrade",
            "how to downgrade",
            "downgrade guide",
            "downgrade to",
            "downgrade roblox",
            "cant downgrade",
            "can't downgrade",
        ),
        keywords=(
            "unsupported",
            "version",
            "downgrade",
            "downgrading",
            "downgraded",
            "updated",
            "update",
            "hash",
        ),
        answer=(
            "> **Unsupported version** — SirHurt hasn't been patched for your Roblox build yet.\n"
            "> 1. Run the bootstrapper again first; it's usually updated shortly after a Roblox "
            "release.\n"
            "> 2. Still failing? Check <#1364178960354906183> for the supported build hash, then install "
            "that build: <https://sirhurt.pages.dev/guide/downgrade/>, you may be on a beta build.\n"
            "> 3. Fully close Roblox (including the tray icon), replace the build, join a game, "
            "wait 5-10s, then inject.\n"
            "> Full steps: <https://sirhurt.pages.dev/guide/troubleshooting/>"
        ),
    ),
    FaqEntry(
        id="injection-failed",
        title="Injection doesn't work / nothing happens after Inject",
        phrases=(
            "inject",
            "injection",
            "injected",
            "injector",
            "waiting for roblox",
            "waiting to attach",
            "failed to attach",
            "attach failed",
            "cant attach",
            "can't attach",
        ),
        keywords=("failed", "nothing", "happens", "attach", "stuck", "waiting", "click"),
        answer=(
            "> **Injection checklist** (work these in order):\n"
            "> 1. Windows **24H2 or newer** — run `winver`.\n"
            "> 2. Roblox **Launch on startup** and **Minimize to tray when closed** both OFF.\n"
            "> 3. Close Roblox completely, including the tray icon, then reopen.\n"
            "> 4. Join a game and wait **5-10 seconds** before injecting.\n"
            "> 5. Run the Bootstrapper **as Administrator**.\n"
            "> 6. Click **Inject** once and log in — **do not click Inject a second time**.\n"
            "> 7. Test with **Infinite Yield** to confirm the injector is live.\n"
            "> Full walkthrough: <https://sirhurt.pages.dev/guide/injection/>"
        ),
    ),
    FaqEntry(
        id="bootstrapper-hang",
        title="Bootstrapper hangs / won't open / closes instantly",
        phrases=(
            "closes instantly",
            "closing instantly",
            "won't open",
            "wont open",
            "doesn't open",
            "doesnt open",
            "bootstrapper hangs",
            "bootstrapper stuck",
            "not opening",
            "exe won't run",
            "exe wont run",
            "won't even open",
            "wont even open",
            "never opens",
        ),
        keywords=(
            "bootstrapper",
            "hangs",
            "stuck",
            "close",
            "closes",
            "instant",
            "instantly",
            "crash",
            "crashes",
            "open",
            "opening",
        ),
        answer=(
            "> **Bootstrapper hangs / closes instantly**\n"
            "> 1. Use **Kill Processes** in the SirHurt UI\n"
            "> 2. Add a **folder exclusion** for your SirHurt folder — an instant close is "
            "usually your antivirus deleting a file mid-load.\n"
            "> 3. Re-download from <https://sirhurt.net> and extract with **7-Zip or WinRAR** "
            "(Windows' built-in extractor can leave the DLLs blocked).\n"
            "> 4. Run the SirHurt Cleaner and press `Y` + `Enter` on every prompt.\n"
            "> 5. Reinstall **both x86 and x64** Visual C++ Redistributables plus the .NET SDK, "
            "then reboot.\n"
            "> 6. Start the Bootstrapper **as Administrator** again.\n"
            "> Full steps: <https://sirhurt.pages.dev/guide/troubleshooting/>"
        ),
    ),
    FaqEntry(
        id="antivirus",
        title="Antivirus flags / quarantines / deletes SirHurt files",
        phrases=(
            "antivirus",
            "anti virus",
            "windows security",
            "windows defender",
            "false positive",
            "quarantine",
            "deleted my files",
            "virus detected",
            "trojan detected",
            "flagged as virus",
            "protection history",
            "defender deleted",
            "antivirus deleted",
            "keeps deleting",
            "deleted the bootstrapper",
            "deleted robloxplayerbeta",
        ),
        keywords=(
            "antivirus",
            "defender",
            "quarantine",
            "quarantined",
            "exclusion",
            "exclusions",
            "flagged",
            "deleted",
            "deletes",
            "deleting",
            "removed",
            "blocked",
            "robloxplayerbeta",
            "virus",
            "trojan",
            "malware",
            "scanner",
            "detected",
        ),
        answer=(
            "> **Antivirus** — injectors get flagged constantly; it's expected noise, not proof "
            "of anything malicious.\n"
            "> 1. Open your antivirus **quarantine/history** and restore anything "
            "SirHurt-related.\n"
            "> 2. Add a **folder exclusion** for your SirHurt folder **and** your Roblox install "
            "directory.\n"
            "> 3. Re-download anything missing from official sources only — never mirrors or "
            "reuploads.\n"
            "> 4. Re-run the bootstrapper as Administrator to confirm it stays open.\n"
            "> Only exclude those specific folders, and don't leave real-time protection "
            "permanently off.\n"
            "> Full steps: <https://sirhurt.pages.dev/guide/preparation/>"
        ),
    ),
    FaqEntry(
        id="scripts-dont-run",
        title="Scripts don't execute after a successful injection",
        phrases=(
            "script doesn't work",
            "script doesnt work",
            "scripts don't work",
            "scripts dont work",
            "script won't execute",
            "script wont execute",
            "script not working",
            "no scripts work",
            "scripts not working",
            "script error",
            "script errors",
            "scripting error",
            "executor error",
            "script gave an error",
            "script gives an error",
            "script throws an error",
        ),
        keywords=(
            "script",
            "scripts",
            "execute",
            "executes",
            "executing",
            "executor",
            "infinite",
            "yield",
            "console",
            "error",
            "errors",
        ),
        answer=(
            "> **Scripts not executing**\n"
            "> 1. Confirm the injection actually succeeded — the bootstrapper should report a "
            "successful attach, not sit at *waiting*.\n"
            "> 2. Make sure Roblox is **in a game**, not on the home screen.\n"
            "> 3. Run a known-good maintained script (**Infinite Yield**) first, so you know "
            "whether the fault is the injector or the script.\n"
            "> 4. Check #announcements for known script outages.\n"
            "> Full steps: <https://sirhurt.pages.dev/guide/troubleshooting/>"
        ),
    ),
    FaqEntry(
        id="roblox-wont-launch",
        title="Roblox won't launch / black or blank window",
        phrases=(
            "roblox won't launch",
            "roblox wont launch",
            "black window",
            "black screen",
            "blank window",
            "blank screen",
            "roblox not opening",
            "roblox won't open",
            "roblox wont open",
            "roblox won't start",
            "roblox wont start",
            "reinstall roblox",
            "reinstalling roblox",
        ),
        keywords=(
            "roblox",
            "launch",
            "black",
            "blank",
            "window",
            "screen",
            "opening",
            "opens",
            "starting",
        ),
        answer=(
            "> **Roblox won't launch / black injection window**\n"
            "> 1. Kill every Roblox process, including the tray process, then relaunch.\n"
            "> 2. Re-check Roblox settings — **Launch on startup** off, **Minimize to tray when "
            "closed** off.\n"
            "> 3. Run the SFC/DISM repair chain in an **Administrator "
            "PowerShell**, then restart.\n"
            "> 4. Still dead? Reinstall Roblox and redo the Preparation steps before injecting "
            "again.\n"
            "> Full steps: <https://sirhurt.pages.dev/guide/troubleshooting/>"
        ),
    ),
    FaqEntry(
        id="roblox-settings",
        title="Roblox settings that break injection",
        phrases=(
            "launch on startup",
            "minimize to tray",
            "close to tray",
            "system tray",
            "tray icon",
            "tray when closed",
        ),
        keywords=("tray", "startup", "minimize", "setting", "settings", "closed"),
        answer=(
            "> **Two Roblox settings must be OFF:**\n"
            "> 1. **Launch on startup** — otherwise Roblox opens a client before the bootstrapper "
            "is ready for it.\n"
            "> 2. **Minimize to tray when closed** (may read *Close Roblox to system tray*) — "
            "otherwise a hidden Roblox process stays alive and the bootstrapper attaches to the "
            "wrong client.\n"
            "> Then fully close Roblox (window and tray) and reopen it once so the changes take "
            "effect.\n"
            "> Roblox can reset these after an update.\n"
            "> Full steps: <https://sirhurt.pages.dev/guide/roblox-settings/>"
        ),
    ),
    FaqEntry(
        id="windows-version",
        title="Windows version requirement",
        phrases=(
            "windows version",
            "version of windows",
            "windows build",
            "windows 24h2",
            "what windows",
            "which windows",
            "24h2",
            "windows 11",
            "winver",
        ),
        keywords=("windows", "winver", "version", "24h2"),
        answer=(
            "> SirHurt prefers **Windows 11 24H2 or newer**. Run `winver` from the Start menu to "
            "check — older builds may not be supported.\n"
            "> Details: <https://sirhurt.pages.dev/guide/preparation/>"
        ),
    ),
    FaqEntry(
        id="prerequisites",
        title="Missing DLL / VC++ / .NET SDK",
        phrases=(
            "missing dll",
            "dll missing",
            "visual c",
            "vc redist",
            "vcredist",
            "net sdk",
            "dotnet",
            "prerequisites",
            "runtime libraries",
            "vc x86",
            "vc x64",
            "x86 redistributable",
            "x64 redistributable",
            "need vc",
        ),
        keywords=(
            "dll",
            "redistributable",
            "redistributables",
            "redist",
            "runtime",
            "runtimes",
            "dotnet",
            "sdk",
            "install",
            "installer",
            "x86",
            "x64",
            "vc",
            "vcpp",
        ),
        answer=(
            "> **Prerequisites** — SirHurt won't start without these:\n"
            "> 1. **x86** Visual C++ Redistributable\n"
            "> 2. **x64** Visual C++ Redistributable \n"
            "> 3. **.NET SDK** — download both the x86 and x64 installers\n"
            "> Use the installers' defaults, then **restart your PC**: the runtimes register on "
            "reboot.\n"
            "> Full steps: <https://sirhurt.pages.dev/guide/preparation/>"
        ),
    ),
    FaqEntry(
        id="cleaner-auth",
        title="Cleaner wiped my login",
        phrases=(
            "logged out",
            "logged me out",
            "need to log in again",
            "log in again",
            "log back in",
            "cleaner cleared",
            "cleaner wiped",
            "wiped my login",
            "auth data",
            "sirhurt cleaner",
            "login got reset",
            "login was reset",
            "login got wiped",
            "login was wiped",
        ),
        keywords=("cleaner", "auth", "login", "logged", "cleared", "again", "wiped", "reset"),
        answer=(
            "> That's expected — the **SirHurt Cleaner removes SirHurt's stored auth along with "
            "the old files**, so you log in again on your next injection. It is not a sign that "
            "something broke.\n"
            "> When you run the cleaner, press `Y` then `Enter` on **every** prompt; answering "
            "only some of them leaves the remnants behind.\n"
            "> Details: <https://sirhurt.pages.dev/guide/roblox-settings/>"
        ),
    ),
    FaqEntry(
        id="rdd-download-fails",
        title="Downgrade Thingamabob 6000 downloads fail",
        phrases=(
            "download fails",
            "download failed",
            "downloads fail",
            "thingamabob",
            "download previous version",
            "rdd fails",
            "download error",
        ),
        keywords=(
            "download",
            "downloads",
            "fails",
            "failed",
            "error",
            "rdd",
            "thingamabob",
            "cdn",
            "disk",
        ),
        answer=(
            "> **Downgrade Thingamabob 6000 download failures**\n"
            "> 1. Read the log panel — it reports the exact HTTP status, which tells you whether "
            "it's your network or Roblox's CDN.\n"
            "> 2. If **Download Latest Version** fails, retry with **Download Previous Version** "
            "— that's usually the build SirHurt wants anyway.\n"
            "> 3. Targeting a specific executor? Pass `?exploit=<name>` so RDD resolves the build "
            "it is pinned to.\n"
            "> 4. On repeated network errors try **Cloudflare WARP** — the log panel links it "
            "under the error.\n"
            "> 5. Make sure you have a few hundred MB of free disk space: the archive is "
            "assembled **in memory in your browser**.\n"
            "> Open it here: <https://sirhurt.pages.dev/rdd/>"
        ),
    ),
    FaqEntry(
        id="account-suspended",
        title="Suspended or banned account",
        phrases=(
            "my account got banned",
            "my account was banned",
            "my account got suspended",
            "my account was suspended",
            "why was i banned",
            "why did i get banned",
            "why am i banned",
            "am i banned",
            "i was banned",
            "i got banned",
            "got my account banned",
            "ban appeal",
            "appeal my ban",
            "my ban appeal",
            "how do i get unbanned",
            "get unbanned",
            "unban me",
            "hwid ban",
            "hwid banned",
            "hwid locked",
            "contact support",
            "support ticket",
            "open a ticket",
            "how do i open a ticket",
            "make a ticket",
        ),
        keywords=(
            "banned",
            "ban",
            "bans",
            "suspended",
            "suspension",
            "suspend",
            "appeal",
            "appeals",
            "unban",
            "unbanned",
            "hwid",
            "reinstated",
            "ticket",
            "tickets",
            "staff",
        ),
        answer=(
            "> **Suspended or banned account**\n"
            "> Talk to staff directly — **Spook** or **Alex** — or open a ticket:\n"
            "> <https://sirhurt.net/login/tickets/tickethistory.php>\n"
            "> Include these or it takes longer:\n"
            "> 1. The username or email on the SirHurt account.\n"
            "> 2. Roughly when you were suspended, and what you were doing.\n"
            "> 3. Screenshots of anything the panel showed you.\n"
            "> Mistaken bans and HWID locks do get reversed; ban evasion and chargebacks "
            "don't.\n"
            "> Staff: <https://discord.gg/sirhurt>\n"
            "> Missing key or payment trouble is handled differently — see the billing answer."
        ),
    ),
    FaqEntry(
        id="billing-issues",
        title="Billing / purchase / product key issues",
        phrases=(
            "selly id",
            "selly",
            "tracking page",
            "product key",
            "where is my key",
            "where's my key",
            "wheres my key",
            "didn't get my key",
            "didnt get my key",
            "no key after",
            "lost my key",
            "resend my key",
            "recover my key",
            "key not working",
            "key doesn't work",
            "key doesnt work",
            "invalid key",
            "never got a key",
            "never got my key",
            "never received my key",
            "didn't get a key",
            "didnt get a key",
            "bought but no key",
            "paid but no key",
            "payment went through",
            "charged twice",
            "double charged",
            "billing",
            "billing issue",
            "billing problem",
            "payment",
            "purchase",
            "refund",
            "chargeback",
        ),
        keywords=(
            "selly",
            "key",
            "keys",
            "purchase",
            "purchased",
            "bought",
            "payment",
            "paid",
            "pay",
            "billing",
            "invoice",
            "refund",
            "charge",
            "charged",
            "order",
            "receipt",
            "tracking",
            "transaction",
        ),
        answer=(
            "> **Billing / product key issues**\n"
            "> 1. Bought through **Selly**? Enter your **Selly ID** on the tracking page to "
            "look up the order and get your product key:\n"
            "> <https://sirhurt.net/login/tracking/tracking.html>\n"
            "> 2. No Selly ID? DM **Spook** or **Alex** with any order details you may have:\n"
            "> <https://discord.gg/sirhurt>\n"
            "> Only keys issued from the official site can be recovered. Keys from resellers, "
            "mirrors or giveaways are at your own risk and cannot be reissued."
        ),
    ),
)

HELP = "\n".join(
    (
        "**SirHurt FAQ** — I can answer these:",
        *(f"- {entry.title}" for entry in FAQ),
        f"Full guide: <{DOCS}/guide/preparation/> — ask in **#support** in the Discord: <{DISCORD}>",
    )
)

# Appended to every reply. "-#" is Discord's small-text (subtext) marker.
FOOTER = (
    "-# This is an automated reply, additional resources can be found in pinned messages. "
    "If this doesnt solve your issue wait for a CSR"
)
