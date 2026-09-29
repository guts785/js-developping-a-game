extends CanvasLayer
class_name TitleScreen
## TitleScreen — the front door: title art, menu, chapter select, credits.

signal new_game
signal continue_game
signal chapter_pick(ch: int)
signal quit_game

var _bg: TextureRect
var _panel: VBoxContainer
var _sub: Panel
var _dim: ColorRect
var _buttons: Array[Button] = []
var _mode := "menu"


func _ready() -> void:
	layer = 30
	visible = false
	process_mode = Node.PROCESS_MODE_ALWAYS

	_bg = TextureRect.new()
	_bg.texture = Ui.tex("res://art/rooms/title.png")
	_bg.stretch_mode = TextureRect.STRETCH_SCALE
	_bg.size = Vector2(640, 360)
	_bg.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_bg)

	var shade := ColorRect.new()
	shade.color = Color(0.02, 0.01, 0.03, 0.45)
	shade.size = Vector2(640, 360)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)

	var t := Ui.make_label(Locale.t("title"), Locale.SZ_HUGE, Ui.COL_GOLD)
	t.position = Vector2(0, 18)
	t.size = Vector2(640, 54)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(t)

	var st := Ui.make_label(Locale.t("subtitle"), Locale.SZ_SUB, Ui.COL_TEXT)
	st.position = Vector2(0, 72)
	st.size = Vector2(640, 24)
	st.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(st)

	var tg := Ui.make_label(Locale.t("tagline"), Locale.SZ_TINY, Ui.COL_DIM)
	tg.position = Vector2(0, 96)
	tg.size = Vector2(640, 20)
	tg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(tg)

	# Modal layer. _sub used to be added BEFORE the menu, so the Play/Settings
	# buttons drew on top of it. Now: menu z=10, dimmer z=15 (and it eats clicks),
	# sub-panel z=20 — nothing can end up behind the menu again.
	_dim = ColorRect.new()
	_dim.color = Color(0.02, 0.01, 0.03, 0.62)
	_dim.size = Vector2(640, 360)
	_dim.z_index = 15
	_dim.mouse_filter = Control.MOUSE_FILTER_STOP
	_dim.visible = false
	add_child(_dim)

	_sub = Ui.make_panel(Color(0.04, 0.03, 0.05, 0.97))
	_sub.position = Vector2(200, 108)
	_sub.size = Vector2(240, 232)
	_sub.z_index = 20
	_sub.visible = false
	add_child(_sub)

	_build_menu()


func _build_menu() -> void:
	_panel = VBoxContainer.new()
	_panel.position = Vector2(240, 140)
	_panel.size = Vector2(160, 190)
	_panel.add_theme_constant_override("separation", 6)
	_panel.alignment = BoxContainer.ALIGNMENT_CENTER
	_panel.z_index = 10
	add_child(_panel)

	var entries := [
		{"t": Locale.t("new_game"), "a": "new"},
		{"t": Locale.t("continue_game"), "a": "continue"},
		{"t": Locale.t("chapters"), "a": "chapters"},
		{"t": Locale.t("settings"), "a": "settings"},
		{"t": Locale.t("credits"), "a": "credits"},
		{"t": Locale.t("quit"), "a": "quit"},
	]
	for e in entries:
		var b := Ui.make_button(str(e["t"]))
		b.custom_minimum_size = Vector2(160, 26)
		var act := str(e["a"])
		b.pressed.connect(func() -> void: _on_action(act))
		_panel.add_child(b)
		_buttons.append(b)
	if GameState.has_save():
		_buttons[1].disabled = false
	else:
		_buttons[1].disabled = true


func _on_action(a: String) -> void:
	AudioManager.play("click", -8.0)
	match a:
		"new":
			visible = false
			new_game.emit()
		"continue":
			if GameState.has_save():
				visible = false
				continue_game.emit()
		"chapters":
			_show_chapters()
		"settings":
			_show_settings()
		"credits":
			_show_credits()
		"quit":
			quit_game.emit()


func _close_sub() -> void:
	_sub.visible = false
	_dim.visible = false


func _clear_sub() -> void:
	for c in _sub.get_children():
		c.queue_free()


func _show_chapters() -> void:
	_clear_sub()
	_sub.visible = true
	_dim.visible = true
	_mode = "chapters"
	var title := Ui.make_label("الفصول", Locale.SZ_BODY, Ui.COL_GOLD)
	title.position = Vector2(0, 6)
	title.size = Vector2(200, 22)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_sub.add_child(title)
	var y := 34.0
	var unlocked := maxi(GameState.max_chapter, 1)
	for ch in range(1, 7):
		var b := Ui.make_button(Locale.t("ch%d" % ch), Locale.SZ_TINY)
		b.position = Vector2(14, y)
		b.size = Vector2(172, 22)
		b.disabled = ch > unlocked
		var c := ch
		b.pressed.connect(func() -> void:
			AudioManager.play("click", -8.0)
			visible = false
			chapter_pick.emit(c))
		_sub.add_child(b)
		y += 25.0
	var back := Ui.make_button(Locale.t("back"), Locale.SZ_TINY)
	back.position = Vector2(14, y + 4)
	back.size = Vector2(172, 22)
	back.pressed.connect(_close_sub)
	_sub.add_child(back)


func _show_settings() -> void:
	_clear_sub()
	_sub.visible = true
	_dim.visible = true
	_mode = "settings"
	var title := Ui.make_label("الإعدادات", Locale.SZ_BODY, Ui.COL_GOLD)
	title.position = Vector2(0, 6)
	title.size = Vector2(200, 22)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_sub.add_child(title)

	var vl := Ui.make_label("الصوت", Locale.SZ_TINY, Ui.COL_DIM)
	vl.position = Vector2(14, 40)
	vl.size = Vector2(60, 18)
	_sub.add_child(vl)
	var slider := HSlider.new()
	slider.min_value = 0.0
	slider.max_value = 1.0
	slider.step = 0.05
	slider.value = float(GameState.settings.get("volume", 0.8))
	slider.position = Vector2(76, 42)
	slider.size = Vector2(110, 16)
	slider.value_changed.connect(func(v: float) -> void: AudioManager.set_volume(v))
	_sub.add_child(slider)

	var sl := CheckButton.new()
	sl.text = "خطوط الشاشة"
	if Ui.font != null:
		sl.add_theme_font_override("font", Ui.font)
	sl.add_theme_font_size_override("font_size", Locale.SZ_TINY)
	sl.add_theme_color_override("font_color", Ui.COL_DIM)
	sl.text_direction = Control.TEXT_DIRECTION_RTL
	sl.button_pressed = bool(GameState.settings.get("scanlines", true))
	sl.position = Vector2(30, 72)
	sl.size = Vector2(160, 20)
	_sub.add_child(sl)

	var fs := CheckButton.new()
	fs.text = Locale.t("fullscreen")
	if Ui.font != null:
		fs.add_theme_font_override("font", Ui.font)
	fs.add_theme_font_size_override("font_size", Locale.SZ_TINY)
	fs.add_theme_color_override("font_color", Ui.COL_DIM)
	fs.text_direction = Control.TEXT_DIRECTION_RTL
	fs.button_pressed = bool(GameState.settings.get("fullscreen", true))
	fs.position = Vector2(30, 98)
	fs.size = Vector2(160, 20)
	fs.toggled.connect(func(on: bool) -> void:
		var shell := get_tree().root.get_node_or_null("Boot")
		if shell != null and shell.has_method("set_fullscreen"):
			shell.set_fullscreen(on))
	_sub.add_child(fs)

	var fh := Ui.make_label(Locale.t("fullscreen_hint"), Locale.SZ_TINY, Ui.COL_DIM)
	fh.position = Vector2(30, 124)
	fh.size = Vector2(160, 18)
	fh.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_sub.add_child(fh)

	var back := Ui.make_button(Locale.t("back"), Locale.SZ_TINY)
	back.position = Vector2(14, 168)
	back.size = Vector2(172, 22)
	back.pressed.connect(_close_sub)
	_sub.add_child(back)


func _show_credits() -> void:
	_clear_sub()
	_sub.visible = true
	_dim.visible = true
	var txt := "البلغة والجن\n\nصنعة مغربية\n\nالرسم، الصوت، والقصة\nتصاوبو من الصفر\n\nالدار البيضاء — 1994"
	var l := Ui.make_label(txt, Locale.SZ_TINY, Ui.COL_DIM)
	l.position = Vector2(10, 20)
	l.size = Vector2(180, 150)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_sub.add_child(l)
	var back := Ui.make_button(Locale.t("back"), Locale.SZ_TINY)
	back.position = Vector2(14, 176)
	back.size = Vector2(172, 22)
	back.pressed.connect(_close_sub)
	_sub.add_child(back)


func open() -> void:
	visible = true
	_close_sub()
	_clear_sub()
	if _panel == null:
		_build_menu()
	else:
		for i in _buttons.size():
			if i == 1:
				_buttons[i].disabled = not GameState.has_save()
