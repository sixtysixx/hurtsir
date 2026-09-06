# ============================================================================
#  SirHurt One-Click Setup (mirrors the hurtsir troubleshooting guide)
#
#  What it does, in order:
#    1. Installs Visual C++ Redistributables (x64 + x86)      - silent
#    2. Installs .NET SDK 10.0.400 (x64 + x86)                - silent
#    3. Downloads + silently installs 7-Zip
#    4. Sets MinimizeToTray / LaunchAtStartup = false in
#       %localappdata%\Roblox\localStorage\appStorage.json
#    5. Creates the dedicated SirHurt folder, adds it to the
#       antivirus (Windows Defender) exclusions, then waits for you to
#       download the SirHurt archive (watches Downloads/Desktop/Documents
#       every 5 s, moves it to the safe folder) and extracts it with 7-Zip
#
#  Run with:  right-click -> Run with PowerShell   (it self-elevates)
#            or: powershell -ExecutionPolicy Bypass -File setup_sirhurt.ps1
#  At the end the PC RESTARTS AUTOMATICALLY. After the next logon the
#  default browser opens https://www.roblox.com/games/189707/Natural-Disaster-Survival
#
# ============================================================================

[CmdletBinding()]
param(
    # Folder where SirHurt is extracted and excluded from AV
    [string]$SirHurtDir = (Join-Path $env:USERPROFILE 'Downloads\sirhurt_utils'),
    # .NET SDK version to install (both architectures)
    [string]$DotnetVersion = '10.0.400'
)

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12


# ----------------------------------------------------------------------------
# 0. Self-elevate to Administrator (needed for installers + AV exclusions)
# ----------------------------------------------------------------------------
$identity  = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host 'Requesting administrator privileges...' -ForegroundColor Yellow
    Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', "-File `"$PSCommandPath`""
    )
    exit
}

# Log everything - the elevated window closes on exit, so keep a transcript
# the user can check afterwards if something goes wrong.
Start-Transcript -Path (Join-Path $env:TEMP 'sirhurt_setup.log') -Force | Out-Null

$script:UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'

$tmp = Join-Path $env:TEMP 'sirhurt_setup'
New-Item -ItemType Directory -Path $tmp -Force | Out-Null

function Write-Step { param([string]$m) Write-Host "`n=== $m ===" -ForegroundColor Cyan }
function Write-Ok   { param([string]$m) Write-Host "  [OK] $m"   -ForegroundColor Green }
function Write-Warn2{ param([string]$m) Write-Host "  [!]  $m"  -ForegroundColor Yellow }

function Get-File {
    param([string]$Url, [string]$Out)
    if (Test-Path $Out) { return $Out }
    Write-Host "  Downloading $Url" -ForegroundColor DarkGray
    try {
        Invoke-WebRequest -Uri $Url -OutFile $Out -UseBasicParsing -UserAgent $script:UA
    } catch {
        Start-BitsTransfer -Source $Url -Destination $Out
    }
    return $Out
}

# All of steps 1-5 are best-effort: a failure here is reported but must
# NEVER prevent steps 6-7 (scheduled task + restart) from running.
try {
# 1. Visual C++ Redistributables (x64 + x86)
# ----------------------------------------------------------------------------
Write-Step 'Step 1/7 - Visual C++ Redistributables (x64 + x86)'
$vc = @{
    'vc_redist.x64.exe' = 'https://aka.ms/vc14/vc_redist.x64.exe'
    'vc_redist.x86.exe' = 'https://aka.ms/vc14/vc_redist.x86.exe'
}
foreach ($name in $vc.Keys) {
    $exe = Get-File -Url $vc[$name] -Out (Join-Path $tmp $name)
    Write-Host "  Installing $name ..." -ForegroundColor DarkGray
    $p = Start-Process -FilePath $exe -ArgumentList '/install', '/quiet', '/norestart' -Wait -PassThru
    # 0 = installed, 1638 = newer already installed, 4000 = installed, reboot required
    if ($p.ExitCode -in 0, 1638, 4000) { Write-Ok "$name finished (exit $($p.ExitCode))" }
    else { Write-Warn2 "$name exited with code $($p.ExitCode)" }
}

# ----------------------------------------------------------------------------
# 2. .NET SDK (x64 + x86)
# ----------------------------------------------------------------------------
Write-Step "Step 2/7 - .NET SDK $DotnetVersion (x64 + x86)"
$sdks = @{
    'dotnet-sdk-win-x64.exe' = "https://builds.dotnet.microsoft.com/dotnet/Sdk/$DotnetVersion/dotnet-sdk-$DotnetVersion-win-x64.exe"
    'dotnet-sdk-win-x86.exe' = "https://builds.dotnet.microsoft.com/dotnet/Sdk/$DotnetVersion/dotnet-sdk-$DotnetVersion-win-x86.exe"
}
foreach ($name in $sdks.Keys) {
    $exe = Get-File -Url $sdks[$name] -Out (Join-Path $tmp $name)
    Write-Host "  Installing $name ..." -ForegroundColor DarkGray
    $p = Start-Process -FilePath $exe -ArgumentList '/install', '/quiet', '/norestart' -Wait -PassThru
    if ($p.ExitCode -in 0, 1638, 4000) { Write-Ok "$name finished (exit $($p.ExitCode))" }
    else { Write-Warn2 "$name exited with code $($p.ExitCode)" }
}

# ----------------------------------------------------------------------------
# 3. 7-Zip (silent install)
# ----------------------------------------------------------------------------
Write-Step 'Step 3/7 - 7-Zip (silent install)'
$sevenZip = Join-Path $env:ProgramFiles '7-Zip\7z.exe'
if (-not (Test-Path $sevenZip)) {
    $installer = Get-File -Url 'https://github.com/ip7z/7zip/releases/download/26.03/7z2603-x64.exe' -Out (Join-Path $tmp '7z2603-x64.exe')
    Write-Host '  Installing 7-Zip ...' -ForegroundColor DarkGray
    Start-Process -FilePath $installer -ArgumentList '/S' -Wait
    if (Test-Path $sevenZip) { Write-Ok '7-Zip installed' }
    else {
        Write-Warn2 '7-Zip not found at default path; extraction will fall back to Expand-Archive'
        $sevenZip = $null
    }
} else {
    Write-Ok '7-Zip already installed'
}

# ----------------------------------------------------------------------------
# 4. Roblox appStorage.json - disable MinimizeToTray / LaunchAtStartup
# ----------------------------------------------------------------------------
Write-Step 'Step 4/7 - Roblox: disable MinimizeToTray & LaunchAtStartup'

# Roblox rewrites localStorage on exit, so kill it before editing
Get-Process -Name 'RobloxPlayerBeta', 'RobloxCrashHandler' -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue

$appStorage = Join-Path $env:LOCALAPPDATA 'Roblox\localStorage\appStorage.json'
if (Test-Path $appStorage) {
    try {
        Copy-Item $appStorage "$appStorage.bak" -Force
        $json = Get-Content $appStorage -Raw | ConvertFrom-Json
        foreach ($key in 'MinimizeToTray', 'LaunchAtStartup') {
            $prop = $json.PSObject.Properties[$key]   # case-insensitive lookup
            if ($prop) {
                # preserve the original value type (Roblox stores strings)
                if ($prop.Value -is [string]) { $prop.Value = 'false' }
                else                          { $prop.Value = $false }
            } else {
                $json | Add-Member -NotePropertyName $key -NotePropertyValue $false
            }
        }
        $json | ConvertTo-Json -Depth 100 -Compress | Set-Content $appStorage -Encoding UTF8
        Write-Ok 'appStorage.json updated (backup at appStorage.json.bak)'
    } catch {
        Write-Warn2 "Failed to edit appStorage.json: $($_.Exception.Message)"
        Write-Warn2 'Disable "Minimize to tray" and "Launch on startup" manually in Roblox settings.'
    }
} else {
    Write-Warn2 'appStorage.json not found (Roblox may not be installed yet).'
    Write-Warn2 'Re-run this script, or disable the settings manually in Roblox.'
}

# ----------------------------------------------------------------------------
# 5. SirHurt: excluded folder -> AV exclusion -> download -> extract
# ----------------------------------------------------------------------------
Write-Step 'Step 5/7 - SirHurt folder, AV exclusion, download & extract'

New-Item -ItemType Directory -Path $SirHurtDir -Force | Out-Null
Write-Ok "Dedicated folder ready: $SirHurtDir"

# --- Windows Defender exclusion (add BOTH the folder and common processes) --
try {
    $pref = Get-MpPreference
    if ($pref.ExclusionPath -notcontains $SirHurtDir) {
        Add-MpPreference -ExclusionPath $SirHurtDir
        Write-Ok "Defender exclusion added for: $SirHurtDir"
    } else {
        Write-Ok 'Defender exclusion already present'
    }
    foreach ($proc in 'SirHurt.exe', 'Bootstrapper.exe') {
        if ($pref.ExclusionProcess -notcontains $proc) {
            Add-MpPreference -ExclusionProcess $proc -ErrorAction SilentlyContinue
        }
    }
} catch {
    Write-Warn2 'Could not add Windows Defender exclusions (third-party AV?).'
    Write-Warn2 "Add $SirHurtDir to your AV exclusion/whitelist MANUALLY, then press Enter."
    Read-Host 'Press Enter once the AV exclusion is in place'
}


# --- SirHurt download: user downloads manually, script watches for it -------

Write-Host ''
Write-Host '  ACTION REQUIRED - download SirHurt manually:' -ForegroundColor Yellow
Write-Host '    1. The official site is opening in your browser.' -ForegroundColor Yellow
Write-Host '    2. Save the SirHurt archive (zip/rar/7z) anywhere in' -ForegroundColor Yellow
Write-Host '       Downloads, Desktop or Documents.' -ForegroundColor Yellow
Write-Host "    3. It will be detected automatically and moved to $SirHurtDir" -ForegroundColor Yellow
Start-Process 'https://sirhurt.net/login/download.php'

function Find-SirHurtArchive {
    # Newest zip/rar/7z in Downloads / Desktop / Documents (top level only).
    # Prefer files with 'sirhurt' in the name; otherwise only accept archives
    # that appeared AFTER the watcher started (skips old unrelated downloads).
    $dirs = @(
        (Join-Path $env:USERPROFILE 'Downloads'),
        (Join-Path $env:USERPROFILE 'Desktop'),
        (Join-Path $env:USERPROFILE 'Documents')) | Where-Object { Test-Path $_ }
    $hits = Get-ChildItem -Path $dirs -File -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Extension -in '.zip', '.rar', '.7z' -and
            ($_.Name -match 'sirhurt' -or $_.CreationTime -gt $script:watchStart)
        }
    $hits | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}

$script:watchStart = Get-Date
Write-Host '  Watching Downloads / Desktop / Documents for the archive (5 s interval)...' -ForegroundColor DarkGray
$archive = $null
while (-not $archive) {
    Start-Sleep -Seconds 5
    $found = Find-SirHurtArchive
    if ($found) {
        # Give the browser time to finish writing, then require a stable size
        # across two checks so we never move a half-downloaded file.
        $size1 = $found.Length
        Start-Sleep -Seconds 3
        $found2 = Find-SirHurtArchive
        if ($found2 -and $found2.FullName -eq $found.FullName -and $found2.Length -eq $size1) {
            $archive = Join-Path $SirHurtDir 'SirHurt V5.zip'
            Move-Item -LiteralPath $found.FullName -Destination $archive -Force
            Write-Ok "Detected and moved: $($found.Name) -> $archive"
        }
    }
}

# --- Extract with 7-Zip into the excluded folder ----------------------------
# SirHurt V5 web zip is DOUBLE zipped: the downloaded archive contains
# "sirhurt v5.zip", which itself holds the actual files. Extract both layers.
$extractDir = Join-Path $SirHurtDir 'SirHurt'
New-Item -ItemType Directory -Path $extractDir -Force | Out-Null

function Expand-SirHurtArchive {
    param([string]$Path, [string]$Dest)
    if ($sevenZip -and (Test-Path $sevenZip)) {
        & $sevenZip x $Path -o"$Dest" -y -bso0 -bsp0
        return ($LASTEXITCODE -eq 0)
    }
    try {
        Expand-Archive -Path $Path -DestinationPath $Dest -Force
        return $true
    } catch {
        Write-Warn2 "Expand-Archive failed ($($_.Exception.Message))"
        return $false
    }
}

if (Expand-SirHurtArchive -Path $archive -Dest $extractDir) {
    Write-Ok "Extracted outer archive to: $extractDir"

    # Layer 2: find the inner "sirhurt v5.zip" and extract it in place
    $inner = Get-ChildItem -Path $extractDir -Recurse -Filter '*.zip' -File |
        Sort-Object Length -Descending |
        Select-Object -First 1
    if ($inner) {
        $innerDest = $inner.DirectoryName
        if (Expand-SirHurtArchive -Path $inner.FullName -Dest $innerDest) {
            Write-Ok "Extracted inner archive: $($inner.Name)"
            Remove-Item -LiteralPath $inner.FullName -Force -ErrorAction SilentlyContinue
        } else {
            Write-Warn2 "Failed to extract inner zip: $($inner.FullName) - extract it manually"
        }
    } else {
        Write-Host '  No inner zip found (single-layer archive) - continuing.' -ForegroundColor DarkGray
    }
} else {
    Write-Warn2 "Extraction failed - extract $archive manually with 7-Zip/WinRAR into $extractDir"
}


} catch {
    Write-Host ''
    Write-Warn2 "Setup step failed: $($_.Exception.Message)"
    Write-Warn2 'Continuing anyway - the restart and post-logon task still run.'
    Write-Warn2 "Full log: $env:TEMP\sirhurt_setup.log"
}

# ----------------------------------------------------------------------------
# 6. One-shot scheduled task: open the game page in the default browser
#    automatically at next logon (after the restart below)
# ----------------------------------------------------------------------------
Write-Step 'Step 6/7 - Register post-logon browser task'

$gameUrl  = 'https://www.roblox.com/games/189707/Natural-Disaster-Survival'
$taskName = 'OpenRobloxGamePageOnce'

$openCmd = "Start-Process '$gameUrl'; " +
           "Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
$encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($openCmd))
$action  = New-ScheduledTaskAction -Execute 'powershell.exe' `
              -Argument "-NoProfile -WindowStyle Hidden -EncodedCommand $encoded"
$trigger  = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
               -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
    -Settings $settings -Description 'Opens the Roblox game page once after logon' -Force | Out-Null
Write-Ok "Task '$taskName' registered (runs once at next logon, then is removed)"

# ----------------------------------------------------------------------------
# 7. Automatic restart
# ----------------------------------------------------------------------------
Write-Step 'Step 7/7 - Restarting automatically'
Write-Host '  The PC will RESTART in 15 seconds - save your work!' -ForegroundColor Yellow
Write-Host "  After logon the default browser opens: $gameUrl" -ForegroundColor Yellow

# /g restarts AND re-opens signed-in apps; /a aborts if the user needs to cancel
shutdown.exe /g /t 15 /c 'SirHurt setup finished - restarting to complete installation'

Write-Step 'ALL DONE'
Write-Host @"

  Summary
  -------
  - VC++ Redistributables (x64 + x86)    : installed
  - .NET SDK $DotnetVersion (x64 + x86)  : installed
  - 7-Zip                                : installed
  - Roblox MinimizeToTray/LaunchAtStartup: disabled (backup written)
  - SirHurt folder (AV-excluded)         : $SirHurtDir
  - SirHurt extracted to                 : $extractDir
  - Post-logon browser task              : registered (one-shot)
  - Restart                              : in 15 seconds

  AFTER THE RESTART (all automatic)
  ---------------------------------
  1. Log in - the default browser opens $gameUrl by itself.
  2. Open Roblox via Sirstrap and join a game.
  3. Run the SirHurt Bootstrapper from $extractDir as Administrator.
  4. Wait 5-10 seconds in-game, then press Inject and log in.

"@ -ForegroundColor Green
