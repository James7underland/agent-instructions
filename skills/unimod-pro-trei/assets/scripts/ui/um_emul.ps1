# Эмуляция под управлением скрипта: открыть словарь программы, войти в эмуляцию,
# прочитать значения, записать значение, выйти.
#
#   .\um_emul.ps1 -Action dict -Prog t1                 # открыть локальный словарь (ДО эмуляции)
#   .\um_emul.ps1 -Action run  -WaitSec 12 -Out r.txt   # войти, подождать, прочитать всё, выйти
#   .\um_emul.ps1 -Action read -Out r.txt               # прочитать словарь, не трогая режим
#   .\um_emul.ps1 -Action set  -Name r_sp -Value 2.5    # записать значение (в эмуляции)
#   .\um_emul.ps1 -Action toggle                        # вход/выход из эмуляции
#
# Что важно знать (проверено 2026-09-19):
#  * Дерево и таблица словаря в UIA — это Grid. GridPattern.GetItem(строка, колонка)
#    отдаёт ИМЯ любой строки, даже не отрисованной, но «Значение» (колонка 2)
#    приходит ТОЛЬКО у строк, которые сейчас на экране. Поэтому read листает
#    таблицу клавишей {PGDN} и склеивает страницы. Без этого дальние переменные
#    молча читаются как 0 — легко принять за неработающую программу.
#  * Редакторы открывать ДО входа в эмуляцию: в эмуляции дерево заблокировано.
#  * Опрашивать не чаще раза в 2 с: IDE уже падала на частом опросе.
param(
    [ValidateSet('dict', 'run', 'read', 'set', 'toggle')][string]$Action = 'run',
    [string]$Prog = '',
    [int]$WaitSec = 10,
    [string]$Out = 'emul.txt',
    [int]$Pages = 8,
    [string]$Name = '',
    [string]$Value = ''
)
. "$PSScriptRoot\ui_lib.ps1"

function Get-UmTree([int]$MinX) {
    $t = @(Get-UmAllElements -MaxDepth 12 | Where-Object {
            $_.Type -eq 'Tree' -and $_.X -gt $MinX -and $_.H -gt 300 })[0]
    if (-not $t) { throw 'дерево/таблица не найдены' }
    return @{ El = $t; G = $t.Element.GetCurrentPattern([System.Windows.Automation.GridPattern]::Pattern) }
}

function Open-UmProgDict([string]$Prog) {
    Show-UmWindow | Out-Null
    Start-Sleep -Milliseconds 400
    $d = Get-UmTree 0
    $g = $d.G
    function Row([string]$name, [int]$maxX, [int]$from) {
        for ($r = $from; $r -lt $g.Current.RowCount; $r++) {
            $it = $g.GetItem($r, 0)
            # регистр важен: вывод ФБ «T1» не должен сойти за программу «t1»
            if (($it.Current.Name -ceq $name) -and ($it.Current.BoundingRectangle.X -lt $maxX)) { return $r }
        }
        return -1
    }
    function ExpandRow([int]$r) {
        $b = $g.GetItem($r, 0).Current.BoundingRectangle
        Invoke-UmClick -X ([int]($b.X + 40)) -Y ([int]($b.Y + $b.Height / 2)) -SleepMs 350
        Send-UmKeys "{RIGHT}" 700
    }
    ExpandRow 0
    $r = Row 'Задачи' 4000 0;  if ($r -lt 0) { throw 'нет узла «Задачи»' }
    ExpandRow $r
    $r = Row 'main' 4000 0;    if ($r -lt 0) { throw 'нет узла «main»' }
    ExpandRow $r
    $rp = Row $Prog 300 0;     if ($rp -lt 0) { throw "программа $Prog не найдена" }
    ExpandRow $rp
    $rd = Row 'Локальный словарь' 4000 $rp
    if ($rd -lt 0) { throw 'нет узла «Локальный словарь»' }
    $b = $g.GetItem($rd, 0).Current.BoundingRectangle
    $x = [int]($b.X + 40); $y = [int]($b.Y + $b.Height / 2)
    [UmNative]::SetCursorPos($x, $y) | Out-Null; Start-Sleep -Milliseconds 150
    [UmNative]::mouse_event(0x0002, 0, 0, 0, [IntPtr]::Zero); [UmNative]::mouse_event(0x0004, 0, 0, 0, [IntPtr]::Zero)
    Start-Sleep -Milliseconds 90
    [UmNative]::mouse_event(0x0002, 0, 0, 0, [IntPtr]::Zero); [UmNative]::mouse_event(0x0004, 0, 0, 0, [IntPtr]::Zero)
    Start-Sleep -Seconds 3
    return $rd
}

function Get-UmEmulButton {
    $e = @(Get-UmAllElements -MaxDepth 12 | Where-Object { $_.Type -eq 'CheckBox' -and $_.Name -match 'Эмуляция' })[0]
    if (-not $e) { throw 'кнопка «Эмуляция» не найдена' }
    return $e
}

function Switch-UmEmul {
    # TogglePattern только читаем: переключать — кликом по кнопке панели режимов
    $e = Get-UmEmulButton
    Invoke-UmClick -X ([int]($e.X + $e.W / 2)) -Y ([int]($e.Y + 18)) -SleepMs 5000
    return (Get-UmEmulButton).Element.GetCurrentPattern(
        [System.Windows.Automation.TogglePattern]::Pattern).Current.ToggleState
}

function Read-UmDict([int]$Pages = 8) {
    $d = Get-UmTree 600
    $g = $d.G
    $rowCount = $g.Current.RowCount
    $b = $g.GetItem(0, 0).Current.BoundingRectangle
    Invoke-UmClick -X ([int]($b.X + 40)) -Y ([int]($b.Y + $b.Height / 2)) -SleepMs 500
    Send-UmKeys "{HOME}" 500
    $vals = @{}
    for ($p = 0; $p -lt $Pages; $p++) {
        for ($r = 0; $r -lt $rowCount; $r++) {
            $v = $g.GetItem($r, 2).Current.Name
            if ($v -ne '') { $vals[$g.GetItem($r, 0).Current.Name] = $v }
        }
        if ($vals.Count -ge $rowCount) { break }
        Send-UmKeys "{PGDN}" 700
    }
    $res = [ordered]@{}
    for ($r = 0; $r -lt $rowCount; $r++) {
        $k = $g.GetItem($r, 0).Current.Name
        $res[$k] = $vals[$k]
    }
    return $res
}

function Set-UmDictValue([string]$Name, [string]$Value) {
    # ячейка «Значение» — единственная, где работает ValuePattern.SetValue
    $d = Get-UmTree 600
    $g = $d.G
    for ($r = 0; $r -lt $g.Current.RowCount; $r++) {
        if ($g.GetItem($r, 0).Current.Name -ceq $Name) {
            $cell = $g.GetItem($r, 2)
            try { $cell.GetCurrentPattern([System.Windows.Automation.ScrollItemPattern]::Pattern).ScrollIntoView() } catch { }
            $cell.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue($Value)
            Start-Sleep -Milliseconds 800
            return $g.GetItem($r, 2).Current.Name
        }
    }
    throw "переменной $Name в словаре нет"
}

switch ($Action) {
    'dict' {
        if (-not $Prog) { throw 'нужен -Prog' }
        $r = Open-UmProgDict $Prog
        "словарь ${Prog}: строка дерева $r"
    }
    'toggle' { "эмуляция: " + (Switch-UmEmul) }
    'read' {
        $v = Read-UmDict $Pages
        $lines = @(); foreach ($k in $v.Keys) { $lines += ("{0}={1}" -f $k, $v[$k]) }
        $lines | Out-File -FilePath $Out -Encoding utf8
        "строк: $($v.Count) -> $Out"
    }
    'set' {
        if (-not $Name) { throw 'нужен -Name' }
        "$Name = " + (Set-UmDictValue $Name $Value)
    }
    'run' {
        if ($Prog) { Open-UmProgDict $Prog | Out-Null }
        "эмуляция: " + (Switch-UmEmul)
        Start-Sleep -Seconds $WaitSec
        $v = Read-UmDict $Pages
        $lines = @(); foreach ($k in $v.Keys) { $lines += ("{0}={1}" -f $k, $v[$k]) }
        $lines | Out-File -FilePath $Out -Encoding utf8
        "строк: $($v.Count) -> $Out"
        Start-Sleep -Seconds 3
        "выход из эмуляции: " + (Switch-UmEmul)
    }
}
