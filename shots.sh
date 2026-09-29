#!/usr/bin/env bash
# Render one frame of each named game state to PNG. Needs a GPU context, so no --headless.
#
# The --import pass is not optional. Godot only re-imports changed source art in editor
# mode; running the game directly serves whatever is already in .godot/imported/. Skip
# it and every regenerated PNG you just drew is silently ignored -- the shots look
# identical and you chase a bug that is not there.
set -u
PROJ='/mnt/c/Users/Admin/Downloads/Claudecode/babouches-and-jnoun'
GODOT='/mnt/c/Users/Admin/Downloads/Godot_v4.6.2-stable_win64.exe/Godot_v4.6.2-stable_win64_console.exe'
cd "$PROJ"
rm -f shot_*.png

"$GODOT" --headless --path 'C:\Users\Admin\Downloads\Claudecode\babouches-and-jnoun' --import 2>&1 \
  | grep -iE "^ERROR|reimport.*(png|ttf|wav)" | tail -3

for t in card play room:kitchen room:riad room:office; do
  timeout 90 "$GODOT" --path 'C:\Users\Admin\Downloads\Claudecode\babouches-and-jnoun' -- --shot "$t" 2>&1 \
    | grep -E "SHOT|SCRIPT ERROR|Parse Error|SHADER ERROR" | head -5
done
echo "--- files ---"
ls -la shot_*.png 2>/dev/null || echo "no shots written"
