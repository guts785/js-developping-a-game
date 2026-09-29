extends Node2D
## Main — the orchestrator. Rooms, hotspots, the player, dialogue, minigames,
## chapter cards, endings, save/load, and the CRT pass.

enum St { TITLE, PLAY, DIALOGUE, MINI, ENDING, CARD }

const ART := 2.0                       # logical (320x180) -> world (640x360)

# ------------------------------------------------------------------ layer bands
# Every overlay owns an explicit band, so nothing can render behind something it
# should cover. Rooms and characters are authored at native 640x360 (ART is only
# the logical->world multiplier for hotspot rects and data coordinates).
const LAYER_FX := 5            # CRT + vignette, world only so Arabic text stays crisp
const LAYER_HUD := 10          # objective banner, inventory strip, hotspot label, toasts
const LAYER_DIALOGUE := 12     # dialogue box rides above the HUD strip
const LAYER_MINIGAME := 20
const LAYER_CARD := 25         # chapter card
const LAYER_TITLE := 30
const LAYER_ENDING := 32
const LAYER_TOP := 40          # tube frame: vignette over the whole picture, UI included
const EXIT_ZONE_L := Rect2(0, 112, 30, 68)
const EXIT_ZONE_R := Rect2(290, 112, 30, 68)

var state: St = St.TITLE
var room_id := "office"
var room: Dictionary = {}
var hotspots: Array = []
var npc_nodes: Array = []
var player: Node2D
var bg: Sprite2D
var hover_marker: Node2D

var hud: Hud
var dialogue: DialogueBox
var minigames: Minigames
var title_screen: TitleScreen
var ending_screen: EndingScreen
var card_layer: CanvasLayer
var card_panel: Panel
var card_art: TextureRect
var card_title: Label
var card_body: Label
var card_btn: Button

var world: Node2D
var fx_layer: CanvasLayer
var ui_layer: CanvasLayer
var dialogue_layer: CanvasLayer
var fx_rect: ColorRect
var fx_mat: ShaderMaterial
var top_layer: CanvasLayer

var hover_hs: Dictionary = {}
var hover_npc: Node2D = null
var hover_exit := ""
var pending_action: Array = []
var pending_ending := ""
var toast_busy := false
var idle_timer := 0.0
var last_click_id := ""
var last_click_time := 0.0
var label_holder: Label
var cursor_tex: Texture2D

# Dev-only. `--inputtest` parks a Callable here so the game can prove that key
# events actually reach it through the display shell's SubViewportContainer.
var _input_probe: Callable = Callable()


func _ready() -> void:
	_ensure_input()
	randomize()
	_build_layers()
	_build_cursor()
	GameState.reset()
	state = St.TITLE
	AudioManager.music("music_menu")
	AudioManager.ambience("")
	title_screen.open()
	# headless verification passes:
	#   godot --headless -- --selftest    (static: data, assets, locale)
	#   godot --headless -- --playtest    (runtime: rooms, hotspots, dialogue, minigames)
	#   godot --headless -- --solve       (progression: is the case finishable)
	var args := OS.get_cmdline_args() + OS.get_cmdline_user_args()
	if args.has("--selftest"):
		SelfTest.run(get_tree())
	elif args.has("--playtest"):
		PlayTest.run(self)
	elif args.has("--solve"):
		Solver.run(get_tree())
	elif args.has("--shot"):
		_run_shots(args)
	elif args.has("--inputtest"):
		_run_input_test()


func _input(event: InputEvent) -> void:
	if _input_probe.is_valid():
		_input_probe.call(event)


## Dev harness: `godot --path . -- --inputtest` injects one key through the real
## input pipeline and reports whether the game saw it. A broken container bridge
## and a broken keybind look identical from the outside, so this separates them.
func _run_input_test() -> void:
	for _n in range(12):
		await get_tree().process_frame
	var seen := {"got": false, "count": 0}
	_input_probe = func(ev: InputEvent) -> void:
		if ev is InputEventKey and ev.pressed and ev.keycode == KEY_J:
			seen["got"] = true
			seen["count"] = int(seen["count"]) + 1
	var ev := InputEventKey.new()
	ev.keycode = KEY_J
	ev.physical_keycode = KEY_J
	ev.pressed = true
	Input.parse_input_event(ev)
	for _n in range(12):
		await get_tree().process_frame
	print("INPUTTEST forwarded=%s copies=%d" % [str(seen["got"]), int(seen["count"])])
	_input_probe = Callable()
	get_tree().quit()


# ------------------------------------------------------------------ shot mode
## Dev harness: `godot --path . -- --shot <target>` renders one frame of a named
## state to res://shot_<target>.png and quits. Needs a real GPU context (no
## --headless). Targets: title, settings, chapters, credits, play, room:<id>.
func _run_shots(args: Array) -> void:
	var target := "title"
	var i := args.find("--shot")
	if i >= 0 and i + 1 < args.size():
		target = str(args[i + 1])
	for _n in range(8):
		await get_tree().process_frame
	match target:
		"settings":
			title_screen._show_settings()
		"chapters":
			title_screen._show_chapters()
		"credits":
			title_screen._show_credits()
		"card":
			# The in-game chapter card, left up. _new_game() opens it and does not
			# dismiss it, so this arm only has to hide the menu behind it.
			title_screen.visible = false
			_new_game()
		_:
			# "play" and "room:<id>" both need a live game behind the shot.
			# GDScript match patterns are exact, so the room: prefix is tested here.
			if target == "play" or target.begins_with("room:"):
				# _new_game() does not hide the title itself -- the menu button does
				# that in _on_action(), so a direct call has to do it here.
				title_screen.visible = false
				_new_game()
	if target.begins_with("room:"):
		await get_tree().create_timer(0.45).timeout
		_dismiss_card()
		_load_room(target.substr(5))
	elif target == "play":
		await get_tree().create_timer(0.45).timeout
		_dismiss_card()
	if target == "play" or target.begins_with("room:"):
		# The first objective arrives from a hotspot, not on_enter, so a bare room
		# load leaves the banner blank. Mirror the real first objective so the
		# captured frame shows a populated HUD.
		hud.set_objective("شوف الجثة، ولقّط البلغة الكحلة")
	for _n in range(24):
		await get_tree().process_frame
	await get_tree().create_timer(0.30).timeout
	_dump_frame_state()
	var stem := "res://shot_%s" % target.replace(":", "_")

	# Two captures, on purpose. The raw one is the 640x360 game buffer with the CRT
	# off -- that is the frame you actually measure pixels on. The other is the real
	# window output at whatever the integer stretch landed on, i.e. what the player
	# sees in fullscreen.
	_set_crt(false)
	for _n in range(4):
		await get_tree().process_frame
	var raw := get_viewport().get_texture().get_image()
	var raw_err := raw.save_png(stem + "_raw.png")

	_set_crt(true)
	for _n in range(4):
		await get_tree().process_frame
	var img := get_tree().root.get_texture().get_image()
	var err := img.save_png(stem + ".png")
	# bisect: hide one CanvasLayer at a time. The layer whose removal clears the
	# artefact is the one drawing it.
	var layers := []
	for c in get_children():
		if c is CanvasLayer:
			layers.append(c)
	for c in layers:
		var was: bool = c.visible
		c.visible = false
		for _n in range(3):
			await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png("res://shot_play_noL%d.png" % c.layer)
		c.visible = was
	for _n in range(3):
		await get_tree().process_frame
	print("SHOT %s -> %s %dx%d err=%d | raw %dx%d err=%d" % [
		target, stem + ".png", img.get_width(), img.get_height(), err,
		raw.get_width(), raw.get_height(), raw_err])
	get_tree().quit()


# ------------------------------------------------------------------ setup
func _build_layers() -> void:
	world = Node2D.new()
	world.name = "World"
	world.y_sort_enabled = true          # walk behind an NPC and he occludes you
	add_child(world)

	bg = Sprite2D.new()
	bg.centered = false
	bg.scale = Vector2(1.0, 1.0)         # rooms are authored at native 640x360
	bg.z_index = -100                    # always the backmost thing in the room
	bg.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	world.add_child(bg)

	hover_marker = Node2D.new()
	hover_marker.z_index = 100           # markers stay legible over furniture
	hover_marker.draw.connect(_draw_hover)
	world.add_child(hover_marker)

	player = load("res://src/core/player.gd").new()
	world.add_child(player)
	player.setup("rachid", "stone", true)
	player.arrived.connect(_execute_pending)

	# CRT pass over the world only
	fx_layer = CanvasLayer.new()
	fx_layer.layer = LAYER_FX
	add_child(fx_layer)
	fx_rect = ColorRect.new()
	fx_rect.size = Vector2(640, 360)
	fx_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fx_mat = ShaderMaterial.new()
	fx_mat.shader = load("res://src/core/retro.gdshader")
	fx_mat.set_shader_parameter("enabled", 1.0 if bool(GameState.settings.get("scanlines", true)) else 0.0)
	fx_rect.material = fx_mat
	fx_layer.add_child(fx_rect)

	# The tube frame rides above everything, UI included. One vignette over the
	# whole picture is what makes the HUD feel printed onto the screen instead of
	# pasted on top of it.
	top_layer = CanvasLayer.new()
	top_layer.layer = LAYER_TOP
	add_child(top_layer)

	var vig := Ui.tex("res://art/ui/vignette.png")
	if vig != null:
		var vr := TextureRect.new()
		vr.texture = vig
		vr.stretch_mode = TextureRect.STRETCH_SCALE
		vr.size = Vector2(640, 360)
		vr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		vr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		top_layer.add_child(vr)

	# UI
	ui_layer = CanvasLayer.new()
	ui_layer.layer = LAYER_HUD
	add_child(ui_layer)

	hud = load("res://src/core/hud.gd").new()
	ui_layer.add_child(hud)
	hud.item_selected.connect(func(id: String) -> void: _on_item_selected(id))
	hud.item_cleared.connect(func() -> void: pass)
	hud.resume_requested.connect(func() -> void: _set_paused(false))
	hud.save_requested.connect(_on_save)
	hud.load_requested.connect(_on_load)
	hud.main_menu_requested.connect(_to_title)
	hud.quit_requested.connect(func() -> void: get_tree().quit())
	hud.scanlines_toggled.connect(func(on: bool) -> void:
		fx_mat.set_shader_parameter("enabled", 1.0 if on else 0.0))
	hud.fullscreen_toggled.connect(func(on: bool) -> void:
		var shell := _shell()
		if shell != null and shell.has_method("set_fullscreen"):
			shell.set_fullscreen(on))

	dialogue_layer = CanvasLayer.new()
	dialogue_layer.layer = LAYER_DIALOGUE
	add_child(dialogue_layer)
	dialogue = load("res://src/core/dialogue_box.gd").new()
	dialogue_layer.add_child(dialogue)
	dialogue.closed.connect(_on_dialogue_closed)

	label_holder = Ui.make_label("", Locale.SZ_SMALL, Ui.COL_GOLD)
	label_holder.position = Vector2(160, 208)
	label_holder.size = Vector2(320, 20)
	label_holder.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	Ui.outline(label_holder)
	label_holder.visible = false
	ui_layer.add_child(label_holder)

	minigames = load("res://src/core/minigames.gd").new()
	ui_layer.add_child(minigames)
	minigames.finished.connect(_on_minigame_finished)

	title_screen = load("res://src/ui/title.gd").new()
	add_child(title_screen)
	title_screen.new_game.connect(_new_game)
	title_screen.continue_game.connect(_continue_game)
	title_screen.chapter_pick.connect(_start_chapter)
	title_screen.quit_game.connect(func() -> void: get_tree().quit())

	ending_screen = load("res://src/ui/ending.gd").new()
	add_child(ending_screen)
	ending_screen.restart.connect(_new_game)
	ending_screen.to_menu.connect(_to_title)

	_build_card()


func _build_cursor() -> void:
	cursor_tex = Ui.tex("res://art/ui/cursor.png")
	if cursor_tex != null:
		Input.set_custom_mouse_cursor(cursor_tex, Input.CURSOR_ARROW, Vector2(2, 2))
		Input.set_custom_mouse_cursor(cursor_tex, Input.CURSOR_POINTING_HAND, Vector2(2, 2))


func _build_card() -> void:
	card_layer = CanvasLayer.new()
	card_layer.layer = LAYER_CARD
	add_child(card_layer)
	card_panel = Ui.make_panel(Color(0.04, 0.03, 0.05, 0.97))
	card_panel.position = Vector2(110, 48)
	card_panel.size = Vector2(420, 264)
	card_panel.visible = false
	card_layer.add_child(card_panel)

	var card_tex := Ui.tex("res://art/ui/chapter_card.png")
	if card_tex != null:
		card_art = TextureRect.new()
		card_art.texture = card_tex
		card_art.stretch_mode = TextureRect.STRETCH_SCALE
		card_art.size = card_panel.size
		card_art.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		card_art.modulate = Color(1, 1, 1, 0.30)
		card_art.mouse_filter = Control.MOUSE_FILTER_IGNORE
		card_panel.add_child(card_art)

	card_title = Ui.make_label("", Locale.SZ_BODY, Ui.COL_GOLD)
	card_title.position = Vector2(0, 18)
	card_title.size = Vector2(420, 26)
	card_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	card_panel.add_child(card_title)

	card_body = Ui.make_label("", Locale.SZ_SMALL, Ui.COL_TEXT)
	card_body.position = Vector2(30, 52)
	card_body.size = Vector2(360, 120)
	card_body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	card_body.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	card_body.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	card_panel.add_child(card_body)

	card_btn = Ui.make_button(Locale.t("ch1_go"), Locale.SZ_SMALL)
	card_btn.position = Vector2(140, 192)
	card_btn.size = Vector2(140, 28)
	card_btn.pressed.connect(_dismiss_card)
	card_panel.add_child(card_btn)


# ------------------------------------------------------------------ flow
func _new_game() -> void:
	GameState.reset()
	GameState.chapter = 1
	GameState.max_chapter = 1
	AudioManager.stop_all()
	AudioManager.music("music_menu")
	# state first. _load_room() only runs a room's on_enter when no card is up, and
	# the card is already showing. Setting the state afterwards let the office's
	# opening narration start underneath the card and then be orphaned there.
	state = St.CARD
	_show_chapter_card(1)
	_load_room("office", "right")


func _continue_game() -> void:
	if not GameState.load_game():
		hud.toast(Locale.t("no_save"))
		title_screen.open()
		return
	AudioManager.stop_all()
	_load_room(GameState.current_room, "right")
	hud.set_objective(GameState.objective)
	state = St.PLAY


func _start_chapter(ch: int) -> void:
	GameState.reset()
	GameState.chapter = ch
	GameState.max_chapter = ch
	_grant_chapter_kit(ch)
	AudioManager.stop_all()
	state = St.CARD
	_show_chapter_card(ch)
	_load_room(Data.first_room_of_chapter(ch), "right")


## Hand the player the tools the earlier chapters would have given them.
func _grant_chapter_kit(ch: int) -> void:
	if ch >= 2:
		GameState.set_flag("body_done")
		GameState.set_flag("hook_taken")
		GameState.set_flag("has_black")
		GameState.set_flag("ch1_ready")
		GameState.set_flag("photo_taken")
		GameState.set_flag("window_done")
		GameState.set_flag("board_done")
		GameState.give("it_hook")
		GameState.give("it_mirror")
		GameState.give("it_candle")
		GameState.give("it_match")
		GameState.give("it_photo")
		GameState.give("it_babouche_black")
		GameState.give("it_badge")
		GameState.give("it_watch")
		GameState.give("it_coin")
	if ch >= 3:
		GameState.set_flag("ch2_done")
		GameState.give("it_necklace")
	if ch >= 4:
		GameState.set_flag("ch3_done")
		GameState.set_flag("zahra_paid")
		GameState.set_flag("zahra_truth")
		GameState.set_flag("harmal_found")
		GameState.set_flag("herbs_taken")
		GameState.give("it_herbs")
		GameState.give("it_salt")
		GameState.give("it_amulet")
		GameState.give("it_key")
	if ch >= 5:
		GameState.set_flag("fqih_taught")
		GameState.set_flag("boukhnecha")
		GameState.set_flag("boukhnecha_allied")
		GameState.set_flag("ledger_taken")
		GameState.set_flag("sigil_seen")
		GameState.set_flag("hidden_door")
		GameState.give("it_ledger")
		GameState.give("it_cassette")
		GameState.give("it_recorder")
		GameState.give("it_sigil")
	if ch >= 6:
		GameState.set_flag("book_read")
		GameState.set_flag("mix_in")
		GameState.set_flag("chant_done")
		GameState.give("it_knife")
		GameState.set_flag("skulls_done")
		GameState.set_flag("black_tag_done")
		GameState.set_flag("lock_done")


func _to_title() -> void:
	state = St.TITLE
	GameState.save_game()
	hud.close_overlays()
	hud.set_inventory_visible(false)
	card_panel.visible = false
	dialogue.visible = false
	AudioManager.stop_all()
	AudioManager.music("music_menu")
	title_screen.open()


func _show_chapter_card(ch: int) -> void:
	card_panel.visible = true
	card_title.text = Locale.t("ch%d" % ch)
	var body := Locale.t("ch%d_sub" % ch)
	if ch == 1:
		body = Locale.t("ch1_card")
	card_body.text = body
	card_btn.text = Locale.t("ch1_go")
	_layout_card()


## A Label overflows rather than clips, and chapter 1's card is six lines of text.
## The button and the panel are therefore sized from the text's real wrapped
## height instead of a fixed offset that only ever fitted the short chapters.
func _layout_card() -> void:
	await get_tree().process_frame
	var h := 0.0
	for i in card_body.get_line_count():
		h += card_body.get_line_height(i)
	card_body.size = Vector2(card_body.size.x, h)
	var btn_y := card_body.position.y + h + 18.0
	card_btn.position = Vector2((card_panel.size.x - card_btn.size.x) * 0.5, btn_y)
	var panel_h := btn_y + card_btn.size.y + 20.0
	card_panel.size = Vector2(card_panel.size.x, panel_h)
	card_panel.position.y = clampf((360.0 - panel_h) * 0.5, 16.0, 240.0)
	if card_art != null:
		card_art.size = card_panel.size
	if "--shot" in OS.get_cmdline_user_args():
		print("CARD body_y=%.0f body_h=%.0f btn_y=%.0f panel_h=%.0f" % [
			card_body.position.y, h, btn_y, panel_h])


func _dismiss_card() -> void:
	AudioManager.play("click", -8.0)
	card_panel.visible = false
	state = St.PLAY
	hud.set_inventory_visible(true)
	var r: Dictionary = room
	if r.has("on_enter") and not GameState.visited.has(room_id):
		GameState.visited[room_id] = true
		run_actions(r["on_enter"])


# ------------------------------------------------------------------ room
func _load_room(id: String, side: String = "right") -> void:
	room_id = id
	room = Data.room(id)
	if room.is_empty():
		push_error("unknown room: " + id)
		return
	var bg_tex := Ui.tex(str(room.get("bg", "")))
	if bg_tex != null:
		bg.texture = bg_tex

	hotspots = []
	for h in room.get("hotspots", []):
		hotspots.append(h)

	for n in npc_nodes:
		n.queue_free()
	npc_nodes.clear()
	for spec in room.get("npcs", []):
		var d: Dictionary = spec
		var npc: Node2D = load("res://src/core/player.gd").new() as Node2D
		world.add_child(npc)
		npc.setup(str(d.get("char", "hmidou")), "stone", false)
		npc.speed = 40.0
		npc.place(float(d.get("x", 160)) * ART, float(d.get("y", 152)) * ART)
		npc.set_meta("spec", d)
		npc_nodes.append(npc)

	var base_y := float(room.get("base_y", 152)) * ART
	var walk: Array = room.get("walk", [30, 292])
	# the floor band he can actually stand on: x across the room, y a strip of depth
	player.set_band(float(walk[0]) * ART + 8.0, float(walk[1]) * ART - 8.0, base_y,
			26.0, maxf(4.0, 360.0 - 46.0 - 8.0 - base_y))
	var x := float(walk[1]) * ART - 40.0 if side == "right" else float(walk[0]) * ART + 40.0
	player.place(x, base_y)

	var ch := int(room.get("chapter", GameState.chapter))
	if ch > GameState.chapter:
		GameState.chapter = ch
		GameState.max_chapter = maxi(GameState.max_chapter, ch)
		_show_chapter_card(ch)
		state = St.CARD
	elif ch < GameState.chapter:
		GameState.chapter = ch

	AudioManager.ambience(str(room.get("ambience", "")))
	AudioManager.music(str(room.get("music", "")))
	GameState.current_room = id

	# With a card up, leave both the visit mark and the entry beat to _dismiss_card():
	# it is the only place that knows the card has come down. Doing it here fired
	# on_enter while the card still covered the screen, so the opening dialogue opened
	# behind it and was then stranded -- a black box the player could not advance or
	# close. Marking the room visited here also swallowed the beat entirely, because
	# _dismiss_card() only runs on_enter for a room it has not seen.
	if state != St.CARD:
		if not GameState.visited.has(id):
			GameState.visited[id] = true
			if room.has("on_enter"):
				run_actions(room["on_enter"])
		else:
			hud.set_objective(GameState.objective)


func _base_y() -> float:
	return float(room.get("base_y", 152)) * ART


# ------------------------------------------------------------------ input
func _ensure_input() -> void:
	# Bound in code rather than project.godot: physical_keycode keeps WASD in the
	# same physical spot on AZERTY, and this can't rot when Godot changes the
	# serialised InputEventKey format.
	_bind("walk_left", [KEY_A, KEY_LEFT])
	_bind("walk_right", [KEY_D, KEY_RIGHT])
	_bind("walk_up", [KEY_W, KEY_UP])
	_bind("walk_down", [KEY_S, KEY_DOWN])
	_bind("interact", [KEY_E, KEY_SPACE, KEY_ENTER])


func _bind(action: String, keys: Array) -> void:
	if not InputMap.has_action(action):
		InputMap.add_action(action)
	for k in keys:
		var ev := InputEventKey.new()
		ev.physical_keycode = k
		InputMap.action_add_event(action, ev)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("interact"):
		if state == St.PLAY and not hud.is_pause_open() and not hud.is_journal_open():
			_interact()
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.alt_pressed and event.keycode == KEY_ENTER:
			_toggle_fullscreen()
			return
		match event.keycode:
			KEY_ESCAPE:
				if minigames.is_active() or dialogue.is_active():
					return
				if hud.is_pause_open():
					hud.close_pause()
					_set_paused(false)
				elif hud.is_journal_open():
					hud.toggle_journal()
				else:
					hud.open_pause()
					_set_paused(true)
				return
			KEY_J:
				if state == St.PLAY:
					hud.toggle_journal()
				return
			KEY_H:
				if state == St.PLAY:
					hud.toast(Locale.t("hint_ch%d" % GameState.chapter), 4.5)
				return
			KEY_F11:
				_toggle_fullscreen()
				return
			KEY_F12:
				_screenshot()
				return
			KEY_I:
				if state == St.PLAY:
					hud.clear_selection()
				return
	if state != St.PLAY:
		return
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_LEFT:
			_click(get_global_mouse_position(), false)
		elif event.button_index == MOUSE_BUTTON_RIGHT:
			_click(get_global_mouse_position(), true)


func _click(pos: Vector2, examine: bool) -> void:
	# NPC first — they sit on top of the scenery
	if hover_npc != null:
		var spec: Dictionary = hover_npc.get_meta("spec")
		var nx: float = hover_npc.position.x
		player.walk_to(clampf(nx + 26.0 * (1.0 if player.position.x < nx else -1.0), 40, 600))
		pending_action = [{"dlg": str(spec.get("dlg", ""))}]
		pending_ending = ""
		return

	if not hover_hs.is_empty():
		var hs: Dictionary = hover_hs
		if not GameState.cond_ok(hs.get("cond", null)):
			# a second hotspot may describe the same object in another state
			var alt := _alt_hotspot(hs)
			if not alt.is_empty():
				hs = alt
			elif hs.has("use"):
				_do_hotspot(hs, "use")
				return
			else:
				return
		var cx := _hs_center_x(hs)
		player.walk_to(cx)
		pending_action = [{"hs": hs, "examine": examine}]
		pending_ending = ""
		return

	if hover_exit != "":
		_click_exit(hover_exit)
		return

	player.walk_to(pos.x)
	pending_action = []


func _click_exit(side: String) -> void:
	var ex: Dictionary = room.get("exits", {}).get(side, {})
	if ex.is_empty():
		return
	if not GameState.cond_ok(ex.get("cond", null)):
		hud.toast(Locale.t("prompt_locked") + " — " + Jokes.pick("wrong_use"), 3.0)
		AudioManager.play("fail", -10.0)
		return
	AudioManager.play("step_stone", -8.0)
	_load_room(str(ex.get("to", room_id)), side)


func _nearest_interactable() -> Dictionary:
	# What [E] acts on: the closest thing to the inspector's feet, plus doorways he
	# is standing in.
	if player == null:
		return {}
	var px: float = player.position.x
	var best: Dictionary = {}
	var best_d := 132.0
	for n in npc_nodes:
		var npc: Node2D = n as Node2D
		var d: float = absf(npc.position.x - px)
		if d < best_d:
			best_d = d
			best = {"kind": "npc", "npc": npc}
	for h in hotspots:
		var hs: Dictionary = h
		if not GameState.cond_ok(hs.get("cond", null)):
			continue
		var d2: float = absf(_hs_center_x(hs) - px)
		if d2 < best_d:
			best_d = d2
			best = {"kind": "hs", "hs": hs}
	for side in ["left", "right"]:
		if not room.get("exits", {}).has(side):
			continue
		var zx := 46.0 if side == "left" else 596.0
		if absf(px - zx) < 54.0:
			return {"kind": "exit", "side": side}
	return best


func _interact() -> void:
	if state != St.PLAY:
		return
	var t := _nearest_interactable()
	if t.is_empty():
		AudioManager.play("fail", -14.0)
		return
	match str(t.get("kind", "")):
		"npc":
			var npc: Node2D = t["npc"]
			var spec: Dictionary = npc.get_meta("spec")
			var side := 1.0 if player.position.x < npc.position.x else -1.0
			player.walk_to(clampf(npc.position.x + 30.0 * side, 40.0, 600.0))
			pending_action = [{"dlg": str(spec.get("dlg", ""))}]
			pending_ending = ""
		"hs":
			var hs: Dictionary = t["hs"]
			if not GameState.cond_ok(hs.get("cond", null)):
				var alt := _alt_hotspot(hs)
				if not alt.is_empty():
					hs = alt
				elif hs.has("use"):
					_do_hotspot(hs, "use")
					return
				else:
					return
			player.walk_to(_hs_center_x(hs))
			pending_action = [{"hs": hs, "examine": false}]
			pending_ending = ""
		"exit":
			_click_exit(str(t.get("side", "")))


func _alt_hotspot(hs: Dictionary) -> Dictionary:
	# hotspots sharing the same rect act as states of one object
	var rect: Array = hs.get("rect", [])
	for other in hotspots:
		var o: Dictionary = other
		if o == hs:
			continue
		if o.get("rect", []) == rect and GameState.cond_ok(o.get("cond", null)):
			return o
	return {}


func _hs_center_x(hs: Dictionary) -> float:
	var r: Array = hs.get("rect", [0, 0, 0, 0])
	var cx := (float(r[0]) + float(r[2])) * 0.5 * ART
	var walk: Array = room.get("walk", [30, 292])
	return clampf(cx, float(walk[0]) * ART + 10.0, float(walk[1]) * ART - 10.0)


func _process(delta: float) -> void:
	if player != null:
		player.input_enabled = (state == St.PLAY
			and not hud.is_pause_open() and not hud.is_journal_open()
			and not minigames.is_active() and not dialogue.is_active())
	if state == St.PLAY:
		_update_hover()
		idle_timer += delta
		if idle_timer > 26.0 and not toast_busy:
			idle_timer = 0.0
			toast_busy = true
			hud.toast(Jokes.pick("idle"), 4.0)
			get_tree().create_timer(4.2).timeout.connect(func() -> void: toast_busy = false)
	elif state == St.TITLE:
		pass


func _update_hover() -> void:
	var pos := get_global_mouse_position()
	hover_hs = {}
	hover_npc = null
	hover_exit = ""

	for n in npc_nodes:
		var npc: Node2D = n as Node2D
		if absf(npc.position.x - pos.x) < 26.0 and pos.y > npc.position.y - 108.0 and pos.y < npc.position.y + 6.0:
			hover_npc = npc as Node2D
			break

	if hover_npc == null:
		for i in range(hotspots.size() - 1, -1, -1):
			var hs: Dictionary = hotspots[i]
			var r: Array = hs.get("rect", [])
			if r.size() < 4:
				continue
			var wr := Rect2(float(r[0]) * ART, float(r[1]) * ART,
							(float(r[2]) - float(r[0])) * ART, (float(r[3]) - float(r[1])) * ART)
			if wr.has_point(pos):
				hover_hs = hs
				break

	if hover_hs.is_empty() and hover_npc == null:
		for side in ["left", "right"]:
			if not room.get("exits", {}).has(side):
				continue
			var z: Rect2 = EXIT_ZONE_L if side == "left" else EXIT_ZONE_R
			var wz := Rect2(z.position.x * ART, z.position.y * ART, z.size.x * ART, z.size.y * ART)
			if wz.has_point(pos):
				hover_exit = side
				break

	# label + cursor feedback
	if hover_npc != null:
		var spec: Dictionary = hover_npc.get_meta("spec")
		label_holder.text = Locale.t(str(spec.get("name", "")))
		label_holder.visible = true
		label_holder.position = Vector2(clampf(pos.x - 160.0, 0, 320), 200)
	elif not hover_hs.is_empty():
		label_holder.text = str(hover_hs.get("label", ""))
		label_holder.visible = true
		label_holder.position = Vector2(clampf(pos.x - 160.0, 0, 320), 200)
	elif hover_exit != "":
		var ex: Dictionary = room.get("exits", {}).get(hover_exit, {})
		label_holder.text = str(ex.get("label", ""))
		label_holder.visible = true
		label_holder.position = Vector2(clampf(pos.x - 160.0, 0, 320), 200)
	else:
		label_holder.visible = false
	hover_marker.queue_redraw()


func _draw_hover() -> void:
	if state != St.PLAY:
		return
	if not hover_hs.is_empty():
		var r: Array = hover_hs.get("rect", [])
		if r.size() >= 4:
			var rect := Rect2(float(r[0]) * ART, float(r[1]) * ART,
							  (float(r[2]) - float(r[0])) * ART, (float(r[3]) - float(r[1])) * ART)
			hover_marker.draw_rect(rect, Color(0.95, 0.78, 0.35, 0.85), false, 1.0)
	elif hover_exit != "":
		var z: Rect2 = EXIT_ZONE_L if hover_exit == "left" else EXIT_ZONE_R
		hover_marker.draw_rect(Rect2(z.position.x * ART, z.position.y * ART, z.size.x * ART, z.size.y * ART),
							   Color(0.95, 0.78, 0.35, 0.85), false, 1.0)

	# WASD affordance — a chevron over whatever [E] would act on right now
	var t := _nearest_interactable()
	if t.is_empty():
		return
	var mx := 0.0
	var top := 0.0
	var col := Color(0.55, 0.95, 0.65, 0.92)
	match str(t.get("kind", "")):
		"npc":
			var npc: Node2D = t["npc"]
			mx = npc.position.x
			top = npc.position.y - 114.0   # clear of the 108px sprite
		"hs":
			var hs: Dictionary = t["hs"]
			var r: Array = hs.get("rect", [0, 0, 0, 0])
			if r.size() < 4:
				return
			mx = _hs_center_x(hs)
			top = float(r[1]) * ART - 6.0
		"exit":
			mx = 46.0 if str(t.get("side", "")) == "left" else 596.0
			top = 160.0
			col = Color(0.95, 0.78, 0.35, 0.92)
		_:
			return
	hover_marker.draw_polyline(PackedVector2Array([
		Vector2(mx - 5.0, top - 11.0), Vector2(mx + 5.0, top - 11.0),
		Vector2(mx, top - 3.0), Vector2(mx - 5.0, top - 11.0)]), col, 1.0)


# ------------------------------------------------------------------ arrival
func _on_player_arrived() -> void:
	pass


func _execute_pending() -> void:
	if pending_action.is_empty():
		return
	var a: Dictionary = pending_action[0]
	pending_action = []
	if a.has("hs"):
		_do_hotspot(a["hs"], "look" if a["examine"] else "use")
	elif a.has("dlg"):
		var id := str(a["dlg"])
		if id != "" and not Data.dialogue(id).is_empty():
			_start_dialogue(id)


func _do_hotspot(hs: Dictionary, mode: String) -> void:
	var id := str(hs.get("id", ""))
	var n := GameState.bump_examine(id)
	if n >= 3 and mode != "look":
		hud.toast(Jokes.pick("repeat"), 3.0)
		AudioManager.play("hover", -14.0)

	# using an inventory item on this hotspot
	if mode == "use" and hud.selected_item != "":
		var item := hud.selected_item
		if hs.has("item_use") and hs["item_use"].has(item):
			run_actions(hs["item_use"][item])
			return
		if hs.has("use") and GameState.cond_ok(hs.get("cond", null)):
			hud.clear_selection()
			_respond(hs, "use")
			return
		AudioManager.play("fail", -10.0)
		hud.toast(Jokes.pick("wrong_use"), 3.2)
		hud.clear_selection()
		return

	if mode == "look":
		if hs.has("look"):
			_respond(hs, "look")
		else:
			hud.toast(Jokes.pick("examine_miss"), 3.2)
		return

	# plain use: prefer the contextual response
	if hs.has("use"):
		_respond(hs, "use")
	elif hs.has("take"):
		_respond(hs, "take")
	elif hs.has("talk"):
		_respond(hs, "talk")
	elif hs.has("look"):
		_respond(hs, "look")
	else:
		hud.toast(Jokes.pick("examine_miss"), 3.2)


func _respond(hs: Dictionary, key: String) -> void:
	var text := str(hs.get(key, ""))
	if text != "":
		show_line("rachid", text)
	if key == "use" and hs.has("on_use"):
		run_actions(hs["on_use"])
	elif key == "look" and hs.has("on_look"):
		run_actions(hs["on_look"])
	elif key == "take" and hs.has("on_take"):
		run_actions(hs["on_take"])


# ------------------------------------------------------------------ actions
func run_actions(actions: Variant) -> void:
	if actions == null:
		return
	for a in (actions as Array):
		await _apply_action(a as Dictionary)


func _apply_action(a: Dictionary) -> void:
	if a.has("flag"):
		GameState.set_flag(str(a["flag"]))
	if a.has("unflag"):
		GameState.flags.erase(str(a["unflag"]))
	if a.has("give"):
		GameState.give(str(a["give"]))
		AudioManager.play("pickup", -6.0)
		hud.toast(GameState.item_name(str(a["give"])), 2.4)
		if str(a["give"]) == "it_babouche_black":
			GameState.set_flag("ch1_ready")
	if a.has("take"):
		GameState.take(str(a["take"]))
	if a.has("sfx"):
		AudioManager.play(str(a["sfx"]), -6.0)
	if a.has("clue"):
		GameState.add_clue(str(a["clue"]))
		hud.toast("دليل جديد: " + str(a["clue"]), 3.4)
		AudioManager.play("page", -12.0)
	if a.has("objective"):
		GameState.set_objective(str(a["objective"]))
	if a.has("say"):
		var who := str(a["say"])
		var text := str(a.get("text", ""))
		await show_line(who, text)
	if a.has("dlg"):
		await _start_dialogue(str(a["dlg"]))
	if a.has("minigame"):
		await _start_minigame(str(a["minigame"]))
	if a.has("goto"):
		_load_room(str(a["goto"]), "left")
	if a.has("ending"):
		var eid := str(a["ending"])
		if eid == "survive" and not GameState.has_item("it_amulet"):
			hud.toast("ما عندكش الحجاب. الحجاب كان عند الحاجة زهرة.", 4.0)
			AudioManager.play("fail", -8.0)
			return
		pending_ending = eid


func show_line(who: String, text: String) -> void:
	if text == "":
		return
	var tree := {"start": "l", "nodes": {"l": [{"who": who, "text": text, "next": "CLOSE"}]}}
	await _start_tree(tree)


func _start_dialogue(id: String) -> void:
	if id == "" or Data.dialogue(id).is_empty():
		return
	state = St.DIALOGUE
	hud.set_inventory_visible(false)
	dialogue.start(id, run_actions)
	await dialogue.closed


func _start_tree(tree: Dictionary) -> void:
	state = St.DIALOGUE
	hud.set_inventory_visible(false)
	dialogue.start_tree(tree, run_actions)
	await dialogue.closed


func _on_dialogue_closed() -> void:
	if state == St.DIALOGUE:
		state = St.PLAY
	hud.set_inventory_visible(true)
	if pending_ending != "":
		var e := pending_ending
		pending_ending = ""
		_show_ending(e)


func _start_minigame(kind: String) -> void:
	state = St.MINI
	hud.set_inventory_visible(false)
	minigames.start(kind)
	await minigames.finished


func _on_minigame_finished(kind: String, success: bool) -> void:
	hud.set_inventory_visible(true)
	state = St.PLAY
	if not success:
		return
	var res: Dictionary = GameState.MINIGAME_RESULTS.get(kind, {})
	for f in res.get("flags", []):
		GameState.set_flag(str(f))
	for it in res.get("items", []):
		GameState.give(str(it))
	if res.has("clue"):
		GameState.add_clue(str(res["clue"]))
	match kind:
		"jars":
			hud.toast(Locale.t("mg_jars_ok"), 3.0)
			GameState.set_objective("هدر مع الحاجة زهرة — خود الحجاب والعشوب")
		"chant":
			hud.toast(Locale.t("mg_chant_perfect"), 3.2)
			GameState.set_objective("هبط للقبو — الدرج فاليمين")
			await show_line("rachid", "خرج على النغم مزيان. والطنجية... سمعت. سمعتني، والله العظيم سمعتني.")
		"lock":
			hud.toast(Locale.t("mg_lock_ok"), 3.0)
			GameState.set_objective("طلع للسطح — هدر مع الأخ المختار")
			await show_line("rachid", "تحل. الريحة اللي خرجت... هادي ماشي ريحة ديال قبو. هادي ريحة ديال طنجية.")


# ------------------------------------------------------------------ endings
func _show_ending(id: String) -> void:
	state = St.ENDING
	hud.set_inventory_visible(false)
	dialogue.visible = false
	ending_screen.show_ending(id)


# ------------------------------------------------------------------ save
func _on_save() -> void:
	if GameState.save_game():
		hud.toast(Locale.t("saved"), 2.4)
	else:
		hud.toast(Locale.t("no_save"), 2.4)


func _on_load() -> void:
	if GameState.load_game():
		hud.close_overlays()
		hud.set_objective(GameState.objective)
		_load_room(GameState.current_room, "right")
		hud.toast(Locale.t("loaded"), 2.4)
	else:
		hud.toast(Locale.t("no_save"), 2.4)


func _set_paused(p: bool) -> void:
	get_tree().paused = p
	if not p:
		hud.close_pause()


func _on_item_selected(_id: String) -> void:
	pass


func _screenshot() -> void:
	# the composited frame, letterbox and all -- what the player is actually looking at
	var img := get_tree().root.get_texture().get_image()
	var path := "user://shot_%d.png" % Time.get_ticks_msec()
	img.save_png(path)
	print("screenshot -> ", ProjectSettings.globalize_path(path))


func _dump_ci(n: Node, depth: int) -> void:
	for k in n.get_children():
		var pad := ""
		for _i in range(depth):
			pad += "  "
		var extra := ""
		if k is Control:
			extra = " pos=(%d,%d) size=(%dx%d) vis=%s" % [int(k.position.x), int(k.position.y), int(k.size.x), int(k.size.y), str(k.visible)]
		elif k is Sprite2D:
			extra = " pos=%s vis=%s" % [str(k.position), str(k.visible)]
		elif k is CanvasItem:
			extra = " vis=%s" % str(k.visible)
		print("      %s%s [%s]%s" % [pad, k.name, k.get_class(), extra])
		if depth < 3:
			_dump_ci(k, depth + 1)


func _dump_frame_state() -> void:
	var vp := get_viewport()
	print("PROBE room=%s vp_size=%s visible=%s" % [str(room.get("id", "?")), str(vp.size), str(vp.get_visible_rect())])
	if bg != null:
		print("PROBE bg tex=%s pos=%s scale=%s centered=%s vis=%s" % [
			(str(bg.texture.get_size()) if bg.texture != null else "null"),
			str(bg.global_position), str(bg.scale), str(bg.centered), str(bg.visible)])
	if bg.texture != null:
		print("PROBE bg path=%s region=%s rect=%s offset=%s" % [
			str(bg.texture.resource_path), str(bg.region_enabled),
			str(bg.region_rect), str(bg.offset)])
	print("PROBE world pos=%s ysort=%s" % [str(world.global_position), str(world.y_sort_enabled)])
	print("PROBE player pos=%s vis=%s" % [str(player.global_position), str(player.visible)])
	if dialogue != null:
		print("PROBE dlg vis=%s active=%s line=%s vc=%s typed=%.1f" % [
			str(dialogue.visible), str(dialogue.is_active()),
			str(dialogue._line_full), str(dialogue._text_label.visible_characters),
			float(dialogue._typed)])
	var cam := vp.get_camera_2d()
	print("PROBE camera=%s" % (str(cam.global_position) if cam != null else "none"))
	for c in get_children():
		if c is CanvasLayer:
			print("PROBE layer %s layer=%d vis=%s kids=%d" % [c.name, c.layer, str(c.visible), c.get_child_count()])
			_dump_ci(c, 1)
	for c in world.get_children():
		if c is CanvasItem:
			print("PROBE world child %s pos=%s vis=%s z=%d" % [c.name, str(c.global_position), str(c.visible), c.z_index])
	for a in ([player] + npc_nodes):
		if a == null:
			continue
		var s = a.get("sprite")
		if s != null and s is Sprite2D:
			print("PROBE actor %s tex=%s hframes=%d scale=%s off=%s filter=%d" % [
				a.name, (str(s.texture.get_size()) if s.texture != null else "null"),
				s.hframes, str(s.scale), str(s.offset), s.texture_filter])


func _set_crt(on: bool) -> void:
	if fx_mat != null:
		fx_mat.set_shader_parameter("enabled", 1.0 if on else 0.0)


func _shell() -> Node:
	return get_tree().root.get_node_or_null("Boot")


func _toggle_fullscreen() -> void:
	var shell := _shell()
	if shell != null and shell.has_method("toggle_fullscreen"):
		shell.toggle_fullscreen()
