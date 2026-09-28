# Сохраняет проект.
#
# ВАЖНО: в Unimod две разные команды сохранения —
#   Ctrl+S        «Сохранить»        — только активный редактор/словарь/форму,
#                                       изменения в остальных элементах НЕ пишутся;
#   Ctrl+Shift+S  «Сохранить проект» — весь проект целиком.
# По умолчанию шлём Ctrl+Shift+S, иначе часть правок молча остаётся в памяти.
param(
    [int]$WaitSec = 8,
    [switch]$EditorOnly   # только активный редактор (Ctrl+S)
)
& (Join-Path $PSScriptRoot "unimod_focus.ps1") | Out-Null
Add-Type -AssemblyName System.Windows.Forms
if ($EditorOnly) {
    [System.Windows.Forms.SendKeys]::SendWait("^s")
    Start-Sleep -Seconds $WaitSec
    "saved (только активный редактор)"
} else {
    [System.Windows.Forms.SendKeys]::SendWait("^+s")
    Start-Sleep -Seconds $WaitSec
    "saved (весь проект)"
}
