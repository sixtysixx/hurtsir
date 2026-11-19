-- flip either of these to false (then re-execute) to skip that one
getgenv().MM2AntiAfk = getgenv().MM2AntiAfk ~= false
getgenv().MM2AntiFling = getgenv().MM2AntiFling ~= false

local SELF = "https://sirhurt.pages.dev/mm2.lua"

-- a teleport/hop wipes the entire lua state, so nothing below can survive one on its own.
-- queue_on_teleport makes the executor re-run this file in the next server (in-client hops
-- only - a manual leave/rejoin needs the executor's auto-execute instead).
local requeue = queue_on_teleport
    or (syn and syn.queue_on_teleport)
    or (fluxus and fluxus.queue_on_teleport)
if type(requeue) == "function" then
    pcall(requeue, 'loadstring(game:HttpGet("' .. SELF .. '"))()')
end

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")

-- re-execute safety: drop the previous run's connections instead of stacking a new set
local conns = getgenv().MM2Conns
if type(conns) ~= "table" then
    conns = {}
    getgenv().MM2Conns = conns
end
for _, c in ipairs(conns) do
    pcall(function() c:Disconnect() end)
end
table.clear(conns)

-- anti idle: the client fires Idled after 20 min of zero input and kicks you.
-- either kill its handler or feed it fake input - both get re-armed every session,
-- so both are redone on a loop instead of once at load time.
if getgenv().MM2AntiAfk then
    local lastInput = os.clock()

    conns[#conns + 1] = UIS.InputBegan:Connect(function() lastInput = os.clock() end)
    conns[#conns + 1] = UIS.InputChanged:Connect(function() lastInput = os.clock() end)

    local function click()
        -- VirtualUser is the cheap way in; VirtualInputManager is a *service*,
        -- Instance.new("VirtualInputManager") always throws (not a creatable class)
        if pcall(function()
            local vu = game:GetService("VirtualUser")
            vu:CaptureController()
            vu:ClickButton2(Vector2.new())
        end) then
            return true
        end

        return pcall(function()
            local vim = game:GetService("VirtualInputManager")
            vim:SendMouseButtonEvent(0, 0, 0, true, game, 0)
            vim:SendMouseButtonEvent(0, 0, 0, false, game, 0)
        end)
    end

    local function killIdled()
        if not getconnections then return end
        local lp = Players.LocalPlayer
        if not lp then return end -- not resolvable during early auto-exec
        for _, c in ipairs(getconnections(lp.Idled)) do
            pcall(function() c:Disable() end) -- "pause" it
            pcall(function() c:Disconnect() end) -- actually remove it
        end
    end

    task.spawn(function()
        while getgenv().MM2AntiAfk do
            pcall(killIdled)
            if os.clock() - lastInput > 30 and click() then
                lastInput = os.clock()
            end
            task.wait(10)
        end
    end)
end

-- anti fling: strips collision off everyone else every frame so touch flings cant grab you
if getgenv().MM2AntiFling then
    conns[#conns + 1] = RunService.Stepped:Connect(function()
        local lp = Players.LocalPlayer
        for _, player in ipairs(Players:GetPlayers()) do
            if player ~= lp and player.Character then
                for _, v in ipairs(player.Character:GetDescendants()) do
                    -- only write when it is actually on, otherwise this is a write storm
                    if v:IsA("BasePart") and v.CanCollide then
                        v.CanCollide = false
                    end
                end
            end
        end
    end)
end

-- verdant last and pcall'd: HttpGet yields and a re-load can error, which used to
-- abort the rest of the file before the anti-afk code ever ran
task.spawn(function()
    local ok, err = pcall(function()
        loadstring(game:HttpGet("https://aptfxx.dev/scripts/verdant/main"))()
    end)
    if not ok then
        warn("[mm2] verdant failed to load: " .. tostring(err))
    end
end)

print("archived verdant @ mm2_raw.lua and @ mm2_ui_raw.lua if u wanna check it out :3")
