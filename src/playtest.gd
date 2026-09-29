extends RefCounted
class_name PlayTest
## PlayTest — drives the real game, not the data. Loads every room, fires every
## hotspot with every verb, runs every dialogue tree to completion, wins every
## minigame, shows every ending, round-trips the save. Run with --playtest.

static var notes: Array[String] = []
static var fails: Array[String] = []
static var counts: Dictionary = {}


static func _note(s: String) -> void:
	notes.append(s)


static func _fail(s: String) -> void:
	fails.append(s)


static func _bump(k: String, n: int = 1) -> void:
	counts[k] = int(counts.get(k, 0)) + n


## Wait until the game is back in PLAY and stable, dismissing anything modal.
static func _settle(main: Node, cap: int = 900) -> void:
	var tree := main.get_tree()
	var stable := 0
	var i := 0
	while i < cap:
		await tree.process_frame
		i += 1
		var st: int = main.state
		if st == main.St.CARD:
			main._dismiss_card()
			stable = 0
			continue
		if st == main.St.MINI:
			main.minigames.auto_win()
			stable = 0
			continue
		if st == main.St.ENDING:
			# a hotspot reached an ending — that is a pass, not a deadlock
			_bump("endings_reached_in_play")
			main.ending_screen.hide()
			main.state = main.St.PLAY
			stable = 0
			continue
		if st == main.St.PLAY:
			stable += 1
			if stable >= 3:
				return
		else:
			stable = 0
	if i >= cap:
		_fail("settle timeout — state stuck at %d" % main.state)


static func run(main: Node) -> void:
	notes.clear()
	fails.clear()
	counts.clear()
	var tree := main.get_tree()

	# the harness drives dialogue itself; a human never has to click
	main.dialogue.auto = true

	print("=== «البلغة والجن» playtest ===")

	# ---------------------------------------------------------------- new game
	main._new_game()
	await tree.process_frame
	main._dismiss_card()
	await _settle(main)
	_note("new game → room=%s chapter=%d" % [GameState.current_room, GameState.chapter])

	# ---------------------------------------------------------------- rooms + hotspots
	for rid in Data.room_ids():
		var id := str(rid)
		var room: Dictionary = Data.room(id)
		main._load_room(id, "left")
		await tree.process_frame
		await _settle(main)
		var hs_count: int = main.hotspots.size()
		if hs_count == 0:
			_fail("%s: no hotspots built" % id)
		var npc_count: int = main.npc_nodes.size()
		_note("%-9s hotspots=%-2d npcs=%d" % [id, hs_count, npc_count])
		_bump("rooms")
		_bump("hotspots", hs_count)

		for hs in main.hotspots:
			var d: Dictionary = hs
			var hid := str(d.get("id", "?"))
			var before_flags: int = GameState.flags.size()
			var before_items: int = GameState.inventory.size()
			for mode in ["look", "use"]:
				main._do_hotspot(d, mode)
				await _settle(main)
				_bump("verbs")
			if d.has("talk"):
				main._do_hotspot(d, "talk")
				await _settle(main)
				_bump("verbs")
			# a hotspot that is legal and reacts to nothing is worth knowing about
			var reacted: bool = (GameState.flags.size() != before_flags) \
				or (GameState.inventory.size() != before_items) \
				or GameState.current_room != id \
				or d.has("look") or d.has("use") or d.has("talk")
			if not reacted:
				_note("  (no reaction) %s.%s" % [id, hid])
			if GameState.current_room != id:
				main._load_room(id, "left")
				await tree.process_frame
				await _settle(main)

	# ---------------------------------------------------------------- every dialogue tree
	for tid in Data.all_dialogue().keys():
		var t := str(tid)
		GameState.set_flag("__probe_%s" % t)
		main._start_dialogue(t)
		await _settle(main)
		if main.dialogue.is_active():
			_fail("dialogue %s did not close" % t)
		_bump("dialogues")
		_note("dialogue ok: %s" % t)

	# ---------------------------------------------------------------- every minigame
	for kind in ["jars", "chant", "lock"]:
		var before: int = GameState.flags.size()
		main._start_minigame(str(kind))
		await _settle(main)
		if main.minigames.is_active():
			_fail("minigame %s did not close" % kind)
		_bump("minigames")
		_note("minigame ok: %-6s flags %d → %d" % [kind, before, GameState.flags.size()])

	# ---------------------------------------------------------------- endings
	for e in ["survive", "price", "new"]:
		main._show_ending(str(e))
		await tree.process_frame
		await tree.process_frame
		if not main.ending_screen.visible:
			_fail("ending screen did not show for %s" % e)
		_bump("endings")
		main.ending_screen.hide()
		main.state = main.St.PLAY

	# ---------------------------------------------------------------- save round trip
	GameState.set_flag("__save_probe")
	GameState.give("it_key")
	var saved_room := GameState.current_room
	var ok := GameState.save_game()
	if not ok:
		_fail("save_game returned false")
	else:
		GameState.reset()
		if not GameState.load_game():
			_fail("load_game returned false")
		else:
			if not GameState.has("__save_probe"):
				_fail("save round trip lost a flag")
			if not GameState.has_item("it_key"):
				_fail("save round trip lost an item")
			if GameState.current_room != saved_room:
				_fail("save round trip lost the room")
			_note("save round trip ok (room=%s)" % GameState.current_room)
			_bump("save")

	# ---------------------------------------------------------------- report
	print("")
	for n in notes:
		print("  " + n)
	print("")
	print("counts: %s" % str(counts))
	print("failures: %d" % fails.size())
	for f in fails:
		print("  FAIL  " + f)
	print("")
	print("PLAYTEST %s" % ("PASS" if fails.is_empty() else "FAIL"))
	tree.quit(0 if fails.is_empty() else 1)
