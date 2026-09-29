extends CanvasLayer
class_name Minigames
## Minigames — three Darija puzzles: الجرات (jars), التعويذة (chant), القفل (lock).

signal finished(kind: String, success: bool)

var _root: Panel
var _title: Label
var _desc: Label
var _body: Control
var _kind := ""
var _tries := 0
var _active := false

# chant state
var _marker := 0.0
var _chant_round := 0
var _chant_hits := 0
var _chant_speed := 0.62
var _zone_a := 0.40
var _zone_b := 0.60
var _chant_note := 0.0
var _chant_done := false

# lock state
var _dials: Array[int] = [3, 3, 3]
const _LOCK_TARGET: Array = [1, 7, 4]     # left, mid, right — from the ledger


func _ready() -> void:
	layer = 20
	visible = false
	process_mode = Node.PROCESS_MODE_ALWAYS


func _build_shell() -> void:
	_root = Ui.make_panel(Color(0.04, 0.03, 0.05, 0.97))
	_root.position = Vector2(120, 40)
	_root.size = Vector2(400, 280)
	add_child(_root)

	_title = Ui.make_label("", Locale.SZ_BODY, Ui.COL_GOLD)
	_title.position = Vector2(0, 10)
	_title.size = Vector2(400, 22)
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_root.add_child(_title)

	_desc = Ui.make_label("", Locale.SZ_TINY, Ui.COL_DIM)
	_desc.position = Vector2(20, 36)
	_desc.size = Vector2(360, 44)
	_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_desc.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_root.add_child(_desc)


func start(kind: String) -> void:
	_kind = kind
	_tries = 0
	_active = true
	visible = true
	for c in get_children():
		c.queue_free()
	_build_shell()
	match kind:
		"jars": _build_jars()
		"chant": _build_chant()
		"lock": _build_lock()
		_: _close(false)


func _close(success: bool) -> void:
	_active = false
	visible = false
	finished.emit(_kind, success)


# ------------------------------------------------------------------ jars
func _build_jars() -> void:
	_title.text = Locale.t("mg_jars_title")
	_desc.text = Locale.t("mg_jars_desc")
	var clues := Ui.make_label(
		"• " + Locale.t("mg_jars_clue1") + "\n• " + Locale.t("mg_jars_clue2") + "\n• " + Locale.t("mg_jars_clue3"),
		Locale.SZ_TINY, Ui.COL_DIM)
	clues.position = Vector2(30, 84)
	clues.size = Vector2(340, 70)
	clues.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_root.add_child(clues)

	var tints := [Color(1.15, 1.05, 0.7, 1.0), Color(0.75, 0.85, 1.0, 1.0), Color(0.7, 0.8, 0.75, 1.0)]
	for i in 3:
		var b := Button.new()
		b.custom_minimum_size = Vector2(64, 64)
		b.size = Vector2(64, 64)
		b.position = Vector2(96 + i * 74, 168)
		b.icon = Ui.tex("res://art/items/jar.png")
		b.expand_icon = true
		b.modulate = tints[i]
		b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		Ui._style_button(b)
		var idx := i
		b.pressed.connect(func() -> void: _jar_pick(idx))
		_root.add_child(b)


func _jar_pick(idx: int) -> void:
	_tries += 1
	if idx == 0:                                  # the one that glints — harmal
		AudioManager.play("pickup", -6.0)
		_title.text = Locale.t("mg_jars_ok")
		await get_tree().create_timer(1.1).timeout
		_close(true)
	else:
		AudioManager.play("fail", -6.0)
		_desc.text = Locale.t("mg_jars_bad") + "\n" + Jokes.pick("fail")


# ------------------------------------------------------------------ chant
func _build_chant() -> void:
	_title.text = Locale.t("mg_chant_title")
	_desc.text = Locale.t("mg_chant_desc") + "\nبل — غا — جن"
	var track := Control.new()
	track.name = "Track"
	track.position = Vector2(40, 150)
	track.size = Vector2(320, 70)
	track.draw.connect(_draw_track)
	_root.add_child(track)
	_marker = 0.0
	_chant_round = 0
	_chant_hits = 0
	_chant_done = false
	_chant_speed = 0.62


func _draw_track() -> void:
	var track := _root.get_node_or_null("Track") as Control
	if track == null:
		return
	var w := track.size.x
	var y := 30.0
	track.draw_rect(Rect2(0, y - 2, w, 8), Color(0.12, 0.10, 0.14, 1))
	track.draw_rect(Rect2(w * _zone_a, y - 6, w * (_zone_b - _zone_a), 16), Color(0.24, 0.42, 0.28, 0.85))
	track.draw_rect(Rect2(w * _marker - 2, y - 12, 4, 28), Color(0.95, 0.72, 0.28, 1))
	# the three letters of the incantation, marking progress
	for i in 3:
		var cx := w * (0.14 + i * 0.36)
		var col := Color(0.85, 0.6, 0.25, 1) if i < _chant_hits else Color(0.35, 0.3, 0.28, 1)
		track.draw_circle(Vector2(cx, y + 30), 5, col)


func _chant_press() -> void:
	if _chant_done or _kind != "chant":
		return
	var in_zone := _marker >= _zone_a and _marker <= _zone_b
	if in_zone:
		_chant_hits += 1
		AudioManager.play("chant_ok", -6.0)
		_desc.text = Locale.t("mg_chant_ok")
	else:
		AudioManager.play("chant_bad", -6.0)
		_desc.text = Locale.t("mg_chant_bad") + "\n" + Jokes.pick("fail")
	_chant_round += 1
	_marker = 0.0
	_chant_speed = 0.62 + 0.16 * _chant_round
	_zone_a = randf_range(0.30, 0.48)
	_zone_b = _zone_a + 0.18
	if _chant_round >= 3:
		_chant_done = true
		var ok := _chant_hits >= 2
		if ok:
			_desc.text = Locale.t("mg_chant_perfect")
		await get_tree().create_timer(1.2).timeout
		_close(ok)


# ------------------------------------------------------------------ lock
func _build_lock() -> void:
	_title.text = Locale.t("mg_lock_title")
	_desc.text = Locale.t("mg_lock_desc") + "\n" + Locale.t("mg_lock_hint")
	_dials = [3, 3, 3]
	var names := ["اليسار", "الوسط", "اليمين"]
	for i in 3:
		var lbl := Ui.make_label(names[i], Locale.SZ_TINY, Ui.COL_DIM)
		lbl.position = Vector2(150 + i * 74, 96)
		lbl.size = Vector2(60, 18)
		lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_root.add_child(lbl)

		var val := Ui.make_label(str(_dials[i]), Locale.SZ_BODY, Ui.COL_GOLD)
		val.name = "Val%d" % i
		val.position = Vector2(150 + i * 74, 132)
		val.size = Vector2(60, 26)
		val.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_root.add_child(val)

		var up := Ui.make_button("▲", Locale.SZ_TINY)
		up.position = Vector2(160 + i * 74, 110)
		up.size = Vector2(40, 20)
		var iu := i
		up.pressed.connect(func() -> void: _dial(iu, 1))
		_root.add_child(up)

		var dn := Ui.make_button("▼", Locale.SZ_TINY)
		dn.position = Vector2(160 + i * 74, 158)
		dn.size = Vector2(40, 20)
		var idn := i
		dn.pressed.connect(func() -> void: _dial(idn, -1))
		_root.add_child(dn)

	var check := Ui.make_button("جرّب القفل", Locale.SZ_SMALL)
	check.position = Vector2(150, 200)
	check.size = Vector2(100, 26)
	check.pressed.connect(_lock_check)
	_root.add_child(check)


func _dial(i: int, d: int) -> void:
	_dials[i] = int(clampf(_dials[i] + d, 1, 9))
	var v := _root.get_node_or_null("Val%d" % i) as Label
	if v != null:
		v.text = str(_dials[i])
	AudioManager.play("click", -16.0)


func _lock_check() -> void:
	var ok := _dials[0] == int(_LOCK_TARGET[0]) and _dials[1] == int(_LOCK_TARGET[1]) and _dials[2] == int(_LOCK_TARGET[2])
	if ok:
		AudioManager.play("door", -4.0)
		_title.text = Locale.t("mg_lock_ok")
		await get_tree().create_timer(1.2).timeout
		_close(true)
	else:
		AudioManager.play("fail", -6.0)
		_desc.text = Locale.t("mg_lock_bad") + "\n" + Jokes.pick("fail")


## Test hook: solve the puzzle the intended way. Used by the --playtest sweep to
## exercise the win path of every minigame without a human hand.
func auto_win() -> void:
	if not _active:
		return
	match _kind:
		"jars":
			_jar_pick(0)
		"chant":
			for i in 3:
				_marker = (_zone_a + _zone_b) * 0.5
				_chant_press()
				if _chant_done:
					break
		"lock":
			_dials = [int(_LOCK_TARGET[0]), int(_LOCK_TARGET[1]), int(_LOCK_TARGET[2])]
			_lock_check()


# ------------------------------------------------------------------ loop
func _process(delta: float) -> void:
	if not _active:
		return
	if _kind == "chant" and not _chant_done:
		_marker += delta * _chant_speed
		if _marker > 1.0:
			_marker = 0.0
			_chant_round += 1
			if _chant_round >= 3:
				_chant_done = true
				var ok := _chant_hits >= 2
				_close(ok)
		var track := _root.get_node_or_null("Track")
		if track != null:
			track.queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if not _active or _kind != "chant":
		return
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_SPACE:
		get_viewport().set_input_as_handled()
		_chant_press()
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		get_viewport().set_input_as_handled()
		_chant_press()


func is_active() -> bool:
	return _active
