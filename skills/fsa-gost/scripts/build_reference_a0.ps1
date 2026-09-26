# Эталонный лист А0: все элементы ФСА, которые используются при построении схем (приборы, клапаны с ИМ,
# оборудование, линии и обрывы, типовые контуры, подвал, буквы, оформление). Результат — <Name>.vsdx и .pdf.
# -Frame: файл Visio с рамкой А3 и штампом кафедры (лист А4 удаляется, лист А3 переносится на А0 и становится фоном).
#   Рассчитан на рамку кафедры АТП: линии внешней рамки — фигуры с ID 1–4 и 140–142.
# -Anonymize: убрать логотип в левом верхнем углу и даты из штампа (для публикации в репозитории).
param(
    [Parameter(Mandatory = $true)][string]$Frame,
    [string]$Stencil = '',
    [string]$OutDir  = (Get-Location).Path,
    [string]$Name    = 'Эталоны_ФСА_А0',
    [switch]$Anonymize
)
$ErrorActionPreference = 'Stop'
$LOGF = Join-Path $env:TEMP 'build_a0.log'; function Log($m) { $fs = [IO.File]::Open($LOGF, 'Append', 'Write', 'ReadWrite'); $bb = [Text.Encoding]::UTF8.GetBytes([string]$m + "`r`n"); $fs.Write($bb, 0, $bb.Length); $fs.Close() }
if (Test-Path $LOGF) { Remove-Item $LOGF }; Log ('start ' + (Get-Date -f HH:mm:ss))
trap { Log ('ERROR: ' + $_ + ' @' + $_.InvocationInfo.ScriptLineNumber); break }
[Threading.Thread]::CurrentThread.CurrentCulture = 'en-US'
if (-not $Stencil) { $Stencil = [string](Join-Path $PSScriptRoot '..\assets\ГОСТ_21.208_КИП.vssx') }
$Frame = [string](Resolve-Path $Frame); $Stencil = [string](Resolve-Path $Stencil); $OutDir = [string](Resolve-Path $OutDir)
$outVsdx = [string](Join-Path $OutDir "$Name.vsdx")
$outPdf  = [string](Join-Path $OutDir "$Name.pdf")
foreach ($f in $outVsdx, $outPdf) { if (Test-Path $f) { Remove-Item $f -Force } }
Copy-Item $Frame $outVsdx

function mm([double]$v) { $v / 25.4 }
function F($s, $cell, $f) { $s.CellsU($cell).FormulaU = [string]$f }
function Q($t) { '"' + ($t -replace '"', '""') + '"' }
function Arr($pts) { $a = New-Object 'double[]' ($pts.Count * 2); for ($i = 0; $i -lt $pts.Count; $i++) { $a[2 * $i] = [double]$pts[$i][0] / 25.4; $a[2 * $i + 1] = [double]$pts[$i][1] / 25.4 }; , $a }
function Style($s, [double]$lw = 0.25, [int]$pat = 1, [string]$fill = 'none') {
    $lwf = if ($lw -ge 0.35) { '1.5 pt' } elseif ($lw -ge 0.2) { '0.75 pt' } else { "$lw mm" }
    F $s 'LineWeight' $lwf; F $s 'LinePattern' $pat; F $s 'LineColor' 'RGB(0,0,0)'; F $s 'LineCap' 0
    switch ($fill) { 'white' { F $s 'FillPattern' 1; F $s 'FillForegnd' 'RGB(255,255,255)' } 'black' { F $s 'FillPattern' 1; F $s 'FillForegnd' 'RGB(0,0,0)' } default { F $s 'FillPattern' 0 } }
    F $s 'ShdwPattern' 0
}
function TextFmt($s, [double]$size = 3.5, [int]$halign = 1, [int]$bold = 0) {
    F $s 'Char.Size' "$size mm"; F $s 'Char.Font' $script:arial; F $s 'Char.Color' 'RGB(0,0,0)'; F $s 'Char.Style' $bold
    F $s 'Para.HorzAlign' $halign
    F $s 'LeftMargin' '0 mm'; F $s 'RightMargin' '0 mm'; F $s 'TopMargin' '0 mm'; F $s 'BottomMargin' '0 mm'
}

$app = New-Object -ComObject Visio.InvisibleApp
$app.AlertResponse = 1
try {
Log 'visio started'
$doc = $app.Documents.OpenEx($outVsdx, 0)
Log 'doc opened'
$stn = $app.Documents.OpenEx($Stencil, 2 + 4 + 8)
$script:arial = $doc.Fonts.Item('Arial').ID
$M = @{}
foreach ($mstItem in $stn.Masters) { $M[$mstItem.NameU] = $mstItem }

# ================================================================ РАМКА А0 (фон)
Log ('STEP РАМКА А0 (фон) ' + (Get-Date -f HH:mm:ss))
$bg = $null; $a4 = $null
foreach ($p in $doc.Pages) { if ($p.PageSheet.CellsU('PageWidth').ResultIU -gt 15) { $bg = $p } else { $a4 = $p } }
$a4.Delete(1)
$bg.Name = 'Рамка А0'; $bg.Background = 1
F $bg.PageSheet 'PageWidth' '1189 mm'; F $bg.PageSheet 'PageHeight' '841 mm'; F $bg.PageSheet 'PrintPageOrientation' 2
$dx = 1184 - 415; $dy = 836 - 292
$frameLines = @(1, 2, 3, 4, 140, 142, 141)
$toStamp = @(); $toTop = @(); $toDel = @()
foreach ($s in $bg.Shapes) {
    if ($frameLines -contains $s.ID) { $toDel += $s; continue }
    [double]$bbL = 0; [double]$bbB = 0; [double]$bbR = 0; [double]$bbT = 0
    $null = $s.BoundingBox(3, [ref]$bbL, [ref]$bbB, [ref]$bbR, [ref]$bbT)
    $cx = ($bbL + $bbR) / 2 * 25.4; $cy = ($bbB + $bbT) / 2 * 25.4
    if ($Anonymize -and $cx -gt 93 -and $cx -lt 113 -and $cy -gt 266 -and $cy -lt 294) { $toDel += $s; continue }   # логотип
    if ($Anonymize -and $s.Text -match '^\s*\d{2}\.\d{2}(\.\d{2,4})?\s*$') { $s.Text = '' }                      # даты в штампе
    if ($cx -ge 229 -and $cy -le 61) { $toStamp += $s } elseif ($cy -gt 151) { $toTop += $s }
}
foreach ($s in $toDel) { $s.Delete() }
function MoveSel($shapes, $mx, $my) { $sel = $bg.CreateSelection(0); foreach ($x in $shapes) { $null = $sel.Select($x, 2) }; $null = $sel.Move((mm $mx), (mm $my)) }
MoveSel $toStamp $dx 0
MoveSel $toTop 0 $dy
$fr = $bg.DrawRectangle((mm 20), (mm 5), (mm 1184), (mm 836)); Style $fr 0.5 1
$lf = $bg.Layers.Add('Рамка'); foreach ($s in $bg.Shapes) { $lf.Add($s, 0) }
function BgText([double]$x, [double]$y, [double]$w, [double]$h, [string]$text, [double]$size = 3.5, [double]$angle = 0) {
    $s = $bg.DrawRectangle((mm ($x - $w / 2)), (mm ($y - $h / 2)), (mm ($x + $w / 2)), (mm ($y + $h / 2))); Style $s 0.25 0; F $s 'LinePattern' 0
    $s.Text = $text; TextFmt $s $size 1
    if ($angle) { F $s 'Angle' "$angle deg" }
    $lf.Add($s, 0); $s
}
$null = BgText (330 + $dx) 52.5 68 13 'ФСА-00-ЭТ' 7
$null = BgText (330 + $dx) 32.5 68 23 "Эталонные элементы`nФСА" 5
$null = BgText (367.5 + $dx) 32.5 5 13 'У' 3.5
$null = BgText (382 + $dx) 22.5 5 5 '1' 3.5
$null = BgText (409 + $dx) 22.5 10 5 '1' 3.5
$null = BgText 55 (285 + $dy) 70 14 'ФСА-00-ЭТ' 5 180
$lf.CellsC(7).FormulaU = '1'

# ================================================================ СТРАНИЦА ЭТАЛОНОВ
Log ('STEP СТРАНИЦА ЭТАЛОНОВ ' + (Get-Date -f HH:mm:ss))
$pg = $doc.Pages.Add(); $pg.Name = 'Эталоны ФСА'
F $pg.PageSheet 'PageWidth' '1189 mm'; F $pg.PageSheet 'PageHeight' '841 mm'
F $pg.PageSheet 'PageScale' '1 mm'; F $pg.PageSheet 'DrawingScale' '1 mm'
F $pg.PageSheet 'PrintPageOrientation' 2; F $pg.PageSheet 'LineJumpCode' 0
$pg.BackPage = 'Рамка А0'

function Label([double]$x, [double]$y, [string]$text, [double]$size = 3.5, [string]$align = 'l', [double]$angle = 0, [int]$bold = 0) {
    $s = $pg.DrawRectangle((mm $x), (mm $y), (mm ($x + 10)), (mm ($y + 4))); Style $s 0.25 0; F $s 'LinePattern' 0
    $s.Text = $text
    TextFmt $s $size (@{ 'l' = 0; 'c' = 1; 'r' = 2 }[$align]) $bold
    F $s 'Width' 'TEXTWIDTH(TheText)'; F $s 'Height' 'TEXTHEIGHT(TheText,Width)'
    F $s 'LocPinX' ('Width*' + @{ 'l' = '0'; 'c' = '0.5'; 'r' = '1' }[$align]); F $s 'LocPinY' 'Height*0.5'
    F $s 'PinX' "$x mm"; F $s 'PinY' "$y mm"
    if ($angle) { F $s 'Angle' "$angle deg" }
    $s
}
function Poly($pts, [double]$lw = 0.25, [bool]$arrow = $false) {
    if ($pts.Count -eq 2) { $s = $pg.DrawLine((mm $pts[0][0]), (mm $pts[0][1]), (mm $pts[1][0]), (mm $pts[1][1])) } else { $s = $pg.DrawPolyline((Arr $pts), 8) }
    Style $s $lw 1
    if ($arrow) { F $s 'EndArrow' 13; F $s 'EndArrowSize' 1 }
    $s
}
function Pipe($pts, [bool]$arrow = $true) { Poly $pts 0.35 $arrow }
function Sig($pts) { Poly $pts 0.25 $false }
function Dot([double]$x, [double]$y, [double]$d = 1.4) { $s = $pg.Drop($M['Узел'], (mm $x), (mm $y)); F $s 'Width' "$d mm"; F $s 'Height' "$d mm"; $s }
function Inst($kind, [double]$x, [double]$y, $letters, $pos, $note = '') {
    $mn = @{ field = 'Прибор по месту'; panel = 'Прибор на щите'; ctrl = 'Прибор на щите (прямоугольник)' }[$kind]
    $s = $pg.Drop($M[$mn], (mm $x), (mm $y))
    F $s 'Prop.Letters' (Q $letters); F $s 'Prop.Pos' (Q $pos); F $s 'Prop.Note' (Q $note); $s
}
function Valve([double]$x, [double]$y, $pos, [string]$act = 'up') {
    $s = $pg.Drop($M['Клапан регулирующий с ИМ'], (mm $x), (mm $y)); F $s 'Prop.Pos' (Q $pos)
    $th = @{ up = 0; left = 90; down = 180; right = 270 }[$act]
    if ($th) { F $s 'Angle' "$th deg" }
    $t = $th * [Math]::PI / 180
    $ax = -7.5 * [Math]::Sin($t); $ay = 7.5 * [Math]::Cos($t)
    $px = $ax + 3.2; $py = $ay
    if ($th -eq 90 -or $th -eq 270) { $px = $ax - 3; $py = $ay - 4.8 }
    $lx = $px * [Math]::Cos($t) + $py * [Math]::Sin($t); $ly = - $px * [Math]::Sin($t) + $py * [Math]::Cos($t)
    F $s 'TxtPinX' "$([Math]::Round($lx + 3.5, 3)) mm"; F $s 'TxtPinY' "$([Math]::Round($ly + 1.75, 3)) mm"
    $s
}
function Num([double]$x, [double]$y, $n) { $s = $pg.Drop($M['Номер обрыва'], (mm $x), (mm $y)); F $s 'Prop.N' (Q "$n"); $s }
function Equip($mn, [double]$x, [double]$y, $pos, [double]$w = 0, [double]$h = 0, [bool]$flip = $false, $txt = $null) {
    $s = $pg.Drop($M[$mn], (mm $x), (mm $y)); F $s 'Prop.Pos' (Q $pos)
    if ($w) { F $s 'Width' "$w mm"; F $s 'Height' "$h mm" }
    if ($flip) { F $s 'FlipX' 1 }
    if ($txt) { F $s 'TxtPinX' "Width*0.5+$($txt[0]) mm"; F $s 'TxtPinY' "Height*0.5+$($txt[1]) mm" }
    $s
}
function Panel([double]$x1, [double]$y1, [double]$x2, [double]$y2, [string]$title) {
    $r = $pg.DrawRectangle((mm $x1), (mm $y1), (mm $x2), (mm $y2)); Style $r 0.35 1
    $hl = Poly @(@($x1, ($y2 - 11)), @($x2, ($y2 - 11))) 0.25
    $null = Label ($x1 + 4) ($y2 - 5.5) $title 6 'l' 0 1
}
function Cap([double]$x, [double]$y, [string]$t, [double]$size = 3.2) { $null = Label $x $y $t $size 'l' }

# ---------------------------------------------------------------- заголовок
$null = Label 594.5 824 'ЭТАЛОННЫЕ ЭЛЕМЕНТЫ ФУНКЦИОНАЛЬНОЙ СХЕМЫ АВТОМАТИЗАЦИИ' 10 'c' 0 1
$null = Label 594.5 811 'ГОСТ 21.208-2013 (обозначения), ГОСТ 21.408-2013 (правила выполнения), требования кафедры АТП — при расхождении действуют требования кафедры' 5 'c'

# ================================================================ A. ПРИБОРЫ
Log ('STEP A. ПРИБОРЫ ' + (Get-Date -f HH:mm:ss))
Panel 30 530 400 800 'А. Приборы и средства автоматизации (ГОСТ 21.208, табл. 1, 3)'
$y = 765
$null = Inst field 55 $y 'FE' '1-1'; Cap 72 $y "Прибор по месту (датчик xE: FE, TE, PE, LE)`nкруг Ø10 мм, 1,5 пт, без черты"; $y -= 30
$null = Inst panel 55 $y 'FT' '1-2'; Cap 72 $y "Прибор на щите (xT, xY): круг Ø10 мм, горизонтальная черта 0,75 пт`nбуквы сверху, позиция N-k снизу; Arial 3,5 мм"; $y -= 30
$null = Inst ctrl 55 $y 'FIRCA' '1-3' 'L'; Cap 80 $y "Регулятор (функция ПЛК) с длинным кодом: прямоугольник 18×10 мм`nс чертой; предел H / L — справа, шрифт 2,5 мм"; $y -= 32
$null = Pipe @(@(38, $y), @(75, $y)); $null = Inst field 56 $y 'FE' '1-1'; Cap 82 $y "FE — в разрыве трубопровода (сужающее устройство)`nтруба 1,5 пт подходит к кругу слева и справа"; $y -= 34
$null = Pipe @(@(38, ($y - 6)), @(75, ($y - 6))); $null = Inst field 56 ($y + 4) 'TE' '2-1'; $null = Sig @(@(56, ($y - 1)), @(56, ($y - 6))); $null = Dot 56 ($y - 6)
Cap 82 $y "TE, PE, LE — рядом с трубой или аппаратом:`nлиния отбора 0,75 пт до стенки + залитая точка Ø1,4…1,8 мм"; $y -= 36
$null = Equip 'Емкость горизонтальная' 60 $y 'Е-5' 40 16; $null = Inst field 91 $y 'LE' '4-1' ; $null = Sig @(@(86, $y), @(80, $y)); $null = Dot 80 $y
Cap 102 $y "LE на аппарате: отбор от стенки ёмкости или колонны"

# ================================================================ B. РЕГУЛИРУЮЩИЕ ОРГАНЫ
Log ('STEP B. РЕГУЛИРУЮЩИЕ ОРГАНЫ ' + (Get-Date -f HH:mm:ss))
Panel 410 530 780 800 'Б. Клапан регулирующий с ИМ (электрический, пневматический)'
$vx = @(440, 520, 600, 680); $acts = @('up', 'down', 'left', 'right'); $capt = @('ИМ вверх', 'ИМ вниз («ИМ снизу»)', 'ИМ влево', 'ИМ вправо')
for ($i = 0; $i -lt 4; $i++) {
    $x = $vx[$i]
    if ($acts[$i] -in 'up', 'down') { $null = Pipe @(@(($x - 22), 740), @(($x + 22), 740)) } else { $null = Pipe @(@($x, 718), @($x, 762)) }
    $null = Valve $x 740 "1-5" $acts[$i]
    $null = Label $x 708 $capt[$i] 3.2 'c'
}
$null = Pipe @(@(430, 668), @(480, 668)); $null = Valve 455 668 '1-5' 'up'; $null = Sig @(@(455, 666.25), @(455, 660)); $null = Num 455 658 '2'
$null = Inst panel 455 690 'FY' '1-4'; $null = Sig @(@(455, 685), @(455, 678))
Cap 490 672 "Блок управления xY — над (под) ИМ, линия к верху ИМ;`nвыносная линия управления — от корпуса клапана`nсо стороны, противоположной ИМ, 5…8 мм, на конце номер обрыва"
Cap 420 620 "Бабочка 7×3,5 мм (два треугольника вершинами), шток 5 мм от центра клапана, ИМ — круг Ø5 мм"
Cap 420 610 "ИМ электрический: круг Ø5, стрелок на штоке нет, у xY пометка не ставится"
# клапан с пневматическим ИМ: квадрат 5×5 на штоке, у xY пометка E/P
$pvx = 705; $pvy = 655
$null = Pipe @(@(680, $pvy), @(735, $pvy))
$bt = $pg.DrawPolyline((Arr @(@(($pvx - 3.5), ($pvy + 1.75)), @(($pvx + 3.5), ($pvy - 1.75)), @(($pvx + 3.5), ($pvy + 1.75)), @(($pvx - 3.5), ($pvy - 1.75)), @(($pvx - 3.5), ($pvy + 1.75)))), 8); Style $bt 0.35 1 'white'
$null = Poly @(@($pvx, $pvy), @($pvx, ($pvy + 5))) 0.35
$sq = $pg.DrawRectangle((mm ($pvx - 2.5)), (mm ($pvy + 5)), (mm ($pvx + 2.5)), (mm ($pvy + 10))); Style $sq 0.35 1 'white'
$null = Label ($pvx + 4) ($pvy + 7.5) '1-5' 3.5 'l'
$null = Inst panel $pvx ($pvy + 22) 'FY' '1-4'; $null = Sig @(@($pvx, ($pvy + 17)), @($pvx, ($pvy + 10)))
$null = Label ($pvx + 5.5) ($pvy + 27) 'E/P' 3.0 'l'
$null = Sig @(@($pvx, ($pvy - 1.75)), @($pvx, ($pvy - 8))); $null = Num $pvx ($pvy - 10) '2'
Cap 655 632 "Клапан с пневматическим ИМ: квадрат 5×5 мм`nна штоке 5 мм, 1,5 пт, белая заливка;`nу xY — пометка «E/P» (электропневмо-`nпреобразователь), шрифт 3 мм"
Cap 420 600 "Позиция ИМ = последний номер контура (1-5, 2-4…), справа или слева от круга ИМ"
Cap 420 590 "Клапан — в разрыве трубы; «ИМ снизу» разворачивает ИМ на 180° (меню фигуры в Visio)"
Cap 420 575 "Толщина: бабочка, шток, ИМ — 1,5 пт; контур ИМ белая заливка"

# ================================================================ C. ОБОРУДОВАНИЕ
Log ('STEP C. ОБОРУДОВАНИЕ ' + (Get-Date -f HH:mm:ss))
Panel 790 530 1180 800 'В. Технологическое оборудование (ГОСТ 2.782, 2.789, 2.790)'
$null = Equip 'Колонна' 815 665 'Д-1' 20 100; Cap 800 605 "Колонна 20×(90…110) мм,`nэллиптические днища"
$null = Equip 'Емкость горизонтальная' 900 760 'Е-2' 40 16; $null = Pipe @(@(860, 760), @(880, 760)); Cap 925 760 "Ёмкость горизонтальная 45×16 мм`n(40×16 в трафарете)"
$null = Equip 'Испаритель' 900 720 'И-1' 26 12 $false @(0, -9.5); Cap 925 720 "Испаритель (кипятильник) 26×12 мм`nс трубным пучком"
$null = Equip 'Насос центробежный' 880 678 'Н-1'; $null = Pipe @(@(860, 678), @(874, 678)); $null = Pipe @(@(886, 684), @(898, 684))
$null = Equip 'Насос центробежный' 930 678 'Н-6' 0 0 $true; $null = Pipe @(@(950, 678), @(936, 678)); $null = Pipe @(@(924, 684), @(912, 684))
Cap 958 678 "Насос Ø12 мм: всас сбоку (центр), нагнетание —`nкасательный патрубок сверху; зеркально — FlipX"
# теплообменник «молния»: теплоноситель проходит по диагонали через изломы (вид из рамкакомпграф)
$hx = 885; $hy = 625
$null = Equip 'Теплообменник' $hx $hy 'Т-2' 0 0 $false @(-9, 10)
$null = Pipe @(@(($hx - 25), $hy), @(($hx - 8), $hy)); $null = Pipe @(@(($hx + 8), $hy), @(($hx + 25), $hy))
$null = Pipe @(@(($hx - 3.826 - 9), ($hy - 7.026 - 9)), @(($hx - 3.826), ($hy - 7.026))) $false
$null = Pipe @(@(($hx + 3.826), ($hy + 7.026)), @(($hx + 3.826 + 9), ($hy + 7.026 + 9)))
Cap 925 630 "Теплообменник Ø16 мм: продукт — слева направо через центр;`nтеплоноситель — диагональ снизу слева вверх вправо с изломом («молния»),`nлинии продолжаются за кругом, стрелка на выходе"
$ax = 885; $ay = 572
$null = Equip 'Теплообменник' $ax $ay 'ВХ-2' 0 0 $false @(-9, 10)
$null = Pipe @(@(($ax - 25), $ay), @(($ax - 8), $ay)); $null = Pipe @(@(($ax + 8), $ay), @(($ax + 25), $ay))
$null = Pipe @(@(($ax - 3.826 - 5), ($ay - 7.026 - 5)), @(($ax - 3.826), ($ay - 7.026))) $false
$null = Pipe @(@(($ax + 3.826), ($ay + 7.026)), @(($ax + 3.826 + 5), ($ay + 7.026 + 5)))
Cap 925 572 "Конденсатор-холодильник / воздушный холодильник:`nтот же знак; короткие наклонные вводы — хладагент (воздух)"
Cap 800 545 "Позиции аппаратов: Н — насос, Т — теплообменник, К/Д — колонна, КХ/ВХ — холодильник, Е — ёмкость, И — испаритель, В — выветриватель"

# ================================================================ D. ЛИНИИ
Log ('STEP D. ЛИНИИ ' + (Get-Date -f HH:mm:ss))
Panel 790 290 1180 520 'Г. Линии, соединения, обрывы (ГОСТ 2.303, ГОСТ 21.408 п. 5.3.6.4)'
$y = 490
$null = Pipe @(@(800, $y), @(870, $y)); Cap 880 $y "Трубопровод — сплошная 1,5 пт; стрелка у входа в аппарат и на выходе из схемы"; $y -= 26
$null = Sig @(@(800, $y), @(870, $y)); Cap 880 $y "Линия связи (контура) — сплошная 0,75 пт, только горизонталь и вертикаль"; $y -= 26
$null = Pipe @(@(800, $y), @(870, $y)) $false; $null = Sig @(@(835, $y), @(835, ($y + 10))); $null = Dot 835 $y; Cap 880 $y "Отбор от трубы / аппарата — линия 0,75 пт + точка Ø1,4…1,8 мм"; $y -= 26
$null = Pipe @(@(800, $y), @(870, $y)); $null = Pipe @(@(835, $y), @(835, ($y - 12))); $null = Dot 835 $y; Cap 880 $y "Разветвление трубопровода — точка в узле"; $y -= 30
$null = Pipe @(@(800, $y), @(870, $y)); $null = Pipe @(@(835, ($y + 10)), @(835, ($y - 10))) $false; Cap 880 $y "Пересечение без соединения — без точки (линиям связи пересечений избегать)"; $y -= 30
$null = Inst field 815 $y 'FE' '1-1'; $null = Sig @(@(820, $y), @(828, $y)); $null = Num 831 $y '1'; Cap 880 $y "Выносная линия 5…8 мм от прибора / клапана, на конце номер обрыва (Arial 3,5 мм, без рамки).`nНумерация СКВОЗНАЯ 1, 2, 3… по колонкам подвала слева направо: у контура регулирования`nдва номера подряд (измерение, затем управление от корпуса клапана), у контура только`nизмерения или только ДУ — один номер; те же номера — над колонками подвала"; $y -= 32
Cap 800 $y "Линия связи подводится к любой точке прибора; боковые — выше или ниже черты. Через приборы линии не проходят."

# ================================================================ E. ТИПОВЫЕ КОНТУРЫ
Log ('STEP E. ТИПОВЫЕ КОНТУРЫ ' + (Get-Date -f HH:mm:ss))
Panel 30 290 780 520 'Д. Состав контуров (развёрнутый способ, позиции N-k по ходу сигнала)'
# расход
$null = Pipe @(@(40, 330), @(190, 330)); $null = Valve 60 330 '1-5' 'up'
$null = Inst field 120 330 'FE' '1-1'; $null = Inst panel 120 352 'FT' '1-2'; $null = Inst ctrl 90 372 'FIRCA' '1-3' 'L'; $null = Inst panel 60 352 'FY' '1-4'
$null = Sig @(@(120, 335), @(120, 347)); $null = Sig @(@(120, 357), @(120, 372), @(99, 372)); $null = Sig @(@(81, 372), @(60, 372), @(60, 357)); $null = Sig @(@(60, 347), @(60, 340))
$null = Sig @(@(120, 325), @(120, 320.5)); $null = Num 120 318.5 '1'; $null = Sig @(@(60, 328.25), @(60, 323.5)); $null = Num 60 321.5 '2'
Cap 40 305 "Расход: FE → FT → FIRC(A) → FY → ИМ`nN-1…N-5; FE в разрыве трубы"
# температура
$null = Pipe @(@(215, 330), @(365, 330)); $null = Valve 240 330 '2-4' 'up'
$null = Inst field 320 345 'TE' '2-1'; $null = Sig @(@(320, 340), @(320, 330)); $null = Dot 320 330
$null = Inst ctrl 285 372 'TIRC' '2-2'; $null = Inst panel 240 352 'TY' '2-3'
$null = Sig @(@(320, 350), @(320, 372), @(294, 372)); $null = Sig @(@(276, 372), @(240, 372), @(240, 357)); $null = Sig @(@(240, 347), @(240, 340))
$null = Sig @(@(325, 345), @(331, 345)); $null = Num 334 345 '3'; $null = Sig @(@(240, 328.25), @(240, 323.5)); $null = Num 240 321.5 '4'
Cap 215 305 "Температура: TE → TIRC → TY → ИМ`n(без TT, как у преподавателя), N-1…N-4"
# давление
$null = Pipe @(@(390, 330), @(560, 330)); $null = Valve 420 330 '3-5' 'up'
$null = Inst field 510 345 'PE' '3-1'; $null = Sig @(@(510, 340), @(510, 330)); $null = Dot 510 330
$null = Inst panel 510 365 'PT' '3-2'; $null = Inst ctrl 470 385 'PIRCAS' '3-3' 'H'; $null = Inst panel 420 352 'PY' '3-4'
$null = Sig @(@(510, 350), @(510, 360)); $null = Sig @(@(510, 370), @(510, 385), @(479, 385)); $null = Sig @(@(461, 385), @(420, 385), @(420, 357)); $null = Sig @(@(420, 347), @(420, 340))
$null = Sig @(@(515, 345), @(521, 345)); $null = Num 524 345 '5'; $null = Sig @(@(420, 328.25), @(420, 323.5)); $null = Num 420 321.5 '6'
Cap 390 305 "Давление: PE → PT → PIRC(A)(S) → PY → ИМ`nN-1…N-5; PE с линией отбора"
# уровень
$null = Equip 'Емкость горизонтальная' 620 372 'Е-1' 40 16
$null = Pipe @(@(630, 364), @(630, 330), @(770, 330)); $null = Valve 740 330 '4-5' 'up'
$null = Inst field 672 372 'LE' '4-1'; $null = Sig @(@(667, 372), @(640, 372)); $null = Dot 640 372
$null = Inst panel 700 372 'LT' '4-2'; $null = Inst ctrl 705 395 'LIRCA' '4-3' 'H, L'; $null = Inst panel 740 352 'LY' '4-4'
$null = Sig @(@(677, 372), @(695, 372)); $null = Sig @(@(700, 377), @(700, 390)); $null = Sig @(@(714, 395), @(740, 395), @(740, 357)); $null = Sig @(@(740, 347), @(740, 340))
$null = Sig @(@(672, 367), @(672, 360.5)); $null = Num 672 358.5 '7'; $null = Sig @(@(740, 328.25), @(740, 323.5)); $null = Num 740 321.5 '8'
Cap 600 305 "Уровень: LE → LT → LIRC(A) → LY → ИМ`nN-1…N-5; LE на стенке аппарата"
Cap 40 460 "Контур образует «П» над или под трубой; ИМ можно развернуть вниз, чтобы убрать пересечения. Контуры нумеруются 1, 2, 3… по ходу процесса слева направо; клапан с ИМ — последний номер контура."
Cap 40 450 "Функции регулятора в порядке I R C A S (FIRCA, PIRCAS); указываются только функции, отмеченные в подвале. Места отбора — строго по эскизу / описанию процесса, лишних труб не дорисовывать."
Cap 40 434 "Размещение регулятора — по задаче и заполненности листа: (1) в контуре на схеме (как здесь) и дублируется точками в подвале; (2) только в контуре на схеме;`n(3) только в подвале — функции строками ПЛК, на схеме остаются датчик, выносные линии и клапан, xY — в строке «Приборы на щите» (подвал, колонки 7–8). На одном листе — один способ, оговорить в примечании."

# ================================================================ F. ПОДВАЛ
Log ('STEP F. ПОДВАЛ ' + (Get-Date -f HH:mm:ss))
Panel 30 70 560 280 'Е. Подвал: функции контуров (приборы по месту, ПЛК, АРМ)'
$x0 = 40; $x1 = 340; $xg = 51; $xf = 85
$rows = @(@('Приборы по месту', 118, 132, ''), @('Приборы на щите', 104, 118, ''), @('Регистрация', 98, 104, 'ПЛК'), @('Стабилизация', 92, 98, 'ПЛК'), @('Сигнализация', 86, 92, 'ПЛК'), @('Блокировка', 80, 86, 'ПЛК'), @('Индикация', 74, 80, 'АРМ'), @('Сигнализация', 68, 74, 'АРМ'), @('Дист. управление', 62, 68, 'АРМ'))
$sh = 12   # смещение подвала вверх внутри панели
$box = $pg.DrawRectangle((mm $x0), (mm (62 + $sh)), (mm $x1), (mm (132 + $sh))); Style $box 0.5 1
foreach ($r in $rows) {
    $ya = $r[1] + $sh; $yb = $r[2] + $sh
    if ($r[1] -gt 62) { $inner = ($r[3] -and ($rows | Where-Object { $_[3] -eq $r[3] -and $_[2] -eq $r[1] })); $null = Poly @(@($(if ($inner) { $xg } else { $x0 }), $ya), @($x1, $ya)) $(if ($r[0] -in 'Приборы по месту', 'Приборы на щите', 'Блокировка') { 0.5 } else { 0.25 }) }
    if ($r[3]) { $null = Label ($xg + 1.5) (($ya + $yb) / 2) $r[0] 3.0 'l' } else { $null = Label (($x0 + $xf) / 2) (($ya + $yb) / 2) $r[0] 3.0 'c' }
}
$null = Poly @(@($xf, (62 + $sh)), @($xf, (132 + $sh))) 0.5
$null = Poly @(@($xg, (80 + $sh)), @($xg, (104 + $sh))) 0.5; $null = Poly @(@($xg, (62 + $sh)), @($xg, (80 + $sh))) 0.5
$null = Label (($x0 + $xg) / 2) (92 + $sh) 'ПЛК' 3.5 'c' 90; $null = Label (($x0 + $xg) / 2) (71 + $sh) 'АРМ' 3.5 'c' 90
$RY = @{ R = 101; C = 95; A = 89; S = 83; I = 77; A2 = 71; DU = 65 }
# колонки: 1–2 расход (регулятор на схеме), 3–4 температура, 5 только измерение, 6 NS двигателя (только ДУ),
# 7–8 уровень с регулятором только в ПЛК (LY на щите, E/P, LL в блокировке)
$loops = @(
    @{ x = 105; n = 1; L = 'FE'; P = '1-1'; f = 'R C A I A2 DU'; lim = '…м³/ч'; cx = 128; cn = 2 },
    @{ x = 165; n = 3; L = 'TE'; P = '2-1'; f = 'R C I DU'; lim = '…°С'; cx = 188; cn = 4 },
    @{ x = 225; n = 5; L = 'PT'; P = '3-1'; f = 'R I A2'; lim = '…МПа'; hl = @{ A2 = 'H' } },
    @{ x = 262; n = 6; L = 'NS'; P = '4-1'; f = 'DU' },
    @{ x = 300; n = 7; L = 'LT'; P = '5-1'; f = 'R C S I A2 DU'; lim = '…мм'; hl = @{ S = 'LL'; A2 = 'H, L' }; cx = 323; cn = 8; Y = 'LY'; YP = '5-2' }
)
foreach ($lp in $loops) {
    $mx = $lp.x
    $null = Inst field $mx (125 + $sh) $lp.L $lp.P
    $null = Num $mx (135.5 + $sh) $lp.n; $null = Sig @(@($mx, (133.5 + $sh)), @($mx, (130 + $sh)))
    $bottom = if ($lp.f -eq 'DU') { $RY['DU'] + $sh } else { 62 + $sh }
    $null = Sig @(@($mx, (120 + $sh)), @($mx, $bottom))
    if ($lp.lim) { $null = Label ($mx + 6.2) (127.5 + $sh) $lp.lim 2.5 'l' }
    if ($lp.cx) {
        $cxx = $lp.cx; $null = Num $cxx (135.5 + $sh) $lp.cn
        if ($lp.Y) {
            $null = Inst panel $cxx (111 + $sh) $lp.Y $lp.YP; $null = Label ($cxx + 5.2) (116.3 + $sh) 'E/P' 2.5 'l'
            $null = Sig @(@($cxx, (133.5 + $sh)), @($cxx, (116 + $sh))); $null = Sig @(@($cxx, (106 + $sh)), @($cxx, ($RY['DU'] + $sh)))
        } else { $null = Sig @(@($cxx, (133.5 + $sh)), @($cxx, ($RY['DU'] + $sh))) }
        $null = Poly @(@($mx, ($RY['C'] + $sh)), @(($cxx - 0.9), ($RY['C'] + $sh))) 0.25 $true
        $null = Dot $cxx ($RY['C'] + $sh) 1.8
    }
    foreach ($fn in $lp.f.Split(' ')) {
        $dx0 = if ($fn -eq 'DU' -and $lp.cx) { $lp.cx } else { $mx }
        $null = Dot $dx0 ($RY[$fn] + $sh) 1.8
        if ($lp.hl -and $lp.hl[$fn]) { $null = Label ($dx0 + 1.8) ($RY[$fn] + $sh) $lp.hl[$fn] 2.5 'l' }
    }
}
Cap 250 262 "Номера обрывов над колонками — СКВОЗНЫЕ 1, 2, 3… слева направо, по одному на колонку"
Cap 250 250 "Строка «Приборы по месту» — круг датчика контура и предел справа («…м³/ч»,`nчисла из задания/регламента, если даны)"
Cap 250 234 "«Приборы на щите» — пустая, если регулятор на схеме; xY с пометкой «E/P»,`nесли регулятор показан только в подвале (колонки 7–8, строка 12…14 мм)"
Cap 250 222 "ПЛК: Регистрация (R), Стабилизация (C) — точка и стрелка`nк колонке управления, Сигнализация (A), Блокировка (S)"
Cap 250 206 "АРМ: Индикация (I), Сигнализация (A), Дист. управление —`nточка на колонке управления"
Cap 250 190 "Колонка измерения — от датчика до низа подвала,`nколонка управления — от номера до «Дист. управление»"
Cap 250 174 "Точки подвала = буквы регулятора (FIRCA → R, C, A, I, A, ДУ); H, L, LL — справа от точки, 2,5 мм"
Cap 250 160 "Шапка 45 мм, группы ПЛК / АРМ вертикально; строка 6 мм,`nлинии между группами 1,5 пт, внутри групп 0,75 пт; шаг контуров ≈47 мм"
Cap 350 128 "Колонки примера: 1–2 — расход, регулятор FIRCA на схеме; 3–4 — температура;`n5 — контур только измерения (одна колонка, PT без регулирования, сигнализация H);`n6 — NS: пуск / останов электродвигателя насоса или вентилятора АВО, только ДУ;`n7–8 — регулятор только в ПЛК: LT по месту, LY «E/P» на щите, блокировка LL`n(защита насоса от сухого хода), сигнализация H, L"
Cap 350 98 "Каскад / работа на два клапана — стрелка в строке «Стабилизация» от колонки`nведущего контура к колонке ведомого; через чужие колонки — с перескоком"
Cap 350 82 "На листе А3: подвал x 25…410, y 62…124 (с xY на щите — выше на 8 мм);`nномера y ≈127,5; таблица контуров x 25…157, y 10…58; условные обозначения x 162…228"

# ================================================================ G. БУКВЫ
Log ('STEP G. БУКВЫ ' + (Get-Date -f HH:mm:ss))
Panel 570 70 780 280 'Ж. Буквенные обозначения (ГОСТ 21.208, табл. 2)'
function Cell([double]$xa, [double]$ya, [double]$xb, [double]$yb, [string]$t, [double]$size = 3.0, [int]$al = 1, [double]$lw = 0.25) {
    $s = $pg.DrawRectangle((mm $xa), (mm $ya), (mm $xb), (mm $yb)); Style $s $lw 1
    if ($t) { $s.Text = $t }; TextFmt $s $size $al
    if ($al -eq 0) { F $s 'LeftMargin' '1.5 mm' }; $s
}
$tx = @(578, 596, 672, 772); $ty = 262; $rh = 10.5
$hd = @('Буква', 'На 1-м месте (величина)', 'На последующих (функция)')
for ($i = 0; $i -lt 3; $i++) { $null = Cell $tx[$i] ($ty - $rh) $tx[$i + 1] $ty $hd[$i] 3.0 1 }
$letters = @(@('F', 'Расход', '—'), @('T', 'Температура', 'Преобразователь'), @('P', 'Давление, вакуум', '—'), @('L', 'Уровень', 'Нижний предел (справа)'),
             @('H', 'Ручное воздействие', 'Верхний предел (справа)'), @('E', 'Напряжение', 'Чувствительный элемент'), @('Y', 'Событие, состояние', 'Блок управления ИМ'),
             @('I', 'Ток', 'Показание (индикация)'), @('R', 'Радиоактивность', 'Регистрация'), @('C', '—', 'Автоматическое регулирование'),
             @('A', 'Анализ (состав)', 'Сигнализация'), @('S', 'Скорость, частота', 'Вкл./откл., блокировка'), @('Q', 'Количество', 'Интегрирование'),
             @('D', 'Плотность', 'Разность, перепад (PDT)'), @('N', 'Резервная — оговорить на схеме', 'NS — пуск / останов двигателя'))
$yy = $ty - $rh
foreach ($r in $letters) {
    $null = Cell $tx[0] ($yy - $rh) $tx[1] $yy $r[0] 3.5 1
    $null = Cell $tx[1] ($yy - $rh) $tx[2] $yy $r[1] 3.0 0
    $null = Cell $tx[2] ($yy - $rh) $tx[3] $yy $r[2] 3.0 0
    $yy -= $rh
}
Cap 578 ($yy - 7) "Порядок: величина → функции I R C A S (FIRCA, TIRC, PIRCAS, LIRCA); N на листе`nрасшифровать: «N — электродвигатель» в условных обозначениях"

# ================================================================ H. ОФОРМЛЕНИЕ
Log ('STEP H. ОФОРМЛЕНИЕ ' + (Get-Date -f HH:mm:ss))
Panel 790 70 1180 280 'З. Лист, рамка, шрифты, порядок работы'
$notes = @(
 'Лист А3 альбомный 420×297 мм; рамка: слева 20 мм, остальные 5 мм; рамка и штамп — на фоновой странице.',
 'Основная надпись 185×55 мм (форма 1): обозначение «…-АТХ», «<Установка>. Схема автоматизации», литера «У», лист / листов.',
 'Дополнительная графа 70×14 мм в левом верхнем углу — обозначение, повёрнутое на 180°.',
 'Зоны А3: технология с контурами y 133…290; оборудование слева направо по ходу процесса.',
 'Шрифт Arial: буквы и позиции приборов 3,5 мм; H/L 2,5 мм; подписи потоков 3,0…3,5 мм.',
 'Внешние потоки подписываются у начала / конца линии: «Сырьё», «Пар», «Газ», «Хладагент» и т. п.',
 'Толщины: 1,5 пт — трубы, аппараты, приборы, клапаны, ИМ, рамки подвала и таблиц;',
 '0,75 пт — линии связи, выносные, отборы, черта в круге, внутренние линии подвала. Все линии сплошные.',
 'Порядок: разбор исходника (оборудование, потоки, контуры) → технология → контуры → выносные линии →',
 'подвал → таблица контуров, условные обозначения, штамп → чек-лист → PDF А3 без обрезки.',
 'В Visio: трафарет ГОСТ_21.208_КИП.vssx; линии связи — полилинии, приклеенные к точкам соединения;',
 'слои Трубопроводы / Оборудование / КИП / Линии связи / Подвал / Контур N; подвал — контейнер.')
$yy = 258
foreach ($n in $notes) { Cap 798 $yy $n 3.2; $yy -= 14 }

$doc.SaveAs($outVsdx) | Out-Null
$doc.ExportAsFixedFormat(1, $outPdf, 1, 0)
'saved'
$stn.Close(); $doc.Close()
} finally { $app.Quit() }
