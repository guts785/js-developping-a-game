@echo off
title البلغة والجن - Launcher
echo.
echo   ==========================================
echo     البلغة والجن  -  Babouches and Jnoun
echo   ==========================================
echo.
echo   launching in Godot 4.6...
echo.

set GODOT=C:\Users\Admin\Downloads\Godot_v4.6.2-stable_win64.exe\Godot_v4.6.2-stable_win64_console.exe
if not exist "%GODOT%" set GODOT=C:\Users\Admin\Desktop\Godot_v4.6.2-stable_win64.exe

if not exist "%GODOT%" (
  echo   Godot not found at either known path.
  echo   Edit GODOT= in this file to point at your Godot 4.6 executable.
  pause
  exit /b 1
)

start "" "%GODOT%" --path "%~dp0."
exit
