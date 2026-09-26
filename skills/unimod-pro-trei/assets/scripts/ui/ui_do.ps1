# Действие над элементом интерфейса Unimod PRO 2, найденным по имени.
#
#   .\ui_do.ps1 -Name "Файл"                       — нажать пункт меню
#   .\ui_do.ps1 -Name "Сборка" -Type Button        — уточнить типом
#   .\ui_do.ps1 -Name "Имя:" -Action value -Value "tank_sim"
#   .\ui_do.ps1 -Name "Отмена" -Action click       — принудительно мышью
#   .\ui_do.ps1 -Name "tank_sim" -Action expand    — раскрыть узел дерева
#   .\ui_do.ps1 -Name "Файл" -List                 — только показать совпадения
#
# Если совпадений несколько — выводит их все и ничего не делает; уточняй -Type
# или -Index. Так исключён случайный клик не по тому элементу.
param(
    [Parameter(Mandatory = $true)][string]$Name,
    [string]$Type,
    [ValidateSet('auto', 'click', 'dblclick', 'invoke', 'value', 'expand', 'collapse', 'select', 'focus')]
    [string]$Action = 'auto',
    [string]$Value,
    [int]$Index = -1,
    [int]$MaxDepth = 10,
    [switch]$List,
    [switch]$IncludeOffscreen
)
. "$PSScriptRoot\ui_lib.ps1"

Show-UmWindow | Out-Null
$root = Get-UmRoot
if ($null -eq $root) { "UIA: окно Unimod не найдено"; return }
$scale = Get-UmScale

$hits = @(Find-UmElement -Name $Name -Type $Type -MaxDepth $MaxDepth)
if (-not $IncludeOffscreen) { $hits = @($hits | Where-Object { -not $_.OffScreen }) }

if ($hits.Count -eq 0) { "НЕ НАЙДЕНО: '$Name'" + $(if ($Type) { " типа $Type" }); return }

if ($List -or ($hits.Count -gt 1 -and $Index -lt 0)) {
    "совпадений: $($hits.Count)"
    for ($i = 0; $i -lt $hits.Count; $i++) {
        $e = $hits[$i]
        "  [$i] '$($e.Name)' [$($e.Type)] окно='$($e.Window)' ($($e.X),$($e.Y) $($e.W)x$($e.H))"
    }
    if (-not $List) { "уточни -Type или -Index — ничего не нажимаю" }
    return
}

$item = if ($Index -ge 0) { $hits[$Index] } else { $hits[0] }
$el = $item.Element
"цель: '$($item.Name)' [$($item.Type)] ($($item.X),$($item.Y))"

# Узлы дерева в этой сборке Qt НЕ поддерживают ExpandCollapsePattern,
# поэтому раскрытие/схлопывание делаем выделением + стрелкой.
function Get-Pattern($e, $p) {
    try { return $e.GetCurrentPattern($p) } catch { return $null }
}
function Select-Item($e) {
    $sp = Get-Pattern $e ([System.Windows.Automation.SelectionItemPattern]::Pattern)
    if ($null -ne $sp) { $sp.Select(); return $true }
    try { $e.SetFocus(); return $true } catch { }
    $pt = Get-UmClickPoint -Element $e -Scale $scale
    Invoke-UmClick -X $pt.X -Y $pt.Y -SleepMs 400
    return $true
}

switch ($Action) {
    'value' {
        $p = Get-Pattern $el ([System.Windows.Automation.ValuePattern]::Pattern)
        if ($null -ne $p) { $p.SetValue($Value); "value = '$Value'" }
        else {
            Select-Item $el | Out-Null
            Send-UmKeys "^a" 150; Send-UmKeys "{DEL}" 150; Send-UmKeys $Value 300
            "value через клавиатуру = '$Value'"
        }
    }
    # Стрелку посылаем ПОСЛЕ клика мышью по узлу. SelectionItemPattern.Select()
    # выделяет узел, но фокус клавиатуры в Qt-дереве остаётся на прежнем узле —
    # и {LEFT} сворачивал не тот узел (однажды — корень со всем деревом).
    'expand' {
        $p = Get-Pattern $el ([System.Windows.Automation.ExpandCollapsePattern]::Pattern)
        if ($null -ne $p) { $p.Expand(); "expanded (pattern)" }
        else {
            $pt = Get-UmClickPoint -Element $el -Scale $scale
            Invoke-UmClick -X $pt.X -Y $pt.Y -SleepMs 500
            Send-UmKeys "{RIGHT}" 500; "expanded (клик + стрелка вправо)"
        }
    }
    'collapse' {
        $p = Get-Pattern $el ([System.Windows.Automation.ExpandCollapsePattern]::Pattern)
        if ($null -ne $p) { $p.Collapse(); "collapsed (pattern)" }
        else {
            $pt = Get-UmClickPoint -Element $el -Scale $scale
            Invoke-UmClick -X $pt.X -Y $pt.Y -SleepMs 500
            Send-UmKeys "{LEFT}" 500; "collapsed (клик + стрелка влево)"
        }
    }
    'select' { Select-Item $el | Out-Null; "selected" }
    'invoke' {
        $p = Get-Pattern $el ([System.Windows.Automation.InvokePattern]::Pattern)
        if ($null -ne $p) { $p.Invoke(); "invoked" }
        else { Invoke-UmElement -Item $item -Scale $scale }
    }
    'focus'  { $el.SetFocus(); "focused" }
    'click'  {
        $pt = Get-UmClickPoint -Element $el -Scale $scale
        Invoke-UmClick -X $pt.X -Y $pt.Y
        "clicked $($pt.X),$($pt.Y)"
    }
    'dblclick' {
        $pt = Get-UmClickPoint -Element $el -Scale $scale
        Invoke-UmClick -X $pt.X -Y $pt.Y -SleepMs 120
        Invoke-UmClick -X $pt.X -Y $pt.Y -SleepMs 800
        "double-clicked $($pt.X),$($pt.Y)"
    }
    default  { Invoke-UmElement -Item $item -Scale $scale }
}
