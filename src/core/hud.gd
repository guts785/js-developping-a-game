extends CanvasLayer
class_name Hud
## Hud — objective banner, inventory strip, journal, pause/settings, toasts.
## RTL Arabic throughout; the inventory strip is the genre's bottom bar.

signal item_selected(id: String)
signal item_cleared
signal resume_requested
signal main_menu_requested
signal quit_requested
signal save_requested
signal load_requested
signal scanlines_toggled(on: bool)
signal fullscreen_toggled(on: bool)

const BAR_H := 46.0
const SLOT := 38.0
const SLOTS_PER_PAGE := 12

var objective_label: Label
var inv_panel: Panel
var inv_slots: Array[Button] = []
var selected_item := ""
var toast_label: Label
var toast_timer := 0.0

var journal_panel: Panel
var journal_text: Label
var pause_panel: Panel
var _inv_visible := true
var _tooltip: Label


func _ready() -> void:
	layer = 10

	# ---------------------------------------------------------- objective
	objective_label = Ui.make_label("", Locale.SZ_SMALL, Ui.COL_GOLD)
	objective_label.position = Vector2(60, 6)
	objective_label.size = Vector2(520, 20)
	objective_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	Ui.outline(objective_label)
	add_child(objective_label)

	# ---------------------------------------------------------- toast
	toast_label = Ui.make_label("", Locale.SZ_SMALL, Ui.COL_TEXT)
	toast_label.position = Vector2(120, 232)
	Ui.outline(toast_label)
	toast_label.size = Vector2(400, 22)
	toast_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	toast_label.visible = false
	add_child(toast_label)

	# ---------------------------------------------------------- inventory bar
	inv_panel = Ui.make_panel(Color(0.05, 0.04, 0.06, 0.88))
	inv_panel.position = Vector2(0, 360 - BAR_H)
	inv_panel.size = Vector2(640, BAR_H)
	# The bar is a wooden ledge with a brass rail, not a black rectangle -- see
	# tools/gen_ui3.py. It goes in first so the slots and the tooltip land on top.
	var bar_tex := Ui.tex("res://art/ui/hud_bar.png")
	if bar_tex != null:
		var bar := TextureRect.new()
		bar.texture = bar_tex
		bar.size = Vector2(640, BAR_H)
		bar.stretch_mode = TextureRect.STRETCH_SCALE
		bar.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
		inv_panel.add_child(bar)
	add_child(inv_panel)
	for i in SLOTS_PER_PAGE:
		var b := Button.new()
		b.custom_minimum_size = Vector2(SLOT, SLOT)
		b.size = Vector2(SLOT, SLOT)
		b.position = Vector2(8 + i * (SLOT + 3), 360 - BAR_H + 4)
		b.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		b.expand_icon = true
		b.flat = false
		b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		b.focus_mode = Control.FOCUS_NONE
		Ui._style_button(b)
		var idx := i
		b.pressed.connect(func() -> void: _on_slot_pressed(idx))
		b.mouse_entered.connect(func() -> void: _show_tooltip(idx))
		b.mouse_exited.connect(func() -> void: _tooltip.visible = false)
		inv_panel.add_child(b)
		inv_slots.append(b)

	_tooltip = Ui.make_label("", Locale.SZ_TINY, Ui.COL_GOLD)
	_tooltip.position = Vector2(200, 360 - BAR_H - 20)
	_tooltip.size = Vector2(280, 18)
	_tooltip.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_tooltip.visible = false
	add_child(_tooltip)

	# bag / journal / menu buttons on the right of the strip
	var jb := Ui.make_button(Locale.t("journal"), Locale.SZ_TINY)
	jb.position = Vector2(556, 360 - BAR_H + 6)
	jb.size = Vector2(78, 18)
	jb.pressed.connect(toggle_journal)
	add_child(jb)

	var mb := Ui.make_button("القائمة", Locale.SZ_TINY)
	mb.position = Vector2(556, 360 - BAR_H + 26)
	mb.size = Vector2(78, 18)
	mb.pressed.connect(open_pause)
	add_child(mb)

	_build_journal()
	_build_pause()
	GameState.inventory_changed.connect(refresh_inventory)
	GameState.objective_changed.connect(func(txt: String) -> void: set_objective(txt))
	refresh_inventory()
	if GameState.objective != "":
		set_objective(GameState.objective)


# ------------------------------------------------------------------ objective
func set_objective(txt: String) -> void:
	objective_label.text = ("المهمة: " + txt) if txt != "" else ""
	toast("مهمة جديدة: " + txt)


func toast(txt: String, seconds: float = 3.2) -> void:
	toast_label.text = txt
	toast_label.visible = true
	toast_timer = seconds


# ------------------------------------------------------------------ inventory
func refresh_inventory() -> void:
	for i in inv_slots.size():
		var b := inv_slots[i]
		var id := GameState.inventory[i] if i < GameState.inventory.size() else ""
		b.icon = Ui.tex("res://art/items/%s.png" % id) if id != "" else null
		b.disabled = id == ""
		b.modulate = Color(1, 1, 1, 1) if id != selected_item else Color(1.0, 0.85, 0.4, 1.0)
		b.set_meta("item_id", id)


func _on_slot_pressed(idx: int) -> void:
	if idx >= GameState.inventory.size():
		return
	var id: String = GameState.inventory[idx]
	if selected_item == id:
		clear_selection()
		return
	selected_item = id
	refresh_inventory()
	AudioManager.play("click", -12.0)
	item_selected.emit(id)
	toast(Locale.item_name(id) + " — " + Locale.t("combine_hint"), 2.4)


func clear_selection() -> void:
	selected_item = ""
	refresh_inventory()
	item_cleared.emit()


func _show_tooltip(idx: int) -> void:
	if idx >= GameState.inventory.size():
		return
	var id: String = GameState.inventory[idx]
	_tooltip.text = Locale.item_name(id)
	_tooltip.visible = true


func set_inventory_visible(v: bool) -> void:
	_inv_visible = v
	inv_panel.visible = v
	for b in inv_slots:
		b.visible = v
	_tooltip.visible = false if not v else _tooltip.visible


# ------------------------------------------------------------------ journal
func _build_journal() -> void:
	journal_panel = Ui.make_panel(Color(0.05, 0.04, 0.06, 0.96))
	journal_panel.position = Vector2(80, 40)
	journal_panel.size = Vector2(480, 280)
	journal_panel.visible = false
	journal_panel.z_index = 30
	add_child(journal_panel)

	var title := Ui.make_label("ملف القضية", Locale.SZ_BODY, Ui.COL_GOLD)
	title.position = Vector2(0, 8)
	title.size = Vector2(480, 22)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	journal_panel.add_child(title)

	journal_text = Ui.make_label("", Locale.SZ_SMALL, Ui.COL_TEXT)
	journal_text.position = Vector2(18, 36)
	journal_text.size = Vector2(444, 200)
	journal_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	journal_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	journal_text.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	journal_panel.add_child(journal_text)

	var close := Ui.make_button(Locale.t("close"), Locale.SZ_SMALL)
	close.position = Vector2(200, 244)
	close.size = Vector2(80, 24)
	close.pressed.connect(func() -> void:
		journal_panel.visible = false
		AudioManager.play("click", -12.0))
	journal_panel.add_child(close)


func toggle_journal() -> void:
	if journal_panel.visible:
		journal_panel.visible = false
		return
	AudioManager.play("page", -8.0)
	var lines: Array[String] = []
	lines.append("الفصل: " + str(GameState.chapter) + " — " + Locale.t("ch%d" % GameState.chapter))
	lines.append("")
	lines.append("المهمة الحالية: " + (GameState.objective if GameState.objective != "" else "—"))
	lines.append("")
	lines.append("الأدلة (" + str(GameState.clues.size()) + "):")
	if GameState.clues.is_empty():
		lines.append("  " + Locale.t("no_clues"))
	for c in GameState.clues:
		lines.append("  • " + str(c))
	journal_text.text = "\n".join(lines)
	journal_panel.visible = true


# ------------------------------------------------------------------ pause
func _build_pause() -> void:
	pause_panel = Ui.make_panel(Color(0.04, 0.03, 0.05, 0.97))
	pause_panel.position = Vector2(190, 40)
	pause_panel.size = Vector2(260, 280)
	pause_panel.visible = false
	pause_panel.z_index = 40
	add_child(pause_panel)

	var title := Ui.make_label("واقف", Locale.SZ_BODY, Ui.COL_GOLD)
	title.position = Vector2(0, 8)
	title.size = Vector2(260, 22)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pause_panel.add_child(title)

	var y := 38.0
	for spec in [
		{"t": "resume", "s": "resume_requested"},
		{"t": "save", "s": "save_requested"},
		{"t": "load", "s": "load_requested"},
	]:
		var b := Ui.make_button(Locale.t(str(spec["t"])), Locale.SZ_SMALL)
		b.position = Vector2(60, y)
		b.size = Vector2(140, 24)
		var sig := str(spec["s"])
		b.pressed.connect(_on_pause_button.bind(sig))
		pause_panel.add_child(b)
		y += 30.0

	# volume slider
	var vl := Ui.make_label("الصوت", Locale.SZ_TINY, Ui.COL_DIM)
	vl.position = Vector2(20, y + 4)
	vl.size = Vector2(60, 18)
	pause_panel.add_child(vl)
	var slider := HSlider.new()
	slider.min_value = 0.0
	slider.max_value = 1.0
	slider.step = 0.05
	slider.value = float(GameState.settings.get("volume", 0.8))
	slider.position = Vector2(90, y + 6)
	slider.size = Vector2(150, 16)
	slider.value_changed.connect(func(v: float) -> void: AudioManager.set_volume(v))
	pause_panel.add_child(slider)
	y += 34.0

	# scanline toggle
	var sl := CheckButton.new()
	sl.text = "خطوط الشاشة"
	if Ui.font != null:
		sl.add_theme_font_override("font", Ui.font)
	sl.add_theme_font_size_override("font_size", Locale.SZ_TINY)
	sl.add_theme_color_override("font_color", Ui.COL_DIM)
	sl.text_direction = Control.TEXT_DIRECTION_RTL
	sl.button_pressed = bool(GameState.settings.get("scanlines", true))
	sl.position = Vector2(60, y)
	sl.size = Vector2(160, 20)
	sl.toggled.connect(func(on: bool) -> void:
		GameState.settings["scanlines"] = on
		scanlines_toggled.emit(on))
	pause_panel.add_child(sl)
	y += 26.0

	var fs := CheckButton.new()
	fs.text = Locale.t("fullscreen")
	if Ui.font != null:
		fs.add_theme_font_override("font", Ui.font)
	fs.add_theme_font_size_override("font_size", Locale.SZ_TINY)
	fs.add_theme_color_override("font_color", Ui.COL_DIM)
	fs.text_direction = Control.TEXT_DIRECTION_RTL
	fs.button_pressed = bool(GameState.settings.get("fullscreen", true))
	fs.position = Vector2(60, y)
	fs.size = Vector2(160, 20)
	fs.toggled.connect(func(on: bool) -> void:
		GameState.settings["fullscreen"] = on
		fullscreen_toggled.emit(on))
	pause_panel.add_child(fs)
	y += 26.0

	var mm := Ui.make_button(Locale.t("main_menu"), Locale.SZ_SMALL)
	mm.position = Vector2(60, y)
	mm.size = Vector2(140, 24)
	mm.pressed.connect(func() -> void:
		AudioManager.play("click", -10.0)
		main_menu_requested.emit())
	pause_panel.add_child(mm)
	y += 30.0

	var qb := Ui.make_button(Locale.t("quit"), Locale.SZ_SMALL)
	qb.position = Vector2(60, y)
	qb.size = Vector2(140, 24)
	qb.pressed.connect(func() -> void:
		AudioManager.play("click", -10.0)
		quit_requested.emit())
	pause_panel.add_child(qb)


func open_pause() -> void:
	pause_panel.visible = true
	AudioManager.play("click", -10.0)


func _on_pause_button(sig: String) -> void:
	AudioManager.play("click", -10.0)
	if sig == "resume_requested":
		close_pause()
	elif sig == "save_requested":
		save_requested.emit()
	elif sig == "load_requested":
		load_requested.emit()


func close_pause() -> void:
	pause_panel.visible = false


func is_pause_open() -> bool:
	return pause_panel.visible


func is_journal_open() -> bool:
	return journal_panel.visible


func close_overlays() -> void:
	pause_panel.visible = false
	journal_panel.visible = false


func _process(delta: float) -> void:
	if toast_timer > 0.0:
		toast_timer -= delta
		if toast_timer <= 0.0:
			toast_label.visible = false
