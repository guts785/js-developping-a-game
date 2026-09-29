extends Node
## Ui — shared theme: the Cairo Arabic font, colours, and widget factories.
## All text is RTL-shaped by Godot's TextServer; we just build the widgets.

const COL_TEXT := Color(0.96, 0.93, 0.85)
const COL_DIM := Color(0.72, 0.67, 0.58)
const COL_GOLD := Color(0.85, 0.61, 0.24)
const COL_RED := Color(0.75, 0.22, 0.18)
const COL_SHADOW := Color(0, 0, 0, 0.85)
const COL_BG := Color(0.06, 0.05, 0.07, 0.92)

var font: FontFile
var theme: Theme


func _ready() -> void:
	_load_font()
	_build_theme()


func _load_font() -> void:
	if ResourceLoader.exists(Locale.FONT_PATH):
		var res: Resource = load(Locale.FONT_PATH)
		if res is FontFile:
			font = res
	if font == null:
		# fall back to the engine's default font so the game never hard-fails
		font = ThemeDB.fallback_font as FontFile
		push_warning("Cairo font missing — Arabic may not shape. Check fonts/Cairo-Regular.ttf")
	_pixelize_font()


## Cairo ships as a smooth outline face, and Godot's default rasteriser leans on
## antialiasing and subpixel positioning. At 640x360 that produces grey fringe
## pixels and glyphs that sit on half-pixel boundaries -- the text ends up looking
## like a modern overlay pasted over pixel art. Killing both snaps every glyph to
## the same grid the sprites use. Hinting goes too: it moves stems off the design
## grid, which at 12-16px smears the Arabic letterforms.
func _pixelize_font() -> void:
	if font == null:
		return
	font.antialiasing = TextServer.FONT_ANTIALIASING_NONE
	font.hinting = TextServer.HINTING_NONE
	font.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
	font.multichannel_signed_distance_field = false
	font.force_autohinter = false


func _build_theme() -> void:
	theme = Theme.new()
	if font != null:
		theme.default_font = font
	theme.default_font_size = Locale.SZ_BODY


func make_label(text: String, size: int = -1, color: Color = COL_TEXT,
				rtl: bool = true) -> Label:
	var l := Label.new()
	l.text = text
	if font != null:
		l.add_theme_font_override("font", font)
	l.add_theme_font_size_override("font_size", size if size > 0 else Locale.SZ_BODY)
	l.add_theme_color_override("font_color", color)
	l.add_theme_color_override("font_shadow_color", COL_SHADOW)
	l.add_theme_constant_override("shadow_offset_x", 1)
	l.add_theme_constant_override("shadow_offset_y", 1)
	l.add_theme_constant_override("line_spacing", 6)
	if rtl:
		l.text_direction = Control.TEXT_DIRECTION_RTL
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


## Text that sits directly on room art needs more than the 1px shadow: gold on a
## lit wall washes out. A real outline keeps it legible over any background.
func outline(l: Label, px: int = 4) -> void:
	l.add_theme_constant_override("outline_size", px)
	l.add_theme_color_override("font_outline_color", Color(0.02, 0.02, 0.03, 0.95))


func make_button(text: String, size: int = -1) -> Button:
	var b := Button.new()
	b.text = text
	if font != null:
		b.add_theme_font_override("font", font)
	b.add_theme_font_size_override("font_size", size if size > 0 else Locale.SZ_BODY)
	b.add_theme_color_override("font_color", COL_TEXT)
	b.add_theme_color_override("font_hover_color", COL_GOLD)
	b.add_theme_color_override("font_pressed_color", COL_RED)
	b.add_theme_color_override("font_focus_color", COL_GOLD)
	b.add_theme_color_override("font_shadow_color", COL_SHADOW)
	b.add_theme_constant_override("shadow_offset_x", 1)
	b.add_theme_constant_override("shadow_offset_y", 1)
	b.text_direction = Control.TEXT_DIRECTION_RTL
	b.focus_mode = Control.FOCUS_ALL
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	_style_button(b)
	b.mouse_entered.connect(func() -> void: AudioManager.play("hover", -16.0))
	return b


func _style_button(b: Button) -> void:
	var normal := StyleBoxFlat.new()
	normal.bg_color = Color(0.10, 0.08, 0.12, 0.86)
	normal.border_color = Color(0.58, 0.46, 0.28, 0.9)
	normal.set_border_width_all(1)
	normal.set_corner_radius_all(1)
	normal.content_margin_left = 10
	normal.content_margin_right = 10
	normal.content_margin_top = 4
	normal.content_margin_bottom = 4
	var hover := normal.duplicate() as StyleBoxFlat
	hover.bg_color = Color(0.20, 0.14, 0.10, 0.95)
	hover.border_color = COL_GOLD
	hover.set_border_width_all(1)
	var pressed := normal.duplicate() as StyleBoxFlat
	pressed.bg_color = Color(0.30, 0.10, 0.08, 0.95)
	pressed.border_color = COL_RED
	b.add_theme_stylebox_override("normal", normal)
	b.add_theme_stylebox_override("hover", hover)
	b.add_theme_stylebox_override("pressed", pressed)
	b.add_theme_stylebox_override("focus", hover)
	b.add_theme_stylebox_override("disabled", normal)


func make_panel(bg: Color = COL_BG) -> Panel:
	var p := Panel.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = bg
	sb.border_color = Color(0.58, 0.46, 0.28, 0.95)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(2)
	p.add_theme_stylebox_override("panel", sb)
	return p


func tex(path: String) -> Texture2D:
	if ResourceLoader.exists(path):
		var t: Resource = load(path)
		if t is Texture2D:
			return t
	return null


func sprite(path: String, scale_f: float = 1.0) -> Sprite2D:
	var s := Sprite2D.new()
	var t := tex(path)
	s.texture = t
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	s.scale = Vector2(scale_f, scale_f)
	return s
