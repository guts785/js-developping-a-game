#!/usr/bin/env bash
# Headless verification: selftest (static) -> playtest (runtime) -> solve (progression).
set -u
PROJ_WIN='C:\Users\Admin\Downloads\Claudecode\babouches-and-jnoun'
GODOT='/mnt/c/Users/Admin/Downloads/Godot_v4.6.2-stable_win64.exe/Godot_v4.6.2-stable_win64_console.exe'
cd /mnt/c/Users/Admin/Downloads/Claudecode/babouches-and-jnoun || exit 1

for pass in selftest playtest solve; do
  timeout 170 "$GODOT" --headless --path "$PROJ_WIN" --quit-after 8000 -- --"$pass" >/tmp/"$pass".log 2>&1
  echo "$pass exit=$? script-errors=$(grep -c 'SCRIPT ERROR' /tmp/"$pass".log)"
done

echo "=== distinct errors ==="
grep -hE "SCRIPT ERROR|Parse Error" /tmp/selftest.log /tmp/playtest.log /tmp/solve.log 2>/dev/null | sort -u | head -12
echo "=== pass summaries ==="
grep -hE "PASS|FAIL|checks|reachable|unreachable|deadlock" /tmp/selftest.log /tmp/playtest.log /tmp/solve.log 2>/dev/null | head -20
