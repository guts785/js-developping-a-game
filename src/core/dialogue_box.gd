extends Control
class_name DialogueBox
## DialogueBox — RTL Arabic dialogue: portrait, typewriter text, choices,
## and automatic rachid barks injected between lines for that Sui-Arts mouth.

signal closed

const BOX_H := 92.0
# The band sits at the TOP of the frame, under the objective line. At the bottom it
# covered y=256..360 while the actors stand at y=204..306 -- it buried the bottom
# 48px of every 102px character, 47% of the sprite, and the floor with it.
const BOX_Y := 28.0
const TYPE_CPS := 42.0

var portrait: Texture2D = null
var _portrait_rect: TextureRect
var _name_label: Label
var _text_label: Label
var _hint_label: Label
var _panel: Panel
var _choice_box: VBoxContainer
var _choices: Array[Button] = []

var _tree: Dictionary = {}
var _nodes: Dictionary = {}
var _node_id := ""
var _lines: Array = []
var _idx := 0
var _typed := 0.0
var _line_full := ""
var _waiting_choice := false
var _line_counter := 0
var _active := false
var runner: Callable = Callable()


func _ready() -> void:
	visible = false
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_anchors_preset(Control.PRESET_FULL_RECT)

	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.18)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(dim)

	# The flat near-black Panel is gone: art/ui/dlg_box.png is now authored at the
	# full 640x104 with a warm dithered field, so a 94%-opaque black rectangle
	# underneath it only punched a hole in the room. The texture IS the panel.
	_panel = Ui.make_panel(Color(0.05, 0.04, 0.06, 0.94))
	_panel.position = Vector2(0, BOX_Y)
	_panel.size = Vector2(640, BOX_H)
	_panel.visible = false
	add_child(_panel)

	# dialogue panel: full surface, 1:1 at 640x104
	var frame_tex := Ui.tex("res://art/ui/dlg_box.png")
	if frame_tex != null:
		var fr := TextureRect.new()
		fr.texture = frame_tex
		fr.stretch_mode = TextureRect.STRETCH_SCALE
		fr.position = Vector2(0, BOX_Y)
		fr.size = Vector2(640, BOX_H)
		fr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		fr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(fr)

	# portrait sits on the right — Arabic reads right-to-left
	_portrait_rect = TextureRect.new()
	_portrait_rect.position = Vector2(640 - 90, BOX_Y + 7)
	_portrait_rect.size = Vector2(78, 78)
	_portrait_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_portrait_rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_portrait_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_portrait_rect)

	_name_label = Ui.make_label("", Locale.SZ_SMALL, Ui.COL_GOLD)
	_name_label.position = Vector2(392, BOX_Y + 5)
	_name_label.size = Vector2(232, 20)
	_name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	add_child(_name_label)

	_text_label = Ui.make_label("", Locale.SZ_BODY, Ui.COL_TEXT)
	_text_label.position = Vector2(20, BOX_Y + 27)
	_text_label.size = Vector2(524, 56)
	_text_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_text_label.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	add_child(_text_label)

	_hint_label = Ui.make_label("▼", Locale.SZ_SMALL, Ui.COL_GOLD)
	_hint_label.position = Vector2(16, BOX_Y + BOX_H - 24)
	_hint_label.size = Vector2(24, 18)
	add_child(_hint_label)

	_choice_box = VBoxContainer.new()
	_choice_box.position = Vector2(300, 120)
	_choice_box.size = Vector2(320, 120)
	_choice_box.add_theme_constant_override("separation", 4)
	_choice_box.alignment = BoxContainer.ALIGNMENT_END
	add_child(_choice_box)


# ------------------------------------------------------------------ start
func start(tree_id: String, runner_callable: Callable) -> void:
	var tree := Data.dialogue(tree_id)
	if tree.is_empty():
		closed.emit()
		return
	start_tree(tree, runner_callable)


func start_tree(tree: Dictionary, runner_callable: Callable) -> void:
	if tree.is_empty():
		closed.emit()
		return
	var _st := get_stack()
	var _tr := ""
	for _i in range(mini(_st.size(), 10)):
		_tr += "\n     %s:%d in %s" % [str(_st[_i].get("source", "")), int(_st[_i].get("line", 0)), str(_st[_i].get("function", ""))]
	print("DLGBOX start_tree id=%s stack:%s" % [str(tree.get("id", "?")), _tr])
	runner = runner_callable
	_tree = tree
	_nodes = tree.get("nodes", {})
	_node_id = str(tree.get("start", "hi"))
	_idx = 0
	_line_counter = 0
	_lines = []
	visible = true
	_active = true
	_enter_node(_node_id)


func _enter_node(id: String) -> void:
	_node_id = id
	_idx = 0
	var arr: Array = _nodes.get(id, [])
	if arr.is_empty():
		_finish()
		return
	_lines = arr.duplicate()
	_show_current()


func _show_current() -> void:
	if _idx >= _lines.size():
		_advance_after_node()
		return
	var line: Dictionary = _lines[_idx]
	if line.has("choices"):
		_show_choices(line)
		return
	_line_counter += 1
	var who := Data.speaker_id(str(line.get("who", "narrator")))
	var text := str(line.get("text", ""))
	# inject a rachid bark every few lines — the genre's mouth
	if _line_counter % 5 == 4 and who != "rachid":
		var bark := Jokes.pick("bark")
		if bark != "":
			who = "rachid"
			text = bark
	_name_label.text = Locale.t(who)
	_set_portrait(who, line)
	_line_full = text
	_typed = 0.0
	_text_label.text = text
	_text_label.visible_characters = 0
	if who == "narrator":
		_name_label.text = ""
		_text_label.add_theme_color_override("font_color", Ui.COL_DIM)
	else:
		_text_label.add_theme_color_override("font_color", Ui.COL_TEXT)
	if line.has("actions"):
		_run(line["actions"])


func _set_portrait(who: String, line: Dictionary) -> void:
	var mood := str(line.get("mood", "neutral"))
	var path := "res://art/chars/%s_portrait_%s.png" % [who, mood]
	var t := Ui.tex(path)
	if t == null:
		t = Ui.tex("res://art/chars/%s_portrait_neutral.png" % who)
	_portrait_rect.texture = t
	_portrait_rect.visible = t != null


func _show_choices(line: Dictionary) -> void:
	_waiting_choice = true
	_text_label.text = ""
	_hint_label.text = ""
	_clear_choices()
	for c in line["choices"]:
		var cd: Dictionary = c
		var b := Ui.make_button(str(cd.get("text", "...")))
		b.custom_minimum_size = Vector2(320, 22)
		b.pressed.connect(func() -> void:
			AudioManager.play("click", -10.0)
			_clear_choices()
			_waiting_choice = false
			if cd.has("actions"):
				_run(cd["actions"])
			var nxt := str(cd.get("next", "CLOSE"))
			if nxt == "CLOSE":
				_finish()
			else:
				_enter_node(nxt))
		_choice_box.add_child(b)
		_choices.append(b)
	# focus the first option so keyboard players can just press enter
	if not _choices.is_empty():
		_choices[0].grab_focus()


func _clear_choices() -> void:
	for b in _choices:
		b.queue_free()
	_choices.clear()


## Test hook: when true the box drives itself — typewriter finished, lines advanced,
## first option picked. Used by the --playtest sweep so dialogue can't deadlock it.
var auto := false
var _auto_t := 0.0


func _pick_choice(i: int) -> void:
	if i < _choices.size():
		_choices[i].pressed.emit()


func _run(actions: Variant) -> void:
	if runner.is_valid():
		runner.call(actions)


# ------------------------------------------------------------------ input
func _unhandled_input(event: InputEvent) -> void:
	if not _active or _waiting_choice:
		return
	var advance := false
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		advance = true
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_SPACE or event.keycode == KEY_ENTER or event.keycode == KEY_ESCAPE:
			advance = true
	if advance:
		accept_event()
		_advance()


func _advance() -> void:
	if _text_label.visible_characters >= 0 and _text_label.visible_characters < _line_full.length():
		_text_label.visible_characters = -1     # finish the typewriter instantly
		return
	_idx += 1
	_show_current()


func _advance_after_node() -> void:
	var last: Dictionary = _lines[_lines.size() - 1] if not _lines.is_empty() else {}
	if last.has("choices"):
		return
	var nxt := str(last.get("next", ""))
	if nxt == "":
		# no explicit next: end of node
		_finish()
		return
	if nxt == "CLOSE":
		_finish()
		return
	_enter_node(nxt)


func _finish() -> void:
	_active = false
	visible = false
	_clear_choices()
	closed.emit()


# ------------------------------------------------------------------ process
func _process(delta: float) -> void:
	if not _active:
		return
	if auto:
		_auto_t += delta
		if _auto_t >= 0.04:
			_auto_t = 0.0
			if _waiting_choice:
				_pick_choice(0)
			else:
				_advance()
		return
	if _waiting_choice:
		return
	if _text_label.visible_characters != -1 and _text_label.visible_characters < _line_full.length():
		_typed += delta * TYPE_CPS
		_text_label.visible_characters = int(_typed)
		if _text_label.visible_characters >= _line_full.length():
			_text_label.visible_characters = -1
			_hint_label.text = "▼"
	else:
		_hint_label.text = "▼" if int(Time.get_ticks_msec() / 500.0) % 2 == 0 else " "


func is_active() -> bool:
	return _active
