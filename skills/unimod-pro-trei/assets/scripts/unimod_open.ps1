# Открывает проект Unimod PRO 2 и прожимает модальные диалоги импорта,
# которые появляются при наличии import.prj / *.import.csv / prog.import.st.
# Возвращает READY, когда главное окно готово.
#
#   .\unimod_open.ps1 -Project "D:\prj\demo01\project.uprj"
#
# ВАЖНО: сам Unimod.exe НЕ понимает в ключе -open пути с пробелами — он режет
# путь по первому пробелу и выдаёт "Не найден файл проекта". Кавычки не спасают.
# Поэтому скрипт сам переводит путь в короткую форму 8.3 (C:\CLAUDE~1\...).
param(
    [Parameter(Mandatory = $true)][string]$Project,
    [string]$Exe = "C:\Program Files\UnimodPRO2\Unimod.exe",
    [int]$MaxIter = 20
)

$sig = @'
using System;using System.Text;using System.Runtime.InteropServices;using System.Collections.Generic;
public class UmWin{
 [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc f, IntPtr l);
 [DllImport("user32.dll")] static extern int GetWindowTextW(IntPtr h, StringBuilder s, int n);
 [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("kernel32.dll", CharSet=CharSet.Unicode)] public static extern int GetShortPathName(string lng, StringBuilder shrt, int cch);
 delegate bool EnumProc(IntPtr h, IntPtr l);
 public static List<string> List(uint want){ var res=new List<string>();
  EnumWindows((h,l)=>{ uint pid; GetWindowThreadProcessId(h,out pid);
   if(pid==want && IsWindowVisible(h)){ var sb=new StringBuilder(512); GetWindowTextW(h,sb,512);
    res.Add(h+"|"+sb.ToString()); } return true;},IntPtr.Zero); return res; }
}
'@
if (-not ("UmWin" -as [type])) { Add-Type -TypeDefinition $sig }
Add-Type -AssemblyName System.Windows.Forms

if (-not (Test-Path $Project)) { "НЕТ ФАЙЛА: $Project"; return }
# Передали каталог проекта вместо .uprj — Unimod в таком случае молча стартует
# БЕЗ проекта (окно есть, деревья пустые), поэтому подставляем файл сами.
if (Test-Path $Project -PathType Container) {
    $cand = Join-Path $Project "project.uprj"
    if (-not (Test-Path $cand)) { "В каталоге нет project.uprj: $Project"; return }
    $Project = $cand
    "передан каталог -> открываю $Project"
}
$projDir = Split-Path $Project -Parent

# лок-файл от аварийно завершённого прошлого запуска
$lock = Join-Path $projDir "cache.tmp"
if (Test-Path $lock) { [System.IO.File]::Delete($lock) }

# путь с пробелами -> короткая форма 8.3
$argPath = $Project
if ($Project -match ' ') {
    $sb = New-Object System.Text.StringBuilder 600
    [UmWin]::GetShortPathName($Project, $sb, 600) | Out-Null
    $short = $sb.ToString()
    if ($short -and $short -notmatch ' ') {
        # короткое имя файла теряет 4-й символ расширения (.UPR вместо .uprj),
        # поэтому берём короткий каталог + длинное имя файла
        $argPath = (Join-Path (Split-Path $short -Parent) (Split-Path $Project -Leaf))
        "путь содержит пробелы -> использую $argPath"
    } else {
        "ВНИМАНИЕ: путь с пробелами, а короткое имя 8.3 недоступно — Unimod не откроет проект"
    }
}

# Рабочий каталог — каталог IDE. Unimod строит пути к ключам OPC-сервера
# (configuration.json → opc[].privateKey/privateCert/publicCertNode) от
# ТЕКУЩЕГО каталога процесса: запущенный из C:\X он пропишет C:/X/opc/config/...,
# хотя сами ключи лежат в <каталог IDE>\opc\config\keys.
Start-Process -FilePath $Exe -ArgumentList "-open", $argPath -WorkingDirectory (Split-Path $Exe -Parent) | Out-Null
Start-Sleep -Seconds 8

for ($i = 1; $i -le $MaxIter; $i++) {
    $p = @(Get-Process -Name Unimod -ErrorAction SilentlyContinue)
    if ($p.Count -eq 0) { "GONE"; return }
    # Маска БЕЗ двоеточия: после «Сохранить проект как» заголовок остаётся
    # 'Unimod PRO 2' без имени, хотя проект открыт. Сплэш зовётся 'Unimod',
    # поэтому 'Unimod PRO 2*' надёжно отличает готовое окно от заставки.
    if ($p[0].MainWindowTitle -like 'Unimod PRO 2*') { "READY after $i iters"; return }
    foreach ($w in [UmWin]::List([uint32]$p[0].Id)) {
        $h = [long]($w.Split('|')[0])
        [UmWin]::SetForegroundWindow([IntPtr]$h) | Out-Null
        Start-Sleep -Milliseconds 700
        [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")   # диалоги сфокусированы на "Да"/"OK"
        Start-Sleep -Milliseconds 1200
    }
    Start-Sleep -Seconds 2
}
"TIMEOUT - title: " + (@(Get-Process -Name Unimod -ErrorAction SilentlyContinue)[0].MainWindowTitle)
"Если висит окно 'Не найден файл проекта' — проверь пробелы в пути."
