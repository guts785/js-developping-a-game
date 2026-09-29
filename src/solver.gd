extends RefCounted
class_name Solver
## Solver — proves the case is finishable. Starts from a clean save, applies every
## hotspot whose condition the player could satisfy, follows goto / minigame /
## dialogue results, and repeats to a fixed point. It over-approximates (it takes
## every dialogue branch), so "reachable" here means "there exists a way" — which is
## exactly the claim that matters: no dead end, every ending still on the table.
## Run with --solve.

static var _goto := ""
static var flags: Dictionary = {}
static var items: Dictionary = {}
static var clues: Dictionary = {}
static var endings: Dictionary = {}
static var visited: Dictionary = {}
static var unreachable: Array[String] = []


static func _cond(cond: Variant) -> bool:
	if cond == null:
		return true
	var d: Dictionary = cond
	if d.has("flag") and not flags.has(str(d["flag"])):
		return false
	if d.has("flag2") and not flags.has(str(d["flag2"])):
		return false
	if d.has("not_flag") and flags.has(str(d["not_flag"])):
		return false
	if d.has("item") and not items.has(str(d["item"])):
		return false
	if d.has("not_item") and items.has(str(d["not_item"])):
		return false
	# chapter gates are satisfied in the over-approximation
	return true


static func _acts(actions: Variant) -> void:
	if actions == null:
		return
	for a in (actions as Array):
		var d: Dictionary = a
		if d.has("flag"):
			flags[str(d["flag"])] = true
		if d.has("unflag"):
			flags.erase(str(d["unflag"]))
		if d.has("give"):
			items[str(d["give"])] = true
			# the runtime grants chapter 1's exit when the black babouche is picked up
			if str(d["give"]) == "it_babouche_black":
				flags["ch1_ready"] = true
		if d.has("take"):
			items.erase(str(d["take"]))
		if d.has("clue"):
			clues[str(d["clue"])] = true
		if d.has("goto"):
			_goto = str(d["goto"])
		if d.has("dlg"):
			_walk(str(d["dlg"]))
		if d.has("minigame"):
			# winning is the intended path; apply the shared result table
			var res: Dictionary = GameState.MINIGAME_RESULTS.get(str(d["minigame"]), {})
			for f in res.get("flags", []):
				flags[str(f)] = true
			for it in res.get("items", []):
				items[str(it)] = true
			if res.has("clue"):
				clues[str(res["clue"])] = true
		if d.has("ending"):
			endings[str(d["ending"])] = true


static func _walk(tree_id: String, depth: int = 0) -> void:
	if depth > 6:
		return
	var t: Dictionary = Data.dialogue(tree_id)
	if t.is_empty():
		return
	var nodes: Dictionary = t.get("nodes", {})
	var seen: Dictionary = {}
	var stack: Array[String] = [str(t.get("start", "hi"))]
	while not stack.is_empty():
		var nid: String = stack.pop_back()
		if seen.has(nid) or not nodes.has(nid):
			continue
		seen[nid] = true
		for line in (nodes[nid] as Array):
			var l: Dictionary = line
			if l.has("actions"):
				_acts(l["actions"])
			if l.has("choices"):
				for c in (l["choices"] as Array):
					var cd: Dictionary = c
					if cd.has("actions"):
						_acts(cd["actions"])
					var nxt := str(cd.get("next", "CLOSE"))
					if nxt != "CLOSE" and not seen.has(nxt):
						stack.append(nxt)
		var last: Dictionary = (nodes[nid] as Array)[(nodes[nid] as Array).size() - 1]
		var ln := str(last.get("next", ""))
		if ln != "" and ln != "CLOSE" and not seen.has(ln):
			stack.append(ln)


static func run(tree: SceneTree) -> void:
	_goto = ""
	flags = {}
	items = {}
	clues = {}
	endings = {}
	visited = {"office": true}
	unreachable.clear()

	print("=== «البلغة والجن» progression solver ===")
	print("(over-approximating: every dialogue branch taken, every puzzle won)")

	var passes := 0
	var moved := true
	while moved and passes < 300:
		passes += 1
		moved = false
		for rid in Data.room_ids():
			var room := str(rid)
			if not visited.has(room):
				continue
			var r: Dictionary = Data.rooms()[room]
			var f0: int = flags.size()
			var i0: int = items.size()
			var c0: int = clues.size()

			if r.has("on_enter"):
				_acts(r["on_enter"])
				_goto = ""

			for h in (r.get("hotspots", []) as Array):
				var hs: Dictionary = h
				if not _cond(hs.get("cond")):
					continue
				for key in ["on_use", "on_look", "on_take"]:
					if hs.has(key):
						_acts(hs[key])
						if _goto != "":
							visited[_goto] = true
							_goto = ""
				if hs.has("talk"):
					_walk(str(hs["talk"]))

			for spec in (r.get("npcs", []) as Array):
				var d: Dictionary = spec
				if d.has("dlg"):
					_walk(str(d["dlg"]))

			for side in (r.get("exits", {}) as Dictionary).keys():
				var ex: Dictionary = r["exits"][side]
				if _cond(ex.get("cond")):
					var to := str(ex.get("to", ""))
					if to != "" and not visited.has(to):
						visited[to] = true

			if flags.size() != f0 or items.size() != i0 or clues.size() != c0:
				moved = true

	# ------------------------------------------------------------------ report
	var all_rooms: Array = Data.room_ids()
	for rid in all_rooms:
		if not visited.has(str(rid)):
			unreachable.append(str(rid))

	var want_endings := ["survive", "price", "new"]
	var missing_endings: Array[String] = []
	for e in want_endings:
		if not endings.has(e):
			missing_endings.append(e)

	print("")
	print("passes:            %d" % passes)
	print("rooms reachable:   %d / %d" % [visited.size(), all_rooms.size()])
	print("  visited:         %s" % str(visited.keys()))
	if not unreachable.is_empty():
		print("  UNREACHABLE:     %s" % str(unreachable))
	print("endings reachable: %d / 3   %s" % [endings.size(), str(endings.keys())])
	print("flags reachable:   %d" % flags.size())
	print("items reachable:   %d   %s" % [items.size(), str(items.keys())])
	print("clues reachable:   %d / %d" % [clues.size(), GameState.TOTAL_CLUES])
	print("")

	var ok := unreachable.is_empty() and missing_endings.is_empty()
	if not missing_endings.is_empty():
		print("MISSING ENDINGS: %s" % str(missing_endings))
	print("SOLVE %s" % ("PASS" if ok else "FAIL"))
	tree.quit(0 if ok else 1)
