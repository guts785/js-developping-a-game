extends Node2D
## Player / NPC actor.
##
## The inspector walks with WASD (free 2D movement inside the room's floor band) —
## clicking a hotspot still auto-walks him there. Depth comes from Y-sorting on the
## world node, so the node origin IS the ground contact point.
##
## Sheet: 8 frames of 36x68 — 0..5 walk cycle, 6..7 idle breathing.

signal arrived

const SHEET_FRAMES := 8
const WALK_FRAMES := 6
const FRAME_W := 54
const FRAME_H := 108
# Authored at native size by tools/gen_sprites3.py -- do not scale this. The sheet
# used to be 36x68 drawn at 1.5x, and nearest-neighbour at 1.5x puts alternating
# 1px/2px pixels on screen: the figure shimmers as it walks and never lines up with
# the room's grid. 102px is 28% of the 360px screen, the adventure-game sweet spot,
# and the frame bottom still sits exactly on the node origin.
const ART_SCALE := 1.0

var sprite: Sprite2D
var halo: Sprite2D
var speed := 96.0
var facing := 1
var base_y := 304.0
var is_player := false
var input_enabled := true
var auto_walking := false
var moving := false

var _anim := 0.0
var _idle_anim := 0.0
var _step_timer := 0.0
var _footstep := "stone"
var _target := Vector2.ZERO

# walkable band, world pixels
var band_min_x := 24.0
var band_max_x := 616.0
var band_min_y := 276.0
var band_max_y := 336.0


func _ready() -> void:
	sprite = Sprite2D.new()
	sprite.hframes = SHEET_FRAMES
	sprite.vframes = 1
	sprite.centered = true
	# frame bottom sits on the node origin → node.y is the feet
	sprite.offset = Vector2(0, -FRAME_H * 0.5)
	sprite.scale = Vector2(ART_SCALE, ART_SCALE)   # offset scales with it, feet stay put
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	# Seat the cast in the room's key.
	#
	# The rooms are darkened to ambient 0.42-0.66 and then relit from their own
	# sources, but these sprite sheets are baked at full brightness and drawn with
	# no modulate at all -- so the cast rendered brighter and more saturated than
	# the light falling on the floor directly beneath it, which is what made them
	# read as stickers laid over the room. Vision put it plainly: the background
	# was the more finished layer and the characters were the weak link.
	#
	# Warm bias, not a neutral darkening: every room's key is a lamp, a window or
	# an ember, so the light the cast should be catching is never white. Kept
	# mild -- the ambient floor is deliberately high for exactly this reason, and
	# pushing the cast much below this turns them muddy instead of seated.
	sprite.modulate = Color(0.94, 0.90, 0.85, 1.0)
	add_child(sprite)
	# Contact shadow at the feet. This is what stops the cast reading as stickers
	# on the backdrop -- the room art grounds its furniture the same way.
	# It replaces art/ui/actor_halo.png, which was meant to do this and never did:
	# that file is 72x32 with a peak alpha of 35 and not one opaque pixel, so it
	# drew nothing on any frame (mean alpha 3.7, against this shadow's 30).
	var sh_tex := Ui.tex("res://art/fx/shadow.png")
	if sh_tex != null:
		halo = Sprite2D.new()
		halo.texture = sh_tex
		halo.centered = true
		# Positioned at +1, not -4. The sprite's legs cover y-30..0, so a shadow centred
		# above the feet has its dark core hidden behind them and only the faint wings
		# show -- measured at 10% darkening, which is under the floor's own texture
		# variation and therefore invisible. Centred just below the feet, the core
		# lands on open floor in front of the figure where it can actually read.
		halo.position = Vector2(0, 1)
		halo.z_index = -1                       # behind the actor, on the floor
		halo.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		add_child(halo)
	z_index = 0          # ordering comes from Y-sort on the parent


func setup(char_id: String, footstep: String = "stone", as_player: bool = false) -> void:
	var t := Ui.tex("res://art/chars/%s_walk.png" % char_id)
	if t != null:
		sprite.texture = t
	_footstep = footstep
	is_player = as_player
	to_idle()


func set_band(min_x: float, max_x: float, base: float, up: float = 30.0, down: float = 30.0) -> void:
	"""Walkable floor band. `up`/`down` are asymmetric on purpose: the inventory
	strip owns the bottom 46px of the screen, so the actor must not walk down into
	it or his feet vanish behind the bar."""
	band_min_x = min_x
	band_max_x = max_x
	base_y = base
	band_min_y = base - up
	band_max_y = base + down
	position.y = clampf(position.y, band_min_y, band_max_y)


func place(x: float, y: float) -> void:
	position = Vector2(x, y)
	_target = position
	auto_walking = false
	moving = false
	to_idle()


func walk_to(x: float) -> void:
	_target = Vector2(clampf(x, band_min_x, band_max_x), position.y)
	auto_walking = true


func stop() -> void:
	auto_walking = false


func to_idle() -> void:
	_anim = 0.0
	if sprite != null and sprite.texture != null:
		sprite.frame = WALK_FRAMES
		sprite.flip_h = facing < 0


func foot_x() -> float:
	return position.x


func _process(delta: float) -> void:
	var dir := Vector2.ZERO
	if is_player and input_enabled:
		dir.x = Input.get_axis("walk_left", "walk_right")
		dir.y = Input.get_axis("walk_up", "walk_down")

	if dir.length() > 0.01:
		auto_walking = false            # the keyboard always wins over auto-walk
		moving = true
		var step := dir.normalized() * speed * delta
		position.x = clampf(position.x + step.x, band_min_x, band_max_x)
		position.y = clampf(position.y + step.y, band_min_y, band_max_y)
		if absf(dir.x) > 0.01:
			facing = 1 if dir.x > 0.0 else -1
	elif auto_walking:
		var dx := _target.x - position.x
		if absf(dx) <= 2.0:
			position.x = _target.x
			auto_walking = false
			moving = false
			to_idle()
			arrived.emit()
			return
		moving = true
		facing = 1 if dx > 0.0 else -1
		position.x += signf(dx) * speed * delta
	else:
		moving = false

	if sprite == null or sprite.texture == null:
		return
	sprite.flip_h = facing < 0
	if moving:
		_anim += delta * 9.0
		sprite.frame = int(_anim) % WALK_FRAMES
		_step_timer += delta
		if _step_timer >= 0.26:
			_step_timer = 0.0
			AudioManager.step(_footstep)
	else:
		_idle_anim += delta * 2.0
		sprite.frame = WALK_FRAMES + (int(_idle_anim) % 2)


func set_frame_sheet(char_id: String) -> void:
	setup(char_id, _footstep, is_player)
