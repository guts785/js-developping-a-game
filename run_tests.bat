@echo off
title البلغة والجن - verification suite
setlocal

set GODOT=C:\Users\Admin\Downloads\Godot_v4.6.2-stable_win64.exe\Godot_v4.6.2-stable_win64_console.exe
if not exist "%GODOT%" set GODOT=C:\Users\Admin\Desktop\Godot_v4.6.2-stable_win64.exe
if not exist "%GODOT%" (
  echo Godot not found. Edit GODOT= in this file.
  pause
  exit /b 1
)

set P=%~dp0.
echo.
echo ============ 1/3  static  (data, assets, locale) ============
"%GODOT%" --headless --path "%P%" --quit-after 2000 -- --selftest
echo exit=%ERRORLEVEL%

echo.
echo ============ 2/3  runtime (rooms, hotspots, dialogue, minigames) ============
"%GODOT%" --headless --path "%P%" --quit-after 20000 -- --playtest
echo exit=%ERRORLEVEL%

echo.
echo ============ 3/3  progression (is the case finishable) ============
"%GODOT%" --headless --path "%P%" --quit-after 5000 -- --solve
echo exit=%ERRORLEVEL%

echo.
echo done.
pause
