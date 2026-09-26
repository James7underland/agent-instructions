# Открытие проекта Unimod PRO 2, защищённого паролем (однопользовательский
# или защищённый режим безопасности).
#
#   .\unimod_open_secure.ps1 -Project "C:\...\proj"                       # только открыть и показать окно входа
#   .\unimod_open_secure.ps1 -Project "C:\...\proj" -Login lab -Password Lab12345 -Fill
#
# ОТЛИЧИЕ ОТ unimod_open.ps1: здесь НЕТ авто-Enter. Обычный скрипт жмёт Enter во
# всех всплывших окнах — на окне входа это пустой пароль, то есть неудачная
# попытка; после maxCountFailInputPassword (по умолчанию 3) проект блокируется,
# а пароль однопользовательского режима не восстанавливается.
# Без -Fill скрипт только ждёт окно входа, снимает экран и сообщает заголовок.
# С -Fill вставляет логин и пароль ЧЕРЕЗ БУФЕР ОБМЕНА (раскладка клавиатуры
# может быть русской — SendKeys с латиницей тогда печатает кириллицу) и жмёт
# Enter ОДИН раз. Буфер после этого очищается.
param(
    [Parameter(Mandatory = $true)][string]$Project,
    [string]$Exe = "C:\Program Files\UnimodPRO2\Unimod.exe",
    [string]$Login,
    [string]$Password,
    [switch]$Fill,
    [string]$ShotPath = "$env:TEMP\unimod_login.png",
    [int]$WaitSec = 40
)
$sig = @"
using System;using System.Text;using System.Runtime.InteropServices;using System.Collections.Generic;
public class UmSec{
 [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc f, IntPtr l);
 [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetWindowTextW(IntPtr h, StringBuilder s, int n);
 [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
 [DllImport("kernel32.dll", CharSet=CharSet.Unicode)] public static extern int GetShortPathName(string lng, StringBuilder shrt, int cch);
 delegate bool EnumProc(IntPtr h, IntPtr l);
 public static List<string> Of(uint want){ var r=new List<string>(); EnumWindows((h,l)=>{ uint pid; GetWindowThreadProcessId(h,out pid); if(pid==want && IsWindowVisible(h)){ var sb=new StringBuilder(256); GetWindowTextW(h,sb,256); r.Add(h+"|"+sb);} return true;},IntPtr.Zero); return r; }
}
"@
if (-not ("UmSec" -as [type])) { Add-Type -TypeDefinition $sig }
Add-Type -AssemblyName System.Windows.Forms, System.Drawing

if (Test-Path $Project -PathType Container) { $Project = Join-Path $Project "project.uprj" }
if (-not (Test-Path $Project)) { "НЕТ ФАЙЛА: $Project"; return }
if ($Fill -and (-not $Login -or -not $Password)) { "для -Fill нужны -Login и -Password"; return }

# usr.cfg: предупредить, если проект, похоже, не защищён
$cfg = Join-Path (Split-Path $Project -Parent) "usr.cfg"
if (Test-Path $cfg) {
    $ed = (Select-String -Path $cfg -Pattern '^edition=(\d+)' | Select-Object -First 1)
    if ($ed) { "usr.cfg: " + $ed.Line }
}
$lock = Join-Path (Split-Path $Project -Parent) "cache.tmp"
if (Test-Path $lock) { [System.IO.File]::Delete($lock) }

$argPath = $Project
if ($Project -match ' ') {
    $sb = New-Object System.Text.StringBuilder 600
    [UmSec]::GetShortPathName($Project, $sb, 600) | Out-Null
    if ($sb.ToString()) { $argPath = Join-Path (Split-Path $sb.ToString() -Parent) (Split-Path $Project -Leaf) }
}
$p = Start-Process -FilePath $Exe -ArgumentList "-open", $argPath -WorkingDirectory (Split-Path $Exe -Parent) -PassThru
$deadline = (Get-Date).AddSeconds($WaitSec)
$dlg = $null
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 800
    $wins = [UmSec]::Of([uint32]$p.Id)
    $other = @($wins | Where-Object { $_ -notlike '*|Unimod PRO 2*' -and $_ -notlike '*|Unimod' -and $_ -notlike '*|' })
    if ($other.Count -gt 0) { $dlg = $other[0]; break }
    if (@($wins | Where-Object { $_ -like '*|Unimod PRO 2*' }).Count -gt 0) { Start-Sleep -Seconds 2
        if (@([UmSec]::Of([uint32]$p.Id) | Where-Object { $_ -notlike '*|Unimod PRO 2*' -and $_ -notlike '*|' }).Count -eq 0) { "READY без окна входа — проект не защищён паролем?"; return } }
}
if (-not $dlg) { "TIMEOUT: окно входа не появилось. Окна: " + (([UmSec]::Of([uint32]$p.Id)) -join ' ; '); return }
$title = $dlg.Split('|', 2)[1]
"окно входа: '$title'"
$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap($b.Width, $b.Height)
[System.Drawing.Graphics]::FromImage($bmp).CopyFromScreen(0, 0, 0, 0, $bmp.Size)
$bmp.Save($ShotPath, [System.Drawing.Imaging.ImageFormat]::Png)
"снимок: $ShotPath"
if (-not $Fill) { "без -Fill ничего не ввожу — посмотри снимок и перезапусти с -Login/-Password/-Fill либо введи вручную"; return }

[UmSec]::SetForegroundWindow([IntPtr][long]($dlg.Split('|')[0])) | Out-Null
Start-Sleep -Milliseconds 600
function Paste($t) { Set-Clipboard -Value $t; Start-Sleep -Milliseconds 150
    [System.Windows.Forms.SendKeys]::SendWait("^a"); Start-Sleep -Milliseconds 150
    [System.Windows.Forms.SendKeys]::SendWait("^v"); Start-Sleep -Milliseconds 350 }
Paste $Login
[System.Windows.Forms.SendKeys]::SendWait("{TAB}"); Start-Sleep -Milliseconds 300
Paste $Password
Set-Clipboard -Value " "
[System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
Start-Sleep -Seconds 4
"окна после входа: " + (([UmSec]::Of([uint32]$p.Id)) -join ' ; ')