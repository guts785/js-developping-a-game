extends CanvasLayer
class_name EndingScreen
## EndingScreen — one of three endings, then the case file summary.

signal restart
signal to_menu

var _panel: Panel
var _title: Label
var _body: Label
var _stats: Label
var _ending_id := ""


func _ready() -> void:
	layer = 32
	visible = false
	process_mode = Node.PROCESS_MODE_ALWAYS

	var shade := ColorRect.new()
	shade.color = Color(0.02, 0.015, 0.02, 0.86)
	shade.size = Vector2(640, 360)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)

	_panel = Ui.make_panel(Color(0.05, 0.04, 0.05, 0.97))
	_panel.position = Vector2(80, 24)
	_panel.size = Vector2(480, 312)
	add_child(_panel)

	var card := Ui.tex("res://art/ui/ending_card.png")
	if card != null:
		var cr := TextureRect.new()
		cr.texture = card
		cr.stretch_mode = TextureRect.STRETCH_SCALE
		cr.position = Vector2(0, 0)
		cr.size = Vector2(480, 312)
		cr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		cr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		cr.modulate = Color(1, 1, 1, 0.35)
		_panel.add_child(cr)

	_title = Ui.make_label("", Locale.SZ_TITLE, Ui.COL_GOLD)
	_title.position = Vector2(0, 16)
	_title.size = Vector2(480, 40)
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_panel.add_child(_title)

	_body = Ui.make_label("", Locale.SZ_SMALL, Ui.COL_TEXT)
	_body.position = Vector2(28, 62)
	_body.size = Vector2(424, 180)
	_body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_body.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_body.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	_panel.add_child(_body)

	_stats = Ui.make_label("", Locale.SZ_TINY, Ui.COL_DIM)
	_stats.position = Vector2(0, 246)
	_stats.size = Vector2(480, 18)
	_stats.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_panel.add_child(_stats)

	var again := Ui.make_button(Locale.t("end_restart"), Locale.SZ_SMALL)
	again.position = Vector2(120, 270)
	again.size = Vector2(110, 26)
	again.pressed.connect(func() -> void:
		AudioManager.play("click", -8.0)
		visible = false
		restart.emit())
	_panel.add_child(again)

	var menu := Ui.make_button(Locale.t("end_menu"), Locale.SZ_SMALL)
	menu.position = Vector2(250, 270)
	menu.size = Vector2(110, 26)
	menu.pressed.connect(func() -> void:
		AudioManager.play("click", -8.0)
		visible = false
		to_menu.emit())
	_panel.add_child(menu)


func show_ending(id: String) -> void:
	_ending_id = id
	visible = true
	GameState.note_ending(id)
	match id:
		"survive":
			_title.text = Locale.t("end_survive_title")
			_body.text = Locale.t("end_survive")
			AudioManager.music("music_menu")
			AudioManager.play("win", -4.0)
		"price":
			_title.text = Locale.t("end_price_title")
			_body.text = Locale.t("end_price")
			AudioManager.music("music_sect")
			AudioManager.play("lose", -4.0)
		"new":
			_title.text = Locale.t("end_new_title")
			_body.text = Locale.t("end_new")
			AudioManager.music("music_sect")
			AudioManager.play("lose", -4.0)
		_:
			_title.text = Locale.t("end_epilogue")
			_body.text = ""
	_stats.text = Locale.tf("end_stats", [mini(GameState.clues.size(), GameState.TOTAL_CLUES),
										  GameState.TOTAL_CLUES,
										  GameState.objectives_done(), GameState.TOTAL_OBJECTIVES])
	AudioManager.ambience("")


func ending_id() -> String:
	return _ending_id
