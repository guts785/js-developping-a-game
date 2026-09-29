extends Control
## Boot — the display shell.
##
## Everything the game draws lives inside a 640x360 SubViewport, so the world art,
## the UI and the CRT pass all sit on one pixel grid. The shell then hands that
## buffer to the window through an integer stretch, which is what makes fullscreen
## safe: the picture can only ever scale by whole pixels, and whatever is left over
## gets letterboxed instead of smeared.
##
## Before this, the game rendered straight into the root viewport, so at 1280x720
## the scanline shader worked in *window* pixels while the art worked in *game*
## pixels -- two grids fighting, which is exactly the shimmer that made the rooms
## and the characters look wrong at 1:1.
##
## F11 / Alt+Enter toggles fullscreen. The choice is remembered in GameState.

const GAME_W := 640
const GAME_H := 360
const WINDOWED_W := 1280
const WINDOWED_H := 720

var view: SubViewportContainer
var sub: SubViewport
var game: Node


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE

	view = SubViewportContainer.new()
	view.name = "View"
	view.stretch = true
	view.stretch_shrink = 1
	view.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	view.set_anchors_preset(Control.PRESET_FULL_RECT)
	view.focus_mode = Control.FOCUS_ALL
	add_child(view)

	sub = SubViewport.new()
	sub.name = "Game"
	sub.size = Vector2i(GAME_W, GAME_H)
	sub.transparent_bg = false
	sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	sub.handle_input_locally = true
	sub.msaa_2d = Viewport.MSAA_DISABLED
	sub.screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED
	sub.use_hdr_2d = false
	sub.snap_2d_transforms_to_pixel = true
	sub.snap_2d_vertices_to_pixel = true
	sub.gui_disable_input = false
	view.add_child(sub)

	game = load("res://src/main.tscn").instantiate()
	game.name = "Main"
	sub.add_child(game)

	apply_window_mode()


# ------------------------------------------------------------------ display
func is_fullscreen() -> bool:
	return DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN


func apply_window_mode() -> void:
	set_fullscreen(bool(GameState.settings.get("fullscreen", true)))


func set_fullscreen(on: bool) -> void:
	GameState.settings["fullscreen"] = on
	if on:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	else:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_size(Vector2i(WINDOWED_W, WINDOWED_H))
		_center_window()


func toggle_fullscreen() -> void:
	set_fullscreen(not is_fullscreen())


func _center_window() -> void:
	var screen := DisplayServer.screen_get_size(DisplayServer.window_get_current_screen())
	var win := DisplayServer.window_get_size()
	if screen.x > win.x and screen.y > win.y:
		DisplayServer.window_set_position((screen - win) / 2)


# F11 / Alt+Enter are also bound inside the game (src/main.gd) so they work while
# a room has focus. This path catches them on the title and card screens.
func _unhandled_input(event: InputEvent) -> void:
	if not (event is InputEventKey) or not event.pressed or event.echo:
		return
	var k: InputEventKey = event
	if k.keycode == KEY_F11 or (k.keycode == KEY_ENTER and k.alt_pressed):
		accept_event()
		toggle_fullscreen()
