# Дамп дерева UI Automation окна Unimod PRO 2.
#   .\ui_tree.ps1                      — всё дерево до глубины 8
#   .\ui_tree.ps1 -MaxDepth 3          — только верхние уровни
#   .\ui_tree.ps1 -Filter "Файл"       — только элементы, чьё имя содержит строку
#   .\ui_tree.ps1 -Type MenuItem       — только элементы указанного типа
param(
    [int]$MaxDepth = 8,
    [string]$Filter,
    [string]$Type,
    [switch]$NoFocus
)
. "$PSScriptRoot\ui_lib.ps1"

if (-not $NoFocus) { Show-UmWindow | Out-Null }

$root = Get-UmRoot
if ($null -eq $root) { "UIA: главное окно Unimod не найдено"; return }

$scale = Get-UmScale
"окно: '$($root.Current.Name)'  масштаб DPI: $scale"

$all = Get-UmAllElements -MaxDepth $MaxDepth
"элементов найдено: $($all.Count)"

$view = $all
if ($Filter) { $view = $view | Where-Object { $_.Name -and $_.Name -like "*$Filter*" } }
if ($Type)   { $view = $view | Where-Object { $_.Type -eq $Type } }

"---"
foreach ($e in $view) {
    $pad = ' ' * ($e.Depth * 2)
    $nm = if ($e.Name) { $e.Name } else { '<без имени>' }
    $aid = if ($e.AutomationId) { " id=$($e.AutomationId)" } else { '' }
    "{0}{1} [{2}]{3}  ({4},{5} {6}x{7})  <{8}>" -f $pad, $nm, $e.Type, $aid, $e.X, $e.Y, $e.W, $e.H, $e.Window
}
"---"
"типов: " + (($all | Group-Object Type | Sort-Object Count -Descending |
              ForEach-Object { "$($_.Name)=$($_.Count)" }) -join ', ')
