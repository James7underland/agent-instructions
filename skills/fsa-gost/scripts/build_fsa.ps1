# Сборка ФСА в Visio по layout.json (эталон — установка ректификации).
# Обозначения: ГОСТ 21.208-2013; правила выполнения схемы: ГОСТ 21.408-2013.
# Запуск: powershell -ExecutionPolicy Bypass -File build_fsa.ps1 -LayoutFile <layout.json> -OutDir <папка> -Name <имя> -Title <название>
# Файл хранить в UTF-8 с BOM (иначе PowerShell 5.1 портит кириллицу).
param(
    [string]$LayoutFile = (Join-Path (Get-Location) 'layout.json'),
    [string]$Frame  = '<work_dir>\Документ1.vsdx',   # A3-рамка со штампом (стр. 2), исходник не меняется
    [string]$OutDir = '<work_dir>\ФСА',
    [string]$Name   = 'ФСА_новая',
    [string]$Title  = 'Установка',
    [string]$Code   = 'ФСА-01-АТХ'       # обозначение документа в штампе
)
$ErrorActionPreference = 'Stop'
[Threading.Thread]::CurrentThread.CurrentCulture = 'en-US'
Add-Type -Path (Get-ChildItem C:\Windows\assembly\GAC_MSIL\Microsoft.Office.Interop.Visio -Recurse -Filter *.dll | Select-Object -First 1).FullName

$srcDoc  = $Frame
$outDir  = $OutDir
$outVsdx = "$outDir\$Name.vsdx"
$outVssx = "$outDir\ГОСТ_21.208_КИП.vssx"
$outPdf  = "$outDir\$Name.pdf"
$LAYOUT = [IO.File]::ReadAllText($LayoutFile, [Text.Encoding]::UTF8) | ConvertFrom-Json

# ---------------------------------------------------------------- helpers
function mm([double]$v) { $v / 25.4 }
function F($s, $cell, $f) { $s.CellsU($cell).FormulaU = [string]$f }
function Q($t) { '"' + ($t -replace '"', '""') + '"' }
function Arr($pts) { $a = New-Object 'double[]' ($pts.Count * 2); for ($i = 0; $i -lt $pts.Count; $i++) { $a[2 * $i] = [double]$pts[$i][0] / 25.4; $a[2 * $i + 1] = [double]$pts[$i][1] / 25.4 }; , $a }
function Style($s, [double]$lw = 0.25, [int]$pat = 1, [string]$fill = 'none') {
    $lwf = if ($lw -ge 0.35) { '1.5 pt' } elseif ($lw -ge 0.2) { '0.75 pt' } else { "$lw mm" }
    F $s 'LineWeight' $lwf; F $s 'LinePattern' $pat; F $s 'LineColor' 'RGB(0,0,0)'; F $s 'LineCap' 0
    switch ($fill) {
        'white' { F $s 'FillPattern' 1; F $s 'FillForegnd' 'RGB(255,255,255)' }
        'black' { F $s 'FillPattern' 1; F $s 'FillForegnd' 'RGB(0,0,0)' }
        default { F $s 'FillPattern' 0 }
    }
    F $s 'ShdwPattern' 0
}
function TextFmt($s, [double]$size = 3.5, [int]$halign = 1) {
    F $s 'Char.Size' "$size mm"; F $s 'Char.Font' $script:arial; F $s 'Char.Color' 'RGB(0,0,0)'
    F $s 'Para.HorzAlign' $halign
    F $s 'LeftMargin' '0 mm'; F $s 'RightMargin' '0 mm'; F $s 'TopMargin' '0 mm'; F $s 'BottomMargin' '0 mm'
}
function EnsureSection($s, [int]$sec) { if (-not $s.SectionExists($sec, 0)) { $s.AddSection($sec) | Out-Null } }
function AddProp($s, $name, $label, $value, [int]$type = 0, $format = '') {
    EnsureSection $s 243
    $s.AddNamedRow(243, $name, 0) | Out-Null
    F $s "Prop.$name.Label" (Q $label); F $s "Prop.$name.Type" $type
    if ($format) { F $s "Prop.$name.Format" (Q $format) }
    F $s "Prop.$name" (Q $value)
}
function AddUser($s, $name, $formula) { EnsureSection $s 242; $s.AddNamedRow(242, $name, 0) | Out-Null; F $s "User.$name" $formula }
function AddAction($s, $name, $menu, $action, $checked) {
    EnsureSection $s 240
    $s.AddNamedRow(240, $name, 0) | Out-Null
    F $s "Actions.$name.Action" $action; F $s "Actions.$name.Menu" (Q $menu)
    if ($checked) { F $s "Actions.$name.Checked" $checked }
}
function AddCnx($s, $pts) {
    EnsureSection $s 7
    foreach ($p in $pts) { $r = $s.AddRow(7, -2, 153); $s.CellsSRC(7, $r, 0).FormulaU = $p[0]; $s.CellsSRC(7, $r, 1).FormulaU = $p[1] }
}
function SetFieldText($s, $template, $fields) {
    $s.Text = $template
    for ($i = $fields.Count - 1; $i -ge 0; $i--) {
        $pos = $template.IndexOf([string][char](0x2460 + $i))
        $ch = $s.Characters; $ch.Begin = $pos; $ch.End = $pos + 1
        $ch.AddCustomFieldU($fields[$i], 37)
    }
}
function GroupOf($page, $shapes) { $sel = $page.CreateSelection(0); foreach ($x in $shapes) { $sel.Select($x, 2) }; $sel.Group() }

# ---------------------------------------------------------------- start
foreach ($f in $outVsdx, $outVssx, $outPdf) { if (Test-Path $f) { Remove-Item $f -Force } }
Copy-Item $srcDoc $outVsdx

$app = New-Object -ComObject Visio.InvisibleApp
$app.AlertResponse = 1
try {
# ================================================================ ТРАФАРЕТ ГОСТ 21.208-2013
$tmp = $app.Documents.Add('')
$tp  = $tmp.Pages.Item(1)
$script:arial = $tmp.Fonts.Item('Arial').ID
$stn = $app.Documents.AddEx('', 1, 512, 0)
function Publish($shape, $name, $prompt) {
    $m = $stn.Masters.Drop($shape, 0, 0)
    $m.Name = $name; $m.NameU = $name; $m.Prompt = $prompt; $m.IconUpdate = 1
    $shape.Delete(); $m
}
function InstrumentProps($g, $loc) {
    AddProp $g 'Letters'  'Буквенное обозначение'   'FT'
    AddProp $g 'Pos'      'Позиционное обозначение' '1-2'
    AddProp $g 'Loop'     'Номер контура'           '1'
    AddProp $g 'Param'    'Параметр'                ''
    AddProp $g 'Location' 'Место установки'         $loc 1 'По месту;На щите'
    AddProp $g 'Note'     'Доп. обозначение справа (H, L, I/P)' ''
    AddProp $g 'Device'   'Наименование'            ''
    AddAction $g 'Field' 'Прибор по месту' ('SETF(GetRef(Prop.Location),' + (Q (Q 'По месту')) + ')') ('STRSAME(Prop.Location,' + (Q 'По месту') + ')')
    AddAction $g 'Panel' 'Прибор на щите'  ('SETF(GetRef(Prop.Location),' + (Q (Q 'На щите')) + ')')  ('STRSAME(Prop.Location,' + (Q 'На щите') + ')')
}
# Прибор: круг Ø10 (табл. 1, 3 ГОСТ 21.208) или прямоугольник 18x10 (допускаемое обозначение)
function New-Instrument($name, $loc, [double]$w) {
    if ($w -eq 10) { $body = $tp.DrawOval((mm 0), (mm 0), (mm 10), (mm 10)) } else { $body = $tp.DrawRectangle((mm 0), (mm 0), (mm $w), (mm 10)) }
    Style $body 0.5 1 'white'
    $ln = $tp.DrawLine((mm 0), (mm 5), (mm $w), (mm 5)); Style $ln 0.25 1
    $nt = $tp.DrawRectangle((mm ($w / 2 - 0.5)), (mm 4.5), (mm ($w / 2 + 0.5)), (mm 5.5)); Style $nt 0.25 0; F $nt 'LinePattern' 0
    $g = GroupOf $tp @($body, $ln, $nt)
    InstrumentProps $g $loc
    F $ln 'Geometry1.NoShow' ('STRSAME(Sheet.' + $g.ID + '!Prop.Location,' + (Q 'По месту') + ')')
    # дополнительное обозначение справа от прибора (п. 5.11.7, табл. А.1 ГОСТ 21.208)
    SetFieldText $nt '①' @("Sheet.$($g.ID)!Prop.Note")
    TextFmt $nt 2.5 0
    F $nt 'Width' 'TEXTWIDTH(TheText)'; F $nt 'Height' '3 mm'; F $nt 'LocPinX' '0 mm'
    F $nt 'PinX' "Sheet.$($g.ID)!Width+0.8 mm"; F $nt 'PinY' "Sheet.$($g.ID)!Height*0.8"
    SetFieldText $g "①`n②" @('Prop.Letters', 'Prop.Pos')
    TextFmt $g 3.5 1
    F $g 'LockAspect' 1; F $g 'SelectMode' 0
    F $g 'TxtWidth' "$w mm"; F $g 'TxtHeight' '10 mm'; F $g 'TxtPinX' "$($w/2) mm"; F $g 'TxtPinY' '5 mm'
    $hw = $w / 2; $dx = if ($w -eq 10) { 0.433 * 10 } else { $hw }
    AddCnx $g @(@('Width*0.5', 'Height'), @('Width*0.5', '0'), @('0', 'Height*0.5'), @('Width', 'Height*0.5'),
                @("Width*0.5-$dx mm", 'Height*0.75'), @("Width*0.5+$dx mm", 'Height*0.75'), @("Width*0.5-$dx mm", 'Height*0.25'), @("Width*0.5+$dx mm", 'Height*0.25'))
    Publish $g $name "Прибор по ГОСТ 21.208-2013. Место установки: $loc"
}
$M = @{}
$M.field = New-Instrument 'Прибор по месту' 'По месту' 10
$M.panel = New-Instrument 'Прибор на щите' 'На щите' 10
$M.ctrl  = New-Instrument 'Прибор на щите (прямоугольник)' 'На щите' 18

# Регулирующий орган с электрическим ИМ: круг Ø5 на штоке 5 мм
$bt = $tp.DrawPolyline((Arr @(@(0, 0), @(7, 3.5), @(7, 0), @(0, 3.5), @(0, 0))), 0); Style $bt 0.35 1 'white'
$st = $tp.DrawLine((mm 3.5), (mm 1.75), (mm 3.5), (mm 6.75)); Style $st 0.35 1
$ac = $tp.DrawOval((mm 1), (mm 6.75), (mm 6), (mm 11.75)); Style $ac 0.5 1 'white'
$g = GroupOf $tp @($bt, $st, $ac)
F $g 'LocPinY' 'Height*1.75/11.75'
AddProp $g 'Pos'    'Позиционное обозначение' '1-5'
AddProp $g 'Loop'   'Номер контура' '1'
AddProp $g 'Device' 'Наименование' 'Клапан регулирующий с электрическим ИМ'
SetFieldText $g '①' @('Prop.Pos')
TextFmt $g 3.5 0
F $g 'TxtWidth' '8 mm'; F $g 'TxtHeight' '4 mm'; F $g 'TxtPinX' '6.7 mm'; F $g 'TxtPinY' '9.25 mm'
F $g 'TxtLocPinX' '0 mm'; F $g 'TxtLocPinY' 'TxtHeight*0.5'; F $g 'TxtAngle' '-Angle'
F $g 'SelectMode' 0
AddCnx $g @(@('0', '1.75 mm'), @('Width', '1.75 mm'), @('Width*0.5', '0'), @('Width*0.5', 'Height'), @('1 mm', '9.25 mm'), @('6 mm', '9.25 mm'))
AddAction $g 'Down' 'ИМ снизу (повернуть на 180°)' 'SETF(GetRef(Angle),IF(Angle=0 deg,180 deg,0 deg))' 'Angle=180 deg'
$M.valve = Publish $g 'Клапан регулирующий с ИМ' 'Регулирующий орган с электрическим ИМ (круг Ø5 на штоке 5 мм); ИМ можно развернуть вниз'

# Насос центробежный
$c = $tp.DrawOval((mm 0), (mm 0), (mm 12), (mm 12)); Style $c 0.35 1 'white'
$n = $tp.DrawLine((mm 6), (mm 12), (mm 12), (mm 12)); Style $n 0.35 1
$g = GroupOf $tp @($c, $n)
AddProp $g 'Pos' 'Позиция' 'Н-1'; AddProp $g 'Device' 'Наименование' 'Насос центробежный'
SetFieldText $g '①' @('Prop.Pos'); TextFmt $g 3.5 1
F $g 'TxtPinY' '6 mm'; F $g 'TxtHeight' '5 mm'; F $g 'TxtWidth' '11 mm'; F $g 'SelectMode' 0
AddCnx $g @(@('0', '6 mm'), @('Width', 'Height'), @('Width*0.5', '0'))
$M.pump = Publish $g 'Насос центробежный' 'Насос центробежный'

# Теплообменник (ГОСТ 2.789)
$c = $tp.DrawOval((mm 0), (mm 0), (mm 16), (mm 16)); Style $c 0.35 1 'white'
# теплоноситель — «молния»: диагональ снизу слева вверх вправо с горизонтальным изломом в центре, концы на окружности
$z = $tp.DrawPolyline((Arr @(@(4.174, 0.974), @(11.2, 8), @(4.8, 8), @(11.826, 15.026))), 0); Style $z 0.35 1
$g = GroupOf $tp @($c, $z)
AddProp $g 'Pos' 'Позиция' 'Т-2'; AddProp $g 'Device' 'Наименование' 'Теплообменный аппарат'
SetFieldText $g '①' @('Prop.Pos'); TextFmt $g 3.5 1
F $g 'TxtWidth' '12 mm'; F $g 'TxtHeight' '5 mm'; F $g 'TxtPinY' 'Height+3 mm'; F $g 'SelectMode' 0
AddCnx $g @(@('0', 'Height*0.5'), @('Width', 'Height*0.5'), @('4.174 mm', '0.974 mm'), @('11.826 mm', '15.026 mm'))
$M.hex = Publish $g 'Теплообменник' 'Теплообменный аппарат (ГОСТ 2.789-74)'

function Set-Geometry($s, $rows) {
    $s.DeleteSection(10); $sec = $s.AddSection(10); $s.AddRow($sec, 0, 137) | Out-Null
    for ($i = 0; $i -lt $rows.Count; $i++) {
        $r = $rows[$i]; $s.AddRow($sec, $i + 1, $r[0]) | Out-Null
        for ($j = 1; $j -lt $r.Count; $j++) { $s.CellsSRC($sec, $i + 1, $j - 1).FormulaU = $r[$j] }
    }
}
$col = $tp.DrawRectangle((mm 0), (mm 0), (mm 20), (mm 80))
Set-Geometry $col @(@(138, '0', 'Width*0.25'), @(139, '0', 'Height-Width*0.25'), @(144, 'Width', 'Height-Width*0.25', 'Width*0.5', 'Height', '0 deg', '2'), @(139, 'Width', 'Width*0.25'), @(144, '0', 'Width*0.25', 'Width*0.5', '0', '0 deg', '2'))
Style $col 0.35 1 'white'
AddProp $col 'Pos' 'Позиция' 'К-3'; AddProp $col 'Device' 'Наименование' 'Колонна ректификационная'
SetFieldText $col '①' @('Prop.Pos'); TextFmt $col 3.5 1
F $col 'TxtPinY' 'Height*0.55'; F $col 'TxtHeight' '6 mm'
$M.column = Publish $col 'Колонна' 'Колонный аппарат с эллиптическими днищами (ГОСТ 2.790)'

$drum = $tp.DrawRectangle((mm 0), (mm 0), (mm 40), (mm 16))
Set-Geometry $drum @(@(138, 'Height*0.25', '0'), @(139, 'Width-Height*0.25', '0'), @(144, 'Width-Height*0.25', 'Height', 'Width', 'Height*0.5', '90 deg', '2'), @(139, 'Height*0.25', 'Height'), @(144, 'Height*0.25', '0', '0', 'Height*0.5', '90 deg', '2'))
Style $drum 0.35 1 'white'
AddProp $drum 'Pos' 'Позиция' 'Е-5'; AddProp $drum 'Device' 'Наименование' 'Емкость орошения'
SetFieldText $drum '①' @('Prop.Pos'); TextFmt $drum 3.5 1
$M.drum = Publish $drum 'Емкость горизонтальная' 'Горизонтальная емкость (емкость орошения)'

$r = $tp.DrawRectangle((mm 0), (mm 0), (mm 26), (mm 12)); Style $r 0.35 1 'white'
$u = $tp.DrawPolyline((Arr @(@(4, 8.5), @(21, 8.5), @(21, 3.5), @(4, 3.5))), 0); Style $u 0.25 1
$tsh = $tp.DrawLine((mm 4), (mm 1.5), (mm 4), (mm 10.5)); Style $tsh 0.25 1
$g = GroupOf $tp @($r, $u, $tsh)
AddProp $g 'Pos' 'Позиция' 'И-7'; AddProp $g 'Device' 'Наименование' 'Испаритель (кипятильник) с паровым обогревом'
SetFieldText $g '①' @('Prop.Pos'); TextFmt $g 3.5 1
F $g 'TxtHeight' '5 mm'; F $g 'SelectMode' 0
$M.reb = Publish $g 'Испаритель' 'Испаритель (кипятильник) колонны'

$nb = $tp.DrawRectangle((mm 0), (mm 0), (mm 6), (mm 4)); Style $nb 0.25 0; F $nb 'LinePattern' 0
AddProp $nb 'N' 'Номер обрыва' '1'
SetFieldText $nb '①' @('Prop.N'); TextFmt $nb 3.5 1
AddCnx $nb @(@('Width*0.5', 'Height'), @('Width*0.5', '0'), @('0', 'Height*0.5'), @('Width', 'Height*0.5'))
$M.num = Publish $nb 'Номер обрыва' 'Номер места разрыва линии связи (п. 5.3.6.4 ГОСТ 21.408)'

$d = $tp.DrawOval((mm 0), (mm 0), (mm 1.4), (mm 1.4)); Style $d 0.1 1 'black'
$M.dot = Publish $d 'Узел' 'Точка соединения / отметка выполняемой функции'

$stn.Title = 'ГОСТ 21.208-2013 КИПиА'
$stn.SaveAsEx($outVssx, 0)
$tmp.Saved = $true; $tmp.Close()
'stencil ok'

# ================================================================ ДОКУМЕНТ
$doc = $app.Documents.OpenEx($outVsdx, 0)
$script:arial = $doc.Fonts.Item('Arial').ID
$doc.Title = $Title; $doc.Subject = 'Схема автоматизации'
$doc.Keywords = 'ФСА; ГОСТ 21.208-2013; ГОСТ 21.408-2013'
$bg = $null; $a4 = $null
foreach ($p in $doc.Pages) { if ($p.PageSheet.CellsU('PageWidth').ResultIU -gt 15) { $bg = $p } else { $a4 = $p } }
$a4.Delete(1)
$bg.Name = 'Рамка А3'; $bg.Background = 1
$lf = $bg.Layers.Add('Рамка'); foreach ($s in $bg.Shapes) { $lf.Add($s, 0) }

$pg = $doc.Pages.Add(); $pg.Name = 'ФСА'
F $pg.PageSheet 'PageWidth' '420 mm'; F $pg.PageSheet 'PageHeight' '297 mm'
F $pg.PageSheet 'PageScale' '1 mm'; F $pg.PageSheet 'DrawingScale' '1 mm'
F $pg.PageSheet 'PrintPageOrientation' 2; F $pg.PageSheet 'LineJumpCode' 0
$pg.BackPage = 'Рамка А3'

$layers = @{}
function Lay($name) { if (-not $layers.ContainsKey($name)) { $layers[$name] = $pg.Layers.Add($name) }; $layers[$name] }
function ToLay($s, $name) { if ($name) { (Lay $name).Add($s, 0) } }
function DropAt($m, [double]$x, [double]$y) { $pg.Drop($m, (mm $x), (mm $y)) }
function Label([double]$x, [double]$y, [string]$text, [double]$size = 3.5, [string]$align = 'l', [double]$angle = 0, $layer = 'Надписи') {
    $s = $pg.DrawRectangle((mm $x), (mm $y), (mm ($x + 10)), (mm ($y + 4))); Style $s 0.25 0; F $s 'LinePattern' 0
    $s.Text = $text
    TextFmt $s $size (@{ 'l' = 0; 'c' = 1; 'r' = 2 }[$align])
    F $s 'Width' 'TEXTWIDTH(TheText)'; F $s 'Height' 'TEXTHEIGHT(TheText,Width)'
    F $s 'LocPinX' ('Width*' + @{ 'l' = '0'; 'c' = '0.5'; 'r' = '1' }[$align]); F $s 'LocPinY' 'Height*0.5'
    F $s 'PinX' "$x mm"; F $s 'PinY' "$y mm"
    if ($angle) { F $s 'Angle' "$angle deg" }
    F $s 'ObjType' 4; ToLay $s $layer; $s
}
function Poly($pts, [double]$lw, [int]$pat, [bool]$arrow, $layer) {
    if ($pts.Count -eq 2) { $s = $pg.DrawLine((mm $pts[0][0]), (mm $pts[0][1]), (mm $pts[1][0]), (mm $pts[1][1])) }
    else { $s = $pg.DrawPolyline((Arr $pts), 8) }
    Style $s $lw $pat
    if ($arrow) { F $s 'EndArrow' 13; F $s 'EndArrowSize' 1 }
    F $s 'ObjType' 4; ToLay $s $layer; $s
}

# ================================================================ ПОДВАЛ (ГОСТ 21.408 + форма по заданию)
$pv = $LAYOUT.podval
$pvShapes = @()
$y0 = ($pv.rows | ForEach-Object { $_.y1 } | Measure-Object -Minimum).Minimum
$y1 = ($pv.rows | ForEach-Object { $_.y2 } | Measure-Object -Maximum).Maximum
$pvBox = $pg.DrawRectangle((mm $pv.x0), (mm $y0), (mm $pv.x1), (mm $y1)); Style $pvBox 0.5 1
AddUser $pvBox 'msvStructureType' (Q 'Container'); AddUser $pvBox 'msvSDContainerResize' '0'; AddUser $pvBox 'msvSDContainerMargin' '0 mm'
AddProp $pvBox 'Title' 'Заголовок' 'Подвал схемы: функции контуров'
F $pvBox 'ObjType' 4; ToLay $pvBox 'Подвал'
foreach ($r in $pv.rows) {
    $inner = $r.group -and ($pv.rows | Where-Object { $_.group -eq $r.group -and $_.y2 -eq $r.y1 })
    if ($r.y1 -gt $y0) { $pvShapes += Poly @(@($(if ($inner) { $pv.xg } else { $pv.x0 }), $r.y1), @($pv.x1, $r.y1)) $(if ($r.key -in @('field', 'panel', 'S')) { 0.5 } else { 0.25 }) 1 $false 'Подвал' }
    if ($r.group) { $pvShapes += Label ($pv.xg + 1.5) (($r.y1 + $r.y2) / 2) $r.title 3.2 'l' 0 'Подвал' }
    else { $pvShapes += Label (($pv.x0 + $pv.xf) / 2) (($r.y1 + $r.y2) / 2) $r.title 3.2 'c' 0 'Подвал' }
}
$pvShapes += Poly @(@($pv.xf, $y0), @($pv.xf, $y1)) 0.5 1 $false 'Подвал'
foreach ($grp in 'ПЛК', 'АРМ') {
    $gr = $pv.rows | Where-Object { $_.group -eq $grp }
    $gy0 = ($gr | ForEach-Object { $_.y1 } | Measure-Object -Minimum).Minimum; $gy1 = ($gr | ForEach-Object { $_.y2 } | Measure-Object -Maximum).Maximum
    $pvShapes += Poly @(@($pv.xg, $gy0), @($pv.xg, $gy1)) 0.5 1 $false 'Подвал'
    $pvShapes += Label (($pv.x0 + $pv.xg) / 2) (($gy0 + $gy1) / 2) $grp 3.5 'c' 90 'Подвал'
}
foreach ($l in $pv.lines) { $pvShapes += Poly $l.pts 0.25 1 $false 'Подвал' }
foreach ($a in $pv.arrows) { $pvShapes += Poly $a.pts 0.25 1 $true 'Подвал' }
foreach ($d in $pv.dots) { $s = DropAt $M.dot $d[0] $d[1]; F $s 'Width' '1.8 mm'; F $s 'Height' '1.8 mm'; ToLay $s 'Подвал'; $pvShapes += $s }
foreach ($t in $pv.texts) { $pvShapes += Label $t.x $t.y $t.text $t.size $t.align 0 'Подвал' }

# ================================================================ ТЕХНОЛОГИЯ
foreach ($p in $LAYOUT.pipes) { Poly $p.pts $p.lw 1 $p.arrow 'Трубопроводы' | Out-Null }
foreach ($p in $LAYOUT.plines) { Poly $p.pts 0.25 1 $false 'Линии связи' | Out-Null }

$SH = @{}
$angles = @{ up = 0; left = 90; down = 180; right = 270 }
foreach ($o in $LAYOUT.symbols) {
    $loopLayer = if ($o.loop) { "Контур $($o.loop)" } else { $null }
    switch ($o.t) {
        { $_ -in 'field', 'panel', 'ctrl' } {
            $s = DropAt $M[$o.t] $o.x $o.y
            F $s 'Prop.Letters' (Q $o.letters); F $s 'Prop.Pos' (Q $o.pos); F $s 'Prop.Loop' (Q "$($o.loop)")
            F $s 'Prop.Param' (Q $o.param); F $s 'Prop.Device' (Q $o.device); F $s 'Prop.Note' (Q $o.note)
            if ($o.npos -eq 'd') { $sub = $s.Shapes.Item(3); F $sub 'PinY' ('Sheet.' + $s.ID + '!Height*0.2') }
            if ($o.podval) { AddUser $s 'Ref' '1'; ToLay $s 'Подвал'; $pvShapes += $s } else { ToLay $s 'КИП'; ToLay $s $loopLayer }
        }
        'valve' {
            $s = DropAt $M.valve $o.x $o.y
            F $s 'Prop.Pos' (Q $o.pos); F $s 'Prop.Loop' (Q "$($o.loop)")
            $th = $angles[$o.act]
            if ($th) { F $s 'Angle' "$th deg" }
            # подпись позиции - справа от ИМ на листе; перевод в локальные координаты фигуры
            $t = $th * [Math]::PI / 180
            $ax = -7.5 * [Math]::Sin($t); $ay = 7.5 * [Math]::Cos($t)
            $px = $ax + 3.2; $py = $ay
            if ($th -eq 90 -or $th -eq 270) { $px = $ax - 3; $py = $ay - 4.8 }
            if ($o.pos_side -eq 'l' -and $th % 180 -eq 0) { $px = $ax - 3.2; F $s 'TxtLocPinX' 'TxtWidth'; F $s 'Para.HorzAlign' 2 }
            $lx = $px * [Math]::Cos($t) + $py * [Math]::Sin($t); $ly = - $px * [Math]::Sin($t) + $py * [Math]::Cos($t)
            F $s 'TxtPinX' "$([Math]::Round($lx + 3.5, 3)) mm"; F $s 'TxtPinY' "$([Math]::Round($ly + 1.75, 3)) mm"
            ToLay $s 'Регулирующие органы'; ToLay $s $loopLayer
        }
        'num' {
            $s = DropAt $M.num $o.x $o.y; F $s 'Prop.N' (Q "$($o.n)")
            if ($o.podval) { ToLay $s 'Подвал'; $pvShapes += $s } else { ToLay $s 'Линии связи' }
        }
        default {
            $mst = @{ pump = $M.pump; hex = $M.hex; column = $M.column; drum = $M.drum; reb = $M.reb }[$o.t]
            $s = DropAt $mst $o.x $o.y; F $s 'Prop.Pos' (Q $o.pos)
            if ($o.w) { F $s 'Width' "$($o.w) mm"; F $s 'Height' "$($o.h) mm" }
            if ($o.flipx) { F $s 'FlipX' 1 }
            if ($o.txt) { F $s 'TxtPinX' "Width*0.5+$($o.txt[0]) mm"; F $s 'TxtPinY' "Height*0.5+$($o.txt[1]) mm" }
            ToLay $s 'Оборудование'
        }
    }
    $SH[$o.id] = $s
}
# линии связи: 1-D линии/полилинии, приклеенные к точкам соединения
foreach ($g in $LAYOUT.signals) {
    $pat = 1   # линии контуров - сплошные тонкие
    $isPod = $g.kind -eq 'pod'
    $s = Poly $g.pts 0.25 $pat $false $(if ($isPod) { 'Подвал' } else { 'Линии связи' })
    $s.CellsU('BeginX').GlueTo($SH[$g.a].CellsSRC(7, $g.ai, 0))
    $s.CellsU('EndX').GlueTo($SH[$g.b].CellsSRC(7, $g.bi, 0))
    if ($isPod) { $pvShapes += $s }
    else {
        foreach ($end in $g.a, $g.b) {
            if ($SH[$end].CellExistsU('Prop.Loop', 0)) { ToLay $s ('Контур ' + $SH[$end].CellsU('Prop.Loop').ResultStr('')); break }
        }
    }
}
foreach ($d in $LAYOUT.dots) { $s = DropAt $M.dot $d[0] $d[1]; ToLay $s 'Трубопроводы' }
foreach ($l in $LAYOUT.labels) { Label $l.x $l.y $l.text $l.size $l.align $l.angle $l.layer | Out-Null }
foreach ($x in $pvShapes) { try { $pvBox.ContainerProperties.AddMember($x, 2) } catch {} }
'drawing ok'

# ================================================================ ТАБЛИЦА КОНТУРОВ (из Shape Data)
function CellBox([double]$x1, [double]$y1, [double]$x2, [double]$y2, [string]$text, [double]$size = 3.5, [int]$align = 1, [double]$lw = 0.25) {
    $s = $pg.DrawRectangle((mm $x1), (mm $y1), (mm $x2), (mm $y2)); Style $s $lw 1
    if ($text) { $s.Text = $text }
    TextFmt $s $size $align
    if ($align -eq 0) { F $s 'LeftMargin' '1.5 mm' }
    F $s 'ObjType' 4; $s
}
$info = @{}
foreach ($s in $pg.Shapes) {
    if (-not $s.Master) { continue }
    $mn = $s.Master.NameU
    if ($mn -notlike 'Прибор*' -and $mn -ne 'Клапан регулирующий с ИМ') { continue }
    if ($s.CellExistsU('User.Ref', 0)) { continue }
    $lp = [int]$s.CellsU('Prop.Loop').ResultStr('')
    if (-not $info.ContainsKey($lp)) { $info[$lp] = @{ pos = @(); fn = ''; param = '' } }
    $info[$lp].pos += $s.CellsU('Prop.Pos').ResultStr('')
    if ($mn -eq 'Прибор на щите (прямоугольник)') { $info[$lp].fn = $s.CellsU('Prop.Letters').ResultStr('') }
    if ($mn -like 'Прибор*' -and -not $info[$lp].param) { $info[$lp].param = $s.CellsU('Prop.Param').ResultStr('') }
}
$tx = @(25, 35, 93, 111, 157); $ty = 54.5; $rh = 5.5; $hh = 8
$tbl = @()
$hdrs = @('№', 'Контролируемый (регулируемый) параметр', 'Функции', 'Позиции приборов контура')
for ($i = 0; $i -lt 4; $i++) { $tbl += CellBox $tx[$i] ($ty - $hh) $tx[$i + 1] $ty $hdrs[$i] 3.0 1 }
$yy = $ty - $hh
foreach ($lp in ($info.Keys | Sort-Object)) {
    $d = $info[$lp]
    $posList = ($d.pos | Sort-Object { [int]($_.Split('-')[1]) }) -join ', '
    $tbl += CellBox $tx[0] ($yy - $rh) $tx[1] $yy "$lp" 3.5 1
    $tbl += CellBox $tx[1] ($yy - $rh) $tx[2] $yy $d.param 3.1 0
    $tbl += CellBox $tx[2] ($yy - $rh) $tx[3] $yy $d.fn 3.2 1
    $tbl += CellBox $tx[3] ($yy - $rh) $tx[4] $yy $posList 3.1 0
    $yy -= $rh
}
$frameT = $pg.DrawRectangle((mm $tx[0]), (mm $yy), (mm $tx[4]), (mm $ty)); Style $frameT 0.5 1; F $frameT 'ObjType' 4
$tbl += $frameT
$tbl += Label (($tx[0] + $tx[4]) / 2) ($ty + 3) 'Таблица контуров' 3.5 'c' 0 'Таблица'
$gT = GroupOf $pg $tbl; ToLay $gT 'Таблица'
AddProp $gT 'Info' 'Назначение' 'Таблица контуров, построена по данным фигур (Shape Data)'

# ================================================================ УСЛОВНЫЕ ОБОЗНАЧЕНИЯ
$lx = 162; $leg = @()
$leg += Label 194 57.5 'Условные обозначения' 3.5 'c' 0 'Таблица'
$ly = 50
$items = @('valve|Клапан регулирующий с ИМ', 'pipe|Трубопровод', 'imp|Линия связи',
           'jdot|Соединение линий (место отбора)', 'dot|Функция выполняется', 'arr|Передача регулирующего сигнала')
foreach ($it in $items) {
    $k, $txt = $it.Split('|')
    switch ($k) {
        'pipe' { $leg += Poly @(@($lx, $ly), @(($lx + 12), $ly)) 0.35 1 $true 'Таблица' }
        'imp'  { $leg += Poly @(@($lx, $ly), @(($lx + 12), $ly)) 0.25 1 $false 'Таблица' }
        'jdot' { $l1 = Poly @(@($lx, $ly), @(($lx + 12), $ly)) 0.35 1 $false 'Таблица'; $l2 = Poly @(@(($lx + 6), ($ly + 3)), @(($lx + 6), $ly)) 0.25 1 $false 'Таблица'; $d = DropAt $M.dot ($lx + 6) $ly; $leg += $l1; $leg += $l2; $leg += $d }
        'valve' { $l1 = Poly @(@($lx, $ly), @(($lx + 12), $ly)) 0.35 1 $false 'Таблица'; $vb = Poly @(@(($lx + 3.5), ($ly - 1.25)), @(($lx + 8.5), ($ly + 1.25)), @(($lx + 8.5), ($ly - 1.25)), @(($lx + 3.5), ($ly + 1.25)), @(($lx + 3.5), ($ly - 1.25))) 0.35 1 $false 'Таблица'; Style $vb 0.35 1 'white'; $vs = Poly @(@(($lx + 6), $ly), @(($lx + 6), ($ly + 4))) 0.35 1 $false 'Таблица'; $va = $pg.DrawOval((mm ($lx + 4.75)), (mm ($ly + 4)), (mm ($lx + 7.25)), (mm ($ly + 6.5))); Style $va 0.5 1 'white'; $leg += $l1; $leg += $vb; $leg += $vs; $leg += $va }
        'dot'  { $l1 = Poly @(@(($lx + 6), ($ly + 2.5)), @(($lx + 6), ($ly - 2.5))) 0.25 1 $false 'Таблица'; $d = DropAt $M.dot ($lx + 6) $ly; F $d 'Width' '1.8 mm'; F $d 'Height' '1.8 mm'; $leg += $l1; $leg += $d }
        'arr'  { $leg += Poly @(@($lx, $ly), @(($lx + 12), $ly)) 0.25 1 $true 'Таблица' }
    }
    $leg += Label ($lx + 15) $ly $txt 3.0 'l' 0 'Таблица'
    $ly -= 6.5
}
$gL = GroupOf $pg $leg; ToLay $gL 'Таблица'

# ================================================================ ШТАМП (фоновая страница, поля Visio)
$FC = 'Microsoft.Office.Interop.Visio.VisFieldCodes'
$script:stamp = $bg.Layers.Add('Штамп')
function BgText([double]$x, [double]$y, [double]$w, [double]$h, [string]$text, [double]$size = 3.5, [double]$angle = 0) {
    $s = $bg.DrawRectangle((mm ($x - $w / 2)), (mm ($y - $h / 2)), (mm ($x + $w / 2)), (mm ($y + $h / 2))); Style $s 0.25 0; F $s 'LinePattern' 0
    if ($text) { $s.Text = $text }
    TextFmt $s $size 1
    if ($angle) { F $s 'Angle' "$angle deg" }
    $script:stamp.Add($s, 0); $s
}
BgText 330 52.5 68 13 $Code 7 | Out-Null
$nm = BgText 330 32.5 68 23 '' 5
$nm.Text = "①`n②"
$ch = $nm.Characters; $ch.Begin = 2; $ch.End = 3; $ch.AddField(2, [int][enum]::Parse($FC, 'visFCodeSubject'), 0)
$ch = $nm.Characters; $ch.Begin = 0; $ch.End = 1; $ch.AddField(2, [int][enum]::Parse($FC, 'visFCodeTitle'), 0)
BgText 367.5 32.5 5 13 'У' 3.5 | Out-Null
$ln = BgText 382 22.5 5 5 '' 3.5; $ln.Text = '①'; $ch = $ln.Characters; $ch.Begin = 0; $ch.End = 1; $ch.AddField(5, [int][enum]::Parse($FC, 'visFCodePageNumber'), 0)
$lt = BgText 409 22.5 10 5 '' 3.5; $lt.Text = '①'; $ch = $lt.Characters; $ch.Begin = 0; $ch.End = 1; $ch.AddField(5, [int][enum]::Parse($FC, 'visFCodeNumberOfPages'), 0)
BgText 55 285 70 14 $Code 5 180 | Out-Null
$lf.CellsC(7).FormulaU = '1'

$doc.SaveAs($outVsdx) | Out-Null
$doc.ExportAsFixedFormat(1, $outPdf, 1, 0)
'saved'
$doc.Close(); $stn.Close()
} finally { $app.Quit() }
