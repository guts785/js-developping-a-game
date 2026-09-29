#!/usr/bin/env bash
# Install the Godot 4.6.2 export templates and cut a standalone Windows build.
# Run after the .tpz download reaches 1,251,900,388 bytes.
set -u
TPZ=/tmp/gt.tpz
EXPECT=1251900388
TPL_DIR="/mnt/c/Users/Admin/AppData/Roaming/Godot/export_templates/4.6.2.stable"
PROJ='/mnt/c/Users/Admin/Downloads/Claudecode/babouches-and-jnoun'
GODOT='/mnt/c/Users/Admin/Downloads/Godot_v4.6.2-stable_win64.exe/Godot_v4.6.2-stable_win64_console.exe'

SZ=$(stat -c %s "$TPZ" 2>/dev/null || echo 0)
echo "download: $SZ / $EXPECT"
if [ "$SZ" -lt "$EXPECT" ]; then
  echo "INCOMPLETE -- resume the download first, nothing installed."
  exit 1
fi

# .tpz is a zip whose payload lives under templates/
python3 - <<'PY'
import zipfile, os
z = zipfile.ZipFile('/tmp/gt.tpz')
bad = z.testzip()
if bad:
    raise SystemExit("corrupt entry: %s" % bad)
dest = "/mnt/c/Users/Admin/AppData/Roaming/Godot/export_templates/4.6.2.stable"
os.makedirs(dest, exist_ok=True)
n = 0
for m in z.namelist():
    if m.endswith("/"):
        continue
    rel = m.split("templates/", 1)[-1] if "templates/" in m else m
    out = os.path.join(dest, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with z.open(m) as src, open(out, "wb") as dst:
        dst.write(src.read())
    n += 1
print("extracted %d files -> %s" % (n, dest))
PY

echo "--- templates present ---"
ls "$TPL_DIR" | grep -iE "windows" | head -5

cd "$PROJ"
mkdir -p build
timeout 600 "$GODOT" --headless --path 'C:\Users\Admin\Downloads\Claudecode\babouches-and-jnoun' \
    --export-release "Windows Desktop" build/BabouchesAndJnoun.exe 2>&1 | tail -12
echo "--- result ---"
ls -la build/ 2>/dev/null
