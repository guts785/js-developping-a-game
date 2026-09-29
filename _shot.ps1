Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class W {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern IntPtr FindWindow(string c, string n);
  public struct RECT { public int Left, Top, Right, Bottom; }
}
"@
$p = Get-Process -Name "*Godot*" -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -ne "" } | Select-Object -First 1
if (-not $p) { Write-Output "NO_WINDOW"; exit 1 }
$h = $p.MainWindowHandle
[W]::ShowWindow($h, 9) | Out-Null
[W]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 1200
$r = New-Object W+RECT
[W]::GetWindowRect($h, [ref]$r) | Out-Null
$w = $r.Right - $r.Left; $ht = $r.Bottom - $r.Top
$bmp = New-Object System.Drawing.Bitmap $w, $ht
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($r.Left, $r.Top, 0, 0, $bmp.Size)
$bmp.Save($args[0], [System.Drawing.Imaging.ImageFormat]::Png)
Write-Output ("OK " + $w + "x" + $ht)
