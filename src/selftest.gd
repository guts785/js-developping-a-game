extends RefCounted
class_name SelfTest
## SelfTest — walks every room, hotspot, dialogue branch, item, flag, sprite and
## sound the game references, and reports what is broken. Run with --selftest.

static var errors: Array[String] = []
static var warnings: Array[String] = []
static var checks := 0


static func _err(msg: String) -> void:
	errors.append(msg)


static func _warn(msg: String) -> void:
	warnings.append(msg)


static func _check(cond: bool, msg: String) -> void:
	checks += 1
	if not cond:
		_err(msg)


static func _res_exists(path: String) -> bool:
	return ResourceLoader.exists(path)


static func _is_ascii(s: String) -> bool:
	for i in s.length():
		if s.unicode_at(i) > 127:
			return false
	return true


static func _audio_names() -> Dictionary:
	var out: Dictionary = {}
	var d := DirAccess.open("res://audio")
	if d == null:
		return out
	for f in d.get_files():
		var n := str(f)
		if n.ends_with(".import"):
			n = n.substr(0, n.length() - 7)
		if n.ends_with(".wav"):
			out[n.substr(0, n.length() - 4)] = true
	return out


static func run(tree: SceneTree) -> void:
	errors.clear()
	warnings.clear()
	checks = 0
	var rooms := Data.rooms()
	var dlg := Data.all_dialogue()
	var audio := _audio_names()

	print("=== «البلغة والجن» self-test ===")
	print("rooms: %d   dialogue trees: %d   audio files: %d   locale keys: %d"
		% [rooms.size(), dlg.size(), audio.size(), Locale.S.size()])

	var all_items: Dictionary = {}
	var flags_set: Dictionary = {}
	var flags_tested: Dictionary = {}
	var chars_used: Dictionary = {}
	var loc_keys_used: Dictionary = {}

	# ------------------------------------------------------------ rooms
	for rid in rooms.keys():
		var id := str(rid)
		var r: Dictionary = rooms[rid]
		_check(r.has("name"), "%s: missing name" % id)
		_check(r.has("bg") and _res_exists(str(r["bg"])), "%s: bg missing %s" % [id, r.get("bg", "?")])
		_check(r.has("base_y") and float(r["base_y"]) > 0.0 and float(r["base_y"]) < 180.0,
			"%s: base_y out of range" % id)
		_check(r.has("walk") and (r["walk"] as Array).size() == 2, "%s: walk range malformed" % id)
		_check(int(r.get("chapter", 0)) >= 1 and int(r.get("chapter", 0)) <= 6,
			"%s: chapter must be 1..6" % id)
		var amb := str(r.get("ambience", ""))
		if amb != "":
			_check(audio.has(amb), "%s: ambience %s not found in audio/" % [id, amb])
		var mus := str(r.get("music", ""))
		if mus != "":
			_check(audio.has(mus), "%s: music %s not found in audio/" % [id, mus])

		for side in (r.get("exits", {}) as Dictionary).keys():
			var ex: Dictionary = r["exits"][side]
			var to := str(ex.get("to", ""))
			_check(rooms.has(to), "%s: exit %s -> unknown room %s" % [id, side, to])
			if ex.has("cond"):
				_collect_cond_flags(ex["cond"], flags_tested, id + ".exit." + str(side))

		var seen_ids: Dictionary = {}
		for h in (r.get("hotspots", []) as Array):
			var hs: Dictionary = h
			var hid := str(hs.get("id", ""))
			_check(hid != "", "%s: hotspot without id" % id)
			if seen_ids.has(hid):
				_warn("%s: duplicate hotspot id %s" % [id, hid])
			seen_ids[hid] = true
			_check(hs.has("label") and str(hs["label"]) != "", "%s/%s: missing label" % [id, hid])
			var rect: Array = hs.get("rect", [])
			_check(rect.size() == 4, "%s/%s: rect must be 4 numbers" % [id, hid])
			if rect.size() == 4:
				_check(float(rect[0]) >= 0.0 and float(rect[2]) <= 320.0 and
					   float(rect[1]) >= 0.0 and float(rect[3]) <= 180.0,
					"%s/%s: rect outside the 320x180 frame: %s" % [id, hid, str(rect)])
				_check(float(rect[2]) > float(rect[0]) and float(rect[3]) > float(rect[1]),
					"%s/%s: rect has no area" % [id, hid])
			var has_verb := hs.has("look") or hs.has("use") or hs.has("take") or hs.has("talk")
			_check(has_verb, "%s/%s: no verbs at all" % [id, hid])
			if hs.has("cond"):
				_collect_cond_flags(hs["cond"], flags_tested, id + "." + hid)
			for key in ["on_use", "on_look", "on_take"]:
				if hs.has(key):
					_collect_actions(hs[key], id + "." + hid, all_items, flags_set, chars_used, loc_keys_used, audio)
			if hs.has("item_use"):
				for it in (hs["item_use"] as Dictionary).keys():
					all_items[str(it)] = true

		for spec in (r.get("npcs", []) as Array):
			var d: Dictionary = spec
			var cid := str(d.get("char", ""))
			chars_used[cid] = true
			_check(_res_exists("res://art/chars/%s_walk.png" % cid), "%s: npc sprite missing for %s" % [id, cid])
			_check(_res_exists("res://art/chars/%s_portrait_neutral.png" % cid),
				"%s: npc portrait missing for %s" % [id, cid])
			var dn := str(d.get("dlg", ""))
			_check(dlg.has(dn), "%s: npc dialogue %s does not exist" % [id, dn])
			loc_keys_used[str(d.get("name", ""))] = true

		if r.has("on_enter"):
			_collect_actions(r["on_enter"], id + ".on_enter", all_items, flags_set, chars_used, loc_keys_used, audio)

	# ------------------------------------------------------------ dialogue
	for tid in dlg.keys():
		var t: Dictionary = dlg[tid]
		var nodes: Dictionary = t.get("nodes", {})
		_check(nodes.has(str(t.get("start", "hi"))), "%s: start node missing" % tid)
		for nid in nodes.keys():
			var arr: Array = nodes[nid]
			_check(arr.size() > 0, "%s/%s: empty node" % [tid, nid])
			for i in arr.size():
				var line: Dictionary = arr[i]
				if line.has("who"):
					var who := str(line["who"])
					chars_used[who] = true
					loc_keys_used[who] = true
					if who != "narrator":
						_check(_res_exists("res://art/chars/%s_portrait_neutral.png" % who),
							"%s/%s[%d]: no portrait for speaker %s" % [tid, nid, i, who])
				if line.has("choices"):
					for c in (line["choices"] as Array):
						var cd: Dictionary = c
						var nxt := str(cd.get("next", "CLOSE"))
						_check(nxt == "CLOSE" or nodes.has(nxt),
							"%s/%s: choice -> unknown node %s" % [tid, nid, nxt])
						_check(str(cd.get("text", "")) != "", "%s/%s: choice with no text" % [tid, nid])
						if cd.has("actions"):
							_collect_actions(cd["actions"], "%s/%s.choice" % [tid, nid],
								all_items, flags_set, chars_used, loc_keys_used, audio)
				if line.has("actions"):
					_collect_actions(line["actions"], "%s/%s" % [tid, nid],
						all_items, flags_set, chars_used, loc_keys_used, audio)
			# trailing next must resolve
			var last: Dictionary = arr[arr.size() - 1]
			var nx := str(last.get("next", ""))
			_check(nx == "" or nx == "CLOSE" or nodes.has(nx),
				"%s/%s: next -> unknown node %s" % [tid, nid, nx])

	# ------------------------------------------------------------ items
	for it in all_items.keys():
		var iid := str(it)
		var base := iid.substr(3) if iid.begins_with("it_") else iid
		_check(_res_exists("res://art/items/%s.png" % base), "item icon missing: %s.png" % base)
		_check(Locale.S.has("it_" + base), "locale key missing: it_%s" % base)
		_check(Locale.S.has("it_" + base + "_d"), "locale key missing: it_%s_d" % base)

	# ------------------------------------------------------------ chars
	for c in chars_used.keys():
		var cid := str(c)
		if cid == "narrator":
			continue
		_check(Locale.S.has(cid), "locale speaker name missing: %s" % cid)
		_check(_res_exists("res://art/chars/%s_walk.png" % cid), "character sheet missing: %s" % cid)

	# ------------------------------------------------------------ flags
	for f in flags_tested.keys():
		if not flags_set.has(f) and not GameState.RUNTIME_FLAGS.has(str(f)):
			_warn("flag tested but never set anywhere: %s (used by %s)" % [f, flags_tested[f]])

	# ------------------------------------------------------------ locale keys
	for k in loc_keys_used.keys():
		var key := str(k)
		# literal Arabic speaker names render as-is through Locale.t's key fallback
		if key.is_empty() or not _is_ascii(key):
			continue
		if not Locale.S.has(key):
			_warn("locale key used in data but not defined: %s" % key)
	for ch in range(1, 7):
		_check(Locale.S.has("ch%d" % ch), "missing chapter title ch%d" % ch)
		_check(Locale.S.has("ch%d_sub" % ch), "missing chapter subtitle ch%d_sub" % ch)
		_check(Locale.S.has("hint_ch%d" % ch), "missing hint hinst_ch%d" % ch)

	# ------------------------------------------------------------ ui assets
	for p in ["res://art/ui/cursor.png", "res://art/ui/dlg_box.png", "res://art/ui/chapter_card.png",
			  "res://art/ui/ending_card.png", "res://art/ui/vignette.png", "res://art/rooms/title.png",
			  "res://fonts/Cairo-Regular.ttf", "res://src/core/retro.gdshader"]:
		_check(_res_exists(p), "core asset missing: %s" % p)

	# ------------------------------------------------------------ sprite sheets
	# An opaque sheet renders as a solid near-black rectangle the size of the actor,
	# which reads as a missing texture. tools/gen_sprites*.py must pass bg=None to Cv
	# when authoring -- the canvas default fills opaque. Check the CORNER of frame 0:
	# a centre pixel is inside the figure and reads opaque either way.
	for cid in ["rachid", "hmidou", "sliman", "zahra", "fqih", "mokhtar", "kamel", "jinn"]:
		var sp := "res://art/chars/%s_walk.png" % cid
		if not _res_exists(sp):
			_check(false, "sprite sheet missing: %s" % sp)
			continue
		var tex := load(sp) as Texture2D
		var img: Image = tex.get_image() if tex != null else null
		if img == null or img.is_empty():
			_warn("could not read pixels of %s" % sp)
			continue
		_check(img.get_width() == 432 and img.get_height() == 108,
			"sprite sheet %s is %dx%d, expected 432x108" % [cid, img.get_width(), img.get_height()])
		var a := img.get_pixel(0, 0).a
		_check(a < 0.05,
			"sprite sheet %s has an opaque corner (a=%.2f) -- pass bg=None to Cv" % [cid, a])

	# ------------------------------------------------------------ endings
	for e in ["survive", "price", "new"]:
		_check(Locale.S.has("end_%s" % e), "ending text missing: end_%s" % e)
		_check(Locale.S.has("end_%s_title" % e), "ending title missing: end_%s_title" % e)

	# ------------------------------------------------------------ report
	print("")
	print("checks run: %d" % checks)
	print("errors:     %d" % errors.size())
	for e in errors:
		print("  ERROR  " + e)
	print("warnings:   %d" % warnings.size())
	for w in warnings:
		print("  warn   " + w)
	print("")
	if errors.is_empty():
		print("SELFTEST PASS")
	else:
		print("SELFTEST FAIL")
	tree.quit(0 if errors.is_empty() else 1)


static func _collect_cond_flags(cond: Variant, out: Dictionary, where: String) -> void:
	if cond == null:
		return
	var d: Dictionary = cond
	for key in ["flag", "flag2", "not_flag"]:
		if d.has(key):
			var f := str(d[key])
			if not out.has(f):
				out[f] = where
	if d.has("item"):
		pass


static func _collect_actions(actions: Variant, where: String, items: Dictionary, flags: Dictionary,
							 chars: Dictionary, loc: Dictionary, audio: Dictionary) -> void:
	if actions == null:
		return
	for a in (actions as Array):
		var d: Dictionary = a
		if d.has("give"):
			items[str(d["give"])] = true
		if d.has("take"):
			items[str(d["take"])] = true
		if d.has("flag"):
			flags[str(d["flag"])] = true
		if d.has("sfx"):
			var s := "sfx_" + str(d["sfx"])
			if not audio.has(s):
				_err("sfx missing in audio/: %s (from %s)" % [s, where])
		if d.has("goto"):
			var to := str(d["goto"])
			if not Data.rooms().has(to):
				_err("%s: goto unknown room %s" % [where, to])
		if d.has("dlg"):
			var dn := str(d["dlg"])
			if not Data.all_dialogue().has(dn):
				_err("%s: dlg unknown tree %s" % [where, dn])
		if d.has("minigame"):
			var mg := str(d["minigame"])
			if not ["jars", "chant", "lock"].has(mg):
				_err("%s: unknown minigame %s" % [where, mg])
		if d.has("ending"):
			var e := str(d["ending"])
			if not ["survive", "price", "new"].has(e):
				_err("%s: unknown ending %s" % [where, e])
		if d.has("say"):
			loc[str(d["say"])] = true
