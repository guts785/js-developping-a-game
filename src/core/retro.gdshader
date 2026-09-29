shader_type canvas_item;
// retro.gdshader — the CRT pass, authored in *game* pixels.
//
// This draws inside the 640x360 SubViewport, so SCREEN_UV * game_size is an exact
// pixel coordinate rather than a window coordinate. Every effect is quantised to
// that grid: a scanline is one game pixel tall no matter what the window or the
// monitor is doing. That is the whole point -- a mask that follows the window
// instead of the art turns into moire the moment you go fullscreen.
//
// `enabled` is blended rather than branched: GLSL ES does not allow an early
// `return` out of the fragment processor, and a real branch would cost more than
// the mix anyway.

uniform sampler2D SCREEN_TEXTURE : hint_screen_texture, filter_nearest;
uniform vec2 game_size = vec2(640.0, 360.0);

// One darkened game-pixel row every `scanline_period` rows.
uniform float scanline_strength : hint_range(0.0, 0.6) = 0.14;
// Two game-pixel period, not three. A 3px band beats against 1px art detail (window
// grilles, tile joints, dither) and the interference reads as moire once the frame
// is upscaled. One dark row in two is uniform against everything.
uniform float scanline_period : hint_range(2.0, 8.0) = 2.0;
// Horizontal fringing, in game pixels (1/640 == one pixel).
uniform float aberration : hint_range(0.0, 0.008) = 0.0016;
uniform float grain_amount : hint_range(0.0, 0.2) = 0.022;
// Tube falloff. Kept low: the room art already carries a baked vignette and the UI
// layer adds a third, so a heavy value here stacks into a crushed border.
uniform float vignette : hint_range(0.0, 1.0) = 0.16;
// Extra darkening in the bottom rows, where a real tube loses the most light.
uniform float bottom_sag : hint_range(0.0, 0.4) = 0.06;
uniform float enabled : hint_range(0.0, 1.0) = 1.0;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

void fragment() {
	vec2 uv = SCREEN_UV;
	vec2 gp = uv * game_size;

	vec3 base = texture(SCREEN_TEXTURE, uv).rgb;

	// chromatic fringe, exactly one game pixel wide
	float r = texture(SCREEN_TEXTURE, uv + vec2(aberration, 0.0)).r;
	float b = texture(SCREEN_TEXTURE, uv - vec2(aberration, 0.0)).b;
	vec3 col = vec3(r, base.g, b);

	// scanlines: whole-pixel rows, never fractional. MULTIPLICATIVE, not
	// subtractive. A flat `col -= strength` drives every dark pixel negative and
	// clamps it to pure black -- which turned the room's shadowed cabinet and the
	// actors' dark clothing into a solid black rectangle that read as a missing
	// texture. Scaling by (1 - strength) keeps the hue and leaves detail in the dark.
	float band = mod(floor(gp.y), scanline_period);
	float dim = 1.0;
	if (band < 1.0) {
		dim = 1.0 - scanline_strength;
	} else if (band < 2.0 && scanline_period > 2.5) {
		dim = 1.0 - scanline_strength * 0.35;   // softer shoulder, still integer
	}
	col *= dim;

	// grain, locked to a 2-pixel cell so it reads as texture, not noise
	vec2 cell = floor(gp * 0.5) + vec2(floor(TIME * 11.0) * 5.0);
	col += (hash(cell) - 0.5) * grain_amount;

	// vignette + tube sag
	vec2 d = (uv - 0.5) * 2.0;
	float v = 1.0 - dot(d, d) * vignette;
	v -= smoothstep(0.55, 1.0, uv.y) * bottom_sag;
	col *= clamp(v, 0.0, 1.0);

	COLOR = vec4(clamp(mix(base, col, enabled), vec3(0.0), vec3(1.0)), 1.0);
}
