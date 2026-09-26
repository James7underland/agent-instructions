param([string]$Dir = (Get-Location).Path, [string]$Name = 'ФСА_новая')
$app = New-Object -ComObject Visio.InvisibleApp
try {
    $doc = $app.Documents.OpenEx("$Dir\$Name.vsdx", 2)
    $pg = $doc.Pages.ItemU('ФСА')
    $w = @{}
    foreach ($s in $pg.Shapes) {
        $k = if ($s.Master) { $s.Master.NameU } elseif ($s.OneD) { '1D:' + '' } else { '2D' }
    }
    foreach ($s in $pg.Shapes) {
        if ($s.OneD -and $s.LayerCount -gt 0) { $key = $s.Layer(1).Name + ' ' + $s.CellsU('LineWeight').FormulaU; $w[$key] = 1 + [int]$w[$key] }
    }
    $w.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Name): $($_.Value)" }
    foreach ($s in $pg.Shapes) { if ($s.Master -and $s.Master.NameU -eq 'Клапан регулирующий с ИМ') { $sub = $s.Shapes.Item(2); "stem " + $s.CellsU('Prop.Pos').ResultStr('') + " = " + [math]::Round($sub.CellsU('Width').ResultIU * 25.4, 2) + " mm, angle " + $s.CellsU('Angle').ResultStr('deg'); break } }
    $doc.Close()
} finally { $app.Quit() }
