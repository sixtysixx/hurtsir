/*
    rdd - https://github.com/latte-soft/rdd

    Copyright (C) 2024-2025 Latte Softworks <latte.to> | MIT License
    Forked by SirHurt
*/
// fix for the phishing message on downloading Roblox (false positive)
const basePath = window.location.href.split("?")[0];
// Version-history + exploit backend. Defaults to the public WEAO tracker API,
// which is the same backend the upstream RDD deployment uses. Override it with
// `window.RDD_API_BASE = "https://..."` or `?api=https://...` to self-host.
const apiBase = (
    new URLSearchParams(window.location.search).get("api") ||
    (typeof window.RDD_API_BASE === "string" ? window.RDD_API_BASE : "") ||
    "https://weao.gg"
).replace(/\/+$/, "");
const usageMsg = `[*] USAGE: ${basePath}?channel=<CHANNEL_NAME>&binaryType=<BINARY_TYPE>&version=<VERSION_HASH>

    Binary Types:
    * WindowsPlayer
    * WindowsStudio64
    * MacPlayer
    * MacStudio
    
    Extra Notes:
    * If \`channel\` isn't provided, it will default to "LIVE" (pseudo identifier for
      the production channel)
    * You can provide \`binaryType\` to fetch the *latest* deployment on a channel, or
      BOTH \`binaryType\` and \`version\` to fetch a specific deployment of a specific
      binary type; for a specific \`version\`, you NEED to provide \`binaryType\` aswell
    * Hitting *Download Latest Version* will automatically fetch the latest deployment of Roblox
    * Hitting *Download Previous Version* will automatically fetch the previous deployment of Roblox (downgrade)
    * If you want to download a specific version, specify the version hash in the version field and hit *Download Specified Hash*

    You can also use an extra flag we provide, \`blobDir\`, for specifying where RDD
    should fetch deployment files/binaries from. This is ONLY useful for using
    different relative paths than normal, such as "/mac/arm64" which is specifically
    present on certain channels

    Blob Directories (Examples):
    * "/" (Default for WindowsPlayer/WindowsStudio64)
    * "/mac/" (Default for MacPlayer/MacStudio)
    * "/mac/arm64/"
    ..
`;

// Roblox's CDN is the default source. Because Roblox blocks the deployment
// manifest and the client archive (RobloxApp.zip) for non-official clients, a
// mirror/backend can be supplied with `window.RDD_MIRROR = "https://..."` or a
// `?mirror=https://...` query parameter.
const _mirrorBase = (
    new URLSearchParams(window.location.search).get("mirror") ||
    (typeof window.RDD_MIRROR === "string" ? window.RDD_MIRROR : "")
).replace(/\/+$/, "");
const hostPath = _mirrorBase || "https://setup-aws.rbxcdn.com";
// Root extract locations for the Win manifests
const extractRoots = {
    player: {
        "RobloxApp.zip": "",
        "redist.zip": "",
        "shaders.zip": "shaders/",
        "ssl.zip": "ssl/",

        "WebView2.zip": "",
        "WebView2RuntimeInstaller.zip": "WebView2RuntimeInstaller/",

        "content-avatar.zip": "content/avatar/",
        "content-configs.zip": "content/configs/",
        "content-fonts.zip": "content/fonts/",
        "content-sky.zip": "content/sky/",
        "content-sounds.zip": "content/sounds/",
        "content-textures2.zip": "content/textures/",
        "content-models.zip": "content/models/",

        "content-platform-fonts.zip": "PlatformContent/pc/fonts/",
        "content-platform-dictionaries.zip": "PlatformContent/pc/shared_compression_dictionaries/",
        "content-terrain.zip": "PlatformContent/pc/terrain/",
        "content-textures3.zip": "PlatformContent/pc/textures/",

        "extracontent-luapackages.zip": "ExtraContent/LuaPackages/",
        "extracontent-translations.zip": "ExtraContent/translations/",
        "extracontent-models.zip": "ExtraContent/models/",
        "extracontent-textures.zip": "ExtraContent/textures/",
        "extracontent-places.zip": "ExtraContent/places/"
    },

    studio: {
        "RobloxStudio.zip": "",
        "RibbonConfig.zip": "RibbonConfig/",
        "redist.zip": "",
        "Libraries.zip": "",
        "LibrariesQt5.zip": "",

        "WebView2.zip": "",
        "WebView2RuntimeInstaller.zip": "",

        "shaders.zip": "shaders/",
        "ssl.zip": "ssl/",

        "Qml.zip": "Qml/",
        "Plugins.zip": "Plugins/",
        "StudioFonts.zip": "StudioFonts/",
        "BuiltInPlugins.zip": "BuiltInPlugins/",
        "ApplicationConfig.zip": "ApplicationConfig/",
        "BuiltInStandalonePlugins.zip": "BuiltInStandalonePlugins/",

        "content-qt_translations.zip": "content/qt_translations/",
        "content-sky.zip": "content/sky/",
        "content-fonts.zip": "content/fonts/",
        "content-avatar.zip": "content/avatar/",
        "content-models.zip": "content/models/",
        "content-sounds.zip": "content/sounds/",
        "content-configs.zip": "content/configs/",
        "content-api-docs.zip": "content/api_docs/",
        "content-textures2.zip": "content/textures/",
        "content-studio_svg_textures.zip": "content/studio_svg_textures/",

        "content-platform-fonts.zip": "PlatformContent/pc/fonts/",
        "content-platform-dictionaries.zip": "PlatformContent/pc/shared_compression_dictionaries/",
        "content-terrain.zip": "PlatformContent/pc/terrain/",
        "content-textures3.zip": "PlatformContent/pc/textures/",

        "extracontent-translations.zip": "ExtraContent/translations/",
        "extracontent-luapackages.zip": "ExtraContent/LuaPackages/",
        "extracontent-textures.zip": "ExtraContent/textures/",
        "extracontent-scripts.zip": "ExtraContent/scripts/",
        "extracontent-models.zip": "ExtraContent/models/",
        "studiocontent-models.zip": "StudioContent/models/",
        "studiocontent-textures.zip": "StudioContent/textures/"
    }
};
const binaryTypes = {
    WindowsPlayer: {
        versionFile: "/version",
        blobDir: "/"
    },
    WindowsStudio64: {
        versionFile: "/versionQTStudio",
        blobDir: "/"
    },
    MacPlayer: {
        versionFile: "/mac/version",
        blobDir: "/mac/"
    },
    MacStudio: {
        versionFile: "/mac/versionStudio",
        blobDir: "/mac/"
    },
}

// Roblox's official deployment API. It reports the *published* build for a
// binary type, which is what actually exists on the CDN. The CDN's `/version`
// file can point at a newer build that is staged but not yet downloadable
// (rbxPkgManifest.txt / RobloxApp.zip answer 403 for it).
const settingsHost = "https://clientsettingscdn.roblox.com";

// Resolve the latest downloadable version hash with no backend required.
async function fetchLatestVersion(binaryType, channelName) {
    const info = binaryTypes[binaryType];
    if (!info) {
        throw new Error(`Unsupported binaryType "${binaryType}"`);
    }

    const isLive = !channelName || /^(live|production)$/i.test(channelName);

    // 1) Official deployment API (CORS-enabled; only LIVE is public).
    try {
        const apiUrl = isLive
            ? `${settingsHost}/v2/client-version/${binaryType}`
            : `${settingsHost}/v2/client-version/${binaryType}/channel/${encodeURIComponent(channelName)}`;
        const apiResponse = await fetch(apiUrl);
        if (apiResponse.ok) {
            const data = await apiResponse.json();
            const hash = data && data.clientVersionUpload;
            if (hash) {
                return hash.startsWith("version-") ? hash : `version-${hash}`;
            }
        }
    } catch {
        // Fall through to the tracker API below.
    }

    // 2) Version-tracker API (same backend the upstream RDD deployment uses).
    try {
        const apiResponse = await fetch(`${apiBase}/api/versions/current`);
        if (apiResponse.ok) {
            const hash = versionFromApiPayload(await apiResponse.json(), binaryType);
            if (hash) {
                return hash.startsWith("version-") ? hash : `version-${hash}`;
            }
        }
    } catch {
        // Fall through to the CDN version file below.
    }

    // 3) CDN `version` file fallback (custom channels, or if the APIs are down).
    const channel = isLive ? "LIVE" : channelName.toLowerCase();
    const channelPath = channel === "LIVE" ? hostPath : `${hostPath}/channel/${channel}`;

    const response = await fetch(channelPath + info.versionFile);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const text = (await response.text()).trim();
    if (!text) {
        throw new Error("Empty version file returned by Roblox CDN");
    }

    return text.startsWith("version-") ? text : `version-${text}`;
}

function versionFromApiPayload(data, binaryType) {
    if (!data) return null;
    if (binaryType === "WindowsPlayer" || binaryType === "WindowsStudio64") return data.Windows || null;
    if (binaryType === "MacPlayer" || binaryType === "MacStudio") return data.Mac || null;
    return null;
}

// Previous ("downgrade") build, straight from the tracker API.
async function fetchPreviousVersion(binaryType) {
    const response = await fetch(`${apiBase}/api/versions/past`);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status} from ${apiBase}/api/versions/past`);
    }

    const hash = versionFromApiPayload(await response.json(), binaryType);
    if (!hash) {
        throw new Error(`No previous release tracked for "${binaryType}"`);
    }

    return hash.startsWith("version-") ? hash : `version-${hash}`;
}

function fieldValue(name, fallback = "") {
    const el = form && form.elements ? form.elements[name] : null;
    return el && typeof el.value === "string" ? el.value : fallback;
}

function fieldChecked(name) {
    const el = form && form.elements ? form.elements[name] : null;
    return !!(el && el.checked);
}

// Keep the mirror choice when handing off to the download tab.
function mirrorSuffix() {
    return _mirrorBase ? `&mirror=${encodeURIComponent(_mirrorBase)}` : "";
}

// Keep a custom API base when handing off to the download tab.
function apiSuffix() {
    return apiBase === "https://weao.gg" ? "" : `&api=${encodeURIComponent(apiBase)}`;
}

const urlParams = new URLSearchParams(window.location.search);

const logBox = document.getElementById("logBox");
const form = document.getElementById("form");
const formDiv = document.getElementById("formDiv");
const progWrap = document.getElementById("progWrap");
const progFill = document.getElementById("progFill");
const progMsg = document.getElementById("progMsg");

function getLink() {
    const channelName = (fieldValue("channel") || "LIVE").trim() || "LIVE";
    let qs = `?channel=${encodeURIComponent(channelName)}&binaryType=${encodeURIComponent(fieldValue("binaryType"))}`;

    const ver = fieldValue("version").trim();
    if (ver !== "") qs += `&version=${encodeURIComponent(ver)}`;

    if (fieldChecked("compressZip")) qs += `&compressZip=true&compressionLevel=${encodeURIComponent(fieldValue("compressionLevel", "1"))}`;
    qs += `&parallelDownloads=${fieldChecked("parallelDownloads")}`;
    qs += mirrorSuffix();
    qs += apiSuffix();

    return basePath + qs;
};

function dlHash() {
    const studioTypes = new Set(['WindowsStudio64', 'MacStudio']);
    if (studioTypes.has(form.binaryType.value) && !form.version.value.trim()) {
        log("[!] Error: A version hash is required for Studio binary types.");
        logBox.style.display = 'flex';
        scrollEnd();
        return;
    }
    window.open(getLink(), "_blank");
};
function copyLink(btn) {
    navigator.clipboard.writeText(getLink());
    if (!btn || btn._copying) return;
    btn._copying = true;
    const orig = btn.innerHTML;
    btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Copied!`;
    btn.style.color       = 'var(--amethyst)';
    btn.style.borderColor = 'rgba(157,78,221,0.3)';
    btn.style.background  = 'rgba(157,78,221,0.07)';
    setTimeout(() => {
        btn.innerHTML = orig;
        btn.style.color = btn.style.borderColor = btn.style.background = '';
        btn._copying = false;
    }, 2000);
};

async function dlLatest() { // Easy button to download the latest version of a binary! 
    const binaryType = form.binaryType.value;
    const channelName = form.channel.value.trim() || form.channel.placeholder;
    let versionHash;

    try {
        log(`[*] Resolving latest published ${binaryType} build (channel: ${channelName})...`);
        versionHash = await fetchLatestVersion(binaryType, channelName);

        let queryString = `?channel=${encodeURIComponent(channelName)}&binaryType=${encodeURIComponent(binaryType)}&version=${encodeURIComponent(versionHash)}`;
        const compressZip = fieldChecked("compressZip");
        const compressionLevel = fieldValue("compressionLevel", "1");
        if (compressZip === true) {
            queryString += `&compressZip=true&compressionLevel=${encodeURIComponent(compressionLevel)}`;
        }

        queryString += `&parallelDownloads=${fieldChecked("parallelDownloads")}`;
        queryString += mirrorSuffix();
        queryString += apiSuffix();

        window.open(basePath + queryString, "_blank");

    } catch (error) {
        log(`[!] Error fetching latest version: ${error.message}`);
        logWarpHint();
    }
}

async function dlPrev() { 
    // Helps restart swift users to downgrade to exploit :sob: 
    const binaryType = form.binaryType.value;
    const channelName = form.channel.value.trim() || form.channel.placeholder;
    let versionHash;

    try {
        log(`[*] Resolving previous ${binaryType} build (channel: ${channelName})...`);
        versionHash = await fetchPreviousVersion(binaryType);

        let queryString = `?channel=${encodeURIComponent(channelName)}&binaryType=${encodeURIComponent(binaryType)}&version=${encodeURIComponent(versionHash)}`;

        const compressZip = form.compressZip.checked;
        const compressionLevel = form.compressionLevel.value;
        if (compressZip === true) {
            queryString += `&compressZip=true&compressionLevel=${compressionLevel}`;
        }

        queryString += `&parallelDownloads=${form.parallelDownloads.checked}`;
        queryString += mirrorSuffix();
        queryString += apiSuffix();

        window.open(basePath + queryString, "_blank");

    } catch (error) {
        log(`[!] Error fetching previous version: ${error.message}`);
        logWarpHint();
    }
}

function scrollEnd() {
    logBox.scrollTop = logBox.scrollHeight;
};

function escHtml(originalText) {
    return originalText
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;")
        .replace(/ /g, "&nbsp;")
        .replace(/\n/g, "<br>");
};

function log(msg = "", end = "\n", autoScroll = true) {
    const content = msg.trimEnd();
    if (!content) return;

    const entry = document.createElement("div");
    entry.className = "entry";

    let type = "l-def";
    let text = content;
    if (content.startsWith("[!]")) { type = "l-err";  text = content.slice(3).trim(); }
    else if (content.startsWith("[+]")) { type = "l-ok";   text = content.slice(3).trim(); }
    else if (content.startsWith("[*]")) { type = "l-info"; text = content.slice(3).trim(); }
    entry.classList.add(type);

    const now = new Date();
    const time = now.toLocaleTimeString("en-US", { hour12: false });

    const badge = document.createElement("span");
    badge.className = "badge";
    badge.textContent = time;

    const msgEl = document.createElement("span");
    msgEl.className = "msg";
    msgEl.textContent = text;

    entry.appendChild(badge);
    entry.appendChild(msgEl);
    logBox.appendChild(entry);
    logBox.style.display = 'flex';

    if (autoScroll) scrollEnd();
};

function logWarpHint() {
    const entry = document.createElement("div");
    entry.className = "entry l-err";

    const badge = document.createElement("span");
    badge.className = "badge";
    badge.textContent = new Date().toLocaleTimeString("en-US", { hour12: false });

    const msg = document.createElement("span");
    msg.className = "msg";
    msg.innerHTML = `Try using <a href="https://one.one.cloudflare.com/" target="_blank">Cloudflare WARP</a> to fix this. If it continues, <a href="https://discord.gg/sirhurt" target="_blank">contact us on Discord</a>.`;

    entry.appendChild(badge);
    entry.appendChild(msg);
    logBox.appendChild(entry);
    logBox.style.display = 'flex';
    scrollEnd();
}

function logLink(url, autoScroll = true) {
    const entry = document.createElement("div");
    entry.className = "entry l-link";

    const now = new Date();

    const badge = document.createElement("span");
    badge.className = "badge";
    badge.textContent = now.toLocaleTimeString("en-US", { hour12: false });

    const link = document.createElement("a");
    link.href = url;
    link.target = "_blank";
    link.className = "msg";
    link.textContent = url;

    entry.appendChild(badge);
    entry.appendChild(link);
    logBox.appendChild(entry);
    logBox.style.display = 'flex';

    if (autoScroll) scrollEnd();
};

const progPct = document.getElementById("progPct");
const progEta = document.getElementById("progEta");
let _progressStartTime = null;

// Function to update the progress bar
function setProgress(percentage, message) {
    if (!_progressStartTime) _progressStartTime = Date.now();

    progWrap.style.display = 'flex';
    progFill.style.width = percentage + '%';
    progPct.textContent = percentage + '%';
    progMsg.textContent = message;

    if (percentage > 0 && percentage < 100) {
        const elapsed = (Date.now() - _progressStartTime) / 1000;
        const rate = percentage / elapsed;
        const secsLeft = Math.round((100 - percentage) / rate);
        if (secsLeft > 0) {
            const m = Math.floor(secsLeft / 60);
            const s = secsLeft % 60;
            progEta.textContent = m > 0 ? `${m}m ${s}s left` : `${s}s left`;
        }
    } else if (percentage >= 100) {
        progEta.textContent = '';
        _progressStartTime = null;
    }

    scrollEnd();
}

// Function to hide the progress bar
function hideProgress() {
    progWrap.style.display = 'none';
    progFill.style.width = '0%';
    progPct.textContent = '0%';
    progEta.textContent = '';
    _progressStartTime = null;
    progMsg.innerText = '';
}

// Prompt download
function saveFile(fileName, data, mimeType = "application/zip") {
    const blob = new Blob([data], { type: mimeType });

    let link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = fileName;
    link.style.cssText = "display:none";

    let button = document.createElement("button");
    button.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> Redownload`;
    button.className = "redownload-btn";
    button.title = fileName;
    button.addEventListener("click", () => link.click());

    document.body.appendChild(link);
    document.getElementById("progWrap").insertAdjacentElement("afterend", button);
    scrollEnd();

    link.click();
};

// Soley for the manifest etc
function request(url, callback, errorOnNotOk = true) {
    const httpRequest = new XMLHttpRequest();
    httpRequest.open("GET", url, true);

    // When the request is done later..
    httpRequest.onload = function () {
        // Handle req issues, and don't call-back
        const statusCode = httpRequest.status
        if (errorOnNotOk && (statusCode < 200 || statusCode >= 400)) {
            log(`[!] Request error (${statusCode}) @ ${url} - ${httpRequest.responseText}`);
            return;
        }

        callback(httpRequest.responseText, statusCode);
    };

    httpRequest.onerror = function (e) {
        log(`[!] Request error @ ${url}`);
    };

    httpRequest.send();
};

function xhrBin(url, callback, progressCallback = null) {
    const httpRequest = new XMLHttpRequest();

    httpRequest.open("GET", url, true);
    httpRequest.responseType = "arraybuffer";

    if (progressCallback) {
        httpRequest.onprogress = function(event) {
            if (event.lengthComputable) {
                const percentage = Math.round((event.loaded / event.total) * 100);
                progressCallback(percentage, event.loaded, event.total);
            }
        };
    }

    // When the request is done later..
    httpRequest.onload = function () {
        // Handle req issues, and don't call-back
        const statusCode = httpRequest.status
        if (statusCode != 200) {
            log(`[!] Binary request error (${statusCode}) @ ${url}`);
            return;
        }

        const arrayBuffer = httpRequest.response;
        if (!arrayBuffer) {
            log(`[!] Binary request error (${statusCode}) @ ${url} - Failed to get binary ArrayBuffer from response`);
            return;
        }

        callback(arrayBuffer, statusCode);
    };

    httpRequest.onerror = function (e) {
        log(`[!] Binary request error @ ${url} - ${e}`);
    };

    httpRequest.send();
};

function fetchBin(url, progressCallback = null) {
    return new Promise((resolve, reject) => {
        const httpRequest = new XMLHttpRequest();
        httpRequest.open("GET", url, true);
        httpRequest.responseType = "arraybuffer";

        if (progressCallback) {
            httpRequest.onprogress = function(event) {
                if (event.lengthComputable) {
                    progressCallback(event.loaded, event.total);
                }
            };
        }

        httpRequest.onload = function() {
            if (httpRequest.status !== 200) {
                reject(new Error(`HTTP ${httpRequest.status}`));
                return;
            }
            if (!httpRequest.response) {
                reject(new Error("No ArrayBuffer in response"));
                return;
            }
            resolve(httpRequest.response);
        };

        httpRequest.onerror = function() {
            reject(new Error("Network error"));
        };

        httpRequest.send();
    });
};

function getQuery(queryString) {
    if (!urlParams.has(queryString)) {
        return null;
    }

    return urlParams.get(queryString) || null;
};

let channel = getQuery("channel");
let version = getQuery("version") || getQuery("guid");
let binaryType = getQuery("binaryType");
let blobDir = getQuery("blobDir");

let compressZip = getQuery("compressZip");
let compressionLevel = getQuery("compressionLevel");
let parallelDownloads = getQuery("parallelDownloads");
let exploit = getQuery("exploit");

let channelPath;
let versionPath;

let binExtractRoots;
let zip;

// Init
main();

async function main() {
    if (window.location.search == "") {
        // We won't log anything else; just exit
        formDiv.hidden = false;
        document.getElementById("usageDiv").hidden = false;
        return;
    }

    // Query params

    if (channel) {
        if (channel.toLowerCase() === "live" || channel.toLowerCase() === "production") {
            channel = "LIVE";
        } else {
            channel = channel.toLowerCase();
        }
    } else {
        channel = "LIVE";
    }

    if (channel === "LIVE") {
        channelPath = `${hostPath}`;
    } else {
        channelPath = `${hostPath}/channel/${channel}`;
    }

    if (version) {
        version = version.toLowerCase();
        if (!version.startsWith("version-")) { // Only the version GUID is actually necessary
            version = "version-" + version
        }
    }


    // We're also checking to make sure blobDir hasn't been included too for the compatibility warning later
    if (version && !binaryType) {
        log("[!] Error: If you provide a specific `version`, you need to set the `binaryType` aswell! See the usage doc below for examples of various `binaryType` inputs:", "\n\n");
        log(usageMsg, "\n", false);
        return;
    }

    if (blobDir) {
        if (blobDir.slice(0) !== "/") {
            blobDir = "/" + blobDir;
        }
        if (blobDir.slice(-1) !== "/") {
            blobDir += "/"
        }

        // We used to support usage of ONLY `blobDir` & `version` in the past, requiring us
        // to essentially "guess" the desired binaryType ourselves! (how fun, right!?)
        if (!binaryType) {
            log(`[!] Error: Using the \`blobDir\` query without defining \`binaryType\` has been
    deprecated, and can no longer be used in requests. If you were using \`blobDir\`
    explicitly for MacPlayer/MacStudio with "blobDir=mac" or "/mac", please replace
    blobDir with a \`binaryType\` of either MacPlayer or MacStudio respectively`, "\n\n");

            log(usageMsg, "\n", false);
            return;
        }
    }

    if (compressZip) {
        if (compressZip !== "true" && compressZip !== "false") {
            log(`[!] Error: The \`compressZip\` query must be a boolean ("true" or "false"), got "${compressZip}"`);
        }

        compressZip = (compressZip === "true");
    } else {
        compressZip = form.compressZip.checked;
    }

    if (compressionLevel !== "") {
        try {
            compressionLevel = parseInt(compressionLevel);
        } catch (err) {
            log(`[!] Error: Failed to parse \`compressionLevel\` query: ${error}`, "\n\n");
            log(usageMsg, "\n", false);
            return;
        }

        if (compressionLevel > 9 || compressionLevel < 1) {
            log(`[!] Error: The \`compressionLevel\` query must be a value between 1 and 9, got ${compressionLevel}`, "\n\n");
            log(usageMsg, "\n", false);
            return;
        }
    } else {
        compressionLevel = form.compressionLevel.value; // Only applies to when `compressZip` is true aswell
    }

    // At this point, we expect `binaryType` to be defined if all is well on input from the user..
    if (!binaryType) {
        if (exploit) {
            formDiv.hidden = false;
            return;
        }
        // Again, we used to support specific versions without denoting binaryType explicitly
        log("[!] Error: Missing required \`binaryType\` query, are you using an old perm link for a specific version?", "\n\n");
        log(usageMsg, "\n", false);
        return;
    }

    let versionFilePath; // Only used if `version` isn't already defined (later, see code below the if-else after this)
    if (binaryType in binaryTypes) {
        const binaryTypeObject = binaryTypes[binaryType];
        versionFilePath = channelPath + binaryTypeObject.versionFile;

        // If `blobDir` has already been defined by the user, we don't want to override it here..
        if (!blobDir) {
            blobDir = binaryTypeObject.blobDir;
        }
    } else {
        log(`[!] Error: \`binaryType\` given, "${binaryType}" not supported. See list below for supported \`binaryType\` inputs:`, "\n\n");
        log(usageMsg);
        return;
    }

    if (exploit && !version) {
        try {
            const list = await fetch(`${apiBase}/api/status/exploits`).then(r => r.json());
            const m = list.find(e => e.title.toLowerCase() === exploit.toLowerCase());
            if (m?.rbxversion) {
                version = m.rbxversion;
                log(`[*] Resolved exploit "${m.title}": ${version}`);
            } else {
                log(`[!] Could not find exploit "${exploit}" or it has no version.`);
                return;
            }
        } catch (err) {
            log(`[!] Failed to fetch exploit version for "${exploit}": ${err.message}`);
            logWarpHint();
            return;
        }
    }

    if (version) {
        fetchManifest();
    } else {
        try {
            version = await fetchLatestVersion(binaryType, channel);
            log(`[*] No version specified, resolved to latest published build: ${version}`);
            fetchManifest();
        } catch (error) {
            log(`[!] Failed to auto-fetch version: ${error.message}`);
            logWarpHint();
        }
    }
};

async function fetchManifest() {
    versionPath = `${channelPath}${blobDir}${version}-`; // aws s3 uses a - for the path :)

    if (binaryType === "MacPlayer" || binaryType === "MacStudio") {
        const zipFileName = (binaryType == "MacPlayer" && "RobloxPlayer.zip") || (binaryType == "MacStudio" && "RobloxStudioApp.zip")
        log(`[+] Fetching zip archive for BinaryType "${binaryType}" (${zipFileName})`);

        // Keep the archive named after the build hash only.
        const outputFileName = `${version}.zip`;

        setProgress(0, `Starting download for ${zipFileName}...`);
        const _startTime = Date.now();
        xhrBin(versionPath + zipFileName, function (zipData) {
            const elapsed = ((Date.now() - _startTime) / 1000).toFixed(1);
            log(`done! Completed in ${elapsed}s`);
            log("Thank you for using SirHurt RDD! If you have any issues, please report them at our discord server: https://discord.gg/sirhurt");
            hideProgress();
            saveFile(outputFileName, zipData);
        }, function(percentage, loaded, total) {
            setProgress(percentage, `Downloading ${zipFileName}: ${fmtBytes(loaded)} / ${fmtBytes(total)}`);
        });
    } else {
        log(`[+] Fetching rbxPkgManifest for ${version}@${channel}..`);

        // TODO: We dont support RDDs /common but should work fine since its our own R2 bucket lol?
        var manifestBody = "";
        try {
            const resp = await fetch(versionPath + "rbxPkgManifest.txt");            if (!resp.ok) {
                if (resp.status === 403) {
                    log("[!] Roblox blocked this request (403 Forbidden).");
                    log("    Roblox no longer serves rbxPkgManifest.txt or RobloxApp.zip to non-official clients,");
                    log("    so the downloader needs a mirror/backend that proxies them.");
                    log("    Set `window.RDD_MIRROR` (or add `?mirror=<url>`) to point RDD at your proxy.");
                } else if (resp.status === 404) {
                    log("[!] Oh no! It seems this version has vanished like a ghost... 👻");
                    log("    We haven't cached this version yet.");
                    log("    If the Roblox Update Tracker just detected a new version, it may take a few minutes to cache it.");
                    log("    Try again after 1-10 minutes!");
                } else {
                    log(`[!] Failed to fetch rbxPkgManifest: (status: ${resp.status}, err: ${(await resp.text()) || "<failed to get response from server>"})`);
                }
                return;
            }
            manifestBody = await resp.text();
        } catch (error) {
            log(`[!] An error occurred while fetching rbxPkgManifest: ${error.message}`);
            logWarpHint();
            return;
        }

        const useParallel = parallelDownloads !== "false";
        dlPackages(manifestBody, useParallel);
    }
};

async function dlPackages(manifestBody, useParallel = form.parallelDownloads.checked) {
    const _startTime = Date.now();
    const pkgManifestLines = manifestBody.split("\n").map(line => line.trim());

    if (pkgManifestLines[0] !== "v0") {
        log(`[!] Error: unknown rbxPkgManifest format version; expected "v0", got "${pkgManifestLines[0]}"`);
        return;
    }

    if (pkgManifestLines.includes("RobloxApp.zip")) {
        binExtractRoots = extractRoots.player;
        if (binaryType === "WindowsStudio64") {
            log(`[!] Error: BinaryType \`${binaryType}\` given, but "RobloxApp.zip" was found in the manifest!`);
            return;
        }
    } else if (pkgManifestLines.includes("RobloxStudio.zip")) {
        binExtractRoots = extractRoots.studio;
        if (binaryType === "WindowsPlayer") {
            log(`[!] Error: BinaryType \`${binaryType}\` given, but "RobloxStudio.zip" was found in the manifest!`);
            return;
        }
    } else {
        log("[!] Error: Bad/unrecognized rbxPkgManifest, aborting..");
        return;
    }

    log(`[+] Fetching blobs for BinaryType \`${binaryType}\`..`);

    zip = new JSZip();
    zip.file("AppSettings.xml", `<?xml version="1.0" encoding="UTF-8"?>
<Settings>
    <ContentFolder>content</ContentFolder>
    <BaseUrl>http://www.roblox.com</BaseUrl>
</Settings>
`);

    const filesToDownload = pkgManifestLines.filter(l => l.includes(".") && l.endsWith(".zip"));
    log(`[*] Download mode: ${useParallel ? "parallel" : "sequential"}`);

    async function procPkg(packageName, blobData) {
        log(`[+] Received "${packageName}"!`);
        if (!(packageName in binExtractRoots)) {
            log(`[*] Package "${packageName}" not in extraction roots, storing at root.`);
            zip.file(packageName, blobData);
        } else {
            log(`[+] Extracting "${packageName}"...`);
            const extractRootFolder = binExtractRoots[packageName];
            await JSZip.loadAsync(blobData).then(async (packageZip) => {
                blobData = null;
                const fileGetPromises = [];
                packageZip.forEach((path, object) => {
                    if (path.endsWith("\\")) return;
                    const fixedPath = path.replace(/\\/g, "/");
                    fileGetPromises.push(object.async("arraybuffer").then(data => {
                        zip.file(extractRootFolder + fixedPath, data);
                    }));
                });
                await Promise.all(fileGetPromises);
                packageZip = null;
            });
            log(`[+] Extracted "${packageName}"!`);
        }
    }

    if (useParallel) {
        const progressMap = {};
        function syncProgress() {
            let totalLoaded = 0, totalSize = 0;
            for (const key in progressMap) {
                totalLoaded += progressMap[key].loaded;
                totalSize  += progressMap[key].total;
            }
            if (totalSize > 0) {
                const pct = Math.round((totalLoaded / totalSize) * 100);
                setProgress(pct, `Downloading ${filesToDownload.length} packages -${fmtBytes(totalLoaded)} / ${fmtBytes(totalSize)}`);
            }
        }

        const downloadPromises = filesToDownload.map(packageName => {
            const blobUrl = versionPath + packageName;
            progressMap[blobUrl] = { loaded: 0, total: 0 };
            log(`[+] Fetching "${packageName}"...`);
            return fetchBin(blobUrl, (loaded, total) => {
                progressMap[blobUrl] = { loaded, total };
                syncProgress();
            }).then(blobData => procPkg(packageName, blobData))
              .catch(err => { log(`[!] Error downloading "${packageName}": ${err.message}`); logWarpHint(); throw err; });
        });

        try {
            await Promise.all(downloadPromises);
        } catch {
            log(`[!] One or more packages failed to download, aborting.`);
            return;
        }
    } else {
        let idx = 0;
        for (const packageName of filesToDownload) {
            idx++;
            log(`[+] Fetching "${packageName}" (${idx}/${filesToDownload.length})...`);
            try {
                const blobData = await fetchBin(versionPath + packageName, (loaded, total) => {
                    if (total > 0) setProgress(
                        Math.round((loaded / total) * 100),
                        `Downloading "${packageName}": ${fmtBytes(loaded)} / ${fmtBytes(total)}`
                    );
                });
                await procPkg(packageName, blobData);
            } catch (err) {
                log(`[!] Error downloading "${packageName}": ${err.message}`);
                logWarpHint();
                return;
            }
        }
    }

    buildZip();

    function buildZip() {
        // Keep the archive named after the build hash only.
        const outputFileName = `${version}.zip`;
        log();
        if (compressZip) {
            log(`[!] NOTE: Compressing final zip (level ${compressionLevel}/9) -this runs on the main thread and may freeze the page for a while. Most of the content is already zipped so gains are minimal.`);
        }
        log("Thank you for using SirHurt RDD! If you have any issues, please report them at our discord server: https://discord.gg/sirhurt");
        log(`[+] Exporting assembled zip file "${outputFileName}"..`);
        hideProgress();

        zip.generateAsync({
            type: "arraybuffer",
            compression: compressZip ? "DEFLATE" : "STORE",
            compressionOptions: { level: compressionLevel }
        }, function update(metadata) {
            const percentage = metadata.percent.toFixed(2);
            setProgress(percentage, `Compressing: ${percentage}%`);
        }).then(function(outputZipData) {
            zip = null;
            const elapsed = ((Date.now() - _startTime) / 1000).toFixed(1);
            log(`[+] Done! Completed in ${elapsed}s`);
            hideProgress();
            saveFile(outputFileName, outputZipData);
        });
    }
};


function fmtBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}