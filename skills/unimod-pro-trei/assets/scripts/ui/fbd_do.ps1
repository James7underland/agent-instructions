# Одиночные действия в редакторе FBD из командной строки (обёртка над fbd_lib.ps1).
# Для серии действий выгоднее один вызов PowerShell с `. fbd_lib.ps1` —
# каждый запуск этого скрипта заново компилирует пиксельный детектор (~1 с).
#
#   .\fbd_do.ps1 view
#   .\fbd_do.ps1 mode -Mode link
#   .\fbd_do.ps1 link  -Prog <prog.json> -Src a_real -Dst '+' -DstSlot 1
#   .\fbd_do.ps1 link  -Prog <prog.json> -SrcCell 2,10 -DstCell 20,11 -DstSlot 1
#   .\fbd_do.ps1 place -Item a_real -Column 10 -Line 5
#   .\fbd_do.ps1 place -Palette 'Оператор' -Item 'Сложение (+)' -Parent 'Арифметические' -Column 20 -Line 6 -TitleRows 1 -Pins 2
#   .\fbd_do.ps1 place -Palette 'Функциональный Блок' -Source 'из Словаря' -Item TON -Parent _TON_1 -Column 30 -Line 5 -TitleRows 1 -Pins 2
#   .\fbd_do.ps1 save  -Prog <prog.json>                    — зафиксировать связи толчком, сохранить, число связей
#   .\fbd_do.ps1 scroll -H 0 -V 480
#   .\fbd_do.ps1 st                                         — код на ST активной схемы текстом
#   .\fbd_do.ps1 menu  -Prog <prog.json> -SrcCell 2,10 -DstCell 20,10 -DstSlot 1 -MenuItem 'Инвертировать'
#                                                         — пункт контекстного меню у входа (связи)
#   .\fbd_do.ps1 delete -Prog <prog.json> -DstCell 20,15            — удалить блок в клетке (со связями)
#   .\fbd_do.ps1 unlink -Prog <prog.json> -DstCell 44,20 -DstSlot 0 — удалить связь, входящую во вход
#   .\fbd_do.ps1 move   -Prog <prog.json> -DstCell 32,19 -Column 44 -Line 20
#   .\fbd_do.ps1 undo | redo
#
# Перед работой окно IDE закреплено поверх остальных (Set-UmTopmost), вкладка
# нужной FBD-программы активна. -Prog передавать всегда: из него берётся размер
# поля (Define). Связи, проведённые мышью, попадают в модель только после правки
# блока — сохранять через `save` (он фиксирует) и сверять с файлом: fbd_dump.py.
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('view', 'mode', 'link', 'place', 'save', 'scroll', 'clear', 'st', 'menu', 'delete', 'unlink', 'move', 'undo', 'redo')][string]$Action,
    [string]$Prog, [string]$Src, [string]$Dst, [int[]]$SrcCell, [int[]]$DstCell,
    [int]$SrcSlot = 0, [int]$DstSlot = 0,
    [ValidateSet('edit', 'link')][string]$Mode,
    [string]$Palette, [string]$Source, [string]$Item, [string]$Parent,
    [int]$Column = -1, [int]$Line = -1, [int]$TitleRows = 0, [int]$Pins = 1,
    $H = $null, $V = $null, [string]$MenuItem
)
. "$PSScriptRoot\fbd_lib.ps1"
Set-UmTopmost | Out-Null

function Pick($p, [string]$name, [int[]]$cell) {
    if ($cell -and $cell.Count -eq 2) { return Get-FbdBlock $p -Column $cell[0] -Line $cell[1] }
    return Get-FbdBlock $p -Name $name
}

if ($Prog -and (Test-Path $Prog)) { Read-FbdProg $Prog | Out-Null }   # размер поля из Define
switch ($Action) {
    'view' {
        $v = Get-FbdView
        "поле ({0},{1}) {2}x{3}; клетка {4:N2}x{5:N2} px; прокрутка {6}/{7}; режим {8}; висящих выборов {9}" -f `
            $v.X, $v.Y, $v.W, $v.H, $v.SX, $v.SY, $v.HS, $v.VS, (Get-FbdMode), (Get-FbdPendingCount -View $v)
    }
    'mode' { if (Set-FbdMode -Mode $Mode) { "режим: $Mode" } else { "НЕ УДАЛОСЬ включить режим $Mode" } }
    'clear' { if (Clear-FbdSelection) { 'выбор снят' } else { 'висящий выбор остался' } }
    'scroll' { $v = Set-FbdScroll -H $H -V $V; "прокрутка {0}/{1}" -f $v.HS, $v.VS }
    'link' {
        $p = Read-FbdProg $Prog
        $s = Pick $p $Src $SrcCell; $d = Pick $p $Dst $DstCell
        $ok = Invoke-FbdLink -Src $s -SrcSlot $SrcSlot -Dst $d -DstSlot $DstSlot
        "{0}.out{1} -> {2}.in{3}: {4}" -f $s.name, ($SrcSlot + 1), $d.name, ($DstSlot + 1), $(if ($ok) { 'связь есть' } else { 'СВЯЗЬ НЕ СОЗДАНА' })
    }
    'place' {
        if ($Palette) { Select-FbdPalette $Palette }
        if ($Source) { Select-FbdCombo -Index 1 -Value $Source | Out-Null }
        $ok = Invoke-FbdPlace -Item $Item -Parent $Parent -Column $Column -Line $Line -TitleRows $TitleRows -Pins $Pins
        "{0} -> ({1},{2}): {3}" -f $Item, $Column, $Line, $(if ($ok) { 'блок на месте' } else { 'БЛОК НЕ ПОЯВИЛСЯ' })
    }
    'save' {
        # связи, проведённые мышью, попадают в модель только после правки блока — фиксируем толчком
        Save-FbdProject -WaitFile $Prog | Out-Null
        $p = Read-FbdProg $Prog
        $sub = Submit-FbdLinks -Prog $p
        if (Save-FbdProject -WaitFile $Prog) { "сохранено (связи зафиксированы: $sub): $Prog, связей в файле $(@((Read-FbdProg $Prog).text.Links).Count)" }
        else { "файл не обновился: $Prog" }
    }
    'st' { Get-FbdStCode }
    'delete' { $p = Read-FbdProg $Prog; $d = Pick $p $Dst $DstCell; "удалён '$($d.name)': " + (Remove-FbdBlock -Block $d) }
    'unlink' { $p = Read-FbdProg $Prog; $d = Pick $p $Dst $DstCell; "связь во вход $DstSlot блока '$($d.name)' удалена: " + (Remove-FbdLink -Dst $d -DstSlot $DstSlot) }
    'move'   { $p = Read-FbdProg $Prog; $d = Pick $p $Dst $DstCell; "'$($d.name)' -> ($Column,$Line): " + (Move-FbdBlock -Block $d -Column $Column -Line $Line) }
    'undo'   { "отмена: " + (Undo-Fbd) }
    'redo'   { "повтор: " + (Redo-Fbd) }
    'menu' {
        # контекстное меню у входа блока DstCell (слот DstSlot): точка на проводе левее входа
        $p = Read-FbdProg $Prog
        $d = Pick $p $Dst $DstCell
        $v = Show-FbdCells -C1 ($d.column - 6) -L1 ($d.line - 1) -C2 ($d.column + 8) -L2 ($d.line + $DstSlot + 1)
        $pt = Get-FbdPinPoint -Block $d -Slot $DstSlot -View $v
        Invoke-FbdContextMenu -X ($pt.Left - [int]($v.SX * 2)) -Y $pt.Y -Item $MenuItem
        "пункт «$MenuItem» выполнен у входа $DstSlot блока $($d.name)"
    }
}
