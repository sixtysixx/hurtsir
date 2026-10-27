--[[

Verdant is under the GNU General Public Licence 3.0
For more information, please view > https://aptfxx.dev/scripts/verdant/licence


   :::     ::: :::::::::: :::::::::  :::::::::      :::     ::::    ::: ::::::::::: 
  :+:     :+: :+:        :+:    :+: :+:    :+:   :+: :+:   :+:+:   :+:     :+:      
 +:+     +:+ +:+        +:+    +:+ +:+    +:+  +:+   +:+  :+:+:+  +:+     +:+       
+#+     +:+ +#++:++#   +#++:++#:  +#+    +:+ +#++:++#++: +#+ +:+ +#+     +#+        
+#+   +#+  +#+        +#+    +#+ +#+    +#+ +#+     +#+ +#+  +#+#+#     +#+         
#+#+#+#   #+#        #+#    #+# #+#    #+# #+#     #+# #+#   #+#+#     #+#          
 ###     ########## ###    ### #########  ###     ### ###    ####     ###           
                                               - Verdant v1.5
                                               -- Sanity Check 1 | iex
]]




-- i need to do this as a part of GNU GPL lol
-- and also because of safety stuff, verdant wont steal ur data but this is the nail in the coffin for ppl who think otherwise
local stfuFile = "Verdant/stfu.txt"
local function isStfuEnabled()
    if type(isfile) ~= "function" then return false end
    local ok, exists = pcall(isfile, stfuFile)
    return ok and exists == true
end

local Confirm
do
	local Players = game:GetService("Players")
	local TweenService = game:GetService("TweenService")
	local UserInputService = game:GetService("UserInputService")
	local SoundService = game:GetService("SoundService")
	local Debris = game:GetService("Debris")

	local Colors = {
		Paper = Color3.fromRGB(20, 38, 30),
		Ink = Color3.fromRGB(242, 237, 224),
		InkMuted = Color3.fromRGB(176, 188, 176),
		Rule = Color3.fromRGB(56, 80, 66),
		Accent = Color3.fromRGB(158, 214, 140),
		OnAccent = Color3.fromRGB(20, 38, 30),
		Danger = Color3.fromRGB(230, 128, 108),
	}
	local SERIF = "rbxasset://fonts/families/Merriweather.json"
	local SANS = "rbxasset://fonts/families/SourceSansPro.json"
	local CLICK_SOUND = "rbxassetid://6895079853"

	local function new(className, props, parent)
		local inst = Instance.new(className)
		for k, v in pairs(props) do
			inst[k] = v
		end
		inst.Parent = parent
		return inst
	end

	local function tween(obj, props, duration, direction)
		local t = TweenService:Create(
			obj,
			TweenInfo.new(duration, Enum.EasingStyle.Quint, direction or Enum.EasingDirection.Out),
			props
		)
		t:Play()
		return t
	end

	local function label(props, parent)
		local base = {
			BackgroundTransparency = 1,
			Size = UDim2.new(1, 0, 0, 0),
			AutomaticSize = Enum.AutomaticSize.Y,
			TextWrapped = true,
			TextXAlignment = Enum.TextXAlignment.Left,
		}
		for k, v in pairs(props) do
			base[k] = v
		end
		return new("TextLabel", base, parent)
	end

	function Confirm(options)
		options = options or {}
        if isStfuEnabled() then
            return options.StfuResult == true
        end
		local playerGui = Players.LocalPlayer:WaitForChild("PlayerGui")

		local gui = new("ScreenGui", {
			Name = "ConfirmDialog",
			IgnoreGuiInset = true,
			ResetOnSpawn = false,
			DisplayOrder = 1000,
			ZIndexBehavior = Enum.ZIndexBehavior.Sibling,
		}, playerGui)

		local overlay = new("TextButton", {
			Size = UDim2.fromScale(1, 1),
			BackgroundColor3 = Color3.new(0, 0, 0),
			BackgroundTransparency = 1,
			AutoButtonColor = false,
			Text = "",
		}, gui)

		local card = new("Frame", {
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.new(0.5, 0, 0.5, 8),
			Size = UDim2.new(0, options.Width or 400, 0, 0),
			AutomaticSize = Enum.AutomaticSize.Y,
			BackgroundColor3 = Colors.Paper,
			BorderSizePixel = 0,
			Active = true,
		}, overlay)
		new("UIStroke", { Color = Colors.Rule, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, card)
		new("UICorner", { CornerRadius = UDim.new(0, 2) }, card)
		new("UIPadding", {
			PaddingTop = UDim.new(0, 26),
			PaddingBottom = UDim.new(0, 22),
			PaddingLeft = UDim.new(0, 28),
			PaddingRight = UDim.new(0, 28),
		}, card)
		new("UIListLayout", { Padding = UDim.new(0, 12), SortOrder = Enum.SortOrder.LayoutOrder }, card)
		local cardScale = new("UIScale", { Scale = 0.97 }, card)

		-- Keep the card inside mobile screens.
		local camera = workspace.CurrentCamera
		if camera and camera.ViewportSize.X < (options.Width or 400) + 32 then
			card.Size = UDim2.new(1, -32, 0, 0)
		end

		label({
			Text = options.Title or "Are you sure?",
			FontFace = Font.new(SERIF, Enum.FontWeight.Bold),
			TextSize = 21,
			TextColor3 = Colors.Ink,
			LayoutOrder = 1,
		}, card)

		if options.Content and options.Content ~= "" then
			label({
				Text = options.Content,
				FontFace = Font.new(SERIF),
				TextSize = 14,
				LineHeight = 1.3,
				TextColor3 = Colors.InkMuted,
				LayoutOrder = 2,
			}, card)
		end

		local row = new("Frame", {
			Size = UDim2.new(1, 0, 0, 34),
			BackgroundTransparency = 1,
			LayoutOrder = 3,
		}, card)
		new("UIListLayout", {
			FillDirection = Enum.FillDirection.Horizontal,
			HorizontalAlignment = Enum.HorizontalAlignment.Right,
			VerticalAlignment = Enum.VerticalAlignment.Center,
			SortOrder = Enum.SortOrder.LayoutOrder,
			Padding = UDim.new(0, 18),
		}, row)

		-- cancel
		local cancel = new("TextButton", {
			Size = UDim2.fromOffset(0, 30),
			AutomaticSize = Enum.AutomaticSize.X,
			BackgroundTransparency = 1,
			AutoButtonColor = false,
			Text = options.CancelText or "Cancel",
			FontFace = Font.new(SANS),
			TextSize = 15,
			TextColor3 = Colors.InkMuted,
			LayoutOrder = 1,
		}, row)
		local underline = new("Frame", {
			AnchorPoint = Vector2.new(0, 1),
			Position = UDim2.new(0, 0, 1, -3),
			Size = UDim2.new(0, 0, 0, 1),
			BackgroundColor3 = Colors.Ink,
			BorderSizePixel = 0,
		}, cancel)
		cancel.MouseEnter:Connect(function()
			tween(cancel, { TextColor3 = Colors.Ink }, 0.15)
			tween(underline, { Size = UDim2.new(1, 0, 0, 1) }, 0.25)
		end)
		cancel.MouseLeave:Connect(function()
			tween(cancel, { TextColor3 = Colors.InkMuted }, 0.15)
			tween(underline, { Size = UDim2.new(0, 0, 0, 1) }, 0.25)
		end)

		-- confirm
		local confirm = new("TextButton", {
			Size = UDim2.fromOffset(0, 34),
			AutomaticSize = Enum.AutomaticSize.X,
			BackgroundColor3 = options.Danger and Colors.Danger or Colors.Accent,
			AutoButtonColor = false,
			Text = options.ConfirmText or "Confirm",
			FontFace = Font.new(SANS, Enum.FontWeight.SemiBold),
			TextSize = 15,
			TextColor3 = Colors.OnAccent,
			LayoutOrder = 2,
		}, row)
		new("UICorner", { CornerRadius = UDim.new(0, 2) }, confirm)
		new("UIPadding", { PaddingLeft = UDim.new(0, 18), PaddingRight = UDim.new(0, 18) }, confirm)
		confirm.MouseEnter:Connect(function()
			tween(confirm, { BackgroundTransparency = 0.12 }, 0.15)
		end)
		confirm.MouseLeave:Connect(function()
			tween(confirm, { BackgroundTransparency = 0 }, 0.15)
		end)

		local answered = Instance.new("BindableEvent")
		local result
		local keyConnection

		local function respond(confirmed)
			if result ~= nil then
				return
			end
			result = confirmed
			local sound = new("Sound", { SoundId = CLICK_SOUND, Volume = 0.2 }, SoundService)
			sound:Play()
			Debris:AddItem(sound, 3)
			keyConnection:Disconnect()

			tween(overlay, { BackgroundTransparency = 1 }, 0.18)
			tween(card, { Position = UDim2.new(0.5, 0, 0.5, 8) }, 0.18, Enum.EasingDirection.In)
			tween(cardScale, { Scale = 0.96 }, 0.18, Enum.EasingDirection.In).Completed:Connect(function()
				gui:Destroy()
			end)

			local callback = confirmed and options.OnConfirm or options.OnCancel
			if typeof(callback) == "function" then
				task.spawn(callback)
			end
			answered:Fire()
		end

		confirm.MouseButton1Click:Connect(function()
			respond(true)
		end)
		cancel.MouseButton1Click:Connect(function()
			respond(false)
		end)
		keyConnection = UserInputService.InputBegan:Connect(function(input, processed)
			if processed then
				return
			end
			if input.KeyCode == Enum.KeyCode.Return or input.KeyCode == Enum.KeyCode.KeypadEnter then
				respond(true)
			elseif input.KeyCode == Enum.KeyCode.Escape then
				respond(false)
			end
		end)

		tween(overlay, { BackgroundTransparency = 0.5 }, 0.25)
		tween(card, { Position = UDim2.fromScale(0.5, 0.5) }, 0.35)
		tween(cardScale, { Scale = 1 }, 0.35)

		if result == nil then
			answered.Event:Wait()
		end
		answered:Destroy()
		return result
	end
end

if not isfile or not writefile or not getgenv or not makefolder or not readfile then
    if Confirm({
        Title = "Uh Oh",
        Content = "Your executor is not supported! It lacks basic libraries such as file manipulation.",
        Danger = true,
        ConfirmText = "Exit"
    }) then
        return
    end
    return
end

if getgenv().VerdantLoaded then
    warn("Stopped the script from running multiple times. If you see this, auto rejoin prob bugged :)")
    return
end

pcall(makefolder, "Verdant")
pcall(makefolder, "Verdant/Hashes")
local configFile = "Verdant/mm2.json"
local EncodingService = game:GetService("EncodingService")
local function sha1(text: string): string
    local binaryHash = EncodingService:ComputeStringHash(text, Enum.HashAlgorithm.Sha1)
    local hex = (binaryHash:gsub(".", function(byte)
        return string.format("%02x", string.byte(byte))
    end))
    return hex
end

local firstTimerPath = "Verdant/firstTimer.txt"
local firstTime = true

if isfile(firstTimerPath) then
    if readfile(firstTimerPath) == "this user is an alpha and has loaded verdant before" then
        firstTime = false
    end
end

if firstTime then
    if Confirm({ Title = "Welcome!", Content = "We've noticed this is your first time! Welcome! We're open source so feel free to explore how it works! The only two scripts loaded are the Verdant UI and Verdant itself, both readable.", Danger = false, ConfirmText = "Load", StfuResult = true }) == true then
        writefile("Verdant/Hashes/main.txt", sha1(game:HttpGet("https://aptfxx.dev/scripts/verdant/main")))
        writefile("Verdant/Hashes/ui.txt", sha1(game:HttpGet("https://aptfxx.dev/scripts/verdantui")))
    else
        return
    end
end

if sha1(game:HttpGet("https://aptfxx.dev/scripts/verdant/main")) ~= readfile("Verdant/Hashes/main.txt") or sha1(game:HttpGet("https://aptfxx.dev/scripts/verdantui")) ~= readfile("Verdant/Hashes/ui.txt") then 
    warn("[Verdant]: Hash Mismatch!")
    warn(string.format("Main: Got %s ( expected %s )", sha1(game:HttpGet("https://aptfxx.dev/scripts/verdant/main")) , readfile("Verdant/Hashes/main.txt")))
    warn(string.format("UI: Got %s ( expected %s )", sha1(game:HttpGet("https://aptfxx.dev/scripts/verdantui")) , readfile("Verdant/Hashes/ui.txt")))
    warn("[Verdant]: This most likely means an update, but this is here as a requirement of GPL which is the licence that Verdant uses.")
    if Confirm({ Title = "Hashes Changed", Content = "The hash of one or more of Verdant's scripts have changed. This could mean Verdant has updated. View recent changelogs @ aptfxx.dev/scripts/verdant/changelogs. (View console for more info)", Danger = true, ConfirmText = "Load", StfuResult = true }) == true then
        writefile("Verdant/Hashes/main.txt", sha1(game:HttpGet("https://aptfxx.dev/scripts/verdant/main")))
        writefile("Verdant/Hashes/ui.txt", sha1(game:HttpGet("https://aptfxx.dev/scripts/verdantui")))
    else
        return
    end
end


task.wait(0.5)
getgenv().VerdantLoaded = true
writefile("Verdant/firstTimer.txt", "this user is an alpha and has loaded verdant before")


local debug = false

local travelDepth = -4
local waitDownDistance = 30
local baseSpeed = 15
local pinTolerance = 2
local clusterRadius = 15
local distanceScale = 30
local verticalPenaltyHorizontalMax = 8
local verticalPenaltyMinY = 5
local verticalPenaltyMultiplier = 0.8


local Players     = game:GetService("Players")
local RunService  = game:GetService("RunService")
local Workspace   = game:GetService("Workspace")
local Lighting    = game:GetService("Lighting")
local MarketplaceService = game:GetService("MarketplaceService")
local RS          = game:GetService("ReplicatedStorage")
local VIM         = game:GetService("VirtualInputManager")
local LocalPlayer = Players.LocalPlayer

local function afDebug(...)
    if debug then print("[Autofarm]", ...) end
end

local function verdantLog(...)
    if getgenv().VerdantDebug then
        print("[Verdant]:", ...)
    end
end

local State = {
    enabled        = false,
    prefer         = "Currency",
    whenDone       = "Reset",
    longevity      = true,
    currency       = "Coins",
    speed          = 1.0,
    ignoreUnsafe   = false,
    unsafeRadius   = 60,
    preferClusters = true,
    hasGoneUnder   = false,
    waiting        = false,
    farmHold       = false,
    endingGame     = false,
    activeCluster  = nil,
    
}

local MiscSettings = {
    lowQuality = false,
    autoHopNoRound = true,
    autoHopLowPlayers = true,
    autoHopNoCoins = true,
    autoHopBotDetection = true,
    autoHopCrowdedFarmers = true,
    autoHopFreeOutfitLobby = true,
    autoHopFlaggedHat = true,
    visualizePath = false,
    voteForBestMap = false,
}

local Session = { startTime = 0, coinsCollected = 0 }

local cList = {
    ["Coins"] = { containers = {"CoinContainer", "CoinAreas", "Coins", "CoinsFolder"} },
}

getgenv().flingActive = getgenv().flingActive or false
getgenv().OldPos = getgenv().OldPos or nil
getgenv().FPDH = getgenv().FPDH or Workspace.FallenPartsDestroyHeight

local function startFling(TargetPlayer)
    if getgenv().flingActive then return end
    getgenv().flingActive = true
    task.spawn(function()
        pcall(function()
            if not TargetPlayer or not TargetPlayer.Character then return end
            local Character = LocalPlayer.Character
            local Humanoid = Character and Character:FindFirstChildOfClass("Humanoid")
            local RootPart = Humanoid and Humanoid.RootPart
            local TCharacter = TargetPlayer.Character
            if not TCharacter then return end

            local THumanoid, TRootPart, THead, Accessory, Handle
            if TCharacter:FindFirstChildOfClass("Humanoid") then
                THumanoid = TCharacter:FindFirstChildOfClass("Humanoid")
            end
            if THumanoid and THumanoid.RootPart then TRootPart = THumanoid.RootPart end
            if TCharacter:FindFirstChild("Head") then THead = TCharacter.Head end
            if TCharacter:FindFirstChildOfClass("Accessory") then
                Accessory = TCharacter:FindFirstChildOfClass("Accessory")
            end
            if Accessory and Accessory:FindFirstChild("Handle") then Handle = Accessory.Handle end

            if not (Character and Humanoid and RootPart) then return end

            if RootPart.Velocity.Magnitude < 50 then
                getgenv().OldPos = RootPart.CFrame
            end
            if THumanoid and THumanoid.Sit then return end

            if THead then Workspace.CurrentCamera.CameraSubject = THead
            elseif Handle then Workspace.CurrentCamera.CameraSubject = Handle
            elseif THumanoid and TRootPart then Workspace.CurrentCamera.CameraSubject = THumanoid end

            if not TCharacter:FindFirstChildWhichIsA("BasePart") then return end

            local FPos = function(BasePart, Pos, Ang)
                RootPart.CFrame = CFrame.new(BasePart.Position) * Pos * Ang
                Character:SetPrimaryPartCFrame(CFrame.new(BasePart.Position) * Pos * Ang)
                RootPart.Velocity = Vector3.new(9e7, -9e8, 9e7)
                RootPart.RotVelocity = Vector3.new(9e8, 9e8, 9e8)
            end

            local SFBasePart = function(BasePart)
                local TimeToWait = 2
                local Time = tick()
                local Angle = 0
                repeat
                    if RootPart and THumanoid then
                        if BasePart.Velocity.Magnitude < 50 then
                            Angle = Angle + 100
                            FPos(BasePart, CFrame.new(0, 1.5, 0) + THumanoid.MoveDirection * BasePart.Velocity.Magnitude / 1.25, CFrame.Angles(math.rad(Angle), 0, 0)); task.wait()
                            FPos(BasePart, CFrame.new(0, -1.5, 0) + THumanoid.MoveDirection * BasePart.Velocity.Magnitude / 1.25, CFrame.Angles(math.rad(Angle), 0, 0)); task.wait()
                            FPos(BasePart, CFrame.new(0, 1.5, 0) + THumanoid.MoveDirection * BasePart.Velocity.Magnitude / 1.25, CFrame.Angles(math.rad(Angle), 0, 0)); task.wait()
                            FPos(BasePart, CFrame.new(0, -1.5, 0) + THumanoid.MoveDirection * BasePart.Velocity.Magnitude / 1.25, CFrame.Angles(math.rad(Angle), 0, 0)); task.wait()
                            FPos(BasePart, CFrame.new(0, 1.5, 0) + THumanoid.MoveDirection, CFrame.Angles(math.rad(Angle), 0, 0)); task.wait()
                            FPos(BasePart, CFrame.new(0, -1.5, 0) + THumanoid.MoveDirection, CFrame.Angles(math.rad(Angle), 0, 0)); task.wait()
                        else
                            FPos(BasePart, CFrame.new(0, 1.5, THumanoid.WalkSpeed), CFrame.Angles(math.rad(90), 0, 0)); task.wait()
                            FPos(BasePart, CFrame.new(0, -1.5, -THumanoid.WalkSpeed), CFrame.Angles(0, 0, 0)); task.wait()
                            FPos(BasePart, CFrame.new(0, 1.5, THumanoid.WalkSpeed), CFrame.Angles(math.rad(90), 0, 0)); task.wait()
                            FPos(BasePart, CFrame.new(0, -1.5, 0), CFrame.Angles(math.rad(90), 0, 0)); task.wait()
                            FPos(BasePart, CFrame.new(0, -1.5, 0), CFrame.Angles(0, 0, 0)); task.wait()
                            FPos(BasePart, CFrame.new(0, -1.5, 0), CFrame.Angles(math.rad(90), 0, 0)); task.wait()
                            FPos(BasePart, CFrame.new(0, -1.5, 0), CFrame.Angles(0, 0, 0)); task.wait()
                        end
                    end
                until Time + TimeToWait < tick() or not getgenv().FlingActive
            end

            Workspace.FallenPartsDestroyHeight = 0 / 0

            local BV = Instance.new("BodyVelocity")
            BV.Parent = RootPart
            BV.Velocity = Vector3.new(0, -9e8, 0)
            BV.MaxForce = Vector3.new(9e9, 9e9, 9e9)

            Humanoid:SetStateEnabled(Enum.HumanoidStateType.Seated, false)

            if TRootPart then SFBasePart(TRootPart)
            elseif THead then SFBasePart(THead)
            elseif Handle then SFBasePart(Handle)
            else
                BV:Destroy()
                Humanoid:SetStateEnabled(Enum.HumanoidStateType.Seated, true)
                Workspace.FallenPartsDestroyHeight = getgenv().FPDH
                return
            end

            BV:Destroy()
            Humanoid:SetStateEnabled(Enum.HumanoidStateType.Seated, true)
            Workspace.CurrentCamera.CameraSubject = Humanoid

            if getgenv().OldPos then
                repeat
                    RootPart.CFrame = getgenv().OldPos * CFrame.new(0, .5, 0)
                    Character:SetPrimaryPartCFrame(getgenv().OldPos * CFrame.new(0, .5, 0))
                    Humanoid:ChangeState("GettingUp")
                    for _, part in pairs(Character:GetChildren()) do
                        if part:IsA("BasePart") then
                            part.Velocity, part.RotVelocity = Vector3.new(), Vector3.new()
                        end
                    end
                    task.wait()
                until (RootPart.Position - getgenv().OldPos.p).Magnitude < 25
                Workspace.FallenPartsDestroyHeight = getgenv().FPDH
            end
        end)
        getgenv().flingActive = false
    end)
end

local roleData = {}

task.spawn(function()
    local remotes = RS:WaitForChild("Remotes", 15)
    if not remotes then return end
    local gameplay = remotes:FindFirstChild("Gameplay")
    if not gameplay then return end
    local pdc = gameplay:WaitForChild("PlayerDataChanged", 15)
    if not pdc then return end
    pdc.OnClientEvent:Connect(function(data)
        if type(data) == "table" then
            roleData = data
            afDebug("roles pushed")
        end
    end)
end)

local function getMyRole()
    local d = roleData[LocalPlayer.Name]
    if not d or d.Dead then return nil end
    return d.Role
end

local function hasRole()
    if getMyRole() then return true end
    local pg = LocalPlayer:FindFirstChild("PlayerGui")
    local mg = pg and pg:FindFirstChild("MainGUI")
    local g  = mg and mg:FindFirstChild("Game")
    local t  = g and g:FindFirstChild("Timer")
    if t and t.Visible then return true end
    local char = LocalPlayer.Character
    if char and (char:FindFirstChild("Knife") or char:FindFirstChild("Gun")) then return true end
    local bp = LocalPlayer:FindFirstChildOfClass("Backpack")
    if bp and (bp:FindFirstChild("Knife") or bp:FindFirstChild("Gun")) then return true end
    return false
end

local function toolHeld(p, name)
    if not p or not p.Character then return false end
    if p.Character:FindFirstChild(name) then return true end
    local bp = p:FindFirstChildOfClass("Backpack")
    return (bp and bp:FindFirstChild(name)) ~= nil
end

local function findRole(role)
    for _, p in ipairs(Players:GetPlayers()) do
        if p ~= LocalPlayer then
            if role == "Murderer" and toolHeld(p, "Knife") then return p end
            if (role == "Sheriff" or role == "Hero") and toolHeld(p, "Gun") then return p end
        end
    end
end

local function isRoundActive()
    local murdererFound, gunFound = false, false
    for _, p in ipairs(Players:GetPlayers()) do
        if toolHeld(p, "Knife") then murdererFound = true end
        if toolHeld(p, "Gun")   then gunFound = true end
    end
    return murdererFound and gunFound
end

local function getRoundState()
    if not hasRole() then return "lobby" end
    if not isRoundActive() then return "waiting" end
    return "active"
end

local function applyLowQualityMode()
    for _, obj in ipairs(Workspace:GetDescendants()) do
        pcall(function()
            if obj:IsA("Texture") or obj:IsA("Decal") then
                obj:Destroy()
            elseif obj:IsA("ParticleEmitter") or obj:IsA("Trail") then
                obj.Enabled = false
            elseif obj:IsA("BasePart") then
                obj.Material = Enum.Material.Plastic
                obj.Reflectance = 0
                obj.CastShadow = false
            end
        end)
    end

    Lighting.GlobalShadows = false
    Lighting.FogEnd = 1e10
    Lighting.Brightness = 1
    Lighting.ClockTime = 14
    Lighting.EnvironmentDiffuseScale = 0
    Lighting.EnvironmentSpecularScale = 0
end

local function enterWaiting()
    if State.waiting then return end
    State.waiting = true
    if MiscSettings.lowQuality then
        applyLowQualityMode()
    end
end

local function getChar() return LocalPlayer.Character end
local function getHum()
    local c = getChar(); if not c then return nil end
    return c:FindFirstChildOfClass("Humanoid")
end
local function getHRP()
    local c = getChar(); if not c then return nil end
    return c:FindFirstChild("HumanoidRootPart") or c.PrimaryPart
end
local function isAlive()
    local h = getHum()
    return h and h.Health > 0
end

-- camera lock
local cameraConn = nil
local savedCameraType = nil
local cameraOffset = Vector3.new(0, 5, 12)

local function stopCameraLock()
    if cameraConn then
        cameraConn:Disconnect()
        cameraConn = nil
    end
    local cam = Workspace.CurrentCamera
    if cam and savedCameraType then
        cam.CameraType = savedCameraType
    end
    savedCameraType = nil
end

local stabilizeConn = nil

local function startStabilize()
    if stabilizeConn then return end
    stabilizeConn = RunService.Heartbeat:Connect(function()
        if not State.enabled then return end
        local c = getChar(); if not c then return end
        for _, p in ipairs(c:GetDescendants()) do
            if p:IsA("BasePart") then
                p.Velocity    = Vector3.zero
                p.RotVelocity = Vector3.zero
            end
        end
        -- this stops the character from jittering all the time and keeps us
        -- from sinking below the pinned Y without exceeding the speed cap
        if State.farmHold and pinnedPos then
            local hrp = getHRP()
            if hrp then
                local dy = hrp.Position.Y - pinnedPos.Y
                if dy < -0.5 and dy > -50 then
                    local maxSnap = (baseSpeed * math.max(State.speed, 0.1)) / 60
                    local snap = math.min(-dy, maxSnap)
                    c:PivotTo(layCF(Vector3.new(
                        hrp.Position.X, hrp.Position.Y + snap, hrp.Position.Z)))
                elseif dy < -50 then
                    pinnedPos = hrp.Position
                end
            end
        end
    end)
end

local function stopStabilize()
    if stabilizeConn then
        stabilizeConn:Disconnect()
        stabilizeConn = nil
    end
    State.farmHold = false
end

local savedHumanoid = nil

local function restoreHumanoid()
    local hum = getHum()
    if hum and savedHumanoid then
        pcall(function()
            hum.WalkSpeed = savedHumanoid.WalkSpeed or 16
            hum.JumpPower = savedHumanoid.JumpPower or 50
        end)
    end
    if hum then
        pcall(function()
            hum.PlatformStand = false
            hum.Sit = false
            hum:ChangeState(Enum.HumanoidStateType.GettingUp)
        end)
    end
    savedHumanoid = nil
end

local function layCF(pos)
    return CFrame.new(pos) * CFrame.Angles(math.rad(-90), 0, 0)
end

local pinnedPos = nil
local function setPinned(pos) pinnedPos = pos end
local function setCollision(char, enabled)
    if not char then return end
    for _, p in ipairs(char:GetDescendants()) do
        if p:IsA("BasePart") then
            p.CanCollide = enabled
        end
    end
end

local function prepareTeleport()
    local char = getChar(); if not char then return end
    local hrp = getHRP();  if not hrp then return end
    local hum = getHum();  if not hum then return end

    if hrp.Anchored then hrp.Anchored = false end
    pcall(function() hum.AutoRotate = false end)
    pcall(function()
        if hum.PlatformStand then hum.PlatformStand = false end
        if hum.Sit then hum.Sit = false end
        if hum:GetState() == Enum.HumanoidStateType.Seated then
            hum:ChangeState(Enum.HumanoidStateType.GettingUp)
        end
    end)
end

local function writeCF(cf)
    local char = getChar(); if not char then return end
    local hrp = getHRP();  if not hrp then return end
    char:PivotTo(cf)
    pcall(function()
        hrp.AssemblyLinearVelocity  = Vector3.zero
        hrp.AssemblyAngularVelocity = Vector3.zero
    end)
    hrp.Velocity    = Vector3.zero
    hrp.RotVelocity = Vector3.zero
    pinnedPos = cf.Position
end

local activePathTarget = nil

local visualizePathEnabled = false
local pathLine = nil
local pathVisualConn = nil

local function hidePathLine()
    if pathLine then pcall(function() pathLine.Visible = false end) end
end

local function setPathVisualization(enabled)
    visualizePathEnabled = enabled == true
    MiscSettings.visualizePath = visualizePathEnabled
    if visualizePathEnabled then
        if not Drawing or type(Drawing.new) ~= "function" then
            visualizePathEnabled = false
            MiscSettings.visualizePath = false
            return false
        end
        if not pathVisualConn then
            pathVisualConn = RunService.RenderStepped:Connect(function()
                if not visualizePathEnabled or not activePathTarget then
                    hidePathLine()
                    return
                end
                if not Drawing or type(Drawing.new) ~= "function" then
                    hidePathLine()
                    return
                end
                if not pathLine then
                    local ok, line = pcall(function()
                        local item = Drawing.new("Line")
                        item.Color = Color3.fromRGB(158, 214, 140)
                        item.Thickness = 2
                        item.Transparency = 1
                        item.Visible = false
                        return item
                    end)
                    if not ok then return end
                    pathLine = line
                end

                local cam = Workspace.CurrentCamera
                local hrp = getHRP()
                if not cam or not hrp then hidePathLine(); return end
                local from = cam:WorldToViewportPoint(hrp.Position)
                local to = cam:WorldToViewportPoint(activePathTarget)
                if from.Z <= 0 or to.Z <= 0 then hidePathLine(); return end
                pathLine.From = Vector2.new(from.X, from.Y)
                pathLine.To = Vector2.new(to.X, to.Y)
                pathLine.Visible = true
            end)
        end
    else
        if pathVisualConn then pathVisualConn:Disconnect(); pathVisualConn = nil end
        hidePathLine()
    end
    return true
end

local watchdogConn = nil

local function startWatchdog()
    if watchdogConn then return end
    watchdogConn = RunService.RenderStepped:Connect(function()
        if not State.enabled then return end
        if not State.hasGoneUnder then return end
        if not State.waiting then return end

        local c   = getChar(); if not c then return end
        local hrp = getHRP();  if not hrp then return end

        if pinnedPos and (hrp.Position - pinnedPos).Magnitude > 200 then
            pinnedPos = hrp.Position
            hrp.Anchored = true
            hrp.CanCollide = false
            State.hasGoneUnder = false
            return
        end

        if not hrp.Anchored then
            hrp.Anchored = true
            hrp.CanCollide = false
        end

        hrp.Velocity    = Vector3.zero
        hrp.RotVelocity = Vector3.zero

        if pinnedPos then
            if (hrp.Position - pinnedPos).Magnitude > pinTolerance then
                c:PivotTo(layCF(pinnedPos))
            end
        end

        local hum = getHum()
        if hum then
            if not hum.PlatformStand then hum.PlatformStand = true end
            if hum.WalkSpeed ~= 0 then hum.WalkSpeed = 0 end
            if hum.JumpPower ~= 0 then hum.JumpPower = 0 end
            local st = hum:GetState()
            if st == Enum.HumanoidStateType.Freefall
            or st == Enum.HumanoidStateType.FallingDown
            or st == Enum.HumanoidStateType.Ragdoll
            or st == Enum.HumanoidStateType.Landed
            or st == Enum.HumanoidStateType.Running
            or st == Enum.HumanoidStateType.RunningNoPhysics
            or st == Enum.HumanoidStateType.Jumping then
                pcall(function() hum:ChangeState(Enum.HumanoidStateType.Physics) end)
            end
        end
    end)
end

local function stopWatchdog()
    if watchdogConn then watchdogConn:Disconnect(); watchdogConn = nil end
    pinnedPos = nil
end

local hrpWasAnchored = nil
local hrpCanCollideWas = nil

local function anchorHRP(state)
    local hrp = getHRP(); if not hrp then return end
    if state then
        if hrpWasAnchored == nil then
            hrpWasAnchored = hrp.Anchored
            hrpCanCollideWas = hrp.CanCollide
            hrp.CanCollide = false
        end
        hrp.Anchored = true
    else
        if hrpWasAnchored ~= nil then
            hrp.Anchored = hrpWasAnchored
            hrp.CanCollide = hrpCanCollideWas or false
            hrpWasAnchored = nil
            hrpCanCollideWas = nil
        else
            hrp.Anchored = false
        end
        local hum = getHum()
        if hum then
            pcall(function()
                hum.PlatformStand = false
                hum.Sit = false
                hum:ChangeState(Enum.HumanoidStateType.GettingUp)
            end)
        end
    end
end

-- drop dow
local function goDown()
    if State.hasGoneUnder then return end

    local c = getChar(); if not c then return end
    local hrp = getHRP(); if not hrp then return end

    hrpWasAnchored = nil
    if hrp.Anchored then hrp.Anchored = false end

    local target = hrp.Position - Vector3.new(0, waitDownDistance, 0)

    do
        local char = getChar()
        if char then
            local hrp2 = getHRP()
            if hrp2 then
                prepareTeleport()
                setCollision(char, false)
                local cur = hrp2.Position
                if (target - cur).Magnitude >= 0.5 then
                    local speed = baseSpeed * math.max(State.speed, 0.1)
                    local guard = 0
                    while (target - cur).Magnitude > 0.5 do
                        guard = guard + 1
                        if guard > 2000 then break end
                        if not getChar() then break end
                        if not State.enabled then break end
                        local dt = RunService.Heartbeat:Wait()
                        dt = math.min(dt, 1/30)
                        local delta = target - cur
                        local step = math.min(delta.Magnitude, speed * dt)
                        cur = cur + delta.Unit * step
                        writeCF(layCF(cur))
                    end
                end
                setPinned(target)
                setCollision(char, true)
            end
        end
    end

    anchorHRP(true)
    setPinned(target)

    State.hasGoneUnder = true
    afDebug("waiting: down "..waitDownDistance.." to Y="..target.Y)
end

local hasFTI = type(firetouchinterest) == "function"

local function getMap()
    local wanted = {}
    for _, cfg in pairs(cList) do for _, n in ipairs(cfg.containers) do wanted[n] = true end end
    for _, v in ipairs(Workspace:GetChildren()) do
        if v:IsA("Model") then
            for name in pairs(wanted) do
                if v:FindFirstChild(name) then return v end
            end
        end
    end
    for _, v in ipairs(Workspace:GetChildren()) do
        if v:IsA("Model") and v:FindFirstChild("Base") then return v end
    end
    return nil
end

local REJECT = {
    ["2part"] = true, ["decalpart"] = true, ["maincoin"] = true,
    ["coinvisual"] = true, ["visual"] = true, ["effect"] = true,
    ["particle"] = true, ["sparkle"] = true, ["glow"] = true,
}

local function isCoinPart(part)
    if not part or not part:IsA("BasePart") then return false end
    local name = part.Name:lower()
    if name == "coin_server" then return true end
    if name:match("^coinarea%d*$") or name:match("^coin_area") then return true end
    if name == "coin" then return true end
    if REJECT[name] then return false end
    if name:find("visual") or name:find("decal") or name:find("effect") then return false end
    if part:FindFirstChildWhichIsA("TouchTransmitter") then
        local p = part.Parent
        if p and p:FindFirstChild("Coin_Server") and part.Name ~= "Coin_Server" then return false end
        return true
    end
    return false
end

local coins, coinSet, touched = {}, {}, {}
local addConn, removeConn, boundContainer
local collectedCount = 0
local coinFails = {}

local function isTouched(c) return touched[c] == true end
local function markTouched(c) touched[c] = true end

local function trackCoin(part)
    if not isCoinPart(part) then return end
    if coinSet[part] or isTouched(part) then return end
    coinSet[part] = true
    table.insert(coins, part)
end

local function scanCoins()
    coins, coinSet, touched = {}, {}, {}

    local container
    do
        local cfg = cList[State.currency]
        if cfg then
            local map = getMap()
            if map then
                for _, name in ipairs(cfg.containers) do
                    local cc = map:FindFirstChild(name)
                    if cc then container = cc; break end
                end
            end
        end
    end

    if boundContainer ~= container then
        boundContainer = container
        if addConn then addConn:Disconnect(); addConn = nil end
        if removeConn then removeConn:Disconnect(); removeConn = nil end
        if container then
            addConn = container.DescendantAdded:Connect(function(d)
                if d:IsA("BasePart") then trackCoin(d) end
            end)
            removeConn = container.DescendantRemoving:Connect(function(d)
                if d:IsA("BasePart") and coinSet[d] then
                    coinSet[d] = nil
                    markTouched(d)
                    collectedCount = collectedCount + 1
                    Session.coinsCollected = Session.coinsCollected + 1
                end
            end)
        end
    end

    if not container then return 0 end
    local n = 0
    for _, d in ipairs(container:GetDescendants()) do
        if d:IsA("BasePart") and isCoinPart(d) then trackCoin(d); n = n + 1 end
    end
    afDebug("scanCoins: "..(container.Name).." tracked="..n)
    return n
end

local function isCoinUnsafe(coin)
    if not State.ignoreUnsafe then return false end
    local m = findRole("Murderer")
    if m and m.Character then
        local r = m.Character:FindFirstChild("HumanoidRootPart")
        if r and (r.Position - coin.Position).Magnitude < State.unsafeRadius then return true end
    end
    return false
end

local lastPlayerSamples = {}
local currentPlayerSamples = {}
local crowdedCoinUntil = setmetatable({}, { __mode = "k" })

local function horizontalDistance(a, b)
    return Vector3.new(a.X - b.X, 0, a.Z - b.Z).Magnitude
end

local function playerProximityPenalty(coin)
    local now = tick()
    local penalty = 0
    local cooldown = crowdedCoinUntil[coin]
    if cooldown then
        if cooldown > now then
            penalty = penalty + 90
        else
            crowdedCoinUntil[coin] = nil
        end
    end

    local coinPosition = coin.Position
    for player, sample in pairs(currentPlayerSamples) do
        local distance = horizontalDistance(sample.position, coinPosition)
        if distance <= 7 then
            penalty = penalty + 24 + (7 - distance) * 2
        elseif distance <= 36 then
            local closingDistance = 0
            if sample.previousPosition and sample.sampleAge and sample.sampleAge <= 1.5 then
                local previousDistance = horizontalDistance(sample.previousPosition, coinPosition)
                closingDistance = previousDistance - distance
            end

            if closingDistance >= 0.8 then
                penalty = penalty + 15 + math.min(closingDistance, 8) * 1.25 + (36 - distance) * 0.15
            elseif not sample.previousPosition or not sample.sampleAge then
                local velocity = Vector3.new(sample.velocity.X, 0, sample.velocity.Z)
                local toCoin = Vector3.new(coinPosition.X - sample.position.X, 0, coinPosition.Z - sample.position.Z)
                if velocity.Magnitude >= 4 and toCoin.Magnitude > 0.01
                   and velocity.Unit:Dot(toCoin.Unit) >= 0.65 then
                    penalty = penalty + 11 + (36 - distance) * 0.2
                end
            end
        end
    end

    return penalty
end

local function collectSafeCoins(pivot)
    do
        local now = tick()
        local nextLast = {}
        local current = {}

        for _, player in ipairs(Players:GetPlayers()) do
            if player ~= LocalPlayer and player.Character then
                local hum = player.Character:FindFirstChildOfClass("Humanoid")
                local root = player.Character:FindFirstChild("HumanoidRootPart")
                if hum and hum.Health > 0 and root then
                    local position = root.Position
                    local previous = lastPlayerSamples[player]
                    local previousPosition, sampleAge

                    if previous then
                        sampleAge = now - previous.time
                        if sampleAge >= 0.15 and sampleAge <= 1.5 then
                            previousPosition = previous.position
                            nextLast[player] = { position = position, time = now }
                        elseif sampleAge < 0.15 then
                            nextLast[player] = previous
                        else
                            nextLast[player] = { position = position, time = now }
                            sampleAge = nil
                        end
                    else
                        nextLast[player] = { position = position, time = now }
                    end

                    current[player] = {
                        position = position,
                        previousPosition = previousPosition,
                        sampleAge = sampleAge,
                        velocity = root.AssemblyLinearVelocity,
                    }
                end
            end
        end

        lastPlayerSamples = nextLast
        currentPlayerSamples = current
    end

    local safe = {}
    for i = #coins, 1, -1 do
        local cc = coins[i]
        if not cc or not cc.Parent or isTouched(cc) then
            coinSet[cc] = nil; table.remove(coins, i)
        elseif not isCoinUnsafe(cc) then
            local dist = (cc.Position - pivot).Magnitude
            table.insert(safe, { coin = cc, dist = dist, scoreDist = dist + playerProximityPenalty(cc) })
        end
    end
    return safe
end

local function pickNearestIn(pool)
    local best, bestD = nil, math.huge
    for _, entry in ipairs(pool) do
        local priority = entry.scoreDist or entry.dist
        if priority < bestD then bestD = priority; best = entry.coin end
    end
    return best
end

local fullBagCache = { t = 0, r = false }
local function isBagFull()
    local now = tick()
    if now - fullBagCache.t < 0.35 then return fullBagCache.r end
    fullBagCache.t = now
    local pg = LocalPlayer:FindFirstChild("PlayerGui")
    local g = pg and pg:FindFirstChild("MainGUI")
    g = g and g:FindFirstChild("Game")
    local bags = g and g:FindFirstChild("CoinBags")
    if not bags then fullBagCache.r = false; return false end
    local vis = false
    for _, d in ipairs(bags:GetDescendants()) do
        if d:IsA("ImageLabel") and d.Name == "FullBagIcon" and d.Visible then vis = true; break end
    end
    fullBagCache.r = vis
    return vis
end

local function handleDone(reason)
    afDebug("handleDone:", reason)
    if State.whenDone == "Reset" then
        local hum = getHum()
        if hum then hum.Health = 0 end
    else
        -- end game
        State.endingGame = true
    end
end

local function flingSurvivors(excludeSelf)
    local survivors = {}
    for _, p in ipairs(Players:GetPlayers()) do
        local d = roleData[p.Name]
        if d and not d.Dead and d.Role == "Survivor" then
            table.insert(survivors, p)
        end
    end

    for _, p in ipairs(survivors) do
        if excludeSelf and p == LocalPlayer then
            -- skip self
        elseif p.Character and p.Character:FindFirstChild("HumanoidRootPart") then
            local tHum = p.Character:FindFirstChildOfClass("Humanoid")
            if tHum and tHum.Health > 0 and not getgenv().flingActive then
                afDebug("flingSurvivors: flinging " .. p.Name)
                startFling(p)
                local timeout = tick() + 4
                while getgenv().flingActive and tick() < timeout do
                    task.wait(0.1)
                end
                task.wait(0.2)
            end
        end
    end
end

local function stopFarm()
    State.enabled = false
    activePathTarget = nil
    hidePathLine()
    restoreHumanoid()
    stopStabilize()
    stopWatchdog()
    anchorHRP(false)
    State.hasGoneUnder = false
    State.waiting = false
    State.farmHold  = false
    State.activeCluster = nil
    stopCameraLock()
end

local function startFarm()
    if State.enabled then return end
    State.enabled = true
    collectedCount = 0
    boundContainer = nil
    coinFails = {}
    State.hasGoneUnder = false
    State.waiting = false
    State.farmHold  = false
    State.activeCluster = nil
    Session.startTime = tick()
    Session.coinsCollected = 0

    task.spawn(function()
        local backoff = 0.5
        while State.enabled do
            local ok, status = pcall(function()
                if State.whenDone == "End Game" then
                    local function isInLobbyWithGameInline()
                        if hasRole() then return false end
                        return findRole("Murderer") ~= nil
                    end
                    local function shouldEndGameInline()
                        if State.whenDone ~= "End Game" then return false end
                        if getMyRole() == "Murderer" then return true end
                        if findRole("Murderer") then return true end
                        return false
                    end
                    if (State.endingGame or isBagFull() or isInLobbyWithGameInline()) and shouldEndGameInline() then
                        stopStabilize()
                        State.endingGame = true
                        local start = tick()
                        local survivorResetRequested = false

                        while State.enabled do
                            local myRole = getMyRole()

                            if myRole == "Survivor" then
                                if not survivorResetRequested then
                                    flingSurvivors(true)
                                    survivorResetRequested = true
                                    local hum = getHum()
                                    if hum and hum.Health > 0 then
                                        afDebug("endGameLoop: survivor finished, resetting local character")
                                        hum.Health = 0
                                    end
                                end
                                task.wait(0.5)

                            elseif myRole == "Zombie" then
                                flingSurvivors(false)
                                task.wait(1)

                            elseif myRole == "Murderer" then
                                afDebug("endGameLoop: we are the murderer -> suicide")
                                local hum = getHum()
                                if hum and hum.Health > 0 then hum.Health = 0 end
                                task.wait(1)

                            elseif not isAlive() then
                                task.wait(0.5)
                                if not findRole("Murderer") and not isRoundActive() then
                                    afDebug("endGameLoop: round ended while dead")
                                    State.endingGame = false
                                    return "round-ended"
                                end

                            else
                                local m = findRole("Murderer")
                                if m then
                                    if not getgenv().flingActive then
                                        afDebug("endGameLoop: flinging murderer " .. m.Name)
                                        startFling(m)
                                    end
                                    task.wait(0.25)
                                else
                                    afDebug("endGameLoop: no murderer visible -> round over")
                                    State.endingGame = false
                                    return "round-ended"
                                end
                            end

                            if tick() - start > 180 then
                                afDebug("endGameLoop: timeout")
                                State.endingGame = false
                                return "end-timeout"
                            end
                        end

                        State.endingGame = false
                        return "stopped"
                    end
                end

                if #coins == 0 and next(coinFails) ~= nil then
                    coinFails = {}
                end

                local roundState = getRoundState()

                if roundState == "lobby" then
                    if State.hasGoneUnder or State.waiting then
                        State.hasGoneUnder = false
                        State.waiting = false
                        State.farmHold = false
                        State.activeCluster = nil
                        stopWatchdog()
                        stopStabilize()
                        anchorHRP(false)
                        restoreHumanoid()
                    end
                    return "no-role"
                end

                if roundState == "waiting" then
                    if not State.hasGoneUnder then
                        State.activeCluster = nil
                        goDown()
                        if State.hasGoneUnder then
                            enterWaiting()
                            startWatchdog()
                        end
                    end
                    return "waiting"
                end

                local char = getChar()
                if not char or not isAlive() then return "respawn" end

                if State.waiting then
                    State.waiting = false
                    stopWatchdog()

                    -- we're already waitDownDistance studs under from goDown the loops
                    -- travelTo will walk us up to the first coin
                    local hrp = getHRP()
                    if hrp and hrp.Anchored then
                        anchorHRP(false)
                    end

                    State.farmHold = true
                    startStabilize()
                    State.hasGoneUnder = false
                    State.activeCluster = nil
                    prepareTeleport()
                    afDebug("round active -> collecting from under")
                end

                local myRole = getMyRole()
                local armed
                if myRole then
                    armed = (myRole == "Murderer" or myRole == "Sheriff" or myRole == "Hero")
                else
                    armed = toolHeld(LocalPlayer, "Knife") or toolHeld(LocalPlayer, "Gun")
                end

                local xpMurderer = (State.prefer == "XP") and (myRole == "Murderer" or (not myRole and toolHeld(LocalPlayer, "Knife")))
                local xpSheriff  = (State.prefer == "XP") and not xpMurderer and armed

                if xpMurderer then
                    State.farmHold = false
                    startStabilize()
                    while State.enabled do
                        if not hasRole() then stopStabilize(); return "no-role" end
                        if not isRoundActive() then stopStabilize(); return "waiting" end

                        local ch = getChar()
                        if not ch or not ch.Parent or not isAlive() then
                            stopStabilize()
                            return "respawn"
                        end

                        local myRoot = ch:FindFirstChild("HumanoidRootPart")
                        if myRoot then
                            local knife = ch:FindFirstChild("Knife")
                            if not knife then
                                local bp = LocalPlayer:FindFirstChildOfClass("Backpack")
                                if bp and bp:FindFirstChild("Knife") then
                                    local hum = getHum()
                                    if hum then hum:EquipTool(bp.Knife) end
                                    task.wait(0.1)
                                    knife = ch:FindFirstChild("Knife")
                                end
                            end
                            if knife then
                                local cam = Workspace.CurrentCamera
                                local vp = cam and cam.ViewportSize
                                local cx, cy = (vp and vp.X / 2) or 400, (vp and vp.Y / 2) or 300
                                for _, p in ipairs(Players:GetPlayers()) do
                                    if p ~= LocalPlayer and p.Character then
                                        local tHum = p.Character:FindFirstChildOfClass("Humanoid")
                                        local tHRP = p.Character:FindFirstChild("HumanoidRootPart")
                                        if tHum and tHum.Health > 0 and tHRP then
                                            local followConn
                                            followConn = RunService.Heartbeat:Connect(function()
                                                if not myRoot.Parent or not tHRP.Parent then
                                                    if followConn then followConn:Disconnect(); followConn = nil end
                                                    return
                                                end
                                                myRoot.CFrame = CFrame.new(
                                                    tHRP.Position - tHRP.CFrame.LookVector * 1.5,
                                                    tHRP.Position
                                                )
                                                myRoot.Velocity    = Vector3.zero
                                                myRoot.RotVelocity = Vector3.zero
                                            end)

                                            task.wait(0.12)

                                            for _ = 1, 3 do
                                                if not tHRP.Parent then break end
                                                if tHum.Health <= 0 then break end

                                                VIM:SendMouseButtonEvent(cx, cy, 0, true,  game, 0)
                                                task.wait(0.03)
                                                VIM:SendMouseButtonEvent(cx, cy, 0, false, game, 0)
                                                pcall(function() knife:Activate() end)
                                                task.wait(0.1)
                                            end

                                            if followConn then followConn:Disconnect(); followConn = nil end
                                            task.wait(0.08)
                                        end
                                    end
                                end
                            end
                        end

                        task.wait(0.15 / math.max(State.speed, 0.1))
                    end
                    stopStabilize()
                    return "stopped"
                end

                if xpSheriff then
                    State.farmHold = false
                    while State.enabled do
                        if not hasRole() then return "no-role" end
                        if not isRoundActive() then return "waiting" end

                        local ch = getChar()
                        if not ch or not ch.Parent or not isAlive() then return "respawn" end

                        local gun = ch:FindFirstChild("Gun")
                        if not gun then
                            local drop = Workspace:FindFirstChild("GunDrop", true)
                            if drop and hasFTI then
                                local root = getHRP()
                                if root then
                                    pcall(function()
                                        firetouchinterest(root, drop, 0)
                                        firetouchinterest(root, drop, 1)
                                    end)
                                end
                            end
                        end

                        local m = findRole("Murderer")
                        if m and m.Character then
                            pcall(function()
                                if not m.Character then return end
                                local ch2 = getChar(); if not ch2 then return end
                                local root = ch2:FindFirstChild("HumanoidRootPart"); if not root then return end
                                local tHRP = m.Character:FindFirstChild("HumanoidRootPart"); if not tHRP then return end

                                local gun2 = ch2:FindFirstChild("Gun")
                                if not gun2 then
                                    local bp = LocalPlayer:FindFirstChildOfClass("Backpack")
                                    if bp and bp:FindFirstChild("Gun") then
                                        local hum = getHum()
                                        if hum then hum:EquipTool(bp.Gun) end
                                        task.wait(0.15)
                                        gun2 = ch2:FindFirstChild("Gun")
                                    end
                                end
                                if not gun2 then return end

                                local shootRemote = gun2:FindFirstChild("Shoot")
                                if not shootRemote or not shootRemote:IsA("RemoteEvent") then return end

                                local pos = tHRP.Position + Vector3.new(0, 8, 0) - tHRP.CFrame.LookVector * 6
                                writeCF(CFrame.new(pos, tHRP.Position))
                                setPinned(pos)
                                task.wait(0.08)

                                local origin = ch2:FindFirstChild("RightHand")
                                            or ch2:FindFirstChild("Right Arm")
                                            or ch2:FindFirstChild("Head")
                                if not origin then return end

                                local tChar = m.Character
                                local part = tChar:FindFirstChild("UpperTorso")
                                          or tChar:FindFirstChild("HumanoidRootPart")
                                          or tChar:FindFirstChild("Head")
                                if not part then return end

                                shootRemote:FireServer(CFrame.new(origin.Position), CFrame.new(part.Position))
                            end)
                        end

                        task.wait(0.6 / math.max(State.speed, 0.1))
                    end
                    return "stopped"
                end

                startStabilize()
                local map = getMap()
                if not map then
                    stopStabilize()
                    goDown()
                    if State.hasGoneUnder then
                        enterWaiting()
                        startWatchdog()
                    end
                    return "waiting"
                end
                local n = scanCoins()
                if n == 0 then
                    stopStabilize()
                    goDown()
                    if State.hasGoneUnder then
                        enterWaiting()
                        startWatchdog()
                    end
                    return "waiting"
                end

                afDebug("starting on "..map.Name.." ("..n.." coins)")

                do
                    local hum = getHum()
                    if hum then
                        if not savedHumanoid then
                            savedHumanoid = { WalkSpeed = hum.WalkSpeed, JumpPower = hum.JumpPower }
                        end
                        pcall(function()
                            hum.WalkSpeed = 0
                            hum.JumpPower = 0
                        end)
                    end
                end

                task.wait(0.15)

                local hrpInit = getHRP()
                if hrpInit then setPinned(hrpInit.Position) end
                State.farmHold = true

                local emptyStreak = 0
                local nextPickStrategy = "nearest"

                while State.enabled do
                    local ch = getChar()
                    if not ch or not ch.Parent or not isAlive() then
                        stopStabilize()
                        return "respawn"
                    end
                    if not (isRoundActive() or hasRole()) then
                        stopStabilize()
                        return "waiting"
                    end

                    local hrpCheck = getHRP()
                    if hrpCheck and hrpCheck.Anchored then
                        anchorHRP(false)
                    end

                    if isBagFull() then
                        handleDone("bag full")
                        stopStabilize()
                        return "done"
                    end

                    local coin
                    if nextPickStrategy == "second-furthest" then
                        coin = (function()
                            local c = getChar(); if not c then return nil end
                            local pivot = c:GetPivot().Position

                            local active
                            if State.activeCluster then
                                local entries = {}
                                for _, coin2 in ipairs(State.activeCluster) do
                                    if coinSet[coin2] and not isTouched(coin2) and coin2.Parent and not isCoinUnsafe(coin2) then
                                        local dist = (coin2.Position - pivot).Magnitude
                                        table.insert(entries, { coin = coin2, dist = dist, scoreDist = dist + playerProximityPenalty(coin2) })
                                    end
                                end
                                if #entries == 0 then
                                    verdantLog("active cluster empty (collected/unsafe/gone) -> cleared")
                                    State.activeCluster = nil
                                    active = nil
                                else
                                    State.activeCluster = {}
                                    for _, e in ipairs(entries) do
                                        table.insert(State.activeCluster, e.coin)
                                    end
                                    verdantLog(string.format("active cluster pruned: %d coins remain", #entries))
                                    active = entries
                                end
                            end

                            -- if we're mid-cluster, keep going within it
                            if active and #active > 0 then
                                if #active == 1 then return active[1].coin end
                                table.sort(active, function(a, b) return a.dist > b.dist end)
                                return active[2].coin
                            end

                            local safe = collectSafeCoins(pivot)
                            if #safe == 0 then return nil end
                            if #safe == 1 then return safe[1].coin end
                            table.sort(safe, function(a, b) return a.dist > b.dist end)
                            return safe[2].coin
                        end)()
                        nextPickStrategy = "nearest"
                        afDebug("retarget: heading to second-furthest coin")
                    else
                        coin = (function()
                            local c = getChar(); if not c then return nil end
                            local pivot = c:GetPivot().Position

                            local safe = collectSafeCoins(pivot)
                            if #safe == 0 then
                                State.activeCluster = nil
                                return nil
                            end

                            if not State.preferClusters then
                                return pickNearestIn(safe)
                            end

                            local function pickByWeightInline(safeArg, pivotArg)
                                local clusters
                                do
                                    -- group safe coins by proximity
                                    local visited = {}
                                    clusters = {}
                                    for _, entry in ipairs(safeArg) do
                                        if not visited[entry.coin] then
                                            local cluster = {}
                                            local queue = { entry }
                                            visited[entry.coin] = true
                                            while #queue > 0 do
                                                local cur = table.remove(queue)
                                                table.insert(cluster, cur)
                                                for _, other in ipairs(safeArg) do
                                                    if not visited[other.coin]
                                                       and (other.coin.Position - cur.coin.Position).Magnitude <= clusterRadius then
                                                        visited[other.coin] = true
                                                        table.insert(queue, other)
                                                    end
                                                end
                                            end
                                            table.insert(clusters, cluster)
                                        end
                                    end
                                end

                                if #clusters == 0 then return nil end
                                local k = 15 / math.max(distanceScale or 30, 1)

                                local bestCluster, bestScore, bestSize, bestNearest, bestIdx = nil, -math.huge, 0, math.huge, 0
                                for idx, cluster in ipairs(clusters) do
                                    local size = #cluster
                                    if size > 0 then
                                        local nearest = math.huge
                                        for _, entry in ipairs(cluster) do
                                            local scoreDist = entry.scoreDist or entry.dist
                                            if scoreDist and scoreDist < nearest then nearest = scoreDist end
                                        end
                                        if nearest ~= math.huge then
                                            local weight = math.min(size, 4) + math.sqrt(math.max(0, size - 4)) * 0.5
                                            local score = weight - nearest * k
                                            afDebug(string.format(
                                                "cluster[%d] size=%d nearest=%.1f w=%.2f score=%.2f",
                                                idx, size, nearest, weight, score))
                                            if score > bestScore or (score == bestScore and size > bestSize) then
                                                bestCluster = cluster
                                                bestScore   = score
                                                bestSize    = size
                                                bestNearest = nearest
                                                bestIdx     = idx
                                            end
                                        end
                                    end
                                end

                                if not bestCluster then return pickNearestIn(safeArg) end

                                if bestSize >= 2 then
                                    State.activeCluster = {}
                                    for _, entry in ipairs(bestCluster) do
                                        table.insert(State.activeCluster, entry.coin)
                                    end
                                    afDebug(string.format("committed to cluster[%d] size=%d nearest=%.1f score=%.2f",
                                        bestIdx, bestSize, bestNearest, bestScore))
                                else
                                    State.activeCluster = nil
                                end

                                return pickNearestIn(bestCluster)
                            end

                            return pickByWeightInline(safe, pivot)
                        end)()
                    end

                    if not coin then
                        emptyStreak = emptyStreak + 1
                        if emptyStreak >= 3 then
                            local m = scanCoins()
                            if m == 0 then
                                if collectedCount > 0 then
                                    handleDone("all collected")
                                    stopStabilize()
                                    return "done"
                                else
                                    return "no-coins"
                                end
                            end
                            emptyStreak = 0
                        end
                        task.wait(0.4)
                    else
                        emptyStreak = 0
                        local result = (function()
                            local belowPos = coin.Position + Vector3.new(0, travelDepth, 0)
                            local cancel = { cancelled = false, done = false }

                            task.spawn(function()
                                local previousDistances = {}
                                while not cancel.done do
                                    task.wait(0.15)
                                    if cancel.done then return end
                                    if not coin.Parent or isTouched(coin) then
                                        cancel.cancelled = true
                                        return
                                    end

                                    local now = tick()
                                    local approaching = 0
                                    local nearby = 0
                                    for _, player in ipairs(Players:GetPlayers()) do
                                        if player ~= LocalPlayer and player.Character then
                                            local hum = player.Character:FindFirstChildOfClass("Humanoid")
                                            local root = player.Character:FindFirstChild("HumanoidRootPart")
                                            if hum and hum.Health > 0 and root then
                                                local distance = horizontalDistance(root.Position, coin.Position)
                                                if distance <= 7 then
                                                    nearby = nearby + 1
                                                end
                                                local previous = previousDistances[player]
                                                if previous and now - previous.time <= 0.8
                                                   and previous.distance - distance >= 0.65 and distance <= 32 then
                                                    approaching = approaching + 1
                                                end
                                                previousDistances[player] = { distance = distance, time = now }
                                            else
                                                previousDistances[player] = nil
                                            end
                                        else
                                            previousDistances[player] = nil
                                        end
                                    end

                                    if approaching >= 2 or nearby >= 2 then
                                        crowdedCoinUntil[coin] = now + 5
                                        cancel.crowded = true
                                        cancel.cancelled = true
                                        return
                                    end
                                end
                            end)

                            local ok2
                            do
                                local char2 = ch
                                activePathTarget = belowPos
                                prepareTeleport()
                                setCollision(char2, false)
                                local t0 = tick()
                                local startPos = char2:GetPivot().Position
                                local horizDist = Vector3.new(belowPos.X - startPos.X, 0, belowPos.Z - startPos.Z).Magnitude
                                local verticalDistance = math.abs(belowPos.Y - startPos.Y)
                                local speed = baseSpeed * math.max(State.speed, 0.1)
                                if horizDist <= verticalPenaltyHorizontalMax and verticalDistance >= verticalPenaltyMinY then
                                    speed = speed * verticalPenaltyMultiplier
                                end
                                ok2 = false
                                while tick() - t0 < 12 do
                                    if not State.enabled then break end
                                    if not char2.Parent then break end
                                    if cancel and cancel.cancelled then break end
                                    local cur = char2:GetPivot().Position
                                    local delta = belowPos - cur
                                    local dist = delta.Magnitude
                                    if dist <= 0.25 then
                                        setPinned(cur)
                                        ok2 = true
                                        break
                                    end
                                    local dt = RunService.Heartbeat:Wait()
                                    dt = math.min(dt, 1/60)
                                    local step = math.min(dist, speed * dt)
                                    if step > 0.01 then
                                        local np = cur + delta.Unit * step
                                        writeCF(layCF(np))
                                        setPinned(np)
                                    end
                                end
                                setCollision(char2, true)
                                activePathTarget = nil
                            end

                            cancel.done = true
                            if cancel.crowded then
                                afDebug("grab: multiple players converging on coin - retargeting")
                                return "crowded"
                            end
                            if cancel.cancelled then
                                afDebug("grab: coin vanished mid-travel - retargeting")
                                return "retarget"
                            end
                            if not ok2 then
                                afDebug("grab: travel failed - skipping target")
                                return false
                            end
                            if not coin.Parent or isTouched(coin) then return true end

                            do
                                local char2 = ch
                                prepareTeleport()
                                setCollision(char2, false)

                                local root = char2:FindFirstChild("HumanoidRootPart")
                                if root and (root.Position - belowPos).Magnitude <= 4 then
                                    if hasFTI and coin and coin.Parent then
                                        local root2 = getHRP()
                                        if root2 then
                                            pcall(function()
                                                firetouchinterest(root2, coin, 0)
                                                firetouchinterest(root2, coin, 1)
                                            end)
                                        end
                                    end
                                end

                                RunService.Heartbeat:Wait()
                                local collected = (not coin.Parent) or isTouched(coin)
                                setCollision(char2, true)
                                return collected
                            end
                        end)()

                        if result == "crowded" then
                            State.activeCluster = nil
                            nextPickStrategy = "nearest"
                        elseif result == "retarget" then
                            nextPickStrategy = "second-furthest"
                        elseif not coin.Parent or isTouched(coin) then
                            coinFails[coin] = nil
                            markTouched(coin)
                        elseif result then
                            coinFails[coin] = nil
                        else
                            coinFails[coin] = nil
                            afDebug("skipping coin after one attempt", coin.Name)
                            markTouched(coin)
                        end
                    end
                end

                stopStabilize()
                return "stopped"
            end)

            if not ok then
                afDebug("error: "..tostring(status))
                status = nil
            end
            if State.enabled then
                if status == "no-role" or status == "waiting" or status == "no-map"
                   or status == "no-coins" or status == "respawn" then
                    backoff = math.min(backoff * 1.4, 5)
                else
                    backoff = 0.5
                end
                task.wait(backoff)
            end
        end
        restoreHumanoid()
        stopStabilize()
        stopWatchdog()
        anchorHRP(false)
        State.hasGoneUnder = false
        State.waiting = false
        State.activeCluster = nil
    end)
end

local cameraRoundActive = false
task.spawn(function()
    while true do
        task.wait(0.5)
        local roundIsActive = State.enabled and getRoundState() == "active"
        if roundIsActive and not cameraRoundActive then
            if not cameraConn then
                local cam = Workspace.CurrentCamera
                if cam then
                    savedCameraType = cam.CameraType
                    cam.CameraType = Enum.CameraType.Scriptable

                    local hrp = getHRP()
                    if hrp then
                        local off = cam.CFrame.Position - hrp.Position
                        if off.Magnitude > 0.1 and off.Magnitude < 100 then
                            cameraOffset = off
                        end
                    end

                    cameraConn = RunService.RenderStepped:Connect(function(dt)
                        local currentCam = Workspace.CurrentCamera
                        if not currentCam then return end
                        if currentCam.CameraType ~= Enum.CameraType.Scriptable then
                            currentCam.CameraType = Enum.CameraType.Scriptable
                        end
                        -- skip follow while flinging
                        if getgenv().flingActive then return end

                        local hrp2 = getHRP()
                        if not hrp2 then return end

                        local basePos = hrp2.Position
                        if State.waiting and State.hasGoneUnder then
                            -- keep the camera above ground so the user isn't staring at the inside of the map
                            basePos = basePos + Vector3.new(0, waitDownDistance, 0)
                        end
                        local targetPos = basePos + cameraOffset
                        local cur = currentCam.CFrame
                        local newPos
                        if (cur.Position - targetPos).Magnitude > 500 then
                            newPos = targetPos
                        else
                            newPos = cur.Position:Lerp(targetPos, math.clamp(dt * 10, 0, 1))
                        end
                        currentCam.CFrame = CFrame.lookAt(newPos, newPos + cur.LookVector)
                    end)
                end
            end
        elseif not roundIsActive and cameraRoundActive then
            stopCameraLock()
            cameraOffset = Vector3.new(0, 5, 12)
        end
        cameraRoundActive = roundIsActive
    end
end)

task.spawn(function()
    while true do
        task.wait(1)
        if State.enabled and State.longevity then
            local gun = Workspace:FindFirstChild("GunDrop", true)
            if gun and hasFTI then
                local r = getHRP()
                if r then
                    pcall(function()
                        firetouchinterest(r, gun, 0)
                        firetouchinterest(r, gun, 1)
                    end)
                end
            end
        end
    end
end)

LocalPlayer.CharacterAdded:Connect(function()
    task.wait(0.5)
    if State.enabled then
        boundContainer = nil
        collectedCount = 0
        coinFails = {}
        savedHumanoid = nil
        hrpWasAnchored = nil
        State.hasGoneUnder = false
        State.waiting = false
        State.activeCluster = nil
        stopWatchdog()
    end
end)

local GuiService      = game:GetService("GuiService")
local TeleportService = game:GetService("TeleportService")
local ServerHttpService = game:GetService("HttpService")

local rejoinScriptUrl = "https://aptfxx.dev/scripts/verdant/main"
getgenv().AutoRejoin = true

if getgenv().AutoRejoinCleanup then
    pcall(getgenv().AutoRejoinCleanup)
    getgenv().AutoRejoinCleanup = nil
end

local autoRejoinTeleportConn = nil
local autoRejoinErrorConn = nil
local teleportFailedConn = nil
local errorLogConn = nil
local queuedThisTeleport = false
local rejoinInProgress = false
local pendingDestinationId = nil
local pendingHopMinPlayers = 4
local unavailableServerIds = {}
local teleportRetryScheduled = false
local lastLoggedError = nil

local function queueRejoinScript()
    if queuedThisTeleport then return false end
    queuedThisTeleport = true
    task.delay(5, function() queuedThisTeleport = false end)

    local qot = queue_on_teleport
        or (syn and syn.queue_on_teleport)
        or (fluxus and fluxus.queue_on_teleport)
    if not qot then return false end
    local ok = pcall(function()
        qot(string.format('loadstring(game:HttpGet("%s"))()', rejoinScriptUrl))
    end)
    return ok
end

local function attemptServerHop(minPlayers, reason)
    if rejoinInProgress then return false end
    rejoinInProgress = true
    local currentJobId = game.JobId
    minPlayers = tonumber(minPlayers) or 4
    reason = tostring(reason or "rejoin requested")
    warn("[Verdant]: " .. reason .. ", searching for another public server")

    task.spawn(function()
        local function fetchServerPage(url)
            local lastError = "request failed"
            local requestFn = (syn and syn.request) or (http and http.request) or http_request or request or (fluxus and fluxus.request)

            local function decodeResponse(responseText, status)
                if type(responseText) ~= "string" or responseText:match("^%s*$") then
                    return nil, "empty response body" .. (status and " (HTTP " .. tostring(status) .. ")" or "")
                end
                if status and (status < 200 or status >= 300) then
                    return nil, "HTTP " .. tostring(status) .. ": " .. responseText:gsub("%s+", " "):sub(1, 100)
                end
                local decodeOk, decoded = pcall(function()
                    return ServerHttpService:JSONDecode(responseText)
                end)
                if decodeOk and type(decoded) == "table" and type(decoded.data) == "table" then
                    return decoded
                end
                return nil, "invalid JSON response: " .. responseText:gsub("%s+", " "):sub(1, 100)
            end

            if type(requestFn) == "function" then
                local ok, response = pcall(function()
                    return requestFn({
                        Url = url,
                        Method = "GET",
                        Headers = { Accept = "application/json", ["Cache-Control"] = "no-cache" }
                    })
                end)
                if ok and type(response) == "table" then
                    local status = tonumber(response.StatusCode or response.Status)
                    local decoded, decodeError = decodeResponse(response.Body or response.body, status)
                    if decoded then return decoded end
                    lastError = decodeError or lastError
                elseif ok and type(response) == "string" then
                    local decoded, decodeError = decodeResponse(response, nil)
                    if decoded then return decoded end
                    lastError = decodeError or lastError
                elseif not ok then
                    lastError = tostring(response)
                end
            end

            local ok, responseText = pcall(function()
                return game:HttpGet(url)
            end)
            if ok then
                local decoded, decodeError = decodeResponse(responseText, nil)
                if decoded then return decoded end
                if decodeError and decodeError ~= "empty response body" then
                    lastError = decodeError
                elseif decodeError and lastError == "request failed" then
                    lastError = decodeError
                end
            else
                lastError = tostring(responseText)
            end

            return nil, lastError
        end

        local activeEndpoint = 1
        local endpointTemplates = {
            "https://games.roblox.com/v1/games/%s/servers/Public?sortOrder=%s&limit=50&excludeFullGames=true",
            "https://games.roblox.com/v1/public-server-browser-service/games/%s/servers/Public?sortOrder=%s&limit=50&excludeFullGames=true"
        }
        local servers = nil
        local lastRequestError = "no eligible servers returned"
        local gotAnyServerList = false
        local maxScanAttempts = 5

        for scanAttempt = 1, maxScanAttempts do
            local scanServers = {}
            local cursor = nil
            local pagesChecked = 0
            local scanFailed = false
            local sortOrder = scanAttempt % 2 == 1 and "Asc" or "Desc"

            while pagesChecked < 3 do
                local body, requestError
                for retry = 1, 2 do
                    local endpointOrder = { activeEndpoint, activeEndpoint == 1 and 2 or 1 }
                    for _, endpointIndex in ipairs(endpointOrder) do
                        local url = string.format(endpointTemplates[endpointIndex], tostring(game.PlaceId), sortOrder)
                        if cursor and cursor ~= "" then
                            url = url .. "&cursor=" .. ServerHttpService:UrlEncode(cursor)
                        end
                        body, requestError = fetchServerPage(url)
                        if body then
                            activeEndpoint = endpointIndex
                            gotAnyServerList = true
                            break
                        end
                    end
                    if body then break end
                    lastRequestError = tostring(requestError or "request failed")
                    if retry < 2 then task.wait(2) end
                end

                if not body then
                    scanFailed = true
                    break
                end

                for _, server in ipairs(body.data) do
                    local playing = type(server) == "table" and tonumber(server.playing) or nil
                    local maxPlayers = type(server) == "table" and tonumber(server.maxPlayers) or nil
                    local serverId = type(server) == "table" and server.id or nil
                    local unavailableUntil = type(serverId) == "string" and unavailableServerIds[serverId] or nil
                    if unavailableUntil and unavailableUntil <= tick() then
                        unavailableServerIds[serverId] = nil
                        unavailableUntil = nil
                    end
                    if type(server) == "table" and type(serverId) == "string"
                        and serverId ~= currentJobId and not unavailableUntil and playing and maxPlayers
                        and playing >= minPlayers and playing < maxPlayers then
                        table.insert(scanServers, server)
                    end
                end

                pagesChecked = pagesChecked + 1
                cursor = body.nextPageCursor
                if not cursor or cursor == "" then break end
                if #scanServers >= 40 then break end
            end

            if #scanServers > 0 then
                servers = scanServers
                break
            end

            if scanAttempt < maxScanAttempts then
                if scanFailed then
                    warn("[Verdant]: Server list request failed (scan " .. tostring(scanAttempt) .. "/" .. tostring(maxScanAttempts) .. "): " .. lastRequestError .. "; retrying")
                else
                    warn("[Verdant]: No eligible server found (attempt " .. tostring(scanAttempt) .. "/" .. tostring(maxScanAttempts) .. "); retrying in 3 seconds")
                end
                task.wait(3)
            end
        end

        if not servers or #servers == 0 then
            if not gotAnyServerList then
                warn("[Verdant]: Server list request failed after " .. tostring(maxScanAttempts) .. " attempts: " .. lastRequestError)
            else
                warn("[Verdant]: Could not find another public server with at least " .. tostring(minPlayers) .. " players after " .. tostring(maxScanAttempts) .. " scans.")
            end
            rejoinInProgress = false
            return
        end

        table.sort(servers, function(a, b)
            local pingA = tonumber(a.ping)
            local pingB = tonumber(b.ping)
            local validPingA = pingA ~= nil and pingA > 0
            local validPingB = pingB ~= nil and pingB > 0
            if validPingA ~= validPingB then
                return validPingA
            end
            if validPingA and validPingB and pingA ~= pingB then
                return pingA < pingB
            end
            local playersA = tonumber(a.playing) or math.huge
            local playersB = tonumber(b.playing) or math.huge
            if playersA ~= playersB then
                return playersA < playersB
            end
            return (tonumber(a.maxPlayers) or math.huge) > (tonumber(b.maxPlayers) or math.huge)
        end)

        local bestCount = math.min(8, #servers)
        local destination = servers[math.random(1, bestCount)]
        pendingDestinationId = destination.id
        pendingHopMinPlayers = minPlayers
        queueRejoinScript()

        local ok, err = pcall(function()
            TeleportService:TeleportToPlaceInstance(game.PlaceId, destination.id, LocalPlayer)
        end)
        if not ok then
            unavailableServerIds[destination.id] = tick() + 600
            pendingDestinationId = nil
            warn("[Verdant]: Server hop failed: " .. tostring(err) .. ". retrying ")
            rejoinInProgress = false
            if not teleportRetryScheduled then
                teleportRetryScheduled = true
                task.delay(2, function()
                    teleportRetryScheduled = false
                    if LocalPlayer.Parent and not rejoinInProgress then
                        attemptServerHop(minPlayers, "Retrying after teleport error")
                    end
                end)
            end
            return
        end

        task.delay(30, function()
            if LocalPlayer.Parent and game.JobId == currentJobId then
                rejoinInProgress = false
            end
        end)
    end)
    return true
end

local preferredMapNames = {
    ["Hospital 3"] = true,
    ["House 2"] = true,
    ["Mansion 2"] = true,
    ["Office 3"] = true,
    ["Workplace"] = true,
}
local mapVoteLoopRunning = false
local mapVoteAttempts = 0
local mapVotesPerLobbyLimit = 10

local function isStillInLobby()
    if not (
        MiscSettings.voteForBestMap
        and Workspace:FindFirstChild("Lobby")
        and getRoundState() == "lobby"
    ) then
        return false
    end

    local votePads = Workspace.Lobby:FindFirstChild("VotePads")
    if not votePads then return false end

    for _, votePad in ipairs(votePads:GetChildren()) do
        local voteInfoGui = votePad:FindFirstChild("VoteInfoGui")

        if voteInfoGui and voteInfoGui.Enabled then
            return true
        end
    end

    return false
end

local function startBestMapVoting()
    if mapVoteLoopRunning then return end
    mapVoteLoopRunning = true

    local function getTotalVisibleMapVotesInline()
        local lobby = Workspace:FindFirstChild("Lobby")
        local votePads = lobby and lobby:FindFirstChild("VotePads")
        if not votePads then return 0 end

        local total = 0
        for index = 1, 3 do
            local votePad = votePads:FindFirstChild("VotePad" .. tostring(index))
            local highest = 0
            if votePad then
                for _, object in ipairs(votePad:GetDescendants()) do
                    if object:IsA("TextLabel") or object:IsA("TextButton") then
                        local name = tostring(object.Name):lower()
                        if (name:find("vote", 1, true) or name:find("count", 1, true))
                            and not name:find("mapname", 1, true) then
                            local count = tonumber(tostring(object.Text or ""):match("(%d+)"))
                            if count then highest = math.max(highest, count) end
                        end
                    end
                end
            end
            total = total + highest
        end
        return total
    end

    task.spawn(function()
        local wasInLobby = false
        local pausedForLobby = false
        while MiscSettings.voteForBestMap do
            if not isStillInLobby() then
                if wasInLobby then
                    mapVoteAttempts = 0
                    pausedForLobby = false
                end
                wasInLobby = false
                task.wait(1)
            else
                wasInLobby = true
                if not pausedForLobby and (mapVoteAttempts >= mapVotesPerLobbyLimit
                    or getTotalVisibleMapVotesInline() >= mapVotesPerLobbyLimit) then
                    pausedForLobby = true
                end
                if pausedForLobby then
                    task.wait(0.5)
                else
                    if isStillInLobby() then
                        local choice
                        do
                            local lobby = Workspace:FindFirstChild("Lobby")
                            local votePads = lobby and lobby:FindFirstChild("VotePads")
                            if votePads then
                                local candidates = {}
                                for index = 1, 3 do
                                    local votePad = votePads:FindFirstChild("VotePad" .. tostring(index))
                                    local gui = votePad and votePad:FindFirstChild("VoteInfoGui", true)
                                    local container = gui and gui:FindFirstChild("Container", true)
                                    local mapLabel = container and container:FindFirstChild("MapName", true)
                                    local pad = votePad and votePad:FindFirstChild("Pad")
                                    local mapName = mapLabel and tostring(mapLabel.Text):gsub("^%s*(.-)%s*$", "%1") or ""
                                    if pad and preferredMapNames[mapName] then
                                        table.insert(candidates, { votePad = votePad, pad = pad, mapName = mapName })
                                    end
                                end
                                if #candidates > 0 then
                                    choice = candidates[math.random(1, #candidates)]
                                end
                            end
                        end

                        local character = LocalPlayer.Character
                        local humanoid = character and character:FindFirstChildOfClass("Humanoid")
                        local root = character and character:FindFirstChild("HumanoidRootPart")

                        if choice and choice.pad and choice.pad:IsA("BasePart") and character and humanoid and root and humanoid.Health > 0 then
                            local oldCharacter = character
                            local pad = choice.pad
                            local targetCFrame = pad.CFrame + Vector3.new(0, pad.Size.Y * 0.5 + 2, 0)
                            pcall(function() character:PivotTo(targetCFrame) end)
                            task.wait(0.25)

                            if isStillInLobby() then
                                if type(firetouchinterest) == "function" and root.Parent and pad.Parent then
                                    pcall(function()
                                        firetouchinterest(root, pad, 0)
                                        firetouchinterest(root, pad, 1)
                                    end)
                                end
                                mapVoteAttempts = mapVoteAttempts + 1

                                task.wait(0.35)
                                if isStillInLobby() and humanoid.Health > 0 then
                                    humanoid.Health = 0
                                end

                                local respawnStart = tick()
                                while isStillInLobby() and LocalPlayer.Character == oldCharacter and tick() - respawnStart < 10 do
                                    task.wait(0.1)
                                end
                                task.wait(0.5)
                            end
                        else
                            task.wait(1)
                        end
                    end
                end
            end
        end
        mapVoteLoopRunning = false
    end)
end

local function startAutoRejoin()
    if autoRejoinTeleportConn then return end

    autoRejoinTeleportConn = LocalPlayer.OnTeleport:Connect(function()
        if getgenv().AutoRejoin then
            queueRejoinScript()
        end
    end)

    autoRejoinErrorConn = GuiService.ErrorMessageChanged:Connect(function(msg)
        if not getgenv().AutoRejoin or not msg or msg == "" then return end
        attemptServerHop(4, "Roblox error: " .. tostring(msg))
    end)

    teleportFailedConn = TeleportService.TeleportInitFailed:Connect(function(player, result, errorMessage, placeId)
        if player ~= LocalPlayer or placeId ~= game.PlaceId or not pendingDestinationId then return end
        local failedServerId = pendingDestinationId
        unavailableServerIds[failedServerId] = tick() + 600
        pendingDestinationId = nil
        rejoinInProgress = false
        local resultName = result and result.Name or tostring(result)
        warn("[Verdant]: Teleport failed (" .. tostring(resultName) .. "): " .. tostring(errorMessage) .. "; trying another server")
        if not teleportRetryScheduled then
            teleportRetryScheduled = true
            task.delay(2, function()
                teleportRetryScheduled = false
                if LocalPlayer.Parent and not rejoinInProgress then
                    attemptServerHop(pendingHopMinPlayers, "Retrying after teleport failure")
                end
            end)
        end
    end)
end

local function stopAutoRejoin()
    if autoRejoinTeleportConn then
        pcall(function() autoRejoinTeleportConn:Disconnect() end)
        autoRejoinTeleportConn = nil
    end
    if autoRejoinErrorConn then
        pcall(function() autoRejoinErrorConn:Disconnect() end)
        autoRejoinErrorConn = nil
    end
    if teleportFailedConn then
        pcall(function() teleportFailedConn:Disconnect() end)
        teleportFailedConn = nil
    end
    queuedThisTeleport = false
end

getgenv().AutoRejoinCleanup = stopAutoRejoin

if getgenv().AutoRejoin then
    startAutoRejoin()
end

errorLogConn = GuiService.ErrorMessageChanged:Connect(function(msg)
    if type(msg) ~= "string" or msg == "" then
        lastLoggedError = nil
        return
    end
    if msg == lastLoggedError then return end
    lastLoggedError = msg
    local reasonText = msg
    if msg:lower():find("invalid position", 1, true) then
        reasonText = reasonText .. " (don't worry, this is normal every now and again)"
    end
    print(string.format("[Verdant]: Kicked for %s", reasonText))
end)

local outfitPriceCache = {}
local freeAvatarCheckInterval = 300
local nextFreeAvatarCheckAt = tick()

task.spawn(function()
    while true do
        task.wait(1)
        local enabled = MiscSettings.autoHopBotDetection and MiscSettings.autoHopFreeOutfitLobby
        if not enabled then
            nextFreeAvatarCheckAt = nil
        elseif not nextFreeAvatarCheckAt then
            nextFreeAvatarCheckAt = tick() + freeAvatarCheckInterval
        elseif tick() >= nextFreeAvatarCheckAt then
            nextFreeAvatarCheckAt = tick() + freeAvatarCheckInterval

            local flagged, flaggedCount, total, ratio
            do
                local players = Players:GetPlayers()
                local totalCount = #players
                if totalCount == 0 then
                    warn("[Verdant]: Avatar checker found no players.")
                    flagged, flaggedCount, total, ratio = nil, 0, 0, 0
                else
                    local flaggedCountLocal = 0
                    local aborted = false
                    for _, player in ipairs(players) do
                        if not MiscSettings.autoHopBotDetection or not MiscSettings.autoHopFreeOutfitLobby then
                            flagged, flaggedCount, total, ratio = nil, flaggedCountLocal, totalCount, 0
                            aborted = true
                            break
                        end

                        local isFlagged = false
                        do
                            local success, appearanceInfo = pcall(function()
                                return Players:GetCharacterAppearanceInfoAsync(player.UserId)
                            end)
                            if success and type(appearanceInfo) == "table" then
                                local assets = appearanceInfo.assets
                                if type(assets) ~= "table" or #assets == 0 then
                                    isFlagged = true
                                else
                                    local totalPrice = 0
                                    for _, asset in ipairs(assets) do
                                        if type(asset) == "table" then
                                            local assetTypeName
                                            do
                                                local assetType = asset.assetType
                                                if assetType ~= nil then
                                                    if type(assetType) == "string" then
                                                        assetTypeName = assetType
                                                    else
                                                        local ok, name = pcall(function() return assetType.Name end)
                                                        if ok and type(name) == "string" then assetTypeName = name end
                                                    end
                                                end
                                            end
                                            local ignored = assetTypeName ~= nil and assetTypeName:match("^TShirt") ~= nil
                                            if not ignored then
                                                local assetId = tonumber(asset.id)
                                                local price = 0
                                                if assetId and assetId ~= 0 then
                                                    if outfitPriceCache[assetId] ~= nil then
                                                        price = outfitPriceCache[assetId]
                                                    else
                                                        local ok2, productInfo = pcall(function()
                                                            return MarketplaceService:GetProductInfo(assetId, Enum.InfoType.Asset)
                                                        end)
                                                        if ok2 and type(productInfo) == "table" then
                                                            if productInfo.IsPublicDomain then
                                                                price = 0
                                                            else
                                                                price = tonumber(productInfo.PriceInRobux) or 0
                                                            end
                                                        end
                                                        outfitPriceCache[assetId] = price
                                                    end
                                                end
                                                totalPrice = totalPrice + price
                                            end
                                        end
                                    end
                                    isFlagged = totalPrice < 30
                                end
                            end
                        end

                        if isFlagged then flaggedCountLocal = flaggedCountLocal + 1 end
                        task.wait(0.1)
                    end

                    if not aborted then
                        local ratioLocal = flaggedCountLocal / totalCount
                        flagged, flaggedCount, total, ratio = ratioLocal > 0.6, flaggedCountLocal, totalCount, ratioLocal
                    end
                end
            end

            if flagged ~= nil then
                if flagged and MiscSettings.autoHopBotDetection and MiscSettings.autoHopFreeOutfitLobby then
                    attemptServerHop(4, string.format(
                        "more than 60%% of avatars have counted outfit cost below 30 Robux (%d/%d, %.0f%%)",
                        flaggedCount, total, ratio * 100
                    ))
                end
            end
            if MiscSettings.autoHopBotDetection and MiscSettings.autoHopFreeOutfitLobby then
                nextFreeAvatarCheckAt = tick() + freeAvatarCheckInterval
            else
                nextFreeAvatarCheckAt = nil
            end
        end
    end
end)

local flaggedHatAssetId = 417457461
local flaggedHatCache = setmetatable({}, { __mode = "k" })

task.spawn(function()
    while true do
        task.wait(10)
        if MiscSettings.autoHopBotDetection and MiscSettings.autoHopFlaggedHat then
            for _, player in ipairs(Players:GetPlayers()) do
                if player ~= LocalPlayer then
                    local hit = false
                    do
                        local character = player.Character
                        if character then
                            local cached = flaggedHatCache[character]
                            if cached ~= nil then
                                hit = cached
                            else
                                local humanoid = character:FindFirstChildOfClass("Humanoid")
                                if humanoid then
                                    local descriptionOk, description = pcall(function()
                                        return humanoid:GetAppliedDescription()
                                    end)
                                    if descriptionOk and description then
                                        local accessoriesOk, accessories = pcall(function()
                                            return description:GetAccessories(true)
                                        end)
                                        if accessoriesOk and type(accessories) == "table" then
                                            for _, accessory in ipairs(accessories) do
                                                if type(accessory) == "table"
                                                    and tonumber(accessory.AssetId or accessory.assetId) == flaggedHatAssetId then
                                                    flaggedHatCache[character] = true
                                                    hit = true
                                                    break
                                                end
                                            end
                                            if not hit then flaggedHatCache[character] = false end
                                        end
                                    end
                                end
                            end
                        end
                    end
                    if hit then
                        attemptServerHop(4, "flagged hat asset " .. tostring(flaggedHatAssetId) .. " detected on " .. player.Name)
                        break
                    end
                end
            end
        end
    end
end)

task.spawn(function()
    local noRoundSeconds = 0
    while true do
        task.wait(1)
        if not MiscSettings.autoHopNoRound then
            noRoundSeconds = 0
        else
            local anyKnife = false
            for _, player in ipairs(Players:GetPlayers()) do
                if toolHeld(player, "Knife") then anyKnife = true; break end
            end
            if anyKnife then
                noRoundSeconds = 0
            else
                noRoundSeconds = noRoundSeconds + 1
                if noRoundSeconds >= 180 then
                    attemptServerHop(4, "no round started for 3 minutes")
                    noRoundSeconds = 0
                end
            end
        end
    end
end)

task.spawn(function()
    while true do
        task.wait(10)
        if MiscSettings.autoHopLowPlayers and #Players:GetPlayers() < 4 then
            attemptServerHop(4, "server population below 4")
        end
    end
end)

task.spawn(function()
    local activeSeconds = 0
    local baseline = Session.coinsCollected
    local prevEnabled = State.enabled
    while true do
        task.wait(1)
        if State.enabled ~= prevEnabled then
            activeSeconds = 0
            baseline = Session.coinsCollected
            prevEnabled = State.enabled
        end
        if not State.enabled or not MiscSettings.autoHopNoCoins then
            activeSeconds = 0
            baseline = Session.coinsCollected
        else
            if Session.coinsCollected > baseline then
                baseline = Session.coinsCollected
                activeSeconds = 0
            end
            if getRoundState() == "active" then
                activeSeconds = activeSeconds + 1
            else
                activeSeconds = 0
                baseline = Session.coinsCollected
            end
            if activeSeconds >= 240 then
                attemptServerHop(4, "no coins collected for 4 minutes")
                activeSeconds = 0
                baseline = Session.coinsCollected
            end
        end
    end
end)

local farmerMovementSamples = {}
local crowdedFarmerChecks = 0
local localMovementSample = nil

task.spawn(function()
    while true do
        task.wait(5)
        if not MiscSettings.autoHopBotDetection or not MiscSettings.autoHopCrowdedFarmers then
            farmerMovementSamples = {}
            crowdedFarmerChecks = 0
            localMovementSample = nil
        else
            local now = tick()
            local present = {}
            local suspectedFarmers = 0
            local referenceSpeed = baseSpeed * math.clamp(State.speed, 0.1, 1.7)
            local myRoot = getHRP()

            if myRoot then
                if localMovementSample then
                    local elapsed = now - localMovementSample.time
                    if elapsed >= 3 and elapsed <= 10 then
                        local measuredSpeed = (myRoot.Position - localMovementSample.position).Magnitude / elapsed
                        if measuredSpeed >= 3 and measuredSpeed <= baseSpeed * 1.7 * 1.5 then
                            referenceSpeed = measuredSpeed
                        end
                    end
                end
                localMovementSample = { position = myRoot.Position, time = now }
            end

            local function routePassesCoinClusterInline(fromPos, toPos)
                local dx = toPos.X - fromPos.X
                local dz = toPos.Z - fromPos.Z
                local lengthSquared = dx * dx + dz * dz
                if lengthSquared < 1 then return false end

                local matches = 0
                for _, coin in ipairs(coins) do
                    if coin and coin.Parent and coinSet[coin] then
                        local pos = coin.Position
                        local t = math.clamp(((pos.X - fromPos.X) * dx + (pos.Z - fromPos.Z) * dz) / lengthSquared, 0, 1)
                        local nearX = fromPos.X + dx * t
                        local nearZ = fromPos.Z + dz * t
                        local nearY = fromPos.Y + (toPos.Y - fromPos.Y) * t
                        local horizontal = math.sqrt((pos.X - nearX) ^ 2 + (pos.Z - nearZ) ^ 2)
                        if horizontal <= 7 and math.abs(pos.Y - nearY) <= 9 then
                            matches = matches + 1
                            if matches >= 2 then return true end
                        end
                    end
                end
                return false
            end

            for _, player in ipairs(Players:GetPlayers()) do
                if player ~= LocalPlayer and player.Character then
                    local root = player.Character:FindFirstChild("HumanoidRootPart")
                    local hum = player.Character:FindFirstChildOfClass("Humanoid")
                    if root and hum and hum.Health > 0 then
                        local id = player.UserId
                        present[id] = true
                        local sample = farmerMovementSamples[id]
                        if not sample then
                            farmerMovementSamples[id] = {
                                position = root.Position,
                                time = now,
                                routeStreak = 0,
                            }
                        else
                            local elapsed = math.max(now - sample.time, 0.1)
                            local moved = (root.Position - sample.position).Magnitude
                            local estimatedSpeed = moved / elapsed
                            local speedSimilar = estimatedSpeed >= 3
                                and math.abs(estimatedSpeed - referenceSpeed) <= math.max(3, referenceSpeed * 0.4)
                            local followsCoinCluster = moved >= 12
                                and routePassesCoinClusterInline(sample.position, root.Position)

                            if not hum.Sit and speedSimilar and followsCoinCluster then
                                sample.routeStreak = math.min(sample.routeStreak + 1, 6)
                            else
                                sample.routeStreak = math.max(sample.routeStreak - 1, 0)
                            end

                            sample.position = root.Position
                            sample.time = now
                            if sample.routeStreak >= 3 then
                                suspectedFarmers = suspectedFarmers + 1
                            end
                        end
                    end
                end
            end

            for id in pairs(farmerMovementSamples) do
                if not present[id] then farmerMovementSamples[id] = nil end
            end

            if suspectedFarmers >= 3 then
                crowdedFarmerChecks = crowdedFarmerChecks + 1
            else
                crowdedFarmerChecks = 0
            end
            if crowdedFarmerChecks >= 2 then
                attemptServerHop(4, "several likely autofarmers detected (" .. tostring(suspectedFarmers) .. ")")
                crowdedFarmerChecks = 0
            end
        end
    end
end)

-- This is Discord config. The only part that isnt open source about this is the actual server.
-- This is off by default.

local HttpService = game:GetService("HttpService")
local remoteUrl = "https://api.nuclei.fyi" -- seperate url from aptfxx.dev i use for APIs

local remoteState = {
    execId = nil,
    encryptedKey = nil,
    sessionCode = nil,
    connected = false,
    allowStats = true,
    allowFarmControl = false,
    allowCodeExecution = false
}

local remoteConfigFile = "Verdant/remote.json"

if isfile and isfile(remoteConfigFile) then
    local ok, data = pcall(function() return HttpService:JSONDecode(readfile(remoteConfigFile)) end)
    if ok and data then
        remoteState.execId = data.execId
        remoteState.encryptedKey = data.encryptedKey
        remoteState.sessionCode = data.sessionCode
        remoteState.allowStats = data.allowStats ~= false
        remoteState.allowFarmControl = data.allowFarmControl == true
        remoteState.allowCodeExecution = data.allowCodeExecution == true
    end
end

local function saveRemoteConfig()
    if not writefile then return end
    local data = {
        execId = remoteState.execId,
        encryptedKey = remoteState.encryptedKey,
        sessionCode = remoteState.sessionCode,
        allowStats = remoteState.allowStats,
        allowFarmControl = remoteState.allowFarmControl,
        allowCodeExecution = remoteState.allowCodeExecution
    }
    pcall(writefile, remoteConfigFile, HttpService:JSONEncode(data))
end

-- HTTP helper 
local function httpReq(method, url, body)
    local req = syn and syn.request or http and http.request or http_request or request
    if not req then return nil end
    local opts = { Url = url, Method = method }
    if body then
        opts.Body = HttpService:JSONEncode(body)
        opts.Headers = { ["Content-Type"] = "application/json" }
    end
    local ok, res = pcall(req, opts)
    if ok and res and (res.StatusCode == 200 or res.StatusCode == 201) then
        local decOk, dec = pcall(HttpService.JSONDecode, HttpService, res.Body)
        return decOk and dec or nil
    end
    return nil
end

task.spawn(function()
    while true do
        task.wait(2)
        if remoteState.execId and remoteState.encryptedKey then
            local url = string.format("%s/poll?execId=%s&key=%s", remoteUrl, remoteState.execId, remoteState.encryptedKey)
            local data = httpReq("GET", url)
            
            if data and data.commands then
                remoteState.connected = true
                for _, cmd in ipairs(data.commands) do
                    local result = { ok = false, message = "Unknown command" }
                    
                    if cmd.command == "get_status" then
                        if not remoteState.allowStats then
                            result = { ok = false, message = "Blocked: Stats disabled by client permissions." }
                        else
                            result = { ok = true, data = {
                                enabled = State.enabled,
                                sessionCoins = Session.coinsCollected,
                                uptime = math.floor(tick() - Session.startTime),
                                playerCount = #Players:GetPlayers(),
                                role = getMyRole() or "none"
                            }}
                        end
                    elseif cmd.command == "toggle_farm" then
                        if not remoteState.allowFarmControl then
                            result = { ok = false, message = "Blocked: Farm control disabled by client permissions." }
                        else
                            if State.enabled then stopFarm() else startFarm() end
                            result = { ok = true, message = "Farm toggled." }
                        end
                    elseif cmd.command == "reset_farm" then
                        if not remoteState.allowFarmControl then
                            result = { ok = false, message = "Blocked: Farm control disabled by client permissions." }
                        else
                            stopFarm()
                            startFarm()
                            result = { ok = true, message = "Farm reset." }
                        end
                    elseif cmd.command == "execute_code" then
                        if not remoteState.allowCodeExecution then
                            result = { ok = false, message = "Blocked: Code execution is disabled on this client!" }
                        else
                            local func, err = loadstring(cmd.args.code)
                            if func then
                                local success, ret = pcall(func)
                                result = { ok = success, message = success and "Code executed successfully." or tostring(ret) }
                            else
                                result = { ok = false, message = "Compile error: " .. tostring(err) }
                            end
                        end
                    end
                    
                    httpReq("POST", string.format("%s/result?execId=%s&key=%s", remoteUrl, remoteState.execId, remoteState.encryptedKey), {
                        commandId = cmd.id,
                        result = result
                    })
                end
            else
                remoteState.connected = false
            end
        else
            remoteState.connected = false
        end
    end
end)


--[[

UI lies beyond this point

]]






local Verdant = loadstring(game:HttpGet("https://aptfxx.dev/scripts/verdantui"))()

local Window = Verdant:AddWindow({
    Name = "Verdant",
    Subtitle = "Autofarm",
    Size = UDim2.fromOffset(700, 700),
    Theme = "Night",
    Keybind = Enum.KeyCode.RightControl,
})

local Tab = Window:AddTab({ Name = "Autofarm", Description = "Autofarm controls" })
Tab:AddSection("Autofarm")

Tab:AddToggle({
    Name = "Enable Autofarm",
    Flag = "AutoFarmEnabled",
    Default = false,
    Callback = function(v) if v then startFarm() else stopFarm() end end,
})

Tab:AddDropdown({
    Name = "Prefer",
    Flag = "AutoFarmPrefer",
    Options = {"Currency", "XP"},
    Default = "Currency",
    Callback = function(o) State.prefer = type(o) == "table" and o[1] or o end,
})

Tab:AddDropdown({
    Name = "When Collected All Coins",
    Flag = "AutoFarmWhenDone",
    Options = {"Reset", "End Game"},
    Default = "Reset",
    Callback = function(o) State.whenDone = type(o) == "table" and o[1] or o end,
})

Tab:AddToggle({
    Name = "Game Longevity",
    Flag = "AutoFarmLongevity",
    Default = true,
    Callback = function(v) State.longevity = v end,
})

Tab:AddDropdown({
    Name = "Currency",
    Flag = "AutoFarmCurrency",
    Options = (function()
        local t = {}; for k in pairs(cList) do table.insert(t, k) end; table.sort(t); return t
    end)(),
    Default = "Coins",
    Callback = function(o)
        State.currency = type(o) == "table" and o[1] or o
        boundContainer = nil
        if State.enabled then scanCoins() end
    end,
})

Tab:AddSlider({
    Name = "Autofarm Speed",
    Flag = "AutoFarmSpeed",
    Min = 0.5,
    Max = 1.7,
    Default = 1.5,
    Increment = 0.01,
    Callback = function(v) State.speed = v end,
})

Tab:AddToggle({
    Name = "Ignore Unsafe Coins",
    Flag = "AutoFarmIgnoreUnsafe",
    Default = false,
    Callback = function(v) State.ignoreUnsafe = v end,
})

Tab:AddToggle({
    Name = "Prefer Clusters",
    Flag = "AutoFarmPreferClusters",
    Description = "Prefers nearby coin groups.",
    Default = true,
    Callback = function(v)
        State.preferClusters = v
        if not v then State.activeCluster = nil end
    end,
})
Tab:AddSlider({
    Name = "Distance Weight",
    Flag = "AutoFarmDistanceScale",
    Min = 10, Max = 100,
    Default = 30, Increment = 5,
    Description = "Balances distance and cluster size.",
    Callback = function(v) distanceScale = v end,
})

Tab:AddSection("Status")

local statusLabel = Tab:AddParagraph({
    Title = "Status",
    Content = "Role: none | Round: Inactive | Revenue: 0/hr | Active For: 0d 0h 0m 0s",
})

task.spawn(function()
    while true do
        task.wait(0.5)
        local role = getMyRole() or "none"
        local roundState = getRoundState()
        local round = (roundState == "active") and "Active"
                   or  (roundState == "waiting") and "Waiting"
                   or  "Lobby"

        local rate, elapsed = 0, 0
        if Session.startTime > 0 then
            elapsed = tick() - Session.startTime
            if elapsed >= 1 then
                rate = math.floor((Session.coinsCollected / (elapsed / 3600)) + 0.5)
            end
        end
        local seconds = math.max(0, math.floor(elapsed))
        local timeStr = string.format("%dd %dh %dm %ds",
            math.floor(seconds / 86400),
            math.floor((seconds % 86400) / 3600),
            math.floor((seconds % 3600) / 60),
            seconds % 60)

        pcall(function()
            statusLabel:SetContent(string.format(
                "Role: %s | Round: %s | Revenue: %d/hr | Active For: %s",
                role, round, rate, timeStr
            ))
        end)
    end
end)

if debug then
    Tab:AddSection("Debug")

    Tab:AddButton({
        Name = "Force Rescan",
        Callback = function()
            boundContainer = nil
            local n = scanCoins()
            Window:Notify({ Title = "Autofarm", Content = "Tracked "..n.." coin parts.", Duration = 4 })
        end,
    })

    Tab:AddButton({
        Name = "Print Round State",
        Callback = function()
            afDebug("hasFTI:", tostring(hasFTI))
            afDebug("hasRole:", tostring(hasRole()))
            afDebug("getRoundState:", getRoundState())
            afDebug("murderer (findRole):", tostring(findRole("Murderer")))
            afDebug("isRoundActive (strict tools):", tostring(isRoundActive()))
            afDebug("hasGoneUnder:", tostring(State.hasGoneUnder))
            afDebug("waiting:", tostring(State.waiting))
            afDebug("farmHold:", tostring(State.farmHold))
            afDebug("pinnedPos:", tostring(pinnedPos))
            local hrp = getHRP()
            if hrp then afDebug("  hrp.Anchored:", hrp.Anchored, " Y:", hrp.Position.Y) end
            for name, d in pairs(roleData) do
                if type(d) == "table" then
                    afDebug("  role["..name.."]:", tostring(d.Role), "Dead="..tostring(d.Dead))
                end
            end
            for _, p in ipairs(Players:GetPlayers()) do
                local k = toolHeld(p, "Knife") and "Knife" or ""
                local g = toolHeld(p, "Gun") and "Gun" or ""
                if k ~= "" or g ~= "" then
                    afDebug("  tool["..p.Name.."]:", k, g)
                end
            end
        end,
    })

    Tab:AddButton({
        Name = "Reset Session Stats",
        Callback = function()
            Session.startTime = tick()
            Session.coinsCollected = 0
            afDebug("session stats reset")
        end,
    })
end


local MiscTab = Window:AddTab({ Name = "Misc", Description = "Misc controls" })
MiscTab:AddSection("Performance")

MiscTab:AddToggle({
    Name = "Low Quality Mode",
    Flag = "MiscLowQuality",
    Description = "Simplifies visuals while waiting.",
    Default = false,
    Callback = function(v)
        MiscSettings.lowQuality = v
        if v and State.waiting then applyLowQualityMode() end
    end,
})

MiscTab:AddToggle({
    Name = "Visualize Path",
    Flag = "MiscVisualizePath",
    Description = "Shows the current path.",
    Default = false,
    Callback = function(v)
        local ok = setPathVisualization(v)
        if not ok then
            Window:Notify({ Title = "Visualize Path", Content = "Your executor does not support the Drawing library.", Type = "Warning" })
        end
    end,
})

MiscTab:AddToggle({
    Name = "Vote for Best Map",
    Flag = "MiscVoteForBestMap",
    Description = "Votes for preferred maps.",
    Default = false,
    Callback = function(v)
        MiscSettings.voteForBestMap = v
        if v then startBestMapVoting() end
    end,
})

MiscTab:AddSection("Auto Rejoin")
MiscTab:AddParagraph({
    Title = "Server selection",
    Content = "Hops to a different public server.",
})
MiscTab:AddToggle({
    Name = "Auto Rejoin on Errors",
    Flag = "MiscAutoRejoinErrors",
    Description = "Hops after Roblox errors.",
    Default = getgenv().AutoRejoin ~= false,
    Callback = function(v)
        getgenv().AutoRejoin = v
        if v then startAutoRejoin() else stopAutoRejoin() end
    end,
})

MiscTab:AddToggle({
    Name = "Auto Hop: No Round",
    Flag = "MiscAutoHopNoRound",
    Description = "Hops after 3 minutes without a round.",
    Default = true,
    Callback = function(v) MiscSettings.autoHopNoRound = v end,
})

MiscTab:AddToggle({
    Name = "Auto Hop: Low Population",
    Flag = "MiscAutoHopLowPlayers",
    Description = "Hops below 4 players.",
    Default = true,
    Callback = function(v) MiscSettings.autoHopLowPlayers = v end,
})

MiscTab:AddToggle({
    Name = "Auto Hop: No Coins",
    Flag = "MiscAutoHopNoCoins",
    Description = "Hops after 4 minutes without collecting.",
    Default = true,
    Callback = function(v) MiscSettings.autoHopNoCoins = v end,
})

MiscTab:AddToggle({
    Name = "Auto Hop: Bot Detection",
    Flag = "MiscAutoHopBotDetection",
    Description = "Hops on detected bot-heavy servers.",
    Default = true,
    Callback = function(v)
        MiscSettings.autoHopBotDetection = v
        MiscSettings.autoHopCrowdedFarmers = v
        MiscSettings.autoHopFreeOutfitLobby = v
        MiscSettings.autoHopFlaggedHat = v
        nextFreeAvatarCheckAt = v and tick() or nil
    end,
})

MiscTab:AddSection("Confirm Dialogues")
MiscTab:AddToggle({
    Name = "STFU",
    Flag = "MiscStfu",
    Description = "Suppresses confirmation dialogs.",
    Default = isStfuEnabled(),
    Callback = function(v)
        if v then
            local ok, err = pcall(writefile, stfuFile, "please be quiet")
            if not ok then
                Window:Notify({ Title = "STFU", Content = "Could not write Verdant/stfu.txt: " .. tostring(err), Type = "Error" })
            end
        elseif isfile and isfile(stfuFile) then
            if type(delfile) ~= "function" then
                Window:Notify({ Title = "STFU", Content = "Your executor does not support delfile, so Verdant/stfu.txt could not be removed.", Type = "Warning" })
                return
            end
            local ok, err = pcall(delfile, stfuFile)
            if not ok then
                Window:Notify({ Title = "STFU", Content = "Could not remove Verdant/stfu.txt: " .. tostring(err), Type = "Error" })
            end
        end
    end,
})

local DiscordTab = Window:AddTab({ Name = "Discord", Description = "Discord controls" })
DiscordTab:AddSection("Connection")

local remoteStatusLabel = DiscordTab:AddParagraph({
    Title = "Status",
    Content = "Disconnected"
})

task.spawn(function()
    while true do
        task.wait(1)
        local statusText = remoteState.connected and "Connected" or "Disconnected"
        
        if remoteState.execId then
            statusText = statusText .. "\n\nExecID: " .. remoteState.execId
            if remoteState.sessionCode then
                statusText = statusText .. "\nSession Code: " .. remoteState.sessionCode
            end
            statusText = statusText .. "\n\nTo connect, run /connect [ExecID] [Key] in Discord."
        else
            statusText = statusText .. "\n\nNo connection generated yet. Click the button below."
        end
        pcall(function() remoteStatusLabel:SetContent(statusText) end)
    end
end)

DiscordTab:AddButton({
    Name = "Generate / Reset Connection",
    Description = "Resets the connection key.",
    Callback = function()
        if Confirm({ Title = "Resetting Keys", Content = "Do you want to reset your key? You will be signed out of Discord.", Danger = true, ConfirmText = "Reset" }) == true then
            local success, msg
            do
                local data = httpReq("POST", remoteUrl .. "/generate", {})
                if data and data.ok then
                    remoteState.execId = data.execId
                    remoteState.encryptedKey = data.encryptedKey
                    remoteState.sessionCode = data.sessionCode
                    saveRemoteConfig()
                    success, msg = true, data
                else
                    success, msg = false, "Failed to connect to server"
                end
            end
            if success then
                Window:Notify({ Title = "Discord", Content = "New connection generated!", Type = "Success", Duration = 3 })
            else
                Window:Notify({ Title = "Discord", Content = tostring(msg), Type = "Error", Duration = 3 })
            end
        else
            print("Cancelled.")
        end
    end
})


DiscordTab:AddSection("Copy Credentials")

DiscordTab:AddButton({
    Name = "Copy ExecID",
    Callback = function()
        if remoteState.execId and setclipboard then
            pcall(setclipboard, remoteState.execId)
            Window:Notify({ Title = "Copied", Content = "ExecID copied to clipboard.", Type = "Success", Duration = 2 })
        else
            Window:Notify({ Title = "Error", Content = "No ExecID generated yet, or clipboard unsupported.", Type = "Warning" })
        end
    end
})

DiscordTab:AddButton({
    Name = "Copy Key",
    Callback = function()
        if remoteState.encryptedKey and setclipboard then
            pcall(setclipboard, remoteState.encryptedKey)
            Window:Notify({ Title = "Copied", Content = "Key copied to clipboard.", Type = "Success", Duration = 2 })
        else
            Window:Notify({ Title = "Error", Content = "No Key generated yet, or clipboard unsupported.", Type = "Warning" })
        end
    end
})

DiscordTab:AddButton({
    Name = "Copy Session Code",
    Callback = function()
        if remoteState.sessionCode and setclipboard then
            pcall(setclipboard, remoteState.sessionCode)
            Window:Notify({ Title = "Copied", Content = "Session Code copied to clipboard.", Type = "Success", Duration = 2 })
        else
            Window:Notify({ Title = "Error", Content = "No Session Code generated yet, or clipboard unsupported.", Type = "Warning" })
        end
    end
})

DiscordTab:AddSection("Intents")
DiscordTab:AddParagraph({
    Title = "Warning",
    Content = "Enabling these allows the Discord bot to perform actions on your client."
})

DiscordTab:AddToggle({
    Name = "Allow Stats",
    Default = remoteState.allowStats,
    Callback = function(v) 
        remoteState.allowStats = v
        saveRemoteConfig()
    end
})

DiscordTab:AddToggle({
    Name = "Allow Farm Control",
    Default = remoteState.allowFarmControl,
    Callback = function(v) 
        remoteState.allowFarmControl = v
        saveRemoteConfig()
    end
})

DiscordTab:AddToggle({
    Name = "Allow Code Execution",
    Default = remoteState.allowCodeExecution,
    Callback = function(v) 
        if v == true then 
            if Confirm({ Title = "Code Execution", Content = "Are you sure you want to grant the Code Execution intent? Anyone with your ExecID and key can execute code on your behalf!", Danger = true, ConfirmText = "Grant" }) == false then
                return
            end
        end
        remoteState.allowCodeExecution = v
        saveRemoteConfig()
    end
})

local SettingsTab = Window:AddTab({ Name = "Settings", Description = "Configuration" })
SettingsTab:AddSection("Config")

SettingsTab:AddButton({
    Name = "Save Config",
    Description = "Saves settings.",
    Callback = function()
        if not writefile then
            Window:Notify({ Title = "Config", Content = "Executor does not support writefile.", Type = "Warning" })
            return
        end
        local ok, err = pcall(writefile, configFile, Verdant:ExportConfigJSON())
        Window:Notify({
            Title = "Config",
            Content = ok and "Saved." or ("Save failed: " .. tostring(err)),
            Type = ok and "Success" or "Error",
        })
    end,
})

SettingsTab:AddButton({
    Name = "Load Config",
    Description = "Loads settings.",
    Callback = function()
        if not isfile or not isfile(configFile) then
            Window:Notify({ Title = "Config", Content = "No saved config found.", Type = "Warning" })
            return
        end
        local ok, data = pcall(readfile, configFile)
        if not ok or not data then
            Window:Notify({ Title = "Config", Content = "Read failed.", Type = "Error" })
            return
        end
        local res = Verdant:LoadConfig(data)
        Window:Notify({
            Title = "Config",
            Content = "Loaded " .. tostring(res.Loaded or 0) .. " value(s).",
            Type = "Success",
        })
    end,
})
SettingsTab:AddButton({
    Name = "Delete Config",
    Description = "Deletes saved settings.",
    Callback = function()
        if isStfuEnabled() then
            Window:Notify({ Title = "STFU", Content = "Confirmation dialogs are disabled. Turn off the STFU toggle first.", Type = "Warning" })
            return
        end
        Window:Dialog({
			Title = "Delete Config?", Content = "This can't be undone.",
			Width = 400, CloseOnOutsideClick = false,
			Buttons = {
				{ Title = "Reset", Style = "Danger", Callback = function() end },   -- return false to keep it open
				{ Title = "Cancel", Style = "Secondary" },
			},
		})       
    end,
})


if isfile and isfile(configFile) then
    local ok, data = pcall(readfile, configFile)
    if ok and data then
        local loadOk, res = pcall(Verdant.LoadConfig, Verdant, data)
        if loadOk and res and (res.Loaded or 0) > 0 then
            task.delay(0.5, function()
                Window:Notify({
                    Title = "Config",
                    Content = "Autoloaded " .. tostring(res.Loaded) .. " value(s).",
                    Type = "Success",
                    Duration = 3,
                })
            end)
        end
    end
end


Verdant:Notify({ Title = "Verdant", Content = "Loaded :) Welcome to Verdant", Type = "Success", Duration = 2 })
