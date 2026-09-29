extends Node
## GameState — flags, inventory, clues, objectives, chapters, save/load.
## Every puzzle in the game reads and writes through here.

const SAVE_PATH := "user://babouches_save.json"
const SLOT_COUNT := 3

## Flags the runtime controller sets directly (item acquisition, minigame results,
## chapter transitions) rather than through a data action. The self-test uses this
## list to tell a real dangling flag from an intentional runtime one.
const RUNTIME_FLAGS: Array[String] = [
	"body_done", "hook_taken", "has_black", "ch1_ready", "photo_taken", "window_done",
	"board_done", "ch2_done", "ch3_done", "zahra_paid", "zahra_truth", "harmal_found",
	"herbs_taken", "fqih_taught", "boukhnecha", "boukhnecha_allied", "ledger_taken",
	"sigil_seen", "hidden_door", "book_read", "mix_in", "chant_done", "skulls_done",
	"black_tag_done", "lock_done", "candle_lit",
]

signal inventory_changed
signal flag_changed(flag: String)
signal objective_changed(text: String)
signal clue_added(text: String)

## What winning each puzzle actually grants. The runtime handler in main.gd and the
## progression solver in selftest.gd both read this table, so the two cannot drift.
const MINIGAME_RESULTS: Dictionary = {
	"jars": {"flags": ["harmal_found"], "items": ["it_herbs"],
			 "clue": "الحرمل: الجرة اللي كتلمع هي الصحيحة."},
	"chant": {"flags": ["chant_done"], "items": [],
			  "clue": "التعويذة نجحت. الجن رجع للباب."},
	"lock": {"flags": ["lock_done"], "items": [],
			 "clue": "قفل الإخوان تحل: ١-٧-٤."},
}

var flags: Dictionary = {}
var inventory: Array[String] = []
var clues: Array[String] = []
var objective: String = ""
var current_room: String = "office"
var chapter: int = 1
var max_chapter: int = 1
var visited: Dictionary = {}
var endings_seen: Dictionary = {}
var examine_counts: Dictionary = {}
var idle_time: float = 0.0
var play_seconds: float = 0.0
var settings: Dictionary = {"volume": 0.8, "scanlines": true, "shake": true}

var TOTAL_CLUES := 24       # distinct clues the solver proved reachable
var TOTAL_OBJECTIVES := 15  # distinct objectives set anywhere in the game
var _objectives_done: Array[String] = []


func reset() -> void:
	flags.clear()
	inventory.clear()
	clues.clear()
	_objectives_done.clear()
	visited.clear()
	examine_counts.clear()
	objective = ""
	current_room = "office"
	chapter = 1
	idle_time = 0.0
	play_seconds = 0.0


# ------------------------------------------------------------------ flags
func set_flag(f: String) -> void:
	if f == "" or flags.has(f):
		return
	flags[f] = true
	flag_changed.emit(f)

func has(f: String) -> bool:
	return flags.has(f)

func cond_ok(cond: Variant) -> bool:
	if cond == null:
		return true
	var d: Dictionary = cond
	if d.has("flag") and not has(str(d["flag"])):
		return false
	if d.has("flag2") and not has(str(d["flag2"])):
		return false
	if d.has("not_flag") and has(str(d["not_flag"])):
		return false
	if d.has("item") and not has_item(str(d["item"])):
		return false
	if d.has("not_item") and has_item(str(d["not_item"])):
		return false
	if d.has("chapter") and chapter < int(d["chapter"]):
		return false
	return true


# ------------------------------------------------------------------ items
func give(item: String) -> void:
	if item == "" or inventory.has(item):
		return
	inventory.append(item)
	inventory_changed.emit()

func take(item: String) -> void:
	if inventory.has(item):
		inventory.erase(item)
		inventory_changed.emit()

func has_item(item: String) -> bool:
	return inventory.has(item)

func item_name(id: String) -> String:
	return Locale.t("it_" + id)

func item_desc(id: String) -> String:
	return Locale.t("it_" + id + "_d")


# ------------------------------------------------------------------ clues / objectives
func add_clue(text: String) -> void:
	if text == "" or clues.has(text):
		return
	clues.append(text)
	clue_added.emit(text)

func set_objective(text: String) -> void:
	if text == objective:
		return
	if objective != "" and not _objectives_done.has(objective):
		_objectives_done.append(objective)
	objective = text
	objective_changed.emit(text)

func objectives_done() -> int:
	return _objectives_done.size()


# ------------------------------------------------------------------ examine spam
func bump_examine(id: String) -> int:
	var n: int = int(examine_counts.get(id, 0)) + 1
	examine_counts[id] = n
	return n


# ------------------------------------------------------------------ save / load
func save_game(slot: int = 0) -> bool:
	var d := {
		"flags": flags,
		"inventory": inventory,
		"clues": clues,
		"objective": objective,
		"current_room": current_room,
		"chapter": chapter,
		"max_chapter": max_chapter,
		"visited": visited,
		"endings_seen": endings_seen,
		"play_seconds": play_seconds,
		"settings": settings,
		"_objectives_done": _objectives_done,
		"version": 1,
	}
	var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(JSON.stringify(d, "\t"))
	f.close()
	return true

func has_save() -> bool:
	return FileAccess.file_exists(SAVE_PATH)

func load_game() -> bool:
	if not has_save():
		return false
	var f := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if f == null:
		return false
	var raw := f.get_as_text()
	f.close()
	var parsed: Variant = JSON.parse_string(raw)
	if typeof(parsed) != TYPE_DICTIONARY:
		return false
	var d: Dictionary = parsed
	flags = d.get("flags", {})
	clues.assign(d.get("clues", []))
	objective = str(d.get("objective", ""))
	current_room = str(d.get("current_room", "office"))
	chapter = int(d.get("chapter", 1))
	max_chapter = int(d.get("max_chapter", 1))
	visited = d.get("visited", {})
	endings_seen = d.get("endings_seen", {})
	play_seconds = float(d.get("play_seconds", 0.0))
	settings = d.get("settings", settings)
	_objectives_done.assign(d.get("_objectives_done", []))
	inventory.clear()
	for it in d.get("inventory", []):
		inventory.append(str(it))
	inventory_changed.emit()
	return true

func note_ending(id: String) -> void:
	endings_seen[id] = true
	save_game()

func _process(delta: float) -> void:
	play_seconds += delta
