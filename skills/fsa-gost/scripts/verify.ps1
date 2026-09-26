# Проверка готовой ФСА: размеры приборов, состав контуров, приклейка линий.
param([string]$Dir = (Get-Location).Path, [string]$Name = 'ФСА_новая')
$ErrorActionPreference = 'Stop'
[Threading.Thread]::CurrentThread.CurrentCulture = 'en-US'
$dir = $Dir
function mmv($c) { [math]::Round($c.ResultIU * 25.4, 2) }
$app = New-Object -ComObject Visio.InvisibleApp
try {
    $st = $app.Documents.OpenEx("$dir\ГОСТ_21.208_КИП.vssx", 2)
    'Трафарет: ' + (($st.Masters | ForEach-Object { $_.NameU }) -join ', ')
    $doc = $app.Documents.OpenEx("$dir\$Name.vsdx", 2)
    $pg = $doc.Pages.ItemU('ФСА')
    'Слои: ' + (($pg.Layers | ForEach-Object { $_.Name }) -join ', ')
    $loops = @{}; $bad = @(); $glued = 0; $lines = 0; $fail = @()
    foreach ($s in $pg.Shapes) {
        if ($s.Master) {
            $n = $s.Master.NameU
            if ($n -like 'Прибор*' -and -not $s.CellExistsU('User.Ref', 0)) {
                $w = mmv $s.CellsU('Width'); $h = mmv $s.CellsU('Height')
                if (($n -eq 'Прибор на щите (прямоугольник)' -and ($w -ne 18 -or $h -ne 10)) -or ($n -ne 'Прибор на щите (прямоугольник)' -and ($w -ne 10 -or $h -ne 10))) { $bad += "$($s.ID) $w x $h" }
                $loops[$s.CellsU('Prop.Loop').ResultStr('')] += @($s.CellsU('Prop.Letters').ResultStr('') + ' ' + $s.CellsU('Prop.Pos').ResultStr(''))
            }
            if ($n -eq 'Клапан регулирующий с ИМ') {
                $loops[$s.CellsU('Prop.Loop').ResultStr('')] += @('ИМ ' + $s.CellsU('Prop.Pos').ResultStr(''))
            }
        }
        if ($s.OneD -and $s.Connects.Count -gt 0) { $lines++; if ($s.Connects.Count -eq 2) { $glued++ } }
    }
    foreach ($k in ($loops.Keys | Sort-Object)) { "Контур ${k}: " + ($loops[$k] -join ', ') }
    'Размеры приборов вне ГОСТ: ' + $(if ($bad) { $bad -join '; ' } else { 'нет' })
    "Линии связи с приклейкой: $lines, приклеены обоими концами: $glued"
    $doc.Close(); $st.Close()
} finally { $app.Quit() }
