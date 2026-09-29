extends Node
## AudioManager — procedural WAV playback: SFX pool, ambience bed, music.
## Everything here was synthesised from scratch by tools/gen_audio.py.

const AUDIO_DIR := "res://audio/"
const SFX_POOL := 8

var _sfx_players: Array[AudioStreamPlayer] = []
var _sfx_idx := 0
var _amb: AudioStreamPlayer
var _music: AudioStreamPlayer
var _cache: Dictionary = {}
var _current_amb := ""
var _current_music := ""


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for i in SFX_POOL:
		var p := AudioStreamPlayer.new()
		p.bus = "Master"
		add_child(p)
		_sfx_players.append(p)
	_amb = AudioStreamPlayer.new()
	_amb.volume_db = -8.0
	add_child(_amb)
	_music = AudioStreamPlayer.new()
	_music.volume_db = -14.0
	add_child(_music)
	_apply_volume()


func _apply_volume() -> void:
	var v: float = float(GameState.settings.get("volume", 0.8))
	AudioServer.set_bus_volume_db(0, linear_to_db(maxf(0.0001, v)))


func set_volume(v: float) -> void:
	GameState.settings["volume"] = clampf(v, 0.0, 1.0)
	_apply_volume()


func _stream(name: String) -> AudioStream:
	if _cache.has(name):
		return _cache[name]
	var path := AUDIO_DIR + name + ".wav"
	if not ResourceLoader.exists(path):
		_cache[name] = null
		return null
	var s: AudioStream = load(path)
	if s is AudioStreamWAV:
		(s as AudioStreamWAV).loop_mode = AudioStreamWAV.LOOP_DISABLED
	_cache[name] = s
	return s


func _loop_stream(name: String) -> AudioStream:
	var s := _stream(name)
	if s is AudioStreamWAV:
		(s as AudioStreamWAV).loop_mode = AudioStreamWAV.LOOP_FORWARD
		(s as AudioStreamWAV).loop_begin = 0
		(s as AudioStreamWAV).loop_end = int((s as AudioStreamWAV).data.size() / 2)
	return s


func play(sfx: String, volume_db: float = 0.0, pitch: float = 1.0) -> void:
	var s := _stream("sfx_" + sfx)
	if s == null:
		return
	var p := _sfx_players[_sfx_idx]
	_sfx_idx = (_sfx_idx + 1) % _sfx_players.size()
	p.stream = s
	p.volume_db = volume_db
	p.pitch_scale = pitch
	p.play()


func ambience(name: String) -> void:
	if name == _current_amb:
		return
	_current_amb = name
	if name == "":
		_amb.stop()
		return
	var s := _loop_stream(name)
	if s == null:
		_amb.stop()
		return
	_amb.stream = s
	_amb.play()


func music(name: String) -> void:
	if name == _current_music:
		return
	_current_music = name
	if name == "":
		_music.stop()
		return
	var s := _loop_stream(name)
	if s == null:
		_music.stop()
		return
	_music.stream = s
	_music.play()


func stop_all() -> void:
	_amb.stop()
	_music.stop()
	_current_amb = ""
	_current_music = ""


func step(surface: String = "stone") -> void:
	play("step_" + surface, -12.0, randf_range(0.92, 1.08))
