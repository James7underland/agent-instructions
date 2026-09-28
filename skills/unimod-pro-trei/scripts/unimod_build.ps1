# Собирает открытый проект (F9) и проверяет результат.
# Признак успеха: app/project.app появился или ОБНОВИЛСЯ во время сборки. Просто
# наличия файла мало: в копии проекта он остаётся от прошлой сборки (2026-09-14).
#
# ВАЖНО про диалоги после НЕуспешной сборки. IDE показывает подряд:
#   1) "В проекте обнаружены ошибки. Упаковать проект и отправить разработчику
#      по электронной почте...? Упаковать проект?"  -> кнопка по умолчанию "Да"!
#   2) "Исправить обнаруженные ошибки?"
# Поэтому здесь шлётся ESC (= "Нет"), а НЕ Enter: Enter на первом диалоге
# запустит упаковку проекта для отправки наружу.
param(
    [Parameter(Mandatory = $true)][string]$ProjectDir,
    [int]$WaitSec = 25
)
$app = Join-Path $ProjectDir "app\project.app"
$before = if (Test-Path $app) { (Get-Item $app).LastWriteTimeUtc } else { $null }
& (Join-Path $PSScriptRoot "unimod_focus.ps1") | Out-Null
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait("{F9}")
Start-Sleep -Seconds $WaitSec

if ((Test-Path $app) -and ($null -eq $before -or (Get-Item $app).LastWriteTimeUtc -ne $before)) {
    $i = Get-Item $app
    "BUILD OK: $($i.Length) bytes, $($i.LastWriteTime)"
    Get-ChildItem (Join-Path $ProjectDir "app") | ForEach-Object { "  {0,8}  {1}" -f $_.Length, $_.Name }
    return
}

# сборка не прошла: аккуратно закрываем диалоги через ESC
$sig = @'
using System;using System.Text;using System.Runtime.InteropServices;using System.Collections.Generic;
public class UmBld{
 [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc f, IntPtr l);
 [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 delegate bool EnumProc(IntPtr h, IntPtr l);
 public static List<long> List(uint want){ var res=new List<long>();
  EnumWindows((h,l)=>{ uint pid; GetWindowThreadProcessId(h,out pid);
   if(pid==want && IsWindowVisible(h)) res.Add((long)h); return true;},IntPtr.Zero); return res; }
}
'@
if (-not ("UmBld" -as [type])) { Add-Type -TypeDefinition $sig }
for ($i = 1; $i -le 4; $i++) {
    $p = @(Get-Process -Name Unimod -ErrorAction SilentlyContinue)
    if ($p.Count -eq 0) { break }
    if ($p[0].MainWindowTitle -like 'Unimod PRO 2:*') { break }
    foreach ($h in [UmBld]::List([uint32]$p[0].Id)) {
        [UmBld]::SetForegroundWindow([IntPtr]$h) | Out-Null
        Start-Sleep -Milliseconds 600
        [System.Windows.Forms.SendKeys]::SendWait("{ESC}")
        Start-Sleep -Milliseconds 900
    }
}
"BUILD FAILED: app/project.app не создан и не обновлён."
"Ошибки смотреть во вкладке 'Список ошибок' внизу окна IDE."
"Частая причина при генерации файлов: 'Ошибка в адресации переменных' —"
"у двух переменных совпал attributes.offset. См. known-issues.md."
