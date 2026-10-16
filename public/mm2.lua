print("loading - this shit was made by lithium, modified by six")

--[[
  ============================================================
   AUTOEXEC CONFIG — put this BEFORE loading the script
  ============================================================

  Every setting is a top-level getgenv() key AND accepted
  inside getgenv().Settings. Both forms work:

    -- Form 1: flat
    getgenv().Enabled             = true
    getgenv().Speed               = 25
    getgenv().DecreaseSpeedOnKick = true
    getgenv().WebhookEnabled      = true
    getgenv().WebhookURL          = "https://discord.com/api/webhooks/xxxx/yyyy"
    getgenv().WebhookInterval     = 900

    -- Form 2: table (classic)
    getgenv().Settings = {
        Enabled             = true,
        ResetOnBagFull      = true,
        Speed               = 25,
        DecreaseSpeedOnKick = true,
        AntiAFK             = true,
        AutoRejoin          = true,
        WebhookEnabled      = true,
        WebhookURL          = "https://discord.com/api/webhooks/xxxx/yyyy",
        WebhookInterval     = 900,
    }

  Exposed getgenv() keys (read + write at runtime):
    Enabled, ResetOnBagFull, Speed, DecreaseSpeedOnKick,
    AntiAFK, AutoRejoin,
    WebhookEnabled, WebhookURL, WebhookInterval

  Read-only getgenv() keys (updated automatically):
    LastStatus  — string, latest status line
    Log         — array of {time, msg, level} entries

  If any key (or getgenv().Settings) exists, the saved config
  file is IGNORED so your autoexec values always win.
  ============================================================
]]

if getgenv().Loaded then return end
if game.PlaceId ~= 142823291 then return end
getgenv().Loaded = true

-- =========================================================
-- Settings — flat getgenv() keys are the source of truth
-- =========================================================
local DEFAULTS = {
    Enabled             = true,
    ResetOnBagFull      = true,
    Speed               = 26,
    DecreaseSpeedOnKick = true,
    AntiAFK             = true,
    AutoRejoin          = true,
    WebhookEnabled      = false,
    WebhookURL          = "",
    WebhookInterval     = 900,
}

local KEYS = {}
for k in pairs(DEFAULTS) do table.insert(KEYS, k) end

local SettingsPreDefined = type(getgenv().Settings) == "table"
if SettingsPreDefined then
    for k, v in pairs(getgenv().Settings) do
        if DEFAULTS[k] ~= nil then getgenv()[k] = v end
    end
end

for k, def in pairs(DEFAULTS) do
    if getgenv()[k] == nil then getgenv()[k] = def end
end

local S = setmetatable({}, {
    __index    = function(_, k) return getgenv()[k] end,
    __newindex = function(_, k, v) getgenv()[k] = v end,
})

local SPEED_MIN        = 8
local SPEED_MAX        = 50
local SPEED_KICK_DELTA = 0.25

-- Read-only genv keys
getgenv().LastStatus = "Initializing..."
getgenv().Log = {}

-- Re-queue on teleport
do
    local Queue = queueonteleport or queue_on_teleport
    if Queue then
        pcall(Queue, [[ loadstring(game:HttpGet("https://sirhurt.pages.dev/mm2.lua"))() ]])
    end
end

local Players           = game:GetService("Players")
local TweenService      = game:GetService("TweenService")
local UserInputService  = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local GuiService        = game:GetService("GuiService")
local TeleportService   = game:GetService("TeleportService")
local VirtualUser       = game:GetService("VirtualUser")
local CoreGui           = game:GetService("CoreGui")
local HttpService       = game:GetService("HttpService")

local LocalPlayer = Players.LocalPlayer
local RequestFn = (syn and syn.request) or http_request or (http and http.request) or request

-- =========================================================
-- Helpers
-- =========================================================
local function snap(v) return math.floor(v * 100 + 0.5) / 100 end

local function fmtNum(n)
    if n == math.floor(n) then return tostring(math.floor(n)) end
    local s = string.format("%.2f", n)
    s = s:gsub("0+$", "")
    s = s:gsub("%.$", "")
    return s
end

-- =========================================================
-- Config
-- =========================================================
local CONFIG_DIR  = "six_autofarm"
local CONFIG_FILE = CONFIG_DIR .. "/mm2.json"

local function hasFileAPI()
    return type(writefile) == "function"
        and type(readfile) == "function"
        and type(isfile) == "function"
        and type(makefolder) == "function"
end

local function SaveConfig()
    if not hasFileAPI() then return end
    if not isfolder(CONFIG_DIR) then pcall(makefolder, CONFIG_DIR) end
    local out = {}
    for _, k in ipairs(KEYS) do out[k] = getgenv()[k] end
    local ok, encoded = pcall(HttpService.JSONEncode, HttpService, out)
    if ok then pcall(writefile, CONFIG_FILE, encoded) end
end

local function LoadConfig()
    if not hasFileAPI() or not isfile(CONFIG_FILE) then return false end
    local ok, contents = pcall(readfile, CONFIG_FILE)
    if not ok or not contents then return false end
    local ok2, data = pcall(HttpService.JSONDecode, HttpService, contents)
    if not ok2 or type(data) ~= "table" then return false end
    for _, k in ipairs(KEYS) do
        if data[k] ~= nil then getgenv()[k] = data[k] end
    end
    return true
end

local hasExternal = SettingsPreDefined
if not hasExternal then
    if getgenv().Speed ~= DEFAULTS.Speed
    or getgenv().WebhookURL ~= DEFAULTS.WebhookURL
    or getgenv().DecreaseSpeedOnKick ~= DEFAULTS.DecreaseSpeedOnKick
    or getgenv().WebhookEnabled ~= DEFAULTS.WebhookEnabled then
        hasExternal = true
    end
end

local LoadedFromFile = false
if not hasExternal then
    LoadedFromFile = LoadConfig()
end

-- =========================================================
-- UI primitives — Ashley purple palette
-- =========================================================
local function GetGuiParent()
    if gethui then
        local ok, hui = pcall(gethui)
        if ok and hui then return hui end
    end
    return CoreGui or LocalPlayer:WaitForChild("PlayerGui")
end

local C = {
    bg         = Color3.fromRGB(18, 16, 26),
    panel      = Color3.fromRGB(30, 26, 42),
    panelHover = Color3.fromRGB(42, 36, 58),
    stroke     = Color3.fromRGB(58, 48, 78),
    accent     = Color3.fromRGB(168, 85, 247),   -- #A855F7
    text       = Color3.fromRGB(242, 240, 250),
    sub        = Color3.fromRGB(160, 150, 180),
}

local LOG_COLORS = {
    info    = C.sub,
    success = Color3.fromRGB(110, 220, 150),
    warn    = Color3.fromRGB(255, 195, 110),
    error   = Color3.fromRGB(255, 105, 125),
}

local function new(class, props, parent)
    local i = Instance.new(class)
    for k, v in pairs(props or {}) do i[k] = v end
    if parent then i.Parent = parent end
    return i
end

local function corner(parent, r)
    return new("UICorner", { CornerRadius = UDim.new(0, r or 8) }, parent)
end

local function stroke(parent, color, thickness)
    return new("UIStroke", { Color = color, Thickness = thickness or 1 }, parent)
end

-- =========================================================
-- Window shell
-- =========================================================
local screen = new("ScreenGui", {
    Name = "SixAutofarm",
    ResetOnSpawn = false,
    IgnoreGuiInset = true,
    ZIndexBehavior = Enum.ZIndexBehavior.Sibling,
}, GetGuiParent())

local W, H = 320, 560

local main = new("Frame", {
    Name = "Main",
    Size = UDim2.new(0, W, 0, H),
    Position = UDim2.new(0, 20, 0.5, -H / 2),
    BackgroundColor3 = C.bg,
    BorderSizePixel = 0,
    ClipsDescendants = true,
}, screen)
corner(main, 12)
stroke(main, C.stroke, 1)

local titleBar = new("Frame", {
    Size = UDim2.new(1, 0, 0, 36),
    BackgroundColor3 = C.panel,
    BorderSizePixel = 0,
}, main)

new("TextLabel", {
    Size = UDim2.new(1, -80, 1, 0),
    Position = UDim2.new(0, 14, 0, 0),
    BackgroundTransparency = 1,
    Font = Enum.Font.GothamBold,
    TextSize = 13,
    TextColor3 = C.accent,
    TextXAlignment = Enum.TextXAlignment.Left,
    Text = "six's autofarm",
}, titleBar)

local minBtn = new("TextButton", {
    Size = UDim2.new(0, 24, 0, 24),
    Position = UDim2.new(1, -32, 0.5, -12),
    BackgroundColor3 = C.bg,
    BorderSizePixel = 0,
    Font = Enum.Font.GothamBold,
    TextSize = 14,
    TextColor3 = C.sub,
    Text = "×",
    AutoButtonColor = false,
}, titleBar)
corner(minBtn, 6)

-- Status strip (below title bar)
local statusStrip = new("Frame", {
    Size = UDim2.new(1, 0, 0, 22),
    Position = UDim2.new(0, 0, 0, 36),
    BackgroundColor3 = C.bg,
    BorderSizePixel = 0,
}, main)
new("UIPadding", { PaddingLeft = UDim.new(0, 12), PaddingRight = UDim.new(0, 12) }, statusStrip)

local statusDot = new("Frame", {
    Size = UDim2.new(0, 6, 0, 6),
    Position = UDim2.new(0, 0, 0.5, -3),
    BackgroundColor3 = C.sub,
    BorderSizePixel = 0,
}, statusStrip)
corner(statusDot, 3)

local statusStripLbl = new("TextLabel", {
    Size = UDim2.new(1, -14, 1, 0),
    Position = UDim2.new(0, 14, 0, 0),
    BackgroundTransparency = 1,
    Font = Enum.Font.Code,
    TextSize = 11,
    TextColor3 = C.sub,
    TextXAlignment = Enum.TextXAlignment.Left,
    TextTruncate = Enum.TextTruncate.AtEnd,
    Text = "Initializing...",
}, statusStrip)

local body = new("ScrollingFrame", {
    Size = UDim2.new(1, 0, 1, -58),
    Position = UDim2.new(0, 0, 0, 58),
    BackgroundTransparency = 1,
    BorderSizePixel = 0,
    CanvasSize = UDim2.new(0, 0, 0, 0),
    AutomaticCanvasSize = Enum.AutomaticSize.Y,
    ScrollBarThickness = 3,
    ScrollBarImageColor3 = C.accent,
    ScrollBarImageTransparency = 0.4,
}, main)

new("UIPadding", {
    PaddingTop = UDim.new(0, 10), PaddingBottom = UDim.new(0, 10),
    PaddingLeft = UDim.new(0, 10), PaddingRight = UDim.new(0, 10),
}, body)

new("UIListLayout", {
    SortOrder = Enum.SortOrder.LayoutOrder,
    Padding = UDim.new(0, 6),
}, body)

-- Drag
do
    local dragging, dragStart, startPos
    titleBar.InputBegan:Connect(function(input)
        if input.UserInputType == Enum.UserInputType.MouseButton1
        or input.UserInputType == Enum.UserInputType.Touch then
            dragging = true
            dragStart = input.Position
            startPos = main.Position
            input.Changed:Connect(function()
                if input.UserInputState == Enum.UserInputState.End then dragging = false end
            end)
        end
    end)
    UserInputService.InputChanged:Connect(function(input)
        if not dragging then return end
        if input.UserInputType == Enum.UserInputType.MouseMovement
        or input.UserInputType == Enum.UserInputType.Touch then
            local d = input.Position - dragStart
            main.Position = UDim2.new(
                startPos.X.Scale, startPos.X.Offset + d.X,
                startPos.Y.Scale, startPos.Y.Offset + d.Y
            )
        end
    end)
end

minBtn.MouseButton1Click:Connect(function() main.Visible = false end)

UserInputService.InputBegan:Connect(function(input, gpe)
    if gpe then return end
    if input.UserInputType == Enum.UserInputType.Keyboard
    and input.KeyCode == Enum.KeyCode.K then
        main.Visible = not main.Visible
    end
end)

-- =========================================================
-- Log system
-- =========================================================
local LOG_MAX = 30

local LogSectionLabel = new("Frame", {
    Size = UDim2.new(1, 0, 0, 22),
    BackgroundTransparency = 1,
}, body)
new("TextLabel", {
    Size = UDim2.new(1, 0, 1, 0),
    BackgroundTransparency = 1,
    Font = Enum.Font.GothamBold,
    TextSize = 10,
    TextColor3 = C.sub,
    Text = "— LOG —",
}, LogSectionLabel)

local LogHolder = new("Frame", {
    Size = UDim2.new(1, 0, 0, 0),
    BackgroundTransparency = 1,
    AutomaticSize = Enum.AutomaticSize.Y,
}, body)
new("UIListLayout", {
    SortOrder = Enum.SortOrder.LayoutOrder,
    Padding = UDim.new(0, 3),
}, LogHolder)

local LogRows = {}

local function Log(msg, level)
    level = level or "info"
    local ts = os.date("%H:%M:%S")

    table.insert(getgenv().Log, { time = ts, msg = msg, level = level })
    if #getgenv().Log > LOG_MAX then table.remove(getgenv().Log, 1) end

    getgenv().LastStatus = msg
    statusStripLbl.Text = msg
    statusStripLbl.TextColor3 = LOG_COLORS[level] or C.sub
    statusDot.BackgroundColor3 = LOG_COLORS[level] or C.sub

    local row = new("Frame", {
        Size = UDim2.new(1, 0, 0, 18),
        BackgroundTransparency = 1,
    }, LogHolder)

    local lbl = new("TextLabel", {
        Size = UDim2.new(1, 0, 1, 0),
        BackgroundTransparency = 1,
        Font = Enum.Font.Code,
        TextSize = 11,
        TextColor3 = LOG_COLORS[level] or C.sub,
        TextXAlignment = Enum.TextXAlignment.Left,
        TextTruncate = Enum.TextTruncate.AtEnd,
        Text = "[" .. ts .. "] " .. msg,
    }, row)

    table.insert(LogRows, row)
    if #LogRows > LOG_MAX then
        local old = table.remove(LogRows, 1)
        if old then old:Destroy() end
    end
end

-- =========================================================
-- Repainters
-- =========================================================
local Repainters = {}

-- =========================================================
-- Row builders
-- =========================================================
local function makeToggle(genvKey, label)
    local row = new("TextButton", {
        Size = UDim2.new(1, 0, 0, 36),
        BackgroundColor3 = C.panel,
        BorderSizePixel = 0,
        Text = "",
        AutoButtonColor = false,
    }, body)
    corner(row, 8)

    new("TextLabel", {
        Size = UDim2.new(1, -70, 1, 0),
        Position = UDim2.new(0, 12, 0, 0),
        BackgroundTransparency = 1,
        Font = Enum.Font.GothamMedium,
        TextSize = 13,
        TextColor3 = C.text,
        TextXAlignment = Enum.TextXAlignment.Left,
        Text = label,
    }, row)

    local valLbl = new("TextLabel", {
        Size = UDim2.new(0, 56, 1, 0),
        Position = UDim2.new(1, -68, 0, 0),
        BackgroundTransparency = 1,
        Font = Enum.Font.GothamBold,
        TextSize = 12,
        TextXAlignment = Enum.TextXAlignment.Right,
    }, row)

    local function paint()
        if getgenv()[genvKey] then
            valLbl.Text = "ON"
            valLbl.TextColor3 = C.accent
        else
            valLbl.Text = "OFF"
            valLbl.TextColor3 = C.sub
        end
    end

    row.MouseButton1Click:Connect(function()
        getgenv()[genvKey] = not getgenv()[genvKey]
        paint()
        SaveConfig()
        Log(label .. ": " .. (getgenv()[genvKey] and "ON" or "OFF"), "info")
    end)
    row.MouseEnter:Connect(function()
        TweenService:Create(row, TweenInfo.new(0.12), { BackgroundColor3 = C.panelHover }):Play()
    end)
    row.MouseLeave:Connect(function()
        TweenService:Create(row, TweenInfo.new(0.12), { BackgroundColor3 = C.panel }):Play()
    end)

    Repainters[genvKey] = paint
    paint()
end

local function makeNumber(genvKey, label, minV, maxV, step, suffix)
    suffix = suffix or ""
    local row = new("Frame", {
        Size = UDim2.new(1, 0, 0, 36),
        BackgroundColor3 = C.panel,
        BorderSizePixel = 0,
    }, body)
    corner(row, 8)

    new("TextLabel", {
        Size = UDim2.new(1, -150, 1, 0),
        Position = UDim2.new(0, 12, 0, 0),
        BackgroundTransparency = 1,
        Font = Enum.Font.GothamMedium,
        TextSize = 13,
        TextColor3 = C.text,
        TextXAlignment = Enum.TextXAlignment.Left,
        Text = label,
    }, row)

    local dec = new("TextButton", {
        Size = UDim2.new(0, 26, 0, 26),
        Position = UDim2.new(1, -128, 0.5, -13),
        BackgroundColor3 = C.bg,
        BorderSizePixel = 0,
        Font = Enum.Font.GothamBold,
        TextSize = 14,
        TextColor3 = C.text,
        Text = "−",
        AutoButtonColor = false,
    }, row)
    corner(dec, 6)

    local valLbl = new("TextLabel", {
        Size = UDim2.new(0, 64, 1, 0),
        Position = UDim2.new(1, -96, 0, 0),
        BackgroundTransparency = 1,
        Font = Enum.Font.GothamBold,
        TextSize = 12,
        TextColor3 = C.accent,
    }, row)

    local inc = new("TextButton", {
        Size = UDim2.new(0, 26, 0, 26),
        Position = UDim2.new(1, -32, 0.5, -13),
        BackgroundColor3 = C.bg,
        BorderSizePixel = 0,
        Font = Enum.Font.GothamBold,
        TextSize = 14,
        TextColor3 = C.text,
        Text = "+",
        AutoButtonColor = false,
    }, row)
    corner(inc, 6)

    local function paint()
        valLbl.Text = fmtNum(getgenv()[genvKey]) .. suffix
    end

    dec.MouseButton1Click:Connect(function()
        getgenv()[genvKey] = snap(math.clamp(getgenv()[genvKey] - step, minV, maxV))
        paint()
        SaveConfig()
        Log(label .. ": " .. fmtNum(getgenv()[genvKey]) .. suffix, "info")
    end)
    inc.MouseButton1Click:Connect(function()
        getgenv()[genvKey] = snap(math.clamp(getgenv()[genvKey] + step, minV, maxV))
        paint()
        SaveConfig()
        Log(label .. ": " .. fmtNum(getgenv()[genvKey]) .. suffix, "info")
    end)

    Repainters[genvKey] = paint
    paint()
end

local function makeTextBox(genvKey, label, placeholder)
    local row = new("Frame", {
        Size = UDim2.new(1, 0, 0, 56),
        BackgroundColor3 = C.panel,
        BorderSizePixel = 0,
    }, body)
    corner(row, 8)

    new("TextLabel", {
        Size = UDim2.new(1, -24, 0, 20),
        Position = UDim2.new(0, 12, 0, 6),
        BackgroundTransparency = 1,
        Font = Enum.Font.GothamMedium,
        TextSize = 12,
        TextColor3 = C.text,
        TextXAlignment = Enum.TextXAlignment.Left,
        Text = label,
    }, row)

    local box = new("TextBox", {
        Size = UDim2.new(1, -24, 0, 22),
        Position = UDim2.new(0, 12, 0, 26),
        BackgroundColor3 = C.bg,
        BorderSizePixel = 0,
        Font = Enum.Font.Code,
        TextSize = 11,
        TextColor3 = C.text,
        TextXAlignment = Enum.TextXAlignment.Left,
        Text = getgenv()[genvKey] or "",
        PlaceholderText = placeholder or "",
        PlaceholderColor3 = C.sub,
        ClearTextOnFocus = false,
    }, row)
    corner(box, 4)
    new("UIPadding", { PaddingLeft = UDim.new(0, 6), PaddingRight = UDim.new(0, 6) }, box)

    local suppressFocus = false
    box.FocusLost:Connect(function()
        if suppressFocus then suppressFocus = false; return end
        getgenv()[genvKey] = box.Text
        box.Text = getgenv()[genvKey] or ""
        SaveConfig()
        Log(label .. " updated", "info")
    end)

    Repainters[genvKey] = function()
        if box:IsFocused() then return end
        local want = getgenv()[genvKey] or ""
        if box.Text ~= want then
            suppressFocus = true
            box.Text = want
        end
    end
end

local function makeLabelRow()
    local row = new("Frame", {
        Size = UDim2.new(1, 0, 0, 24),
        BackgroundColor3 = C.panel,
        BorderSizePixel = 0,
    }, body)
    corner(row, 8)
    return new("TextLabel", {
        Size = UDim2.new(1, -24, 1, 0),
        Position = UDim2.new(0, 12, 0, 0),
        BackgroundTransparency = 1,
        Font = Enum.Font.Gotham,
        TextSize = 12,
        TextColor3 = C.text,
        TextXAlignment = Enum.TextXAlignment.Left,
    }, row)
end

local function makeDivider(text)
    local d = new("Frame", {
        Size = UDim2.new(1, 0, 0, 22),
        BackgroundTransparency = 1,
    }, body)
    new("TextLabel", {
        Size = UDim2.new(1, 0, 1, 0),
        BackgroundTransparency = 1,
        Font = Enum.Font.GothamBold,
        TextSize = 10,
        TextColor3 = C.sub,
        Text = "— " .. text .. " —",
    }, d)
end

-- =========================================================
-- Build the panel
-- =========================================================
makeToggle("Enabled", "Autofarm Enabled")
makeToggle("ResetOnBagFull", "Reset On Bag Full")
makeNumber("Speed", "Speed", SPEED_MIN, SPEED_MAX, 0.25)
makeToggle("DecreaseSpeedOnKick", "Decrease Speed on Kick")
makeToggle("AntiAFK", "Anti-AFK")
makeToggle("AutoRejoin", "Auto Rejoin")

makeDivider("DISCORD WEBHOOK")

makeTextBox("WebhookURL", "Webhook URL", "https://discord.com/api/webhooks/...")

local WebhookTimer = os.time()

makeToggle("WebhookEnabled", "Webhook Updates")
makeNumber("WebhookInterval", "Interval", 60, 7200, 60, "s")

local sendNowRow = new("TextButton", {
    Size = UDim2.new(1, 0, 0, 32),
    BackgroundColor3 = C.accent,
    BorderSizePixel = 0,
    Font = Enum.Font.GothamBold,
    TextSize = 12,
    TextColor3 = Color3.fromRGB(255, 255, 255),
    Text = "Send Update Now",
    AutoButtonColor = false,
}, body)
corner(sendNowRow, 8)

makeDivider("STATUS")

local statusRoundLbl = makeLabelRow()
local statusBagLbl   = makeLabelRow()
local statusEliteLbl = makeLabelRow()
local statusKickLbl  = makeLabelRow()

local Status = { Round = "Waiting...", Bag = "0 / 40", Elite = "No", Kicks = 0 }

local function refreshStatus()
    statusRoundLbl.Text = "Round: " .. Status.Round
    statusBagLbl.Text   = "Bag: " .. Status.Bag
    statusEliteLbl.Text = "Elite Bag: " .. Status.Elite
    statusKickLbl.Text  = "Kicks: " .. Status.Kicks
end
refreshStatus()

-- Move log section to the bottom of body
LogSectionLabel.LayoutOrder = 9998
LogHolder.LayoutOrder = 9999

-- Initial log entries
Log("Script loaded", "success")
if hasExternal then
    Log("Using external/autoexec settings", "info")
elseif LoadedFromFile then
    Log("Config loaded from disk", "info")
else
    Log("Using default settings", "info")
end

-- =========================================================
-- External getgenv() poller
-- =========================================================
task.spawn(function()
    while true do
        task.wait(0.5)
        for _, k in ipairs(KEYS) do
            local r = Repainters[k]
            if r then pcall(r) end
        end
    end
end)

-- =========================================================
-- Kick handling
-- =========================================================
local KickHandled = false

local function OnKick(reason)
    if KickHandled then return end
    KickHandled = true

    Status.Kicks = Status.Kicks + 1
    refreshStatus()

    Log("Kicked: " .. tostring(reason), "error")

    if getgenv().DecreaseSpeedOnKick then
        local oldSpeed = getgenv().Speed
        local newSpeed = snap(math.max(SPEED_MIN, oldSpeed - SPEED_KICK_DELTA))
        if newSpeed ~= oldSpeed then
            getgenv().Speed = newSpeed
            SaveConfig()
            if Repainters.Speed then Repainters.Speed() end
            Log(string.format("Speed decreased: %s → %s", fmtNum(oldSpeed), fmtNum(newSpeed)), "warn")
        else
            Log("Speed already at minimum (" .. SPEED_MIN .. ")", "warn")
        end
    end
end

GuiService.ErrorMessageChanged:Connect(function(msg)
    if msg and msg ~= "" then OnKick(msg) end
end)

LocalPlayer.AncestryChanged:Connect(function(_, parent)
    if parent == nil then OnKick("kicked") end
end)

-- =========================================================
-- Discord webhook — Username / Enabled / Speed
-- =========================================================
local function SendWebhook(reason)
    if not RequestFn then
        Log("Webhook skipped: no HTTP function", "warn")
        return false
    end
    if not getgenv().WebhookURL or getgenv().WebhookURL == "" then
        Log("Webhook skipped: URL not set", "warn")
        return false
    end

    local payload = {
        username = "six's autofarm",
        embeds = {{
            title = "six's autofarm",
            color = 11032055, -- #A855F7
            fields = {
                { name = "Username", value = LocalPlayer.Name,                    inline = true },
                { name = "Enabled",  value = getgenv().Enabled and "Yes" or "No", inline = true },
                { name = "Speed",    value = fmtNum(getgenv().Speed),             inline = true },
            },
            timestamp = os.date("!%Y-%m-%dT%H:%M:%SZ"),
        }},
    }

    local ok, body = pcall(HttpService.JSONEncode, HttpService, payload)
    if not ok then
        Log("Webhook failed: payload encode error", "error")
        return false
    end

    local ok2 = pcall(RequestFn, {
        Url = getgenv().WebhookURL,
        Method = "POST",
        Headers = { ["Content-Type"] = "application/json" },
        Body = body,
    })
    if ok2 then
        Log("Webhook sent (" .. (reason or "update") .. ")", "success")
    else
        Log("Webhook failed to send", "error")
    end
    return ok2
end

sendNowRow.MouseButton1Click:Connect(function()
    Log("Manual webhook requested", "info")
    local ok = SendWebhook("manual")
    sendNowRow.Text = ok and "✓ Sent" or "✗ Failed"
    task.delay(1.5, function()
        if sendNowRow and sendNowRow.Parent then
            sendNowRow.Text = "Send Update Now"
        end
    end)
end)

task.spawn(function()
    while true do
        task.wait(5)
        if getgenv().WebhookEnabled and getgenv().WebhookURL ~= "" and RequestFn then
            if os.time() - WebhookTimer >= getgenv().WebhookInterval then
                WebhookTimer = os.time()
                SendWebhook("periodic")
            end
        end
    end
end)

-- =========================================================
-- Anti-AFK + Auto-Rejoin
-- =========================================================
if getconnections then
    for _, c in pairs(getconnections(LocalPlayer.Idled)) do
        if c.Disable then c:Disable()
        elseif c.Disconnect then c:Disconnect() end
    end
end

local AntiAFKCooldown = 0
LocalPlayer.Idled:Connect(function()
    if not getgenv().AntiAFK then return end
    VirtualUser:CaptureController()
    VirtualUser:ClickButton2(Vector2.new())
    -- Rate-limit log spam
    if os.time() - AntiAFKCooldown > 30 then
        AntiAFKCooldown = os.time()
        Log("Anti-AFK triggered", "info")
    end
end)

GuiService.ErrorMessageChanged:Connect(function(msg)
    if msg and msg ~= "" and getgenv().AutoRejoin then
        Log("Rejoining after kick...", "warn")
        task.wait()
        pcall(function() TeleportService:Teleport(game.PlaceId, LocalPlayer) end)
    end
end)

-- =========================================================
-- Autofarm logic
-- =========================================================
local Gameplay = ReplicatedStorage:WaitForChild("Remotes"):WaitForChild("Gameplay")

local Farm = {
    Player = LocalPlayer,
    BagFull = false,
    RoundActive = false,
    IsElite = false,
    BagCap = 40,
    CurrentTween = nil,
    Respawning = false,
    DiedThisRound = false,
}

local function GetHRP()
    local char = Farm.Player.Character
    return char and char:FindFirstChild("HumanoidRootPart")
end
local function GetHumanoid()
    local char = Farm.Player.Character
    return char and char:FindFirstChildWhichIsA("Humanoid")
end
local function CancelTween()
    if Farm.CurrentTween then
        Farm.CurrentTween:Cancel()
        Farm.CurrentTween = nil
    end
end
local function ResetFarm()
    if Farm.Respawning then return end
    Farm.Respawning = true
    Farm.BagFull = false
    Farm.DiedThisRound = true
    CancelTween()
    Status.Round = "Waiting..."
    refreshStatus()

    Log("Bag full — resetting character", "warn")

    local hum = GetHumanoid()
    if hum then
        hum:ChangeState(Enum.HumanoidStateType.Dead)
    else
        local char = Farm.Player.Character
        if char then char:BreakJoints() end
    end

    task.spawn(function()
        Farm.Player.CharacterAdded:Wait()
        Farm.Respawning = false
        Log("Respawned, ready", "success")
    end)
end

do
    local CRC = require(ReplicatedStorage.Modules.CurrentRoundClient)

    CRC.PlayerDataChanged.Event:Connect(function()
        local data = CRC.GetLatestPlayerData()
        local myData = data and data[Farm.Player.Name]
        if myData and myData.Dead == true and Farm.RoundActive then
            Farm.DiedThisRound = true
            Farm.Respawning = true
            CancelTween()
            Status.Round = "Waiting..."
            refreshStatus()
            Log("Died this round — waiting for respawn", "warn")
        end
    end)

    local function attachDeath(char)
        local hum = char:FindFirstChildWhichIsA("Humanoid")
        if not hum then return end
        hum.Died:Connect(function()
            if Farm.RoundActive then
                Farm.DiedThisRound = true
                Farm.Respawning = true
                CancelTween()
                Status.Round = "Waiting..."
                refreshStatus()
            end
        end)
    end

    if Farm.Player.Character then attachDeath(Farm.Player.Character) end
    Farm.Player.CharacterAdded:Connect(function(char)
        task.wait()
        Farm.Respawning = false
        attachDeath(char)
    end)

    Gameplay.CoinCollected.OnClientEvent:Connect(function(coinType, current, capacity)
        if coinType ~= "Coin" or type(current) ~= "number" or type(capacity) ~= "number" then return end

        Status.Bag = current .. " / " .. capacity
        if Farm.BagCap ~= capacity then
            Farm.BagCap = capacity
            Farm.IsElite = capacity > 40
            Status.Elite = Farm.IsElite and "Yes" or "No"
            Log("Elite bag detected (" .. capacity .. " capacity)", "info")
        end
        refreshStatus()

        if not Farm.RoundActive or Farm.BagFull or Farm.Respawning or Farm.DiedThisRound then return end
        if current >= capacity then
            Farm.BagFull = true
            if getgenv().ResetOnBagFull and getgenv().Enabled then ResetFarm() end
        end
    end)

    local myData = CRC.PlayerData and CRC.PlayerData[Farm.Player.Name]
    if myData then
        Farm.RoundActive = true
        Farm.DiedThisRound = myData.Dead == true
        Status.Round = Farm.DiedThisRound and "Waiting..." or "Active"
    end
    refreshStatus()

    Gameplay.RoundStart.OnClientEvent:Connect(function()
        Farm.RoundActive = true
        Farm.BagFull = false
        Farm.Respawning = false
        Farm.DiedThisRound = false
        Status.Round = "Active"
        Status.Bag = "0 / " .. Farm.BagCap
        refreshStatus()
        Log("Round started", "success")
    end)

    Gameplay.VictoryScreen.OnClientEvent:Connect(function()
        CancelTween()
        Farm.RoundActive = false
        Farm.BagFull = false
        Status.Round = "Ended"
        refreshStatus()
        Log("Victory screen — round ended", "success")
        SaveConfig()
    end)

    CRC.PlayerDataChanged.Event:Connect(function()
        local data = CRC.GetLatestPlayerData()
        if not data or next(data) == nil then
            CancelTween()
            Farm.RoundActive = false
            Farm.BagFull = false
            Status.Round = "Waiting..."
            refreshStatus()
            Log("Round data cleared — waiting", "info")
        end
    end)

    Gameplay.RoundEndFade.OnClientEvent:Connect(function()
        if Farm.RoundActive then
            CancelTween()
            Farm.RoundActive = false
            Farm.BagFull = false
            Status.Round = "Ended"
            refreshStatus()
            Log("Round ended", "info")
            SaveConfig()
        end
    end)
end

local function GetNearestCoin()
    local hrp = GetHRP()
    if not hrp then return nil end
    local closest, dist = nil, math.huge
    for _, obj in pairs(workspace:GetChildren()) do
        local container = obj:FindFirstChild("CoinContainer")
        if container then
            for _, coin in pairs(container:GetChildren()) do
                if coin:GetAttribute("CoinID") == "Coin" and coin:FindFirstChild("TouchInterest") then
                    local d = (hrp.Position - coin.Position).Magnitude
                    if d < dist then
                        closest = coin
                        dist = d
                    end
                end
            end
        end
    end
    return closest, dist
end

local function TweenTo(position, distance)
    local hrp = GetHRP()
    local hum = GetHumanoid()
    if not hrp or not hum then return end
    CancelTween()
    local target = CFrame.new(position.X, position.Y + hum.HipHeight, position.Z)
    local tween = TweenService:Create(
        hrp,
        TweenInfo.new(distance / math.max(0.1, getgenv().Speed), Enum.EasingStyle.Linear),
        { CFrame = target }
    )
    Farm.CurrentTween = tween
    tween:Play()
    return tween
end

task.spawn(function()
    local wasFarming = false
    while true do
        task.wait()
        if not getgenv().Enabled or not Farm.RoundActive or Farm.BagFull
        or Farm.Respawning or Farm.DiedThisRound then
            if wasFarming then
                wasFarming = false
                Log("Farming paused", "info")
            end
            continue
        end

        if not wasFarming then
            wasFarming = true
            Log("Farming active", "success")
        end

        local hrp = GetHRP()
        if not hrp then continue end
        local coin, dist = GetNearestCoin()
        if coin then
            if dist > 150 then
                hrp.CFrame = coin.CFrame
            else
                local tween = TweenTo(coin.CFrame, dist)
                if tween then
                    repeat task.wait()
                    until not coin:FindFirstChild("TouchInterest")
                        or not Farm.RoundActive
                        or Farm.BagFull
                        or Farm.Respawning
                        or Farm.DiedThisRound
                    CancelTween()
                end
            end
        else
            task.wait(0.3)
        end
    end
end)