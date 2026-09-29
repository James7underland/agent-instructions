# Читает вкладку «Список ошибок» Unimod PRO 2 как текст.
# Полезно после сборки (F9) и после кнопки «Проверка» в редакторе ST —
# не надо разглядывать скриншот, ошибки приходят строками.
#
#   .\ui_errors.ps1
#   .\ui_errors.ps1 -Raw     — без форматирования, по одной ячейке в строке
param([switch]$Raw)
. "$PSScriptRoot\ui_lib.ps1"

Show-UmWindow | Out-Null
$all = @(Get-UmAllElements -MaxDepth 18 | Where-Object { -not $_.OffScreen -and $_.Type -eq 'DataItem' -and $_.Name })

if ($all.Count -eq 0) { "ошибок нет (список пуст)"; return }

if ($Raw) { $all | Sort-Object Y, X | ForEach-Object { "({0},{1}) '{2}'" -f $_.X, $_.Y, $_.Name }; return }

# ячейки группируются по Y (строка таблицы), внутри строки сортируем по X.
# @() обязательно: при единственной группе $rows.Count вернул бы число ячеек
# в ней, а не число строк.
$rows = @($all | Group-Object Y | Sort-Object { [int]$_.Name })
"ошибок: $($rows.Count)"
foreach ($r in $rows) {
    $cells = $r.Group | Sort-Object X | ForEach-Object { $_.Name }
    # порядок колонок: № · Описание · Источник · Строка · Столбец · Категория
    "  " + ($cells -join ' | ')
}
