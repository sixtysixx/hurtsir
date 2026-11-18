-- flip either of these to false (then re-execute) to skip that one
getgenv().MM2AntiAfk = getgenv().MM2AntiAfk ~= false
getgenv().MM2AntiFling = getgenv().MM2AntiFling ~= false
loadstring(game:HttpGet("https://aptfxx.dev/scripts/verdant/main"))()
print("archived verdant @ mm2_raw.lua and @ mm2_ui_raw.lua if u wanna check it out :3")

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local LocalPlayer = Players.LocalPlayer

-- anti idle: kills existing Idled handlers and clicks instead so the client never goes afk
if getgenv().MM2AntiAfk ~= false then
    if getconnections then
        for _, c in ipairs(getconnections(LocalPlayer.Idled)) do
            pcall(function() c:Disable() end) -- supposed to "pause" it
            pcall(function() c:Disconnect() end) -- supposed to disconnect it
        end
    end

    LocalPlayer.Idled:Connect(function()
        local VirtualInputManager = Instance.new("VirtualInputManager")
        VirtualInputManager:SendMouseButtonEvent(0, 0, 0, true, game, 0)
        VirtualInputManager:SendMouseButtonEvent(0, 0, 0, false, game, 0)
        VirtualInputManager:Destroy()
    end)
end

-- anti fling: strips collision off everyone else every frame so touch flings cant grab you
if getgenv().MM2AntiFling ~= false then
    RunService.Stepped:Connect(function()
        for _, player in pairs(Players:GetPlayers()) do
            if player ~= LocalPlayer and player.Character then
                for _, v in pairs(player.Character:GetDescendants()) do
                    if v:IsA("BasePart") then
                        v.CanCollide = false
                    end
                end
            end
        end
    end)
end
