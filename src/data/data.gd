extends RefCounted
class_name Data
## Data — the one place rooms and dialogue trees are assembled.

static var _rooms: Dictionary = {}
static var _dlg: Dictionary = {}
static var _loaded := false


static func _ensure() -> void:
	if _loaded:
		return
	_rooms = {}
	_rooms.merge(RoomsA.rooms())
	_rooms.merge(RoomsB.rooms())
	_dlg = {}
	_dlg.merge(RoomsA.dialogue())
	_dlg.merge(RoomsB.dialogue())
	_loaded = true


static func rooms() -> Dictionary:
	_ensure()
	return _rooms


static func room(id: String) -> Dictionary:
	_ensure()
	return _rooms.get(id, {})


static func dialogue(id: String) -> Dictionary:
	_ensure()
	return _dlg.get(id, {})


static func all_dialogue() -> Dictionary:
	_ensure()
	return _dlg


## Speakers appear in the room data either as character ids (rachid, jinn) or as the
## literal Arabic name the writer typed (المفتش رشيد). Both must resolve to the same
## character so the portrait lookup and the barks work. Single source of truth here.
static var SPEAKERS: Dictionary = {
	"المفتش رشيد": "rachid",
	"الراوي": "narrator",
	"الحاجة زهرة": "zahra",
	"كمال": "kamel",
	"الفقيه بوبكر": "fqih",
	"حميدو": "hmidou",
	"سليمان": "sliman",
	"بوخنشة": "jinn",
	"الأخ المختار": "mokhtar",
}


static func speaker_id(who: String) -> String:
	if SPEAKERS.has(who):
		return str(SPEAKERS[who])
	return who


static func room_ids() -> Array:
	_ensure()
	return _rooms.keys()


static func hotspot(room_id: String, hs_id: String) -> Dictionary:
	var r := room(room_id)
	for h in r.get("hotspots", []):
		if str(h.get("id", "")) == hs_id:
			return h
	return {}


static func first_room_of_chapter(ch: int) -> String:
	for id in rooms().keys():
		var r: Dictionary = rooms()[id]
		if int(r.get("chapter", 0)) == ch and id != "rooftop":
			return str(id)
	return "office"


static func chapter_rooms(ch: int) -> Array:
	var out: Array = []
	for id in rooms().keys():
		var r: Dictionary = rooms()[id]
		if int(r.get("chapter", 0)) == ch:
			out.append(id)
	return out
