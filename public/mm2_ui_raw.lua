--!nonstrict

local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local SoundService = game:GetService("SoundService")
local RunService = game:GetService("RunService")
local Debris = game:GetService("Debris")
local HttpService = game:GetService("HttpService")

local LocalPlayer = Players.LocalPlayer

local Library = {}
Library.Flags = {} -- [id] = element
Library.Elements = {} -- value elements in creation order (export order)
Library.Windows = {}
Library.Settings = {
	Sounds = true,
	AnimationScale = 1,
	ClickVolume = 0.2,
}

--------------------------------------------------------------------------------
-- Themes
--------------------------------------------------------------------------------

local Forest = {
	Paper = Color3.fromRGB(20, 38, 30), -- page background
	Raised = Color3.fromRGB(27, 48, 38), -- hover tint, cards, dialogs
	Ink = Color3.fromRGB(242, 237, 224), -- primary text and strong rules
	InkMuted = Color3.fromRGB(176, 188, 176), -- descriptions, secondary text
	InkFaint = Color3.fromRGB(116, 136, 124), -- placeholders, inactive
	Rule = Color3.fromRGB(56, 80, 66), -- hairlines
	Accent = Color3.fromRGB(158, 214, 140),
	OnAccent = Color3.fromRGB(20, 38, 30),
	Overlay = Color3.fromRGB(0, 0, 0),

	Success = Color3.fromRGB(158, 214, 140),
	Info = Color3.fromRGB(150, 188, 226),
	Warning = Color3.fromRGB(230, 192, 116),
	Danger = Color3.fromRGB(230, 128, 108),

	SerifFamily = "rbxasset://fonts/families/Merriweather.json",
	SansFamily = "rbxasset://fonts/families/SourceSansPro.json",
	Rounding = 0.5, -- corner rounding multiplier (0 = square)

	ShadowImage = "rbxassetid://6014261993",
	ClickSound = "rbxassetid://139719503904449",
	NotifySound = "rbxassetid://6644702473",
}

local function extend(base, overrides)
	local result = table.clone(base)
	for k, v in pairs(overrides) do
		result[k] = v
	end
	return result
end

Library.Themes = {
	Forest = Forest,
	Paper = extend(Forest, {
		Paper = Color3.fromRGB(246, 242, 232),
		Raised = Color3.fromRGB(238, 233, 220),
		Ink = Color3.fromRGB(26, 36, 30),
		InkMuted = Color3.fromRGB(88, 100, 92),
		InkFaint = Color3.fromRGB(150, 156, 148),
		Rule = Color3.fromRGB(214, 207, 190),
		Accent = Color3.fromRGB(34, 106, 68),
		OnAccent = Color3.fromRGB(246, 242, 232),
		Overlay = Color3.fromRGB(30, 30, 24),
		Success = Color3.fromRGB(34, 106, 68),
		Info = Color3.fromRGB(44, 88, 150),
		Warning = Color3.fromRGB(170, 116, 20),
		Danger = Color3.fromRGB(168, 54, 40),
	}),
	Sage = extend(Forest, {
		Paper = Color3.fromRGB(226, 234, 222),
		Raised = Color3.fromRGB(216, 226, 211),
		Ink = Color3.fromRGB(22, 40, 30),
		InkMuted = Color3.fromRGB(74, 96, 82),
		InkFaint = Color3.fromRGB(128, 146, 134),
		Rule = Color3.fromRGB(190, 204, 186),
		Accent = Color3.fromRGB(38, 112, 72),
		OnAccent = Color3.fromRGB(226, 234, 222),
		Overlay = Color3.fromRGB(20, 30, 24),
		Success = Color3.fromRGB(38, 112, 72),
		Info = Color3.fromRGB(44, 88, 150),
		Warning = Color3.fromRGB(160, 110, 20),
		Danger = Color3.fromRGB(160, 52, 40),
	}),
	Night = extend(Forest, {
		Paper = Color3.fromRGB(17, 19, 18),
		Raised = Color3.fromRGB(25, 28, 26),
		Ink = Color3.fromRGB(234, 234, 228),
		InkMuted = Color3.fromRGB(164, 168, 162),
		InkFaint = Color3.fromRGB(104, 110, 106),
		Rule = Color3.fromRGB(48, 52, 50),
		Accent = Color3.fromRGB(124, 204, 146),
		OnAccent = Color3.fromRGB(17, 19, 18),
		Success = Color3.fromRGB(124, 204, 146),
	}),
}

local Theme = table.clone(Forest)
Library.Theme = Theme

-- Theme bindings: instance -> { [property] = themeKey | function(Theme) }
local Bindings = setmetatable({}, { __mode = "k" })
-- Stateful components re-render themselves on theme change.
local Refreshers = {}

local function resolve(key)
	if typeof(key) == "function" then
		return key(Theme)
	end
	return Theme[key]
end

local function bind(inst, props)
	local entry = Bindings[inst]
	if not entry then
		entry = {}
		Bindings[inst] = entry
	end
	for prop, key in pairs(props) do
		entry[prop] = key
		inst[prop] = resolve(key)
	end
	return inst
end

local function onThemeChanged(owner, fn)
	table.insert(Refreshers, { Owner = owner, Fn = fn })
end

--------------------------------------------------------------------------------
-- Helpers
--------------------------------------------------------------------------------

local Window = {}
Window.__index = Window

local Tab = {}
Tab.__index = Tab

local Element = {}
Element.__index = Element

local MASTHEAD = 62
local DOUBLE_RULE = 5
local TABSTRIP = 38
local CONTENT_TOP = MASTHEAD + DOUBLE_RULE + TABSTRIP + 1
local ROW_INSET = 10 -- horizontal inset of row content inside the hover tint
local OPTION_HEIGHT = 32

local function create(className, props, children)
	local inst = Instance.new(className)
	local parent, themed
	for key, value in pairs(props or {}) do
		if key == "Parent" then
			parent = value
		elseif key == "Theme" then
			themed = value
		else
			inst[key] = value
		end
	end
	if themed then
		bind(inst, themed)
	end
	for _, child in ipairs(children or {}) do
		child.Parent = inst
	end
	if parent then
		inst.Parent = parent
	end
	return inst
end

local function scaled(seconds)
	return (seconds or 0.2) * Library.Settings.AnimationScale
end

local function tween(obj, props, duration, style, direction)
	local t = TweenService:Create(
		obj,
		TweenInfo.new(scaled(duration), style or Enum.EasingStyle.Quint, direction or Enum.EasingDirection.Out),
		props
	)
	t:Play()
	return t
end

local function tweenAll(objects, props, duration)
	for _, obj in ipairs(objects) do
		tween(obj, props, duration)
	end
end

local function fontFor(familyKey, weight, style)
	return function(T)
		return Font.new(T[familyKey], weight or Enum.FontWeight.Regular, style or Enum.FontStyle.Normal)
	end
end

-- `radius` is a design radius in px; Theme.Rounding scales it (0 = square).
local function corner(radius)
	if radius == "full" then
		return create("UICorner", { CornerRadius = UDim.new(1, 0) })
	end
	radius = radius or 4
	return create("UICorner", {
		Theme = {
			CornerRadius = function(T)
				return UDim.new(0, math.floor(radius * (T.Rounding or 0) + 0.5))
			end,
		},
	})
end

local function stroke(colorKey, thickness, transparency)
	return create("UIStroke", {
		Thickness = thickness or 1,
		Transparency = transparency or 0,
		ApplyStrokeMode = Enum.ApplyStrokeMode.Border,
		Theme = { Color = colorKey or "Rule" },
	})
end

local function padding(top, bottom, left, right)
	return create("UIPadding", {
		PaddingTop = UDim.new(0, top or 0),
		PaddingBottom = UDim.new(0, bottom or 0),
		PaddingLeft = UDim.new(0, left or 0),
		PaddingRight = UDim.new(0, right or 0),
	})
end

local function listLayout(pad, direction)
	return create("UIListLayout", {
		Padding = UDim.new(0, pad or 0),
		FillDirection = direction or Enum.FillDirection.Vertical,
		SortOrder = Enum.SortOrder.LayoutOrder,
	})
end

-- A solid line. props.Color: theme key (default "Rule"), or false when the caller manages the color.
local function rule(props)
	local base = { BorderSizePixel = 0 }
	if props.Color ~= false then
		base.Theme = { BackgroundColor3 = props.Color or "Rule" }
	end
	for k, v in pairs(props) do
		if k ~= "Color" then
			base[k] = v
		end
	end
	return create("Frame", base)
end

--[[
	Text factory. Extra props:
		Font = "Sans" (default) | "Serif"
		Weight = Enum.FontWeight, Italic = bool
		Color = theme key (default "Ink"), or false when the caller manages TextColor3
		Class = "TextLabel" (default) | "TextButton" | "TextBox"
]]
local function text(props)
	local family = props.Font == "Serif" and "SerifFamily" or "SansFamily"
	local style = props.Italic and Enum.FontStyle.Italic or Enum.FontStyle.Normal
	local color = props.Color
	if color == nil then
		color = "Ink"
	end
	local className = props.Class or "TextLabel"
	local base = {
		BackgroundTransparency = 1,
		TextSize = 14,
		TextXAlignment = Enum.TextXAlignment.Left,
	}
	if className ~= "TextBox" then
		base.Text = ""
	end
	if className == "TextButton" then
		base.AutoButtonColor = false
	end
	for k, v in pairs(props) do
		if k ~= "Font" and k ~= "Weight" and k ~= "Italic" and k ~= "Color" and k ~= "Class" then
			base[k] = v
		end
	end
	local themed = { FontFace = fontFor(family, props.Weight, style) }
	if color then
		themed.TextColor3 = color
	end
	if className == "TextBox" then
		themed.PlaceholderColor3 = "InkFaint"
	end
	base.Theme = themed
	return create(className, base)
end

-- An underlined text link: the underline draws in from the left on hover.
local function link(props)
	local normalKey = props.Color or "InkMuted"
	local hoverKey = props.HoverColor or "Ink"
	local options = {
		Class = "TextButton",
		AutomaticSize = Enum.AutomaticSize.X,
		Color = normalKey,
	}
	for k, v in pairs(props) do
		if k ~= "HoverColor" and k ~= "Color" then
			options[k] = v
		end
	end
	local button = text(options)
	local underline = rule({
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.new(0, 0, 1, -3),
		Size = UDim2.new(0, 0, 0, 1),
		Color = hoverKey,
		Parent = button,
	})
	button.MouseEnter:Connect(function()
		tween(button, { TextColor3 = Theme[hoverKey] }, 0.15)
		tween(underline, { Size = UDim2.new(1, 0, 0, 1) }, 0.25)
	end)
	button.MouseLeave:Connect(function()
		tween(button, { TextColor3 = Theme[normalKey] }, 0.15)
		tween(underline, { Size = UDim2.new(0, 0, 0, 1) }, 0.25)
	end)
	return button, underline
end

-- A thin chevron drawn from two hairlines (font independent). Points down at Rotation 0.
local function chevron(parent, colorKey, props)
	local holder = create("Frame", {
		BackgroundTransparency = 1,
		Size = UDim2.fromOffset(10, 10),
	})
	for k, v in pairs(props or {}) do
		holder[k] = v
	end
	local bars = {}
	for i, rotation in ipairs({ 45, -45 }) do
		bars[i] = rule({
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.new(0.5, i == 1 and -2 or 2, 0.5, 0),
			Size = UDim2.fromOffset(6, 1),
			Rotation = rotation,
			Color = colorKey,
			Parent = holder,
		})
	end
	holder.Parent = parent
	return holder, bars
end

local function toAsset(image)
	if image == nil or image == "" or image == 0 then
		return nil
	end
	if typeof(image) == "number" then
		return "rbxassetid://" .. image
	end
	if typeof(image) == "string" and image:match("^%d+$") then
		return "rbxassetid://" .. image
	end
	return image
end

local function headshot(userId)
	return "rbxthumb://type=AvatarHeadShot&id=" .. tostring(userId) .. "&w=48&h=48"
end

local function safeCall(callback, ...)
	if typeof(callback) ~= "function" then
		return
	end
	local args = table.pack(...)
	task.spawn(function()
		local ok, err = pcall(callback, table.unpack(args, 1, args.n))
		if not ok then
			warn("[Verdant] Callback error: " .. tostring(err))
		end
	end)
end

local function playSound(id, volume)
	if not Library.Settings.Sounds or not id or id == "" then
		return
	end
	local sound = Instance.new("Sound")
	sound.SoundId = id
	sound.Volume = volume or Library.Settings.ClickVolume
	sound.Parent = SoundService
	sound:Play()
	Debris:AddItem(sound, 3)
end

local function click(volume)
	playSound(Theme.ClickSound, volume)
end

local function isPointer(input)
	return input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch
end

local function isMove(input)
	return input.UserInputType == Enum.UserInputType.MouseMovement or input.UserInputType == Enum.UserInputType.Touch
end

local function getPlayerGui()
	return LocalPlayer:WaitForChild("PlayerGui")
end

local function clockTime()
	return os.date("%H:%M")
end

-- Fades a "veil" (a solid frame the color of the page) away, so whatever is underneath
-- appears to fade in. Cheaper and crisper than CanvasGroups.
local function liftVeil(veil, duration)
	veil.Visible = true
	veil.BackgroundTransparency = 0
	local t = tween(veil, { BackgroundTransparency = 1 }, duration or 0.3, Enum.EasingStyle.Quad)
	t.Completed:Connect(function()
		if veil.BackgroundTransparency >= 1 then
			veil.Visible = false
		end
	end)
	return t
end

local function dropVeil(veil, duration)
	veil.Visible = true
	return tween(veil, { BackgroundTransparency = 0 }, duration or 0.2, Enum.EasingStyle.Quad)
end

--------------------------------------------------------------------------------
-- Library API
--------------------------------------------------------------------------------

function Library:SetTheme(theme)
	local source = theme
	if typeof(theme) == "string" then
		source = Library.Themes[theme]
		assert(source, "[Verdant] Unknown theme: " .. theme)
	end
	assert(typeof(source) == "table", "[Verdant] SetTheme expects a theme name or table")
	for k, v in pairs(source) do
		Theme[k] = v
	end

	for inst, entry in pairs(Bindings) do
		if inst:IsDescendantOf(game) then
			local colors = {}
			for prop, key in pairs(entry) do
				local value = resolve(key)
				if typeof(value) == "Color3" then
					colors[prop] = value
				else
					inst[prop] = value
				end
			end
			if next(colors) then
				tween(inst, colors, 0.35)
			end
		end
	end

	for i = #Refreshers, 1, -1 do
		local refresher = Refreshers[i]
		if refresher.Owner:IsDescendantOf(game) then
			task.spawn(refresher.Fn)
		elseif not refresher.Owner.Parent then
			table.remove(Refreshers, i)
		end
	end
end

function Library:AddTheme(name, theme)
	Library.Themes[name] = extend(Forest, theme)
	return Library.Themes[name]
end

function Library:GetThemes()
	local names = {}
	for name in pairs(Library.Themes) do
		table.insert(names, name)
	end
	table.sort(names)
	return names
end

function Library:SetAccent(color)
	self:SetTheme({ Accent = color, Success = color })
end

function Library:SetSounds(enabled)
	Library.Settings.Sounds = enabled == true
end

function Library:SetAnimationScale(scale)
	Library.Settings.AnimationScale = math.max(tonumber(scale) or 1, 0)
end

function Library:GetElement(id)
	return Library.Flags[id]
end

function Library:GetFlag(id)
	local element = Library.Flags[id]
	return element and element:Get()
end

function Library:SetFlag(id, value, silent)
	local element = Library.Flags[id]
	if element and element.Set then
		element:Set(value, silent)
	end
end

-- Returns every value element (toggles, sliders, textboxes, dropdowns, player selectors)
-- in creation order:
-- { Version = 1, Objects = { { Id = "Main/WalkSpeed", Type = "Slider", Value = 16 }, ... } }
function Library:ExportConfig()
	local objects = {}
	for _, element in ipairs(Library.Elements) do
		if Library.Flags[element.Id] == element then
			local value
			if element._serialize then
				value = element:_serialize()
			else
				value = element:Get()
			end
			if typeof(value) == "table" then
				value = table.clone(value)
			end
			table.insert(objects, { Id = element.Id, Type = element.Type, Value = value })
		end
	end
	return { Version = 1, Objects = objects }
end

function Library:ExportConfigJSON()
	return HttpService:JSONEncode(self:ExportConfig())
end

-- Accepts what ExportConfig / ExportConfigJSON returned (table or JSON string), or a flat
-- { [id] = value } table. Each element is set, then its callbacks and OnChanged listeners
-- are fired once (in the order it was exported) unless options.Silent is true.
-- Returns { Loaded = number, Missing = { ids that don't exist or changed type } }.
function Library:LoadConfig(config, options)
	options = options or {}
	local result = { Loaded = 0, Missing = {} }

	if typeof(config) == "string" then
		local ok, decoded = pcall(function()
			return HttpService:JSONDecode(config)
		end)
		if not ok then
			warn("[Verdant] LoadConfig: invalid JSON (" .. tostring(decoded) .. ")")
			return result
		end
		config = decoded
	end
	if typeof(config) ~= "table" then
		warn("[Verdant] LoadConfig expects a table or JSON string")
		return result
	end

	local objects = config.Objects
	if typeof(objects) ~= "table" then
		objects = {}
		for id, value in pairs(config) do
			table.insert(objects, { Id = id, Value = value })
		end
	end

	for _, object in ipairs(objects) do
		local element = Library.Flags[object.Id]
		if element and element.Set and (object.Type == nil or object.Type == element.Type) then
			local value = object.Value
			if element._deserialize then
				value = element:_deserialize(value)
			end
			element:Set(value, true)
			if not options.Silent then
				if element.Type == "Textbox" then
					element:_fire(element:Get(), false)
				else
					element:_fire(element:Get())
				end
			end
			result.Loaded += 1
		else
			table.insert(result.Missing, object.Id)
		end
	end
	return result
end

function Library:ImportConfig(config, silent)
	return self:LoadConfig(config, { Silent = silent })
end

function Library:Destroy()
	for i = #Library.Windows, 1, -1 do
		Library.Windows[i]:Destroy()
	end
end

--------------------------------------------------------------------------------
-- Notifications (library-level, so they work with or without a window)
--------------------------------------------------------------------------------

local notifyHolder
local notifyOrder = 0

local function getNotifyHolder()
	if notifyHolder and notifyHolder.Parent and notifyHolder.Parent.Parent then
		return notifyHolder
	end
	local gui = create("ScreenGui", {
		Name = "Verdant_Notifications",
		ResetOnSpawn = false,
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling,
		DisplayOrder = 200,
		Parent = getPlayerGui(),
	})
	notifyHolder = create("Frame", {
		AnchorPoint = Vector2.new(1, 1),
		Position = UDim2.new(1, -20, 1, -20),
		Size = UDim2.new(0, 320, 1, -40),
		BackgroundTransparency = 1,
		Parent = gui,
	}, {
		create("UIListLayout", {
			Padding = UDim.new(0, 10),
			SortOrder = Enum.SortOrder.LayoutOrder,
			VerticalAlignment = Enum.VerticalAlignment.Bottom,
		}),
	})
	return notifyHolder
end

function Library:Notify(options)
	options = options or {}
	local duration = options.Duration
	if duration == nil then
		duration = 5
	end
	local persistent = duration == false or duration == 0
	local kind = options.Type == "Error" and "Danger" or options.Type
	local colorKey = (kind and Theme[kind]) and kind or "Accent"
	notifyOrder += 1

	local wrapper = create("Frame", {
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 1,
		LayoutOrder = notifyOrder,
		Parent = getNotifyHolder(),
	})

	local card = create("Frame", {
		Position = UDim2.fromOffset(340, 0),
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BorderSizePixel = 0,
		Theme = { BackgroundColor3 = "Paper" },
		Parent = wrapper,
	}, { stroke("Rule", 1), corner(4) })

	-- Colored margin rule on the left (scale height = the card's own height).
	rule({ Size = UDim2.new(0, 2, 1, 0), Color = colorKey, Parent = card })

	local body = create("Frame", {
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 1,
		Parent = card,
	}, { padding(12, 12, 18, 14), listLayout(4) })

	local header = create("Frame", {
		Size = UDim2.new(1, 0, 0, 20),
		BackgroundTransparency = 1,
		LayoutOrder = 1,
		Parent = body,
	})

	local textX = 0
	local image = toAsset(options.Image)
	if image then
		create("ImageLabel", {
			AnchorPoint = Vector2.new(0, 0.5),
			Position = UDim2.fromScale(0, 0.5),
			Size = UDim2.fromOffset(16, 16),
			BackgroundTransparency = 1,
			Image = image,
			Theme = { ImageColor3 = colorKey },
			Parent = header,
		})
		textX = 24
	end

	text({
		Position = UDim2.fromOffset(textX, 0),
		Size = UDim2.new(1, -(textX + 70), 1, 0),
		Font = "Serif",
		Weight = Enum.FontWeight.Bold,
		TextSize = 15,
		Text = options.Title or "Notice",
		TextTruncate = Enum.TextTruncate.AtEnd,
		Parent = header,
	})

	text({
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.new(1, -20, 0, 0),
		Size = UDim2.fromOffset(44, 20),
		Font = "Serif",
		Italic = true,
		TextSize = 12,
		Color = "InkFaint",
		TextXAlignment = Enum.TextXAlignment.Right,
		Text = clockTime(),
		Parent = header,
	})

	local closeButton = text({
		Class = "TextButton",
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.new(1, 2, 0, 0),
		Size = UDim2.fromOffset(16, 20),
		TextSize = 18,
		Color = "InkFaint",
		TextXAlignment = Enum.TextXAlignment.Right,
		Text = "Ã—",
		Parent = header,
	})
	closeButton.MouseEnter:Connect(function()
		tween(closeButton, { TextColor3 = Theme.Ink }, 0.15)
	end)
	closeButton.MouseLeave:Connect(function()
		tween(closeButton, { TextColor3 = Theme.InkFaint }, 0.15)
	end)

	if options.Content and options.Content ~= "" then
		text({
			Size = UDim2.new(1, 0, 0, 0),
			AutomaticSize = Enum.AutomaticSize.Y,
			Color = "InkMuted",
			TextWrapped = true,
			Text = options.Content,
			LayoutOrder = 2,
			Parent = body,
		})
	end

	if options.SubContent and options.SubContent ~= "" then
		text({
			Size = UDim2.new(1, 0, 0, 0),
			AutomaticSize = Enum.AutomaticSize.Y,
			Font = "Serif",
			Italic = true,
			TextSize = 12,
			Color = "InkFaint",
			TextWrapped = true,
			Text = options.SubContent,
			LayoutOrder = 3,
			Parent = body,
		})
	end

	local bar
	if not persistent then
		local track = create("Frame", {
			Size = UDim2.new(1, 0, 0, 7),
			BackgroundTransparency = 1,
			LayoutOrder = 4,
			Parent = body,
		})
		bar = rule({
			AnchorPoint = Vector2.new(0, 1),
			Position = UDim2.fromScale(0, 1),
			Size = UDim2.new(1, 0, 0, 1),
			Color = "Rule",
			Parent = track,
		})
	end

	if options.Sound ~= false then
		playSound(Theme.NotifySound, 0.25)
	end
	tween(card, { Position = UDim2.fromOffset(0, 0) }, 0.45, Enum.EasingStyle.Quint)
	if bar then
		tween(bar, { Size = UDim2.new(0, 0, 0, 1) }, duration, Enum.EasingStyle.Linear)
	end

	local notification = { Closed = false }

	function notification:Close()
		if self.Closed or not wrapper.Parent then
			return
		end
		self.Closed = true
		task.spawn(function()
			local out = tween(card, { Position = UDim2.fromOffset(340, 0) }, 0.3, Enum.EasingStyle.Quint, Enum.EasingDirection.In)
			out.Completed:Wait()
			local height = wrapper.AbsoluteSize.Y
			wrapper.AutomaticSize = Enum.AutomaticSize.None
			wrapper.Size = UDim2.new(1, 0, 0, height)
			local shrink = tween(wrapper, { Size = UDim2.new(1, 0, 0, 0) }, 0.25)
			shrink.Completed:Wait()
			wrapper:Destroy()
		end)
	end

	closeButton.MouseButton1Click:Connect(function()
		notification:Close()
	end)
	if not persistent then
		task.delay(duration, function()
			notification:Close()
		end)
	end

	return notification
end

--------------------------------------------------------------------------------
-- Window
--------------------------------------------------------------------------------

function Library:AddWindow(options)
	assert(RunService:IsClient(), "[Verdant] The UI library can only be used on the client.")
	options = options or {}

	if options.Theme then
		Library:SetTheme(options.Theme)
	end
	if options.Sounds ~= nil then
		Library.Settings.Sounds = options.Sounds == true
	end

	local self = setmetatable({}, Window)
	self.Name = options.Name or "Verdant"
	self.Subtitle = options.Subtitle or ""
	self.Keybind = options.Keybind == nil and Enum.KeyCode.LeftControl or options.Keybind
	self.Draggable = options.Draggable ~= false
	self.Resizable = options.Resizable ~= false
	self.MinSize = options.MinSize or Vector2.new(500, 340)
	self.Tabs = {}
	self.Connections = {}
	self.CloseCallbacks = {}
	self.Visible = true
	self.Minimized = false
	self.ActiveTab = nil

	local size = options.Size or UDim2.fromOffset(660, 460)
	if typeof(size) == "Vector2" then
		size = UDim2.fromOffset(size.X, size.Y)
	end
	self.Size = size

	local playerGui = getPlayerGui()
	local guiName = "Verdant_" .. self.Name
	local existing = playerGui:FindFirstChild(guiName)
	if existing then
		existing:Destroy()
	end

	local gui = create("ScreenGui", {
		Name = guiName,
		ResetOnSpawn = false,
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling,
		DisplayOrder = 100,
		Parent = playerGui,
	})
	self.Gui = gui

	-- Root holds the shadow + page; drag/resize/minimize act on it.
	local root = create("Frame", {
		Name = "Root",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = options.Position or UDim2.fromScale(0.5, 0.5),
		Size = size,
		BackgroundTransparency = 1,
		Parent = gui,
	})
	self.Root = root
	self.Scale = create("UIScale", { Scale = 0.97, Parent = root })

	self.Shadow = create("ImageLabel", {
		Name = "Shadow",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.new(0.5, 0, 0.5, 6),
		Size = UDim2.new(1, 56, 1, 56),
		BackgroundTransparency = 1,
		ImageColor3 = Color3.new(0, 0, 0),
		ImageTransparency = 1,
		ScaleType = Enum.ScaleType.Slice,
		SliceCenter = Rect.new(49, 49, 450, 450),
		ZIndex = 0,
		Theme = { Image = "ShadowImage" },
		Parent = root,
	})

	local main = create("Frame", {
		Name = "Page",
		Size = UDim2.fromScale(1, 1),
		BorderSizePixel = 0,
		ClipsDescendants = true,
		Theme = { BackgroundColor3 = "Paper" },
		Parent = root,
	}, { stroke("Rule", 1), corner(4) })
	self.Main = main

	-- Masthead ----------------------------------------------------------------
	local masthead = create("Frame", {
		Name = "Masthead",
		Size = UDim2.new(1, 0, 0, MASTHEAD),
		BackgroundTransparency = 1,
		Parent = main,
	})

	local titleHolder = create("Frame", {
		BackgroundTransparency = 1,
		Position = UDim2.fromOffset(28, 0),
		Size = UDim2.new(0.6, -28, 1, 0),
		Parent = masthead,
	}, {
		create("UIListLayout", {
			FillDirection = Enum.FillDirection.Horizontal,
			VerticalAlignment = Enum.VerticalAlignment.Center,
			SortOrder = Enum.SortOrder.LayoutOrder,
			Padding = UDim.new(0, 10),
		}),
	})

	local icon = toAsset(options.Icon)
	if icon then
		create("ImageLabel", {
			BackgroundTransparency = 1,
			Size = UDim2.fromOffset(20, 20),
			Image = icon,
			LayoutOrder = 1,
			Theme = { ImageColor3 = "Ink" },
			Parent = titleHolder,
		})
	end

	self.TitleLabel = text({
		Font = "Serif",
		Weight = Enum.FontWeight.Bold,
		TextSize = 22,
		Text = self.Name,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 30),
		LayoutOrder = 2,
		Parent = titleHolder,
	})

	self.SubtitleLabel = text({
		Font = "Serif",
		Italic = true,
		TextSize = 14,
		Color = "InkMuted",
		Text = self.Subtitle,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 30),
		Position = UDim2.fromOffset(0, 2),
		LayoutOrder = 3,
		Parent = titleHolder,
	})

	local meta = create("Frame", {
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.new(1, -28, 0, 0),
		Size = UDim2.new(0.4, 0, 1, 0),
		BackgroundTransparency = 1,
		Parent = masthead,
	}, {
		create("UIListLayout", {
			FillDirection = Enum.FillDirection.Horizontal,
			HorizontalAlignment = Enum.HorizontalAlignment.Right,
			VerticalAlignment = Enum.VerticalAlignment.Center,
			SortOrder = Enum.SortOrder.LayoutOrder,
			Padding = UDim.new(0, 18),
		}),
	})

	if options.Profile then
		local profile = create("Frame", {
			Size = UDim2.fromOffset(0, 22),
			AutomaticSize = Enum.AutomaticSize.X,
			BackgroundTransparency = 1,
			LayoutOrder = 0,
			Parent = meta,
		}, {
			create("UIListLayout", {
				FillDirection = Enum.FillDirection.Horizontal,
				VerticalAlignment = Enum.VerticalAlignment.Center,
				SortOrder = Enum.SortOrder.LayoutOrder,
				Padding = UDim.new(0, 8),
			}),
		})
		create("ImageLabel", {
			Size = UDim2.fromOffset(20, 20),
			Image = headshot(LocalPlayer.UserId),
			LayoutOrder = 1,
			Theme = { BackgroundColor3 = "Raised" },
			Parent = profile,
		}, { corner(4) })
		text({
			Size = UDim2.fromOffset(0, 22),
			AutomaticSize = Enum.AutomaticSize.X,
			Color = "InkMuted",
			Text = LocalPlayer.DisplayName,
			LayoutOrder = 2,
			Parent = profile,
		})
	end

	self.StatusLabel = text({
		Size = UDim2.fromOffset(0, 22),
		AutomaticSize = Enum.AutomaticSize.X,
		Font = "Serif",
		Italic = true,
		TextSize = 13,
		Color = false,
		TextColor3 = Theme.InkFaint,
		LayoutOrder = 1,
		Parent = meta,
	})

	local minimizeLink = link({ Size = UDim2.fromOffset(0, 22), Text = "Hide", LayoutOrder = 2, Parent = meta })
	minimizeLink.MouseButton1Click:Connect(function()
		click()
		self:Minimize()
	end)

	local closeLink = link({
		Size = UDim2.fromOffset(0, 22),
		Text = "Close",
		HoverColor = "Danger",
		LayoutOrder = 3,
		Parent = meta,
	})
	closeLink.MouseButton1Click:Connect(function()
		click()
		self:Destroy()
	end)

	-- Newspaper double rule: heavy over light.
	rule({ Position = UDim2.fromOffset(0, MASTHEAD), Size = UDim2.new(1, 0, 0, 2), Color = "Ink", Parent = main })
	rule({ Position = UDim2.fromOffset(0, MASTHEAD + 4), Size = UDim2.new(1, 0, 0, 1), Color = "Ink", Parent = main })

	-- Section tabs --------------------------------------------------------------
	local strip = create("ScrollingFrame", {
		Name = "Tabs",
		Position = UDim2.fromOffset(28, MASTHEAD + DOUBLE_RULE),
		Size = UDim2.new(1, -56, 0, TABSTRIP),
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		ScrollBarThickness = 0,
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.X,
		ScrollingDirection = Enum.ScrollingDirection.X,
		Parent = main,
	})
	self.TabList = create("Frame", {
		Name = "Buttons",
		Size = UDim2.new(0, 0, 1, 0),
		AutomaticSize = Enum.AutomaticSize.X,
		BackgroundTransparency = 1,
		Parent = strip,
	}, {
		create("UIListLayout", {
			FillDirection = Enum.FillDirection.Horizontal,
			VerticalAlignment = Enum.VerticalAlignment.Center,
			SortOrder = Enum.SortOrder.LayoutOrder,
			Padding = UDim.new(0, 26),
		}),
	})
	self.TabIndicator = rule({
		Name = "Indicator",
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.new(0, 0, 1, 0),
		Size = UDim2.new(0, 0, 0, 2),
		Color = "Accent",
		Parent = strip,
	})
	rule({ Position = UDim2.fromOffset(0, CONTENT_TOP - 1), Size = UDim2.new(1, 0, 0, 1), Parent = main })

	-- Content -----------------------------------------------------------------
	self.Content = create("Frame", {
		Name = "Content",
		Position = UDim2.fromOffset(0, CONTENT_TOP),
		Size = UDim2.new(1, 0, 1, -CONTENT_TOP),
		BackgroundTransparency = 1,
		ClipsDescendants = true,
		Parent = main,
	})

	-- Veils (see liftVeil): one over the content for tab changes, one over the whole page.
	self.ContentVeil = create("Frame", {
		Size = UDim2.fromScale(1, 1),
		BorderSizePixel = 0,
		ZIndex = 40,
		Visible = false,
		Theme = { BackgroundColor3 = "Paper" },
		Parent = self.Content,
	})
	self.PageVeil = create("Frame", {
		Size = UDim2.fromScale(1, 1),
		BorderSizePixel = 0,
		ZIndex = 45,
		Theme = { BackgroundColor3 = "Paper" },
		Parent = main,
	})

	-- Resize grip: two short diagonal hairlines.
	local grip = create("TextButton", {
		Name = "ResizeGrip",
		AnchorPoint = Vector2.new(1, 1),
		Position = UDim2.new(1, -2, 1, -2),
		Size = UDim2.fromOffset(16, 16),
		BackgroundTransparency = 1,
		AutoButtonColor = false,
		Text = "",
		ZIndex = 30,
		Visible = self.Resizable,
		Parent = main,
	})
	local gripBars = {}
	for i, length in ipairs({ 10, 5 }) do
		gripBars[i] = rule({
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.new(0.5, i == 1 and 0 or 3, 0.5, i == 1 and 0 or 3),
			Size = UDim2.fromOffset(length, 1),
			Rotation = -45,
			Color = "InkFaint",
			ZIndex = 30,
			Parent = grip,
		})
	end
	grip.MouseEnter:Connect(function()
		tweenAll(gripBars, { BackgroundColor3 = Theme.Ink }, 0.15)
	end)
	grip.MouseLeave:Connect(function()
		tweenAll(gripBars, { BackgroundColor3 = Theme.InkFaint }, 0.15)
	end)
	self.Grip = grip

	-- Dragging: the window eases toward the pointer every frame (no tween restarts).
	local dragging, dragStart, dragOrigin = false, nil, nil
	self._dragTarget = nil
	masthead.InputBegan:Connect(function(input)
		if not self.Draggable or not isPointer(input) then
			return
		end
		dragging = true
		dragStart = input.Position
		dragOrigin = self._dragTarget or root.Position
		local connection
		connection = input.Changed:Connect(function()
			if input.UserInputState == Enum.UserInputState.End then
				dragging = false
				connection:Disconnect()
			end
		end)
	end)

	local resizing, resizeStart, resizeSize, resizePos = false, nil, nil, nil
	grip.InputBegan:Connect(function(input)
		if not self.Resizable or self.Minimized or not isPointer(input) then
			return
		end
		if self._dragTarget then
			root.Position = self._dragTarget
			self._dragTarget = nil
		end
		resizing = true
		resizeStart = input.Position
		resizeSize = self.Size
		resizePos = root.Position
		local connection
		connection = input.Changed:Connect(function()
			if input.UserInputState == Enum.UserInputState.End then
				resizing = false
				connection:Disconnect()
			end
		end)
	end)

	self:_connect(UserInputService.InputChanged, function(input)
		if not isMove(input) then
			return
		end
		if dragging then
			local delta = input.Position - dragStart
			self._dragTarget = UDim2.new(
				dragOrigin.X.Scale,
				dragOrigin.X.Offset + delta.X,
				dragOrigin.Y.Scale,
				dragOrigin.Y.Offset + delta.Y
			)
		elseif resizing then
			local delta = input.Position - resizeStart
			local viewport = workspace.CurrentCamera and workspace.CurrentCamera.ViewportSize or Vector2.new(1920, 1080)
			local width = math.clamp(resizeSize.X.Offset + delta.X, self.MinSize.X, viewport.X)
			local height = math.clamp(resizeSize.Y.Offset + delta.Y, self.MinSize.Y, viewport.Y)
			self.Size = UDim2.fromOffset(width, height)
			root.Size = self.Size
			root.Position = UDim2.new(
				resizePos.X.Scale,
				resizePos.X.Offset + (width - resizeSize.X.Offset) / 2,
				resizePos.Y.Scale,
				resizePos.Y.Offset + (height - resizeSize.Y.Offset) / 2
			)
		end
	end)

	self:_connect(RunService.RenderStepped, function(dt)
		local target = self._dragTarget
		if not target then
			return
		end
		local speed = 22 / math.max(Library.Settings.AnimationScale, 0.05)
		local alpha = 1 - math.exp(-dt * speed)
		local current = root.Position
		local x = current.X.Offset + (target.X.Offset - current.X.Offset) * alpha
		local y = current.Y.Offset + (target.Y.Offset - current.Y.Offset) * alpha
		if not dragging and math.abs(target.X.Offset - x) < 0.3 and math.abs(target.Y.Offset - y) < 0.3 then
			root.Position = target
			self._dragTarget = nil
		else
			root.Position = UDim2.new(target.X.Scale, x, target.Y.Scale, y)
		end
	end)

	-- Keybind -----------------------------------------------------------------
	self:_connect(UserInputService.InputBegan, function(input, processed)
		if not processed and self.Keybind and input.KeyCode == self.Keybind then
			self:Toggle()
		end
	end)

	self:_resetStatus()
	onThemeChanged(self.StatusLabel, function()
		if not self._statusCustom then
			self.StatusLabel.TextColor3 = Theme.InkFaint
		end
	end)
	self:_open()

	table.insert(Library.Windows, self)
	return self
end

function Window:_connect(signal, fn)
	local connection = signal:Connect(fn)
	table.insert(self.Connections, connection)
	return connection
end

-- Open: settle from 97% scale while the page veil lifts.
function Window:_open()
	self.Root.Visible = true
	self.Scale.Scale = 0.97
	tween(self.Scale, { Scale = 1 }, 0.4, Enum.EasingStyle.Quint)
	tween(self.Shadow, { ImageTransparency = 0.6 }, 0.4)
	liftVeil(self.PageVeil, 0.35)
end

function Window:_close(callback)
	tween(self.Scale, { Scale = 0.97 }, 0.22, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
	tween(self.Shadow, { ImageTransparency = 1 }, 0.22)
	local t = dropVeil(self.PageVeil, 0.2)
	t.Completed:Connect(function()
		if callback then
			callback()
		end
	end)
end

function Window:_resetStatus()
	self._statusCustom = false
	self.StatusLabel.TextColor3 = Theme.InkFaint
	if self.Keybind then
		self.StatusLabel.Text = self.Keybind.Name .. " to hide"
	else
		self.StatusLabel.Text = ""
	end
end

function Window:SetTitle(name, subtitle)
	if name then
		self.Name = name
		self.TitleLabel.Text = name
	end
	if subtitle then
		self.Subtitle = subtitle
		self.SubtitleLabel.Text = subtitle
	end
end

function Window:SetStatus(message, kind)
	if message == nil or message == "" then
		self:_resetStatus()
		return
	end
	self._statusCustom = true
	local label = self.StatusLabel
	local colorKey = (kind and Theme[kind]) and kind or "InkMuted"
	label.TextTransparency = 1
	label.Text = tostring(message)
	label.TextColor3 = Theme[colorKey]
	tween(label, { TextTransparency = 0 }, 0.3)
end

function Window:SetKeybind(keycode)
	self.Keybind = keycode
	if not self._statusCustom then
		self:_resetStatus()
	end
end

function Window:SetDraggable(enabled)
	self.Draggable = enabled == true
end

function Window:SetResizable(enabled)
	self.Resizable = enabled == true
	self.Grip.Visible = self.Resizable and not self.Minimized
end

function Window:OnClose(fn)
	table.insert(self.CloseCallbacks, fn)
end

function Window:SetTheme(theme)
	Library:SetTheme(theme)
end

function Window:Notify(options)
	return Library:Notify(options)
end

function Window:Minimize()
	if self._dragTarget then
		self.Root.Position = self._dragTarget
		self._dragTarget = nil
	end
	local fullHeight = self.Size.Y.Offset
	local collapsed = MASTHEAD + DOUBLE_RULE
	local shift = (fullHeight - collapsed) / 2
	local pos = self.Root.Position
	self.Minimized = not self.Minimized
	self.Grip.Visible = self.Resizable and not self.Minimized
	if self.Minimized then
		tween(self.Root, {
			Size = UDim2.new(self.Size.X.Scale, self.Size.X.Offset, 0, collapsed),
			Position = UDim2.new(pos.X.Scale, pos.X.Offset, pos.Y.Scale, pos.Y.Offset - shift),
		}, 0.4)
	else
		tween(self.Root, {
			Size = self.Size,
			Position = UDim2.new(pos.X.Scale, pos.X.Offset, pos.Y.Scale, pos.Y.Offset + shift),
		}, 0.4)
		liftVeil(self.ContentVeil, 0.4)
	end
end

function Window:Toggle(state)
	if state == nil then
		state = not self.Visible
	end
	if state == self.Visible then
		return
	end
	self.Visible = state
	if state then
		self:_open()
	else
		self:_close(function()
			if not self.Visible then
				self.Root.Visible = false
			end
		end)
	end
end

function Window:Destroy()
	if self.Destroyed then
		return
	end
	self.Destroyed = true
	for _, connection in ipairs(self.Connections) do
		connection:Disconnect()
	end
	table.clear(self.Connections)
	for _, tab in ipairs(self.Tabs) do
		for _, element in ipairs(tab._elements) do
			if element._cleanup then
				element:_cleanup()
			end
		end
	end
	local index = table.find(Library.Windows, self)
	if index then
		table.remove(Library.Windows, index)
	end
	for _, fn in ipairs(self.CloseCallbacks) do
		safeCall(fn)
	end
	self:_close(function()
		self.Gui:Destroy()
	end)
	task.delay(scaled(0.3) + 0.1, function()
		if self.Gui.Parent then
			self.Gui:Destroy()
		end
	end)
end

function Window:SelectTab(target)
	for _, tab in ipairs(self.Tabs) do
		if tab == target or tab.Name == target then
			tab:Select()
			return tab
		end
	end
end

--------------------------------------------------------------------------------
-- Dialogs
--------------------------------------------------------------------------------

function Window:Dialog(options)
	options = options or {}
	if self.Minimized then
		self:Minimize()
	end
	if not self.Visible then
		self:Toggle(true)
	end

	local dialog = { Closed = false }
	local width = options.Width or 400

	local overlay = create("TextButton", {
		Name = "DialogOverlay",
		Size = UDim2.fromScale(1, 1),
		BackgroundTransparency = 1,
		AutoButtonColor = false,
		Text = "",
		ZIndex = 50,
		Theme = { BackgroundColor3 = "Overlay" },
		Parent = self.Main,
	})

	local card = create("Frame", {
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.new(0.5, 0, 0.5, 8),
		Size = UDim2.new(0, width, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BorderSizePixel = 0,
		Active = true,
		Theme = { BackgroundColor3 = "Paper" },
		Parent = overlay,
	}, { stroke("Rule", 1), corner(4), padding(26, 22, 28, 28), listLayout(12) })
	local cardScale = create("UIScale", { Scale = 0.97, Parent = card })

	text({
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		Font = "Serif",
		Weight = Enum.FontWeight.Bold,
		TextSize = 21,
		TextWrapped = true,
		Text = options.Title or "Dialog",
		LayoutOrder = 1,
		Parent = card,
	})

	if options.Content and options.Content ~= "" then
		text({
			Size = UDim2.new(1, 0, 0, 0),
			AutomaticSize = Enum.AutomaticSize.Y,
			Font = "Serif",
			TextSize = 14,
			Color = "InkMuted",
			TextWrapped = true,
			LineHeight = 1.3,
			Text = options.Content,
			LayoutOrder = 2,
			Parent = card,
		})
	end

	local buttonRow = create("Frame", {
		Size = UDim2.new(1, 0, 0, 34),
		BackgroundTransparency = 1,
		LayoutOrder = 3,
		Parent = card,
	}, {
		create("UIListLayout", {
			FillDirection = Enum.FillDirection.Horizontal,
			HorizontalAlignment = Enum.HorizontalAlignment.Right,
			VerticalAlignment = Enum.VerticalAlignment.Center,
			SortOrder = Enum.SortOrder.LayoutOrder,
			Padding = UDim.new(0, 18),
		}),
	})

	local keyConnection

	function dialog:Close()
		if self.Closed then
			return
		end
		self.Closed = true
		if keyConnection then
			keyConnection:Disconnect()
		end
		tween(overlay, { BackgroundTransparency = 1 }, 0.18)
		tween(card, { Position = UDim2.new(0.5, 0, 0.5, 8) }, 0.18, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
		local t = tween(cardScale, { Scale = 0.96 }, 0.18, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
		t.Completed:Connect(function()
			overlay:Destroy()
		end)
		safeCall(options.OnClose)
	end

	local activators = {}
	local buttons = options.Buttons or { { Title = "OK", Style = "Primary" } }
	-- Rendered right-to-left reading order: secondary links first, primary action last (rightmost).
	for i, def in ipairs(buttons) do
		local style = def.Style or (i == 1 and "Primary" or "Secondary")
		local button
		if style == "Secondary" then
			button = link({ Size = UDim2.fromOffset(0, 30), TextSize = 15, Text = def.Title or "Cancel", LayoutOrder = i })
		else
			local fillKey = style == "Danger" and "Danger" or "Accent"
			button = text({
				Class = "TextButton",
				Size = UDim2.fromOffset(0, 34),
				AutomaticSize = Enum.AutomaticSize.X,
				Weight = Enum.FontWeight.SemiBold,
				TextSize = 15,
				Color = "OnAccent",
				Text = def.Title or "OK",
				LayoutOrder = -i,
				BackgroundTransparency = 0,
				Theme = nil,
			})
			bind(button, { BackgroundColor3 = fillKey })
			padding(0, 0, 18, 18).Parent = button
			corner(4).Parent = button
			button.MouseEnter:Connect(function()
				tween(button, { BackgroundTransparency = 0.12 }, 0.15)
			end)
			button.MouseLeave:Connect(function()
				tween(button, { BackgroundTransparency = 0 }, 0.15)
			end)
		end
		button.Parent = buttonRow

		local function activate()
			if dialog.Closed then
				return
			end
			click()
			local keepOpen = false
			if typeof(def.Callback) == "function" then
				local ok, result = pcall(def.Callback)
				if not ok then
					warn("[Verdant] Dialog callback error: " .. tostring(result))
				end
				keepOpen = ok and result == false
			end
			if not keepOpen then
				dialog:Close()
			end
		end
		activators[i] = activate
		button.MouseButton1Click:Connect(activate)
	end

	-- Primary (filled) buttons sit rightmost; secondary links to their left.
	for _, child in ipairs(buttonRow:GetChildren()) do
		if child:IsA("TextButton") then
			child.LayoutOrder = child.BackgroundTransparency < 1 and (1000 + child.LayoutOrder) or child.LayoutOrder
		end
	end

	keyConnection = UserInputService.InputBegan:Connect(function(input, processed)
		if processed or dialog.Closed then
			return
		end
		if input.KeyCode == Enum.KeyCode.Return or input.KeyCode == Enum.KeyCode.KeypadEnter then
			activators[1]()
		elseif input.KeyCode == Enum.KeyCode.Escape then
			activators[#activators]()
		end
	end)

	overlay.MouseButton1Click:Connect(function()
		if options.CloseOnOutsideClick then
			dialog:Close()
		end
	end)

	tween(overlay, { BackgroundTransparency = 0.5 }, 0.25)
	tween(card, { Position = UDim2.fromScale(0.5, 0.5) }, 0.35)
	tween(cardScale, { Scale = 1 }, 0.35)
	return dialog
end

function Window:Confirm(options)
	options = options or {}
	local function respond(confirmed)
		return function()
			safeCall(confirmed and options.OnConfirm or options.OnCancel)
			safeCall(options.Callback, confirmed)
		end
	end
	return self:Dialog({
		Title = options.Title or "Are you sure?",
		Content = options.Content,
		Width = options.Width,
		Buttons = {
			{ Title = options.ConfirmText or "Confirm", Style = options.Danger and "Danger" or "Primary", Callback = respond(true) },
			{ Title = options.CancelText or "Cancel", Style = "Secondary", Callback = respond(false) },
		},
	})
end

--------------------------------------------------------------------------------
-- Tabs
--------------------------------------------------------------------------------

function Window:AddTab(options)
	options = options or {}
	local tab = setmetatable({}, Tab)
	tab.Window = self
	tab.Tab = tab
	tab.Name = options.Name or ("Tab " .. (#self.Tabs + 1))
	tab.Index = #self.Tabs + 1
	tab._order = 0
	tab._elements = {}

	local button = create("TextButton", {
		Name = tab.Name,
		Size = UDim2.new(0, 0, 1, 0),
		AutomaticSize = Enum.AutomaticSize.X,
		BackgroundTransparency = 1,
		AutoButtonColor = false,
		Text = "",
		LayoutOrder = tab.Index,
		Parent = self.TabList,
	}, {
		create("UIListLayout", {
			FillDirection = Enum.FillDirection.Horizontal,
			VerticalAlignment = Enum.VerticalAlignment.Center,
			SortOrder = Enum.SortOrder.LayoutOrder,
			Padding = UDim.new(0, 7),
		}),
	})

	local icon = create("ImageLabel", {
		Size = UDim2.fromOffset(14, 14),
		BackgroundTransparency = 1,
		ImageColor3 = Theme.InkFaint,
		Visible = false,
		LayoutOrder = 1,
		Parent = button,
	})

	local nameLabel = text({
		Size = UDim2.new(0, 0, 1, 0),
		AutomaticSize = Enum.AutomaticSize.X,
		TextSize = 15,
		Color = false,
		TextColor3 = Theme.InkFaint,
		Text = tab.Name,
		LayoutOrder = 2,
		Parent = button,
	})

	local page = create("ScrollingFrame", {
		Name = tab.Name,
		Size = UDim2.fromScale(1, 1),
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		ScrollBarThickness = 2,
		ScrollBarImageTransparency = 0.4,
		VerticalScrollBarInset = Enum.ScrollBarInset.ScrollBar,
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollingDirection = Enum.ScrollingDirection.Y,
		Visible = false,
		Theme = { ScrollBarImageColor3 = "InkFaint" },
		Parent = self.Content,
	}, { listLayout(0), padding(22, 30, 18, 18) })

	-- Page heading: the tab name set large, with an optional italic standfirst.
	local heading = create("Frame", {
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 1,
		LayoutOrder = 0,
		Parent = page,
	}, { listLayout(4), padding(0, 14, ROW_INSET, ROW_INSET) })

	tab.HeadingTitle = text({
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		Font = "Serif",
		Weight = Enum.FontWeight.Bold,
		TextSize = 28,
		TextWrapped = true,
		Text = tab.Name,
		LayoutOrder = 1,
		Parent = heading,
	})
	tab.HeadingDescription = text({
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		Font = "Serif",
		Italic = true,
		TextSize = 14,
		Color = "InkMuted",
		TextWrapped = true,
		Text = options.Description or "",
		Visible = options.Description ~= nil and options.Description ~= "",
		LayoutOrder = 2,
		Parent = heading,
	})

	tab.Button = button
	tab.Icon = icon
	tab.Label = nameLabel
	tab.Page = page
	tab.Container = page

	tab:SetImage(options.Image or options.Icon)

	button.MouseEnter:Connect(function()
		if self.ActiveTab ~= tab then
			tween(nameLabel, { TextColor3 = Theme.InkMuted }, 0.15)
		end
	end)
	button.MouseLeave:Connect(function()
		if self.ActiveTab ~= tab then
			tween(nameLabel, { TextColor3 = Theme.InkFaint }, 0.15)
		end
	end)
	button.MouseButton1Click:Connect(function()
		if self.ActiveTab ~= tab then
			click(0.15)
		end
		tab:Select()
	end)
	-- Fonts load asynchronously; keep the underline matched to the label's real width.
	button:GetPropertyChangedSignal("AbsoluteSize"):Connect(function()
		if self.ActiveTab == tab then
			tab:_placeIndicator(0)
		end
	end)

	onThemeChanged(button, function()
		tab:_style(self.ActiveTab == tab, 0.3)
	end)

	table.insert(self.Tabs, tab)
	if not self.ActiveTab then
		tab:Select()
	end
	return tab
end

function Tab:SetName(name)
	self.Name = name
	self.Label.Text = name
	self.HeadingTitle.Text = name
end

function Tab:SetDescription(description)
	self.HeadingDescription.Text = description or ""
	self.HeadingDescription.Visible = description ~= nil and description ~= ""
end

function Tab:SetImage(image)
	local asset = toAsset(image)
	self.Icon.Image = asset or ""
	self.Icon.Visible = asset ~= nil
end

function Tab:_placeIndicator(duration)
	local window = self.Window
	local x = self.Button.AbsolutePosition.X - window.TabList.AbsolutePosition.X
	local width = self.Button.AbsoluteSize.X
	tween(window.TabIndicator, {
		Position = UDim2.new(0, x, 1, 0),
		Size = UDim2.new(0, width, 0, 2),
	}, duration)
end

function Tab:_style(active, duration)
	tween(self.Label, { TextColor3 = active and Theme.Ink or Theme.InkFaint }, duration)
	tween(self.Icon, { ImageColor3 = active and Theme.Ink or Theme.InkFaint }, duration)
end

function Tab:_setActive(active)
	self:_style(active, 0.2)
	if not active then
		self.Page.Visible = false
		return
	end
	local window = self.Window
	self:_placeIndicator(0.35)

	self.Page.Visible = true
	self.Page.CanvasPosition = Vector2.zero
	self.Page.Position = UDim2.fromOffset(0, 10)
	tween(self.Page, { Position = UDim2.fromOffset(0, 0) }, 0.4)
	liftVeil(window.ContentVeil, 0.3)
end

function Tab:Select()
	local window = self.Window
	if window.ActiveTab == self then
		return
	end
	if window.ActiveTab then
		window.ActiveTab:_setActive(false)
	end
	window.ActiveTab = self
	self:_setActive(true)
end

--------------------------------------------------------------------------------
-- Elements: shared behaviour
--------------------------------------------------------------------------------

function Element:Get()
	return self.Value
end

function Element:SetName(name)
	self.Name = name
	self.Title.Text = name
end

function Element:SetDescription(description)
	self.Description.Text = description or ""
	self.Description.Visible = description ~= nil and description ~= ""
end

function Element:SetVisible(visible)
	self.Frame.Visible = visible == true
end

function Element:SetLocked(locked)
	self.Locked = locked == true
	local transparency = self.Locked and 0.55 or 0
	for _, child in ipairs(self.Frame:GetDescendants()) do
		if child:IsA("TextLabel") or child:IsA("TextBox") or child:IsA("TextButton") then
			tween(child, { TextTransparency = transparency }, 0.2)
		end
	end
	if self.Locked and self.Close then
		self:Close()
	end
end

function Element:OnChanged(fn)
	table.insert(self._listeners, fn)
	local listeners = self._listeners
	return {
		Disconnect = function()
			local index = table.find(listeners, fn)
			if index then
				table.remove(listeners, index)
			end
		end,
	}
end

function Element:_fire(...)
	safeCall(self.Callback, ...)
	for _, fn in ipairs(self._listeners) do
		safeCall(fn, ...)
	end
end

function Element:Destroy()
	if self.Id and Library.Flags[self.Id] == self then
		Library.Flags[self.Id] = nil
	end
	local index = table.find(Library.Elements, self)
	if index then
		table.remove(Library.Elements, index)
	end
	if self._cleanup then
		self:_cleanup()
	end
	local frame = self.Frame
	frame.AutomaticSize = Enum.AutomaticSize.None
	frame.Size = UDim2.new(1, 0, 0, frame.AbsoluteSize.Y)
	frame.ClipsDescendants = true
	local t = tween(frame, { Size = UDim2.new(1, 0, 0, 0) }, 0.25, Enum.EasingStyle.Quint, Enum.EasingDirection.In)
	t.Completed:Connect(function()
		frame:Destroy()
	end)
end

-- Gives a value element its config ID: options.Flag / options.Id if set, otherwise
-- "Tab/Section/Name" from the names it was created with (renaming later keeps the ID).
-- Auto IDs that collide get " #2", " #3", ... in creation order.
local function register(container, options, element, typeName)
	element.Type = typeName
	local id = options.Flag or options.Id
	if not id then
		local parts = { container.Tab.Name }
		if container ~= container.Tab then
			table.insert(parts, container.Name)
		end
		table.insert(parts, element.Name ~= "" and element.Name or typeName)
		local base = table.concat(parts, "/")
		id = base
		local n = 1
		while Library.Flags[id] ~= nil do
			n += 1
			id = base .. " #" .. n
		end
	end
	element.Id = id
	element.Flag = id
	Library.Flags[id] = element
	table.insert(Library.Elements, element)
end

--[[
	The shared row:

	  Name                                              [control]
	  Description, set in italic serif.
	  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

	`rightWidth` px on the right are reserved for the control (element.Control).
	mode: "hover" (tint on hover) or "none". Extra content (slider track, dropdown list)
	goes into element.Frame between the header (LayoutOrder 1) and the rule (LayoutOrder 99).
]]
function Tab:_element(options, rightWidth, mode)
	mode = mode or "hover"
	self._order += 1

	local frame = create("Frame", {
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		ClipsDescendants = true,
		LayoutOrder = self._order,
		Theme = { BackgroundColor3 = "Raised" },
		Parent = self.Container,
	}, { listLayout(0), corner(4) })

	local header = create("TextButton", {
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 1,
		AutoButtonColor = false,
		Text = "",
		LayoutOrder = 1,
		Parent = frame,
	})

	local labels = create("Frame", {
		Position = UDim2.fromOffset(ROW_INSET, 0),
		Size = UDim2.new(1, -(ROW_INSET * 2 + rightWidth + (rightWidth > 0 and 20 or 0)), 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 1,
		Parent = header,
	}, { listLayout(3), padding(13, 13, 0, 0) })

	local title = text({
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		TextSize = 15,
		TextWrapped = true,
		Text = options.Name or options.Title or "",
		LayoutOrder = 1,
		Parent = labels,
	})

	local description = text({
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		Font = "Serif",
		Italic = true,
		TextSize = 13,
		Color = "InkMuted",
		TextWrapped = true,
		Text = options.Description or "",
		Visible = options.Description ~= nil and options.Description ~= "",
		LayoutOrder = 2,
		Parent = labels,
	})

	local control = create("Frame", {
		AnchorPoint = Vector2.new(1, 0.5),
		Position = UDim2.new(1, -ROW_INSET, 0.5, 0),
		Size = UDim2.fromOffset(rightWidth, 28),
		BackgroundTransparency = 1,
		Parent = header,
	})

	local divider = create("Frame", {
		Size = UDim2.new(1, 0, 0, 1),
		BackgroundTransparency = 1,
		LayoutOrder = 99,
		Parent = frame,
	})
	rule({ Position = UDim2.fromOffset(ROW_INSET, 0), Size = UDim2.new(1, -ROW_INSET * 2, 1, 0), Parent = divider })

	local element = setmetatable({
		Window = self.Window,
		Name = options.Name or options.Title or "",
		Callback = options.Callback,
		Locked = false,
		Frame = frame,
		Header = header,
		Title = title,
		Description = description,
		Control = control,
		_listeners = {},
		_hovered = false,
	}, Element)

	if mode == "hover" then
		header.MouseEnter:Connect(function()
			element._hovered = true
			if not element.Locked then
				tween(frame, { BackgroundTransparency = 0.35 }, 0.15)
			end
		end)
		header.MouseLeave:Connect(function()
			element._hovered = false
			tween(frame, { BackgroundTransparency = 1 }, 0.2)
		end)
	end

	table.insert(self.Tab._elements, element)

	if options.Locked then
		task.defer(function()
			element:SetLocked(true)
		end)
	end
	return element
end

--------------------------------------------------------------------------------
-- Section
--------------------------------------------------------------------------------

function Tab:AddSection(options)
	if typeof(options) == "string" then
		options = { Name = options }
	end
	options = options or {}
	self._order += 1

	local holder = create("Frame", {
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 1,
		LayoutOrder = self._order,
		Parent = self.Container,
	}, { listLayout(0), padding(22, 0, 0, 0) })

	local headerRow = create("Frame", {
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 1,
		LayoutOrder = 0,
		Parent = holder,
	}, { padding(0, 8, ROW_INSET, ROW_INSET) })

	local title = text({
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		Font = "Serif",
		Weight = Enum.FontWeight.Bold,
		TextSize = 17,
		TextWrapped = true,
		Text = options.Name or "Section",
		Parent = headerRow,
	})

	-- A strong rule under the subhead; rows below carry their own hairlines.
	local ruleHolder = create("Frame", {
		Size = UDim2.new(1, 0, 0, 1),
		BackgroundTransparency = 1,
		LayoutOrder = 1,
		Parent = holder,
	})
	rule({
		Position = UDim2.fromOffset(ROW_INSET, 0),
		Size = UDim2.new(1, -ROW_INSET * 2, 1, 0),
		Color = "Ink",
		Parent = ruleHolder,
	})

	local section = setmetatable({
		Window = self.Window,
		Tab = self.Tab,
		Name = options.Name or "Section",
		Container = holder,
		Frame = holder,
		_order = 1,
	}, Tab)

	function section:SetName(name)
		self.Name = name
		title.Text = name
	end

	function section:SetVisible(visible)
		holder.Visible = visible == true
	end

	return section
end

--------------------------------------------------------------------------------
-- Button
--------------------------------------------------------------------------------

function Tab:AddButton(options)
	options = options or {}
	local idleText = options.Hint or "Run"
	local button = self:_element(options, 110, "hover")

	local action = create("Frame", {
		AnchorPoint = Vector2.new(1, 0.5),
		Position = UDim2.fromScale(1, 0.5),
		Size = UDim2.new(1, 0, 1, 0),
		BackgroundTransparency = 1,
		Parent = button.Control,
	})

	local arrow = text({
		AnchorPoint = Vector2.new(1, 0.5),
		Position = UDim2.new(1, 0, 0.5, 0),
		Size = UDim2.fromOffset(16, 22),
		TextSize = 16,
		Color = false,
		TextColor3 = Theme.InkMuted,
		TextXAlignment = Enum.TextXAlignment.Right,
		Text = "â†’",
		Parent = action,
	})

	local hint = text({
		AnchorPoint = Vector2.new(1, 0.5),
		Position = UDim2.new(1, -22, 0.5, 0),
		Size = UDim2.fromOffset(0, 22),
		AutomaticSize = Enum.AutomaticSize.X,
		TextSize = 15,
		Color = false,
		TextColor3 = Theme.InkMuted,
		TextXAlignment = Enum.TextXAlignment.Right,
		Text = idleText,
		Parent = action,
	})
	local underline = rule({
		AnchorPoint = Vector2.new(1, 1),
		Position = UDim2.new(1, 0, 1, -2),
		Size = UDim2.new(0, 0, 0, 1),
		Color = "Accent",
		Parent = hint,
	})

	local statusToken
	local function setHint(message, colorKey)
		tween(hint, { TextTransparency = 1 }, 0.1).Completed:Wait()
		hint.Text = message
		hint.TextColor3 = Theme[colorKey]
		tween(hint, { TextTransparency = button.Locked and 0.55 or 0 }, 0.15)
	end

	local function setHover(on)
		local colorKey = on and "Accent" or "InkMuted"
		if not statusToken then
			tween(hint, { TextColor3 = Theme[colorKey] }, 0.15)
		end
		tween(arrow, { TextColor3 = Theme[colorKey], Position = UDim2.new(1, on and 3 or 0, 0.5, 0) }, 0.25)
		tween(underline, { Size = UDim2.new(on and 1 or 0, 0, 0, 1) }, 0.25)
	end

	button.Header.MouseEnter:Connect(function()
		if not button.Locked then
			setHover(true)
		end
	end)
	button.Header.MouseLeave:Connect(function()
		setHover(false)
	end)

	function button:Fire()
		local token = {}
		statusToken = token
		task.spawn(function()
			local ok, err = true, nil
			if typeof(self.Callback) == "function" then
				ok, err = pcall(self.Callback)
			end
			for _, fn in ipairs(self._listeners) do
				safeCall(fn)
			end
			if not ok then
				warn("[Verdant] Callback error: " .. tostring(err))
			end
			if statusToken ~= token then
				return
			end
			setHint(ok and "Done" or "Failed", ok and "Accent" or "Danger")
			task.wait(1.4)
			if statusToken == token then
				statusToken = nil
				setHint(idleText, button._hovered and "Accent" or "InkMuted")
			end
		end)
	end

	function button:SetCallback(callback)
		self.Callback = callback
	end

	button.Header.MouseButton1Click:Connect(function()
		if button.Locked then
			return
		end
		click()
		-- The arrow pushes forward on press.
		arrow.Position = UDim2.new(1, 8, 0.5, 0)
		tween(arrow, { Position = UDim2.new(1, button._hovered and 3 or 0, 0.5, 0) }, 0.35)
		button:Fire()
	end)

	return button
end

--------------------------------------------------------------------------------
-- Toggle: "Off  On", the current word underlined.
--------------------------------------------------------------------------------

function Tab:AddToggle(options)
	options = options or {}
	local toggle = self:_element(options, 80, "hover")
	toggle.Value = options.Default == true

	local words = create("Frame", {
		AnchorPoint = Vector2.new(1, 0.5),
		Position = UDim2.fromScale(1, 0.5),
		Size = UDim2.new(0, 0, 0, 22),
		AutomaticSize = Enum.AutomaticSize.X,
		BackgroundTransparency = 1,
		Parent = toggle.Control,
	}, {
		create("UIListLayout", {
			FillDirection = Enum.FillDirection.Horizontal,
			VerticalAlignment = Enum.VerticalAlignment.Center,
			SortOrder = Enum.SortOrder.LayoutOrder,
			Padding = UDim.new(0, 12),
		}),
	})

	local function word(label, order)
		return text({
			Class = "TextButton",
			Size = UDim2.new(0, 0, 1, 0),
			AutomaticSize = Enum.AutomaticSize.X,
			TextSize = 15,
			Color = false,
			Text = label,
			LayoutOrder = order,
			Parent = words,
		})
	end
	local offWord = word("Off", 1)
	local onWord = word("On", 2)

	local underline = rule({
		AnchorPoint = Vector2.new(0, 1),
		Size = UDim2.new(0, 0, 0, 2),
		Color = false,
		Parent = toggle.Control,
	})
	underline.BackgroundColor3 = Theme.Ink

	-- Measured from sizes only (the words sit flush right), so dragging the window
	-- doesn't trigger any work.
	local function render(duration)
		local selected = toggle.Value and onWord or offWord
		local other = toggle.Value and offWord or onWord
		tween(selected, { TextColor3 = Theme.Ink }, duration)
		tween(other, { TextColor3 = Theme.InkFaint }, duration)
		local x = toggle.Control.AbsoluteSize.X - words.AbsoluteSize.X
		if toggle.Value then
			x += offWord.AbsoluteSize.X + 12
		end
		tween(underline, {
			Position = UDim2.new(0, x, 0.5, 12),
			Size = UDim2.new(0, selected.AbsoluteSize.X, 0, 2),
			BackgroundColor3 = toggle.Value and Theme.Accent or Theme.InkMuted,
		}, duration)
	end

	function toggle:Set(value, silent)
		self.Value = value == true
		render(0.3)
		if not silent then
			self:_fire(self.Value)
		end
	end

	local function choose(value)
		if toggle.Locked then
			return
		end
		click(0.15)
		toggle:Set(value)
	end

	toggle.Header.MouseButton1Click:Connect(function()
		choose(not toggle.Value)
	end)
	offWord.MouseButton1Click:Connect(function()
		choose(false)
	end)
	onWord.MouseButton1Click:Connect(function()
		choose(true)
	end)

	-- Keep the underline aligned once fonts load.
	words:GetPropertyChangedSignal("AbsoluteSize"):Connect(function()
		render(0)
	end)

	onThemeChanged(words, function()
		render(0.3)
	end)

	render(0)
	register(self, options, toggle, "Toggle")
	return toggle
end

--------------------------------------------------------------------------------
-- Slider: a large number on the right, a ruler track underneath.
--------------------------------------------------------------------------------

function Tab:AddSlider(options)
	options = options or {}
	local window = self.Window
	local min = options.Min or 0
	local max = options.Max or 100
	if max <= min then
		max = min + 1
	end
	local increment = options.Increment or 1
	local suffix = options.Suffix or ""
	local decimalPart = tostring(increment):match("%.(%d+)")
	local decimals = decimalPart and #decimalPart or 0

	local slider = self:_element(options, 110, "hover")
	slider.Min = min
	slider.Max = max

	local function round(value)
		value = math.clamp(value, min, max)
		value = min + math.floor((value - min) / increment + 0.5) * increment
		value = math.clamp(value, min, max)
		return tonumber(string.format("%." .. decimals .. "f", value))
	end

	local function format(value)
		return string.format("%." .. decimals .. "f", value) .. suffix
	end

	local valueBox = text({
		Class = "TextBox",
		AnchorPoint = Vector2.new(1, 0.5),
		Position = UDim2.fromScale(1, 0.5),
		Size = UDim2.new(1, 0, 0, 28),
		Font = "Serif",
		Weight = Enum.FontWeight.Bold,
		TextSize = 20,
		TextXAlignment = Enum.TextXAlignment.Right,
		ClearTextOnFocus = false,
		Text = "",
		Parent = slider.Control,
	})

	-- Ruler track row
	local trackRow = create("Frame", {
		Size = UDim2.new(1, 0, 0, 26),
		BackgroundTransparency = 1,
		LayoutOrder = 2,
		Parent = slider.Frame,
	})
	local track = create("Frame", {
		Position = UDim2.fromOffset(ROW_INSET, 4),
		Size = UDim2.new(1, -ROW_INSET * 2, 0, 12),
		BackgroundTransparency = 1,
		Parent = trackRow,
	})
	rule({
		AnchorPoint = Vector2.new(0, 0.5),
		Position = UDim2.fromScale(0, 0.5),
		Size = UDim2.new(1, 0, 0, 1),
		Parent = track,
	})
	for i = 0, 10 do
		rule({
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromScale(i / 10, 0.5),
			Size = UDim2.fromOffset(1, (i % 5 == 0) and 9 or 5),
			Parent = track,
		})
	end
	local fill = rule({
		AnchorPoint = Vector2.new(0, 0.5),
		Position = UDim2.fromScale(0, 0.5),
		Size = UDim2.new(0, 0, 0, 2),
		Color = "Accent",
		Parent = track,
	})
	local handle = rule({
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0, 0.5),
		Size = UDim2.fromOffset(2, 14),
		Color = false,
		ZIndex = 2,
		Parent = track,
	})
	handle.BackgroundColor3 = Theme.Ink

	local hitbox = create("TextButton", {
		Size = UDim2.fromScale(1, 1),
		BackgroundTransparency = 1,
		AutoButtonColor = false,
		Text = "",
		ZIndex = 3,
		Parent = trackRow,
	})

	local active = false
	local function render(duration)
		local alpha = (slider.Value - min) / (max - min)
		tween(fill, { Size = UDim2.new(alpha, 0, 0, 2) }, duration)
		tween(handle, { Position = UDim2.fromScale(alpha, 0.5) }, duration)
		valueBox.Text = format(slider.Value)
	end

	local function styleHandle()
		local big = active or slider._hovered
		tween(handle, {
			Size = UDim2.fromOffset(2, big and 18 or 14),
			BackgroundColor3 = active and Theme.Accent or Theme.Ink,
		}, 0.15)
	end

	function slider:Set(value, silent)
		local rounded = round(tonumber(value) or self.Value)
		local changed = rounded ~= self.Value
		self.Value = rounded
		render(0.1)
		if changed and not silent then
			self:_fire(self.Value)
		end
	end

	local dragging = false
	local function updateFromX(x)
		local alpha = math.clamp((x - track.AbsolutePosition.X) / track.AbsoluteSize.X, 0, 1)
		slider:Set(min + (max - min) * alpha)
	end

	local function hoverRow(on)
		slider._hovered = on
		if not slider.Locked then
			tween(slider.Frame, { BackgroundTransparency = (on or dragging) and 0.35 or 1 }, 0.15)
		end
		styleHandle()
	end

	hitbox.InputBegan:Connect(function(input)
		if slider.Locked or not isPointer(input) then
			return
		end
		dragging = true
		active = true
		styleHandle()
		updateFromX(input.Position.X)
	end)
	hitbox.MouseEnter:Connect(function()
		hoverRow(true)
	end)
	hitbox.MouseLeave:Connect(function()
		hoverRow(false)
	end)
	slider.Header.MouseEnter:Connect(function()
		styleHandle()
	end)
	slider.Header.MouseLeave:Connect(function()
		styleHandle()
	end)
	window:_connect(UserInputService.InputChanged, function(input)
		if dragging and isMove(input) then
			updateFromX(input.Position.X)
		end
	end)
	window:_connect(UserInputService.InputEnded, function(input)
		if dragging and isPointer(input) then
			dragging = false
			active = false
			click(0.1)
			hoverRow(slider._hovered)
		end
	end)

	valueBox.Focused:Connect(function()
		if slider.Locked then
			valueBox:ReleaseFocus()
			return
		end
		tween(valueBox, { TextColor3 = Theme.Accent }, 0.15)
	end)
	valueBox.FocusLost:Connect(function()
		tween(valueBox, { TextColor3 = Theme.Ink }, 0.15)
		local number = tonumber((valueBox.Text:gsub("[^%d%.%-]", "")))
		if number and not slider.Locked then
			slider:Set(number)
		end
		valueBox.Text = format(slider.Value)
	end)

	onThemeChanged(track, function()
		styleHandle()
	end)

	slider.Value = round(options.Default or min)
	render(0)
	register(self, options, slider, "Slider")
	return slider
end

--------------------------------------------------------------------------------
-- Textbox: an underlined field, like a form on paper.
--------------------------------------------------------------------------------

function Tab:AddTextbox(options)
	options = options or {}
	local textbox = self:_element(options, 210, "hover")
	textbox.Value = options.Default or ""

	local box = text({
		Class = "TextBox",
		Size = UDim2.new(1, 0, 1, 0),
		TextSize = 15,
		PlaceholderText = options.Placeholder or "Type here",
		TextTruncate = Enum.TextTruncate.AtEnd,
		ClearTextOnFocus = options.ClearOnFocus == true,
		Text = textbox.Value,
		Parent = textbox.Control,
	})

	rule({
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.fromScale(0, 1),
		Size = UDim2.new(1, 0, 0, 1),
		Color = "InkFaint",
		Parent = textbox.Control,
	})
	local focusLine = rule({
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.fromScale(0, 1),
		Size = UDim2.new(0, 0, 0, 2),
		Color = "Accent",
		Parent = textbox.Control,
	})

	if options.NumbersOnly then
		box:GetPropertyChangedSignal("Text"):Connect(function()
			local filtered = box.Text:gsub("[^%d%.%-]", "")
			if filtered ~= box.Text then
				box.Text = filtered
			end
		end)
	end

	textbox.Header.MouseButton1Click:Connect(function()
		if not textbox.Locked then
			box:CaptureFocus()
		end
	end)

	box.Focused:Connect(function()
		if textbox.Locked then
			box:ReleaseFocus()
			return
		end
		tween(focusLine, { Size = UDim2.new(1, 0, 0, 2) }, 0.35)
	end)
	box.FocusLost:Connect(function(enterPressed)
		tween(focusLine, { Size = UDim2.new(0, 0, 0, 2) }, 0.3)
		if textbox.Locked then
			box.Text = textbox.Value
			return
		end
		textbox.Value = box.Text
		textbox:_fire(box.Text, enterPressed)
	end)

	function textbox:Set(value, silent)
		self.Value = tostring(value)
		box.Text = self.Value
		if not silent then
			self:_fire(self.Value, false)
		end
	end

	register(self, options, textbox, "Textbox")
	return textbox
end

--------------------------------------------------------------------------------
-- Label & Paragraph
--------------------------------------------------------------------------------

local function freeformElement(tab, name)
	tab._order += 1
	local frame = create("Frame", {
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 1,
		LayoutOrder = tab._order,
		Parent = tab.Container,
	}, { padding(12, 12, ROW_INSET, ROW_INSET), listLayout(6) })
	local element = setmetatable({
		Window = tab.Window,
		Name = name,
		Locked = false,
		Frame = frame,
		_listeners = {},
	}, Element)
	table.insert(tab.Tab._elements, element)
	return element
end

function Tab:AddLabel(options)
	if typeof(options) == "string" then
		options = { Text = options }
	end
	options = options or {}
	local value = options.Text or options.Name or "Label"
	local element = freeformElement(self, value)

	element.Title = text({
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		TextSize = 15,
		Color = false,
		TextColor3 = Theme.InkMuted,
		TextWrapped = true,
		Text = value,
		Parent = element.Frame,
	})
	element.Description = element.Title
	element.Text = value
	element.Value = value

	function element:Set(newText)
		self.Text = tostring(newText)
		self.Value = self.Text
		self.Title.Text = self.Text
	end

	function element:SetColor(color)
		tween(self.Title, { TextColor3 = color }, 0.2)
	end

	-- A label is just its text; there is no separate description line.
	function element:SetDescription() end

	onThemeChanged(element.Frame, function()
		element.Title.TextColor3 = Theme.InkMuted
	end)

	return element
end

function Tab:AddParagraph(options)
	options = options or {}
	local element = freeformElement(self, options.Title or "Paragraph")
	element.TitleText = options.Title or "Paragraph"
	element.Content = options.Content or ""

	element.Title = text({
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		Font = "Serif",
		Weight = Enum.FontWeight.Bold,
		TextSize = 16,
		TextWrapped = true,
		Text = element.TitleText,
		LayoutOrder = 1,
		Parent = element.Frame,
	})

	element.Description = text({
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		Font = "Serif",
		TextSize = 14,
		Color = "InkMuted",
		TextWrapped = true,
		LineHeight = 1.35,
		Text = element.Content,
		LayoutOrder = 2,
		Parent = element.Frame,
	})

	function element:Set(newOptions)
		if typeof(newOptions) == "string" then
			newOptions = { Content = newOptions }
		end
		if newOptions.Title then
			self.TitleText = newOptions.Title
			self.Title.Text = newOptions.Title
		end
		if newOptions.Content then
			self.Content = newOptions.Content
			self.Description.Text = newOptions.Content
		end
	end

	function element:SetName(name)
		self:Set({ Title = name })
	end

	function element:SetDescription(description)
		self:Set({ Content = description })
	end

	function element:SetTitle(title)
		self:Set({ Title = title })
	end

	function element:SetContent(content)
		self:Set({ Content = content })
	end

	return element
end

--------------------------------------------------------------------------------
-- Selector (shared by Dropdown and PlayerSelector)
--------------------------------------------------------------------------------

--[[
	adapter = {
		type = "Dropdown" | "PlayerSelector",
		placeholder = string,
		text = function(option) -> string,         -- shown in the value area
		search = function(option) -> string,       -- matched against the search field
		icon = function(option) -> image | nil,    -- optional image beside the value
		renderRow = function(row, option) -> primaryLabel,
		normalize = function(value) -> value,      -- optional, converts user input for :Set
	}
]]
function Tab:_selector(options, adapter)
	local MAX_VISIBLE = options.MaxVisible or 7
	local RIGHT = 220

	local selector = self:_element(options, RIGHT, "hover")
	selector.Options = table.clone(options.Options or {})
	selector.Multi = options.Multi == true
	selector.Open = false
	selector.Value = selector.Multi and {} or nil

	local control = selector.Control

	-- Value area: right-aligned value, optional avatar, chevron.
	local arrow, arrowBars = chevron(control, "InkMuted", {
		AnchorPoint = Vector2.new(1, 0.5),
		Position = UDim2.new(1, 0, 0.5, 1),
	})

	local valueLabel = text({
		AnchorPoint = Vector2.new(1, 0.5),
		Position = UDim2.new(1, -20, 0.5, 0),
		Size = UDim2.new(1, -20, 0, 22),
		TextSize = 15,
		Color = false,
		TextXAlignment = Enum.TextXAlignment.Right,
		TextTruncate = Enum.TextTruncate.AtEnd,
		Parent = control,
	})

	local valueIcon
	if adapter.icon then
		valueIcon = create("ImageLabel", {
			AnchorPoint = Vector2.new(1, 0.5),
			Position = UDim2.new(1, -20, 0.5, 0),
			Size = UDim2.fromOffset(20, 20),
			Visible = false,
			Theme = { BackgroundColor3 = "Raised" },
			Parent = control,
		}, { corner(4) })
	end

	local function placeIcon()
		if not valueIcon then
			return
		end
		local textWidth = math.min(valueLabel.TextBounds.X, valueLabel.AbsoluteSize.X)
		valueIcon.Position = UDim2.new(1, -(20 + textWidth + 8), 0.5, 0)
	end
	valueLabel:GetPropertyChangedSignal("TextBounds"):Connect(placeIcon)

	-- Expanding list ------------------------------------------------------------
	local holder = create("Frame", {
		Size = UDim2.new(1, 0, 0, 0),
		BackgroundTransparency = 1,
		ClipsDescendants = true,
		LayoutOrder = 2,
		Parent = selector.Frame,
	})

	local searchable = options.Searchable
	if searchable == nil then
		searchable = #selector.Options > 8 or adapter.type == "PlayerSelector"
	end
	local SEARCH_HEIGHT = searchable and 36 or 0

	local searchBox, searchLine
	if searchable then
		local searchFrame = create("Frame", {
			Position = UDim2.fromOffset(ROW_INSET + 16, 2),
			Size = UDim2.new(1, -(ROW_INSET * 2 + 16), 0, 28),
			BackgroundTransparency = 1,
			Parent = holder,
		})
		searchBox = text({
			Class = "TextBox",
			Size = UDim2.fromScale(1, 1),
			Font = "Serif",
			Italic = true,
			TextSize = 14,
			PlaceholderText = "Search",
			ClearTextOnFocus = false,
			Text = "",
			Parent = searchFrame,
		})
		rule({
			AnchorPoint = Vector2.new(0, 1),
			Position = UDim2.fromScale(0, 1),
			Size = UDim2.new(1, 0, 0, 1),
			Parent = searchFrame,
		})
		searchLine = rule({
			AnchorPoint = Vector2.new(0, 1),
			Position = UDim2.fromScale(0, 1),
			Size = UDim2.new(0, 0, 0, 1),
			Color = "Accent",
			Parent = searchFrame,
		})
	end

	local emptyLabel = text({
		Position = UDim2.fromOffset(ROW_INSET + 16, SEARCH_HEIGHT),
		Size = UDim2.new(1, -(ROW_INSET * 2 + 16), 0, OPTION_HEIGHT),
		Font = "Serif",
		Italic = true,
		TextSize = 14,
		Color = "InkFaint",
		Text = "Nothing matches.",
		Visible = false,
		Parent = holder,
	})

	local list = create("ScrollingFrame", {
		Position = UDim2.fromOffset(ROW_INSET, SEARCH_HEIGHT),
		Size = UDim2.new(1, -ROW_INSET * 2, 0, 0),
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		ScrollBarThickness = 2,
		ScrollBarImageTransparency = 0.4,
		VerticalScrollBarInset = Enum.ScrollBarInset.ScrollBar,
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollingDirection = Enum.ScrollingDirection.Y,
		Theme = { ScrollBarImageColor3 = "InkFaint" },
		Parent = holder,
	}, { listLayout(0) })

	local entries = {}

	local function isSelected(option)
		if selector.Multi then
			return table.find(selector.Value, option) ~= nil
		end
		return selector.Value == option
	end

	local function styleEntry(option, entry, hovered, duration)
		local selected = isSelected(option)
		duration = duration or 0.15
		tween(entry.Label, {
			TextColor3 = selected and Theme.Accent or (hovered and Theme.Ink or Theme.InkMuted),
		}, duration)
		tween(entry.Mark, { Size = UDim2.fromOffset(2, selected and 16 or 0) }, duration + 0.1)
	end

	local function displayText()
		local texts, first = {}, nil
		if selector.Multi then
			for _, v in ipairs(selector.Value) do
				table.insert(texts, adapter.text(v))
				first = first or v
			end
		elseif selector.Value ~= nil then
			texts = { adapter.text(selector.Value) }
			first = selector.Value
		end
		if #texts == 0 then
			return adapter.placeholder or "None", nil, true
		end
		return table.concat(texts, ", "), first, false
	end

	local function updateDisplay(duration, animate)
		local display, first, empty = displayText()
		local apply = function()
			valueLabel.Text = display
			valueLabel.TextColor3 = empty and Theme.InkFaint or Theme.Ink
			if valueIcon then
				local image = first ~= nil and adapter.icon(first) or nil
				valueIcon.Visible = image ~= nil
				valueIcon.Image = image or ""
				placeIcon()
			end
		end
		if animate then
			-- A quick fade between values rather than a hard swap.
			task.spawn(function()
				tween(valueLabel, { TextTransparency = 1 }, 0.08).Completed:Wait()
				apply()
				tween(valueLabel, { TextTransparency = selector.Locked and 0.55 or 0 }, 0.15)
			end)
		else
			apply()
		end
		for option, entry in pairs(entries) do
			styleEntry(option, entry, false, duration)
		end
	end

	local function resize(duration)
		local visible = 0
		for _, entry in pairs(entries) do
			if entry.Row.Visible then
				visible += 1
			end
		end
		local shown = math.min(visible, MAX_VISIBLE)
		emptyLabel.Visible = shown == 0
		local listHeight = shown * OPTION_HEIGHT
		list.Size = UDim2.new(1, -ROW_INSET * 2, 0, listHeight)
		local contentHeight = SEARCH_HEIGHT + math.max(listHeight, OPTION_HEIGHT) + 8
		tween(holder, { Size = UDim2.new(1, 0, 0, selector.Open and contentHeight or 0) }, duration or 0.3)
	end

	local function applyFilter()
		local query = searchBox and searchBox.Text:lower() or ""
		for option, entry in pairs(entries) do
			entry.Row.Visible = query == "" or adapter.search(option):lower():find(query, 1, true) ~= nil
		end
		resize()
	end

	local function choose(option)
		if selector.Locked then
			return
		end
		click(0.15)
		if selector.Multi then
			local value = table.clone(selector.Value)
			local index = table.find(value, option)
			if index then
				table.remove(value, index)
			else
				table.insert(value, option)
			end
			selector:Set(value)
		else
			selector:Set(option)
			selector:Close()
		end
	end

	local function build()
		for _, entry in pairs(entries) do
			entry.Row:Destroy()
		end
		table.clear(entries)
		for i, option in ipairs(selector.Options) do
			local row = create("TextButton", {
				Size = UDim2.new(1, 0, 0, OPTION_HEIGHT),
				BackgroundTransparency = 1,
				AutoButtonColor = false,
				Text = "",
				LayoutOrder = i,
				Parent = list,
			})
			-- Margin mark for the selected option.
			local mark = rule({
				AnchorPoint = Vector2.new(0, 0.5),
				Position = UDim2.new(0, 2, 0.5, 0),
				Size = UDim2.fromOffset(2, 0),
				Color = "Accent",
				Parent = row,
			})
			local primary = adapter.renderRow(row, option)
			local entry = { Row = row, Mark = mark, Label = primary }
			row.MouseEnter:Connect(function()
				styleEntry(option, entry, true)
			end)
			row.MouseLeave:Connect(function()
				styleEntry(option, entry, false)
			end)
			row.MouseButton1Click:Connect(function()
				choose(option)
			end)
			entries[option] = entry
		end
		updateDisplay(0, false)
		applyFilter()
	end

	if searchBox then
		searchBox.Focused:Connect(function()
			tween(searchLine, { Size = UDim2.new(1, 0, 0, 1) }, 0.3)
		end)
		searchBox.FocusLost:Connect(function()
			tween(searchLine, { Size = UDim2.new(0, 0, 0, 1) }, 0.3)
		end)
		searchBox:GetPropertyChangedSignal("Text"):Connect(applyFilter)
	end

	function selector:SetOpen(open)
		open = open == true
		if open == self.Open then
			return
		end
		self.Open = open
		tween(arrow, { Rotation = open and 180 or 0 }, 0.3)
		tweenAll(arrowBars, { BackgroundColor3 = open and Theme.Ink or Theme.InkMuted }, 0.2)
		if not open and searchBox then
			searchBox.Text = ""
		end
		resize()
	end

	function selector:Close()
		self:SetOpen(false)
	end

	function selector:Set(value, silent)
		if adapter.normalize then
			value = adapter.normalize(value)
		end
		local before = displayText()
		if self.Multi then
			local selected = {}
			if typeof(value) == "table" then
				for _, option in ipairs(self.Options) do
					if table.find(value, option) then
						table.insert(selected, option)
					end
				end
			elseif value ~= nil and table.find(self.Options, value) then
				selected = { value }
			end
			self.Value = selected
		else
			if value ~= nil and not table.find(self.Options, value) then
				return
			end
			self.Value = value
		end
		updateDisplay(nil, displayText() ~= before)
		if not silent then
			self:_fire(self:Get())
		end
	end

	function selector:Get()
		return self.Multi and table.clone(self.Value) or self.Value
	end

	function selector:Refresh(newOptions, keepSelection)
		self.Options = table.clone(newOptions or {})
		if self.Multi then
			local kept = {}
			if keepSelection then
				for _, v in ipairs(self.Value) do
					if table.find(self.Options, v) then
						table.insert(kept, v)
					end
				end
			end
			self.Value = kept
		elseif not (keepSelection and table.find(self.Options, self.Value)) then
			self.Value = nil
		end
		build()
	end

	function selector:Add(option)
		if not table.find(self.Options, option) then
			table.insert(self.Options, option)
			build()
		end
	end

	function selector:Remove(option)
		local index = table.find(self.Options, option)
		if not index then
			return
		end
		table.remove(self.Options, index)
		if self.Multi then
			local valueIndex = table.find(self.Value, option)
			if valueIndex then
				table.remove(self.Value, valueIndex)
			end
		elseif self.Value == option then
			self.Value = nil
		end
		build()
	end

	function selector:Clear()
		self:Refresh({})
	end

	function selector:IsSelected(option)
		return isSelected(option)
	end

	selector.Header.MouseButton1Click:Connect(function()
		if selector.Locked then
			return
		end
		click(0.15)
		selector:SetOpen(not selector.Open)
	end)

	onThemeChanged(holder, function()
		updateDisplay(0.3, false)
	end)

	build()
	if options.Default ~= nil then
		selector:Set(options.Default, true)
	end
	resize(0)
	register(self, options, selector, adapter.type or "Dropdown")
	return selector
end

--------------------------------------------------------------------------------
-- Dropdown
--------------------------------------------------------------------------------

function Tab:AddDropdown(options)
	options = options or {}
	local format = options.Format or tostring

	return self:_selector(options, {
		type = "Dropdown",
		placeholder = options.Placeholder or "None",
		text = format,
		search = format,
		renderRow = function(row, option)
			return text({
				Position = UDim2.fromOffset(16, 0),
				Size = UDim2.new(1, -22, 1, 0),
				TextSize = 15,
				Color = false,
				TextColor3 = Theme.InkMuted,
				Text = format(option),
				TextTruncate = Enum.TextTruncate.AtEnd,
				Parent = row,
			})
		end,
	})
end

--------------------------------------------------------------------------------
-- Player selector
--------------------------------------------------------------------------------

function Tab:AddPlayerSelector(options)
	options = options or {}
	local excludeLocal = options.ExcludeLocalPlayer == true

	local function currentPlayers(leaving)
		local list = {}
		for _, player in ipairs(Players:GetPlayers()) do
			if player ~= leaving and not (excludeLocal and player == LocalPlayer) then
				table.insert(list, player)
			end
		end
		table.sort(list, function(a, b)
			return a.DisplayName:lower() < b.DisplayName:lower()
		end)
		return list
	end

	local function toPlayer(value)
		if typeof(value) == "Instance" and value:IsA("Player") then
			return value
		end
		if typeof(value) == "string" then
			local player = Players:FindFirstChild(value)
			if player and player:IsA("Player") then
				return player
			end
			for _, p in ipairs(Players:GetPlayers()) do
				if p.DisplayName == value then
					return p
				end
			end
		end
		return nil
	end

	local selectorOptions = table.clone(options)
	selectorOptions.Options = currentPlayers()

	local selector = self:_selector(selectorOptions, {
		type = "PlayerSelector",
		placeholder = options.Placeholder or "Nobody",
		text = function(player)
			return player.DisplayName
		end,
		search = function(player)
			return player.DisplayName .. " " .. player.Name
		end,
		icon = function(player)
			return headshot(player.UserId)
		end,
		normalize = function(value)
			if typeof(value) == "table" then
				local players = {}
				for _, v in ipairs(value) do
					local player = toPlayer(v)
					if player then
						table.insert(players, player)
					end
				end
				return players
			end
			return toPlayer(value)
		end,
		renderRow = function(row, player)
			create("ImageLabel", {
				AnchorPoint = Vector2.new(0, 0.5),
				Position = UDim2.new(0, 16, 0.5, 0),
				Size = UDim2.fromOffset(22, 22),
				Image = headshot(player.UserId),
				Theme = { BackgroundColor3 = "Raised" },
				Parent = row,
			}, { corner(4) })
			local names = create("Frame", {
				Position = UDim2.fromOffset(48, 0),
				Size = UDim2.new(1, -54, 1, 0),
				BackgroundTransparency = 1,
				ClipsDescendants = true,
				Parent = row,
			}, {
				create("UIListLayout", {
					FillDirection = Enum.FillDirection.Horizontal,
					VerticalAlignment = Enum.VerticalAlignment.Center,
					SortOrder = Enum.SortOrder.LayoutOrder,
					Padding = UDim.new(0, 8),
				}),
			})
			local name = text({
				Size = UDim2.new(0, 0, 1, 0),
				AutomaticSize = Enum.AutomaticSize.X,
				TextSize = 15,
				Color = false,
				TextColor3 = Theme.InkMuted,
				Text = player.DisplayName,
				LayoutOrder = 1,
				Parent = names,
			})
			text({
				Size = UDim2.new(0, 0, 1, 0),
				AutomaticSize = Enum.AutomaticSize.X,
				Font = "Serif",
				Italic = true,
				TextSize = 13,
				Color = "InkFaint",
				Text = "@" .. player.Name .. (player == LocalPlayer and ", you" or ""),
				LayoutOrder = 2,
				Parent = names,
			})
			return name
		end,
	})

	-- Players come and go: keep the list live and drop selections for players who leave.
	local function sync(leaving)
		local wasSelected = leaving and selector:IsSelected(leaving)
		selector:Refresh(currentPlayers(leaving), true)
		if wasSelected then
			selector:_fire(selector:Get())
		end
	end

	local connections = {
		Players.PlayerAdded:Connect(function()
			sync(nil)
		end),
		Players.PlayerRemoving:Connect(function(player)
			sync(player)
		end),
	}

	local baseRefresh = selector.Refresh
	function selector:Refresh(newOptions, keepSelection)
		if newOptions == nil then
			return baseRefresh(self, currentPlayers(), true)
		end
		return baseRefresh(self, newOptions, keepSelection)
	end

	function selector:_cleanup()
		for _, connection in ipairs(connections) do
			connection:Disconnect()
		end
		table.clear(connections)
	end

	function selector:_serialize()
		if self.Multi then
			local names = {}
			for _, player in ipairs(self.Value) do
				table.insert(names, player.Name)
			end
			return names
		end
		return self.Value and self.Value.Name or nil
	end

	return selector
end

return Library
