# البلغة والجن — Babouches and Jnoun

لعبة مغامرة ثنائية الأبعاد بنمط «point-and-click» بالبكسل آرت، على طريقة ألعاب Sui Arts
(*Dentures and Demons* / *Moth Lake*) — نفس الأسلوب، نفس الإحساس، قصة جديدة بالكامل.

اللغة الوحيدة داخل اللعبة: **الدارجة المغربية بالحرف العربي**.

---

## القصة

المفتش **رشيد البلغاوي** كيتسنى التقاعد. بلغة كحلة، جنّ في طنجية، وسبع ديار
فالدار البيضاء. سبعة فصول، تلاتة نهايات، وواحد ماشي بحال اللي كنتي كتظن.

## التشغيل

    play.bat

أو مباشرة:

    Godot_v4.6.2-stable_win64_console.exe --path .

## الفحص — التلاتة خاصهم ينجحو

    run_tests.bat

| الفحص | شنو كيدير |
|---|---|
| `--selftest` | 836 فحص ساكن: كل غرفة، كل هوت سبوت، كل حوار، كل أيكونة، كل مفتاح ترجمة، كل صوت |
| `--playtest` | كيلعب اللعبة بيدو: 7 غرف، 60 هوت سبوت، 123 فعل، 7 شجرات حوار، 3 ألغاز، 3 نهايات، وحفظ/تحميل |
| `--solve` | كيثبت أن القضية كتكمّل: 7/7 غرف، 3/3 نهايات |

آخر تشغيل: **selftest PASS · playtest PASS · solve PASS** (0 أخطاء سكريبت).

## التحكم

| الفعل | الزر |
|---|---|
| المشي | `W` `A` `S` `D` (ولا الأسهم) |
| فعل / هدر | `E` ولا `Space` |
| مشي أوتوماتيك | كليك بالماوس على شي حاجة |
| الدفتر | `J` |
| تلميح | `H` |
| إسكرين شوت | `F12` |
| وقفة | `Esc` |

رشيد كيمشي بـ **WASD** فأرضية البيت — فوق وتحت، ويمين ويسار. ملي كتقرب من شي حاجة،
كتطلع سهم خضر فوق منها: دوستي `E` وكيديرها. الكليك مازال كيخدم: رشيد كيمشي بوحدو
للمكان وكيدير الفعل. الصور كتتقاطع حسب العمق (Y-sort): كتقدر تدوز مورا الحوايج
وقدامها بحال فالألعاب الحقيقية.

---

## Build notes (English)

### Engine

Godot **4.6.2**, `gl_compatibility` renderer, 640x360 logical viewport. Rooms are
authored natively at **640x360** and character sheets at **36x68** per frame — the art
is 2x the pixel density of the first pass, not an upscale. Integer scaling,
nearest-neighbour filtering, pixel snapping on.

### Layout

    art/        8 rooms at 640x360, 9 characters (8-frame 36x68 walk sheets + 88x88
                portraits), 24 item icons, UI frames, cursor, chapter cards, ending card,
                vignette
    audio/      22 procedural WAVs (4 ambience, 2 music, 16 sfx)
    fonts/      Cairo (Arabic, RTL — shaping left to Godot's TextServer)
    tools/      pxlib.py, roomlib.py, gen_rooms2.py, gen_sprites2.py   <- v2 (current art)
                artlib.py, gen_rooms.py, gen_sprites.py, gen_ui.py, gen_audio.py  <- v1
    src/
      main.gd          orchestrator: rooms, hotspots, walk, dialogue, minigames,
                       chapter cards, endings, save/load, CRT pass
      main.tscn
      autoload/        locale.gd (every string), game_state.gd, audio_manager.gd, ui.gd
      core/            player.gd, dialogue_box.gd, hud.gd, minigames.gd, retro.gdshader
      data/            rooms_a.gd (ch1-3), rooms_b.gd (ch4-6 + endings), jokes.gd, data.gd
      ui/              title.gd, ending.gd
      selftest.gd      static integrity pass
      playtest.gd      runtime sweep
      solver.gd        progression proof

### Everything is generated

No third-party assets. All art comes from `tools/*.py` (stdlib only — no PIL, no numpy)
against a locked 24-colour Moroccan-noir palette at native pixel scale. All audio is
additive synthesis in `tools/gen_audio.py` (SR 22050, maqam-based, oud/qanun/darbuka
models). Re-run any generator to regenerate its assets deterministically.

**No Arabic text is baked into any PNG** — `gen_ui.py` deliberately leaves text out so
Godot's TextServer does the RTL shaping and letter joining. Baked Arabic breaks ligatures.

### Data-driven design

Rooms are dictionaries: `hotspots` (rect in art space, label, `look`/`use`/`talk`,
optional `cond`, optional `on_use` action list), `npcs`, `exits`, `ambience`, `music`,
`on_enter`. Actions are `flag`, `unflag`, `give`, `take`, `sfx`, `clue`, `objective`,
`say`, `dlg`, `goto`, `minigame`, `ending`. Conditions are `flag`, `flag2`, `not_flag`,
`item`, `not_item`, `chapter`.

Two tables are shared between the runtime and the verification passes so they cannot
drift: `GameState.MINIGAME_RESULTS` (what winning each puzzle grants) and
`GameState.RUNTIME_FLAGS` (flags the controller sets directly rather than via data).

### Speakers

Room data may name a speaker by character id (`rachid`) or by the literal Arabic name
(`المفتش رشيد`). `Data.speaker_id()` normalises both to the same character so portraits
and the auto-interleaved barks work either way.

### Tone

The crude register of the genre is a feature, not an accident. The profanity/humour
bank lives in `src/data/jokes.gd` and the engine fires it contextually — on examines,
wrong item uses, repeat clicks, idle time, and fourth-wall moments — so the mouth of
المفتش رشيد stays in one file and stays tunable.

### Style

24-colour palette, 640x360 rooms, CRT pass (scanlines, chromatic fringing, grain, slight
barrel) applied to the world layer only so Arabic UI text stays crisp.

Atmosphere is painted into the pixels rather than added as an overlay: light shafts
through windows (`shaft`), ambient occlusion under furniture (`ao`), dithered vertical
gradients on the walls (`dither_grad_v`), floating dust (`motes`), fog bands, pooled
lamp light (`light_pool`) and ordered-dither falloff on every shadow. Characters are a
jointed rig — hip/knee/ankle and shoulder/elbow — with cloth sway, rim light, an ink
outline pass so limbs separate from the garment, and per-mood faces on the portraits.

### Z-order

Every overlay owns an explicit band, so nothing can render behind something it should
cover:

    world (Y-sorted, bg z=-100)  <  fx 5  <  hud 10  <  dialogue 12  <  minigames 20
    <  chapter card 25  <  title 30  <  ending 32

Inside the world, depth is **Y-sorted**: `player.position.y` is the ground contact
point, so the inspector passes behind and in front of NPCs and furniture correctly.
Hotspot markers sit at `z_index = 100` so they stay legible over any prop.

### Exporting a standalone .exe (optional)

`play.bat` runs the game straight from source with the installed Godot — no templates
needed. For a distributable build, open the project in the editor once
(**Editor → Manage Export Templates → Download**), then:

    Godot_v4.6.2-stable_win64_console.exe --headless --path . \
        --export-release "Windows Desktop" build/BabouchesAndJnoun.exe

Templates are installed and the standalone build exists:

    build/BabouchesAndJnoun.exe     104 MB   <- double-click to play, no Godot needed
    build/BabouchesAndJnoun.pck       5 MB   <- game data, must sit next to the exe

`export_presets.cfg` is committed, so the build is reproducible with:

    Godot_v4.6.2-stable_win64_console.exe --headless --path . \
        --export-release "Windows Desktop" build/BabouchesAndJnoun.exe

The exported binary runs the same three verification passes as the source tree
(`BabouchesAndJnoun.exe --headless -- --selftest|--playtest|--solve`).

### Rendering a screenshot of any game state

    bash shots.sh

Renders one frame of each named state (title, settings, chapters, play,
room:<id>) to `shot_<target>.png` at window resolution. Needs a GPU context, so
no `--headless`. This is how the layout and z-order bugs in this pass were
actually caught rather than guessed at.
