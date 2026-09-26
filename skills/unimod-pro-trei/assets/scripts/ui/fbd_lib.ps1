# Работа мышью в редакторе FBD Unimod PRO 2 — без зашитых координат.
#
#   . "$PSScriptRoot\fbd_lib.ps1"
#   $prog = Read-FbdProg "C:\prj\demo\tasks\main\logic\prog.json"
#   $a = Get-FbdBlock $prog -Name 'a_real'; $op = Get-FbdBlock $prog -Name '+'
#   Invoke-FbdLink -Src $a -Dst $op -DstSlot 1
#
# Геометрия (проверено 2026-09-13, масштабы 12x18, 16x24, 22x30):
#   шаг клетки   sx = (Maximum гориз. полосы + ширина поля) / 500
#                sy = (Maximum верт. полосы + высота поля) / 500
#   левый край   x = поле.X + sx*column - прокрутка_по_горизонтали
#   строка k-го вывода  y = поле.Y + sy*(line + k) - прокрутка_по_вертикали
#   верх блока   y(line) - sy/2 - sy*строк_заголовка  (переменная 0, оператор и ФБ 1)
#   ширина блока — целое число клеток, зависит от длины имени; берётся с экрана.
# Значение полосы прокрутки = смещение в пикселях, его можно и читать, и ставить.
# Всё считается заново на каждом вызове, поэтому масштаб, панели и прокрутка
# координатам не мешают.

. "$PSScriptRoot\ui_lib.ps1"

if (-not ("FbdPix" -as [type])) {
    Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

public class FbdPix {
    static byte[] Grab(int X, int Y, int W, int H, out int stride) {
        using (var bmp = new Bitmap(W, H, PixelFormat.Format24bppRgb)) {
            using (var g = Graphics.FromImage(bmp)) g.CopyFromScreen(X, Y, 0, 0, new Size(W, H));
            var data = bmp.LockBits(new Rectangle(0, 0, W, H), ImageLockMode.ReadOnly, PixelFormat.Format24bppRgb);
            stride = data.Stride;
            byte[] buf = new byte[stride * H];
            Marshal.Copy(data.Scan0, buf, 0, buf.Length);
            bmp.UnlockBits(data);
            return buf;
        }
    }
    // «тёмный» = серый или чёрный: max(R,G,B) < thr. Пурпурная метка выбора сюда не попадает.
    public static bool[] Mask(int X, int Y, int W, int H, int thr) {
        int stride; byte[] buf = Grab(X, Y, W, H, out stride);
        bool[] d = new bool[W * H];
        for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++) {
                int i = y * stride + x * 3;
                d[y * W + x] = Math.Max(buf[i], Math.Max(buf[i + 1], buf[i + 2])) < thr;
            }
        return d;
    }
    public static double Dark(int X, int Y, int W, int H, int thr) {
        bool[] d = Mask(X, Y, W, H, thr); int c = 0;
        foreach (bool b in d) if (b) c++;
        return (double)c / d.Length;
    }
    // пурпурные пиксели — метка выбранного («висящего») вывода в режиме соединения
    public static int Magenta(int X, int Y, int W, int H) {
        int stride; byte[] buf = Grab(X, Y, W, H, out stride); int c = 0;
        for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++) {
                int i = y * stride + x * 3;               // BGR
                if (buf[i + 2] > 200 && buf[i] > 200 && buf[i + 1] < 90) c++;
            }
        return c;
    }
    // прямоугольники блоков {x, y, w, h} в экранных координатах
    public static int[][] Rects(int X, int Y, int W, int H, int thr, int minW) {
        bool[] d = Mask(X, Y, W, H, thr);
        var raw = new List<int[]>();
        for (int y = 0; y < H - 12; y++) {
            int x = 0;
            while (x < W) {
                if (!d[y * W + x]) { x++; continue; }
                int x1 = x;
                while (x < W && d[y * W + x]) x++;
                int x2 = x - 1;
                if (x2 - x1 + 1 < minW) continue;
                if (!VRun(d, W, H, x1, y) || !VRun(d, W, H, x2, y)) continue;
                int yb = -1;
                for (int yy = y + 10; yy < H; yy++) {
                    if (!Near(d, W, x1, yy) || !Near(d, W, x2, yy)) break;
                    int cnt = 0;
                    for (int xx = x1; xx <= x2; xx++) if (d[yy * W + xx]) cnt++;
                    if (cnt >= (x2 - x1 + 1) * 8 / 10) { yb = yy; break; }
                }
                if (yb > 0) raw.Add(new int[] { x1, y, x2 - x1 + 1, yb - y + 1 });
            }
        }
        // только дубли двухпиксельной кромки; заголовок оператора и его тело остаются
        // разными прямоугольниками — иначе склеились бы две переменные одна над другой
        raw.Sort((a, b) => a[1] != b[1] ? a[1].CompareTo(b[1]) : a[0].CompareTo(b[0]));
        var res = new List<int[]>();
        foreach (var r in raw) {
            bool dup = false;
            foreach (var m in res)
                if (Math.Abs(m[0] - r[0]) <= 2 && Math.Abs(m[2] - r[2]) <= 3 && Math.Abs(m[1] - r[1]) <= 2) { dup = true; break; }
            if (!dup) res.Add(r);
        }
        foreach (var m in res) { m[0] += X; m[1] += Y; }
        return res.ToArray();
    }
    static bool Near(bool[] d, int W, int x, int y) {
        for (int dx = -2; dx <= 2; dx++) { int xx = x + dx; if (xx >= 0 && xx < W && d[y * W + xx]) return true; }
        return false;
    }
    static bool VRun(bool[] d, int W, int H, int x, int y) {
        for (int yy = y; yy < y + 12; yy++) if (yy >= H || !Near(d, W, x, yy)) return false;
        return true;
    }
}
'@
}

# строк заголовка над первым выводом, по коду type блока
$script:FbdTitleRows = @{ 0 = 0; 1 = 0; 2 = 1; 3 = 1; 4 = 1; 12 = 1; 13 = 0; 15 = 1; 16 = 1 }

# ---------------- схема на диске ----------------

# Размер поля схемы в клетках. IDE берёт его из Define (column_max/line_max) и
# сохраняет как есть: при 1000 полоса прокрутки вдвое длиннее, а клетка та же.
# Read-FbdProg запоминает размер последней прочитанной схемы — читать схему
# той вкладки, с которой работаешь.
$script:FbdGrid = @{ Columns = 500; Lines = 500 }

function Read-FbdProg {
    param([Parameter(Mandatory = $true)][string]$Path)
    $j = [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
    if (-not $j.text.Blocks -and $j.text.Blocks -isnot [array]) { $j.text | Add-Member Blocks @() -Force }
    $df = @($j.text.Define)[0]
    $script:FbdGrid = @{
        Columns = $(if ($df -and $df.column_max) { [int]$df.column_max } else { 500 })
        Lines   = $(if ($df -and $df.line_max) { [int]$df.line_max } else { 500 })
    }
    return $j
}

function Get-FbdBlock {
    param([Parameter(Mandatory = $true)]$Prog, [string]$Name, [int]$Column = -1, [int]$Line = -1, [int]$SaveId = -1)
    $b = @($Prog.text.Blocks | Where-Object {
        ($SaveId -lt 0 -or $_.save_id -eq $SaveId) -and (-not $Name -or $_.name -eq $Name) -and
        ($Column -lt 0 -or $_.column -eq $Column) -and ($Line -lt 0 -or $_.line -eq $Line) })
    if ($b.Count -ne 1) { throw "Get-FbdBlock: найдено блоков $($b.Count) (name=$Name column=$Column line=$Line)" }
    return $b[0]
}

# Сохранить проект кнопкой панели (клавиши до IDE могут не дойти) и дождаться записи файла.
function Save-FbdProject {
    param([string]$WaitFile, [int]$TimeoutMs = 20000)
    $t0 = if ($WaitFile -and (Test-Path $WaitFile)) { (Get-Item $WaitFile).LastWriteTimeUtc } else { $null }
    $btn = Find-FbdFast -ControlType ([System.Windows.Automation.ControlType]::Button) -Name 'Сохранить проект'
    if ($btn.Count -eq 0) { throw 'кнопка «Сохранить проект» не найдена' }
    $btn[0].GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
    if ($t0) {
        $sw = [Diagnostics.Stopwatch]::StartNew()
        while ((Get-Item $WaitFile).LastWriteTimeUtc -eq $t0 -and $sw.ElapsedMilliseconds -lt $TimeoutMs) { Start-Sleep -Milliseconds 200 }
        if ((Get-Item $WaitFile).LastWriteTimeUtc -eq $t0) { return $false }
    } else { Start-Sleep -Seconds 3 }
    Start-Sleep -Milliseconds 500
    return $true
}

# ---------------- поле схемы ----------------

# Быстрый поиск элементов главного окна: FindAll с условием в 10-50 раз быстрее
# обхода дерева через Get-UmAllElements (40 мс против 500).
function Find-FbdFast {
    param([Parameter(Mandatory = $true)][System.Windows.Automation.ControlType]$ControlType, [string]$Name)
    $A = [System.Windows.Automation.AutomationElement]
    $cond = New-Object System.Windows.Automation.PropertyCondition($A::ControlTypeProperty, $ControlType)
    if ($Name) {
        $cond = New-Object System.Windows.Automation.AndCondition($cond,
                (New-Object System.Windows.Automation.PropertyCondition($A::NameProperty, $Name)))
    }
    $root = Get-UmRoot
    if ($null -eq $root) { throw 'окно Unimod не найдено' }
    return @($root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $cond) |
             Where-Object { try { -not $_.Current.IsOffscreen } catch { $false } })
}

$script:FbdBars = $null

# Геометрия активной вкладки схемы: поле, шаг клетки, прокрутка.
# Полосы прокрутки кэшируются; кэш сбрасывается сам, если вкладка сменилась.
function Get-FbdView {
    param([switch]$Refresh)
    $ok = $false
    if ($script:FbdBars -and -not $Refresh) {
        try { $ok = -not $script:FbdBars.H.Current.IsOffscreen -and -not $script:FbdBars.V.Current.IsOffscreen } catch { $ok = $false }
    }
    if (-not $ok) {
        $script:FbdBars = $null
        $bars = Find-FbdFast -ControlType ([System.Windows.Automation.ControlType]::ScrollBar)
        foreach ($hb in $bars) {
            $hr = $hb.Current.BoundingRectangle
            if ($hr.Width -lt 400 -or $hr.Height -gt 40) { continue }
            foreach ($vb in $bars) {
                $vr = $vb.Current.BoundingRectangle
                if ($vr.Height -lt 300 -or $vr.Width -gt 40) { continue }
                if ([math]::Abs(($hr.X + $hr.Width) - $vr.X) -le 2 -and [math]::Abs(($vr.Y + $vr.Height) - $hr.Y) -le 2) {
                    $script:FbdBars = @{ H = $hb; V = $vb }
                }
            }
        }
        if (-not $script:FbdBars) { throw 'Get-FbdView: поле схемы не найдено — открыта ли вкладка FBD-программы?' }
    }
    $hb = $script:FbdBars.H; $vb = $script:FbdBars.V
    $hr = $hb.Current.BoundingRectangle; $vr = $vb.Current.BoundingRectangle
    $hp = $hb.GetCurrentPattern([System.Windows.Automation.RangeValuePattern]::Pattern)
    $vp = $vb.GetCurrentPattern([System.Windows.Automation.RangeValuePattern]::Pattern)
    return [pscustomobject]@{
        X = [int]$hr.X; Y = [int]$vr.Y; W = [int]$hr.Width; H = [int]$vr.Height
        SX = ($hp.Current.Maximum + $hr.Width) / [double]$script:FbdGrid.Columns
        SY = ($vp.Current.Maximum + $vr.Height) / [double]$script:FbdGrid.Lines
        HS = [int]$hp.Current.Value; VS = [int]$vp.Current.Value
        HBar = $hp; VBar = $vp
    }
}

# Поставить прокрутку поля (пиксели). Не переданное значение не меняется,
# отрицательное прижимается к 0, слишком большое — к максимуму.
function Set-FbdScroll {
    param($H = $null, $V = $null)
    $view = Get-FbdView
    if ($null -ne $H) { $view.HBar.SetValue([double][math]::Min([math]::Max([int]$H, 0), $view.HBar.Current.Maximum)) }
    if ($null -ne $V) { $view.VBar.SetValue([double][math]::Min([math]::Max([int]$V, 0), $view.VBar.Current.Maximum)) }
    Start-Sleep -Milliseconds 300
    return Get-FbdView
}

# Прокрутить так, чтобы прямоугольник клеток [c1..c2]x[l1..l2] был виден целиком.
function Show-FbdCells {
    param([int]$C1, [int]$L1, [int]$C2 = -1, [int]$L2 = -1, [int]$Margin = 2)
    if ($C2 -lt 0) { $C2 = $C1 + 8 }; if ($L2 -lt 0) { $L2 = $L1 + 3 }
    $view = Get-FbdView
    $x1 = $view.SX * ($C1 - $Margin); $x2 = $view.SX * ($C2 + $Margin)
    $y1 = $view.SY * ($L1 - $Margin); $y2 = $view.SY * ($L2 + $Margin)
    $h = $view.HS; $v = $view.VS
    if ($x1 -lt $h -or $x2 -gt $h + $view.W) { $h = [int][math]::Max($x1, 0) }
    if ($y1 -lt $v -or $y2 -gt $v + $view.H) { $v = [int][math]::Max($y1, 0) }
    if ($h -ne $view.HS -or $v -ne $view.VS) { return Set-FbdScroll -H $h -V $v }
    return $view
}

function Test-FbdVisible {
    param($View, [int]$X, [int]$Y, [int]$Pad = 4)
    return ($X -ge $View.X + $Pad -and $X -lt $View.X + $View.W - $Pad -and $Y -ge $View.Y + $Pad -and $Y -lt $View.Y + $View.H - $Pad)
}

# Прямоугольник блока на экране. Ширина — по пикселям; блок должен быть виден.
function Get-FbdRect {
    param([Parameter(Mandatory = $true)]$Block, $View)
    if (-not $View) { $View = Get-FbdView }
    $rows = $script:FbdTitleRows[[int]$Block.type]; if ($null -eq $rows) { $rows = 1 }
    $left = [int]($View.X + $View.SX * $Block.column - $View.HS)
    $top = [int]($View.Y + $View.SY * $Block.line - $View.VS - $View.SY / 2 - $View.SY * $rows)
    # область поиска должна вместить блок целиком, иначе нижняя кромка не найдётся
    $pins = [math]::Max([math]::Max([int]$Block.inp_count, [int]$Block.out_count), 1)
    $x0 = [math]::Max($View.X, $left - 6); $y0 = [math]::Max($View.Y, $top - 6)
    $w = [math]::Min($View.X + $View.W, $left + 700) - $x0
    $h = [math]::Min($View.Y + $View.H, $top + [int]($View.SY * ($rows + $pins + 1)) + 12) - $y0
    if ($w -lt 20 -or $h -lt 12) { return $null }
    $hit = @([FbdPix]::Rects($x0, $y0, $w, $h, 200, [int]($View.SX * 1.5)) |
             Where-Object { [math]::Abs($_[0] - $left) -le 3 -and [math]::Abs($_[1] - $top) -le 3 } | Select-Object -First 1)
    if ($hit.Count -eq 0) { return $null }
    return [pscustomobject]@{ X = $left; Y = $top; W = $hit[0][2]; H = $hit[0][3] }
}

# Точка клика по выводу: вход — у левого края внутри блока, выход — у правого.
function Get-FbdPinPoint {
    param([Parameter(Mandatory = $true)]$Block, [int]$Slot = 0, [switch]$Out, $View)
    if (-not $View) { $View = Get-FbdView }
    $r = Get-FbdRect -Block $Block -View $View
    if (-not $r) { throw "блок '$($Block.name)' ($($Block.column),$($Block.line)) не найден на экране — прокрути к нему" }
    $y = [int]($View.Y + $View.SY * ($Block.line + $Slot) - $View.VS)
    $inset = [int][math]::Round($View.SX * 0.6)
    $x = if ($Out) { $r.X + $r.W - $inset } else { $r.X + $inset }
    return [pscustomobject]@{ X = $x; Y = $y; Left = $r.X; Right = $r.X + $r.W }
}

# ---------------- режимы и выбор ----------------

function Get-FbdMode {
    $st = @{}
    foreach ($n in @('режим редактирования', 'режим соединения')) {
        $e = Find-FbdFast -ControlType ([System.Windows.Automation.ControlType]::CheckBox) -Name $n
        if ($e.Count -eq 0) { throw "кнопка «$n» не найдена — открыта ли вкладка FBD-программы?" }
        $st[$n] = ($e[0].GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern).Current.ToggleState -eq 'On')
    }
    if ($st['режим соединения'] -and -not $st['режим редактирования']) { return 'link' }
    if ($st['режим редактирования'] -and -not $st['режим соединения']) { return 'edit' }
    return 'mixed'
}

# Переключать ТОЛЬКО кликом мыши. TogglePattern.Toggle() меняет вид кнопки, но
# не режим редактора — именно так раньше получалось «оба режима включены».
# Кликом мышью режимы взаимоисключающие, и ToggleState после клика верен.
function Set-FbdMode {
    param([Parameter(Mandatory = $true)][ValidateSet('edit', 'link')][string]$Mode)
    $name = if ($Mode -eq 'link') { 'режим соединения' } else { 'режим редактирования' }
    for ($i = 0; $i -lt 3; $i++) {
        if ((Get-FbdMode) -eq $Mode) { return $true }
        $e = (Find-FbdFast -ControlType ([System.Windows.Automation.ControlType]::CheckBox) -Name $name)[0]
        $r = $e.Current.BoundingRectangle
        Invoke-UmClick ([int]($r.X + $r.Width / 2)) ([int]($r.Y + $r.Height / 2)) -SleepMs 300
    }
    return ((Get-FbdMode) -eq $Mode)
}

# Пустая точка поля для «сбросного» клика: без тёмных и пурпурных пикселей вокруг.
$script:FbdEmpty = $null
function Get-FbdEmptyPoint {
    param($View)
    if (-not $View) { $View = Get-FbdView }
    $e = $script:FbdEmpty
    if ($e -and (Test-FbdVisible -View $View -X $e.X -Y $e.Y -Pad 14) -and
        [FbdPix]::Dark($e.X - 12, $e.Y - 12, 25, 25, 200) -eq 0 -and [FbdPix]::Magenta($e.X - 12, $e.Y - 12, 25, 25) -eq 0) {
        return $e
    }
    for ($fy = 0.92; $fy -ge 0.1; $fy -= 0.08) {
        for ($fx = 0.95; $fx -ge 0.05; $fx -= 0.07) {
            $x = [int]($View.X + $View.W * $fx); $y = [int]($View.Y + $View.H * $fy)
            if ([FbdPix]::Dark($x - 12, $y - 12, 25, 25, 200) -eq 0 -and [FbdPix]::Magenta($x - 12, $y - 12, 25, 25) -eq 0) {
                $script:FbdEmpty = [pscustomobject]@{ X = $x; Y = $y }
                return $script:FbdEmpty
            }
        }
    }
    throw 'на видимой части поля нет пустого места'
}

function Get-FbdPendingCount {
    param($View)
    if (-not $View) { $View = Get-FbdView }
    return [FbdPix]::Magenta($View.X, $View.Y, $View.W, $View.H)
}

# Ждать условие, опрашивая каждые 50 мс (вместо фиксированных пауз).
function Wait-FbdUntil {
    param([Parameter(Mandatory = $true)][scriptblock]$Test, [int]$TimeoutMs = 1000)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    do { if (& $Test) { return $true }; Start-Sleep -Milliseconds 50 } while ($sw.ElapsedMilliseconds -lt $TimeoutMs)
    return [bool](& $Test)
}

# Снять «висящий» выбор вывода: клик по пустому месту. Висящий выбор съедает
# следующий клик — из-за него связи создаются не между теми выводами.
function Clear-FbdSelection {
    param($View)
    if (-not $View) { $View = Get-FbdView }
    $p = Get-FbdEmptyPoint -View $View
    Invoke-UmClick $p.X $p.Y -SleepMs 60
    return (Wait-FbdUntil -TimeoutMs 600 -Test { (Get-FbdPendingCount -View $View) -eq 0 })
}

# ---------------- связи ----------------

# Есть ли провод, входящий во вход: тёмная линия слева от левого края блока.
function Test-FbdWire {
    param([Parameter(Mandatory = $true)]$Block, [int]$Slot = 0, $View)
    if (-not $View) { $View = Get-FbdView }
    $p = Get-FbdPinPoint -Block $Block -Slot $Slot -View $View
    $w = [int][math]::Max(6, $View.SX / 2)
    return ([FbdPix]::Dark($p.Left - [int]$View.SX, $p.Y - 1, $w, 3, 200) -ge 0.3)
}

# Провести связь выход -> вход с проверкой. Возвращает $true, если провод появился.
# ВНИМАНИЕ (проверено 2026-09-14): провод на экране — ещё не связь. IDE не считает
# новую связь изменением (у вкладки не появляется «*»), и сохранение пишет схему
# БЕЗ неё, код ST её тоже не видит. Связь попадает в модель при следующей правке
# блока: перенос, удаление, новый блок. Поэтому после серии связей — Submit-FbdLinks,
# затем Save-FbdProject и сверка файла.
function Invoke-FbdLink {
    param([Parameter(Mandatory = $true)]$Src, [Parameter(Mandatory = $true)]$Dst,
          [int]$SrcSlot = 0, [int]$DstSlot = 0, [int]$Retries = 2)
    if (-not (Set-FbdMode -Mode link)) { throw 'не удалось включить «режим соединения»' }
    $c1 = [math]::Min($Src.column, $Dst.column); $c2 = [math]::Max($Src.column, $Dst.column) + 8
    $l1 = [math]::Min($Src.line, $Dst.line) - 1; $l2 = [math]::Max($Src.line + $SrcSlot, $Dst.line + $DstSlot) + 1
    $view = Show-FbdCells -C1 $c1 -L1 $l1 -C2 $c2 -L2 $l2
    $fits = ($view.SX * ($c2 - $c1 + 4) -le $view.W) -and ($view.SY * ($l2 - $l1 + 4) -le $view.H)
    if ($fits -and (Test-FbdWire -Block $Dst -Slot $DstSlot -View $view)) {
        Write-Host "  вход $DstSlot блока '$($Dst.name)' уже занят"; return $false
    }
    for ($try = 0; $try -le $Retries; $try++) {
        Clear-FbdSelection -View $view | Out-Null
        if (-not $fits) { $view = Show-FbdCells -C1 $Src.column -L1 ($Src.line - 1) -C2 ($Src.column + 8) -L2 ($Src.line + $SrcSlot + 1) }
        $ps = Get-FbdPinPoint -Block $Src -Slot $SrcSlot -Out -View $view
        Invoke-UmClick $ps.X $ps.Y -SleepMs 60
        # у выбранного вывода появляется пурпурная точка; нет её — промах, повтор
        if (-not (Wait-FbdUntil -TimeoutMs 800 -Test { [FbdPix]::Magenta($ps.Right - 14, $ps.Y - 12, 28, 24) -gt 0 })) { continue }
        if (-not $fits) { $view = Show-FbdCells -C1 $Dst.column -L1 ($Dst.line - 1) -C2 ($Dst.column + 8) -L2 ($Dst.line + $DstSlot + 1) }
        $pd = Get-FbdPinPoint -Block $Dst -Slot $DstSlot -View $view
        Invoke-UmClick $pd.X $pd.Y -SleepMs 60
        if (Wait-FbdUntil -TimeoutMs 1200 -Test { Test-FbdWire -Block $Dst -Slot $DstSlot -View $view }) {
            if ((Get-FbdPendingCount -View $view) -gt 0) { Clear-FbdSelection -View $view | Out-Null }
            return $true
        }
    }
    Clear-FbdSelection | Out-Null
    return $false
}

# Признак несохранённых изменений: имя вкладки схемы оканчивается на « *».
function Test-FbdTabModified {
    param([Parameter(Mandatory = $true)][string]$Name)
    $t = @(Find-FbdFast -ControlType ([System.Windows.Automation.ControlType]::TabItem) |
           Where-Object { $_.Current.Name -eq $Name -or $_.Current.Name -eq "$Name *" })
    if ($t.Count -eq 0) { throw "вкладки '$Name' нет" }
    return $t[0].Current.Name.EndsWith('*')
}

# Зафиксировать проведённые мышью связи: перенести переменную или константу со
# свободным местом справа на две клетки и вернуть назад. Положение не меняется,
# IDE перенумеровывает порядок по расположению (как после любой правки) и вносит
# все висящие связи в модель. $Prog — схема, прочитанная ПОСЛЕ последнего
# сохранения (блоки ищутся по ней).
function Submit-FbdLinks {
    param([Parameter(Mandatory = $true)]$Prog)
    $blocks = @($Prog.text.Blocks | Where-Object { $_.type -ne 14 })
    $pick = $null
    foreach ($b in ($blocks | Where-Object { ($_.type -eq 0 -or $_.type -eq 1) -and $_.line -ge 1 -and $_.column -ge 0 -and
                                            $_.line -lt ($script:FbdGrid.Lines - 2) -and $_.column -lt ($script:FbdGrid.Columns - 12) } | Sort-Object line, column)) {
        $w = [math]::Max(3, [math]::Ceiling($b.name.Length / 2) + 1)
        $busy = @($blocks | Where-Object { $_.save_id -ne $b.save_id -and $_.line -ge ($b.line - 2) -and $_.line -le ($b.line + 2) -and
                                           $_.column -gt $b.column -and $_.column -le ($b.column + $w + 4) })
        if ($busy.Count -eq 0) { $pick = $b; break }
    }
    if (-not $pick) { throw 'Submit-FbdLinks: нет переменной или константы со свободными клетками справа' }
    $to = Move-FbdBlock -Block $pick -Column ($pick.column + 2) -Line $pick.line
    $moved = [pscustomobject]@{ name = $pick.name; type = $pick.type; column = $pick.column + 2; line = $pick.line
                                inp_count = $pick.inp_count; out_count = $pick.out_count }
    $back = Move-FbdBlock -Block $moved -Column $pick.column -Line $pick.line
    return ($to -and $back)
}

# ---------------- размещение ----------------

# Элементы без списка (константа, метка, прыжок, шина, соединение) ставятся
# перетаскиванием значка-руки «Применить в программе» на нужную клетку поля
# (проверено 2026-09-18). Клик по значку ничего не даёт — нужно именно тащить.
#   -Palette  'Константа' | 'Метка' | 'Прыжок' | 'Шина' | 'Соединение'
#   -Kind     значение второго комбобокса ('целая', 'Левая  силовая шина', 'Return', …)
#   -Value    текст поля ввода (значение константы, имя метки); набирается с клавиатуры,
#             SetValue в этом поле не срабатывает
function Invoke-FbdPlaceHand {
    param([Parameter(Mandatory = $true)][string]$Palette, [string]$Kind, [string]$Value,
          [Parameter(Mandatory = $true)][int]$Column, [Parameter(Mandatory = $true)][int]$Line,
          [int]$TitleRows = 0)
    Select-FbdPalette $Palette
    Start-Sleep -Milliseconds 400
    if ($Kind) { Select-FbdCombo -Index 1 -Value $Kind | Out-Null; Start-Sleep -Milliseconds 300 }
    $view = Get-FbdView
    if ($PSBoundParameters.ContainsKey('Value')) {
        $ed = @(Find-FbdFast -ControlType ([System.Windows.Automation.ControlType]::Edit)) |
              Where-Object { $_.Current.BoundingRectangle.X -gt ($view.X + $view.W) }
        if ($ed.Count -eq 0) { throw "на панели «$Palette» нет поля ввода" }
        $r = $ed[0].Current.BoundingRectangle
        Invoke-UmClick ([int]($r.X + $r.Width / 2)) ([int]($r.Y + $r.Height / 2)) -SleepMs 350
        Send-UmKeys "^a" 150
        Send-UmKeys $Value 350
        Send-UmKeys "{ENTER}" 400
    }
    $t = @(Find-FbdFast -ControlType ([System.Windows.Automation.ControlType]::Text)) |
         Where-Object { $_.Current.Name -match 'Применить в программе' }
    if ($t.Count -eq 0) { throw 'значок-рука «Применить в программе» не найден' }
    $hr = $t[0].Current.BoundingRectangle
    $view = Show-FbdCells -C1 $Column -L1 ([math]::Max(0, $Line - 2)) -C2 ($Column + 8) -L2 ($Line + 3)
    $x2 = [int]($view.X + $view.SX * $Column + $view.SX / 4 - $view.HS)
    $y2 = [int]($view.Y + $view.SY * ($Line - $TitleRows) - $view.SY / 4 - $view.VS)
    Invoke-UmDrag -X1 ([int]($hr.X + 20)) -Y1 ([int]($hr.Y + 20)) -X2 $x2 -Y2 $y2
    Start-Sleep -Milliseconds 700
    $probe = [pscustomobject]@{ type = 1; column = $Column; line = $Line; inp_count = 0; out_count = 1 }
    return [bool](Get-FbdRect -Block $probe -View (Get-FbdView))
}

# Выбрать элемент палитры справа (флажок с именем: 'Переменная', 'Константа',
# 'Оператор', 'Функциональный Блок', 'Функция', 'Структура', …). Кликом мыши.
function Select-FbdPalette {
    param([Parameter(Mandatory = $true)][string]$Name)
    $e = Find-FbdFast -ControlType ([System.Windows.Automation.ControlType]::CheckBox) -Name $Name
    if ($e.Count -eq 0) { throw "в палитре нет элемента '$Name'" }
    $r = $e[0].Current.BoundingRectangle
    # клик по значку палитры иногда не доходит — проверяем по верхнему комбобоксу и повторяем
    for ($try = 0; $try -lt 3; $try++) {
        Invoke-UmClick ([int]($r.X + $r.Width / 2)) ([int]($r.Y + $r.Height / 2)) -SleepMs 700
        $view = Get-FbdView
        $cb = @(Find-FbdFast -ControlType ([System.Windows.Automation.ControlType]::ComboBox)) |
              Where-Object { $_.Current.BoundingRectangle.X -gt ($view.X + $view.W) } |
              Sort-Object { $_.Current.BoundingRectangle.Y }
        if ($cb.Count -eq 0) { continue }
        $cur = $cb[0].GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
        if ($cur -eq $Name) { return }
    }
    throw "палитра не переключилась на '$Name'"
}

# Выбрать значение в комбобоксе панели «Добавить/Изменить» (-Index 0 — тип
# элемента, 1 — источник, 2 — словарь). SetValue, Select() и Invoke() по пункту
# значение НЕ меняют; работает только клик по пункту раскрытого списка. Координаты
# пунктов в UIA фиктивные (0, 19*N) — это смещения от окна всплывающего списка.
function Select-FbdCombo {
    param([Parameter(Mandatory = $true)][int]$Index, [Parameter(Mandatory = $true)][string]$Value)
    $view = Get-FbdView
    $cbs = @(Find-FbdFast -ControlType ([System.Windows.Automation.ControlType]::ComboBox) |
             Where-Object { $_.Current.BoundingRectangle.X -gt ($view.X + $view.W) } |
             Sort-Object { $_.Current.BoundingRectangle.Y })
    if ($cbs.Count -le $Index) { throw "в панели нет комбобокса №$Index" }
    $cb = $cbs[$Index]
    $vp = $cb.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
    if ($vp.Current.Value -eq $Value) { return $true }
    $walker = [System.Windows.Automation.TreeWalker]::RawViewWalker
    $names = @(); $list = $walker.GetFirstChild($cb)
    if ($list) { $it = $walker.GetFirstChild($list); while ($it) { $names += $it.Current.Name; $it = $walker.GetNextSibling($it) } }
    $n = [array]::IndexOf($names, $Value)
    if ($n -lt 0) { throw "в комбобоксе №$Index нет значения '$Value' (есть: $($names -join ', '))" }
    $r = $cb.Current.BoundingRectangle
    Invoke-UmClick ([int]($r.X + $r.Width / 2)) ([int]($r.Y + $r.Height / 2)) -SleepMs 600
    $pop = @(Get-UmRoots | Where-Object { $_.Current.Name -ne '' -and $_.Current.Name -notlike 'Unimod PRO 2*' -and
                                          $_.Current.BoundingRectangle.Height -lt 600 })
    if ($pop.Count -eq 0) { throw 'всплывающий список не открылся' }
    $pb = $pop[0].Current.BoundingRectangle
    $ih = $pb.Height / [math]::Max($names.Count, 1)
    Invoke-UmClick ([int]($pb.X + 40)) ([int]($pb.Y + $ih * $n + $ih / 2)) -SleepMs 700
    return ($vp.Current.Value -eq $Value)
}

# Найти пункт в списке панели; при -Parent сначала раскрыть родителя
# (категорию оператора или экземпляр ФБ). Список прокручивается колесом.
function Find-FbdPanelItem {
    param([Parameter(Mandatory = $true)][string]$Name, [string]$Parent)
    $view = Get-FbdView
    $right = $view.X + $view.W
    $find = { param($n) @(Find-FbdFast -ControlType ([System.Windows.Automation.ControlType]::TreeItem) -Name $n |
                          Where-Object { $_.Current.BoundingRectangle.X -gt $right }) }
    for ($pass = 0; $pass -lt 12; $pass++) {
        $hit = & $find $Name
        if ($hit.Count -gt 0) { return $hit[0] }
        if ($Parent) {
            $par = & $find $Parent
            if ($par.Count -gt 0) {
                $pb = $par[0].Current.BoundingRectangle
                $arrow = { Invoke-UmClick ([int]($pb.X - 12)) ([int]($pb.Y + $pb.Height / 2)) -SleepMs 500 }
                & $arrow                                   # раскрыть родителя
                $hit = & $find $Name
                if ($hit.Count -gt 0) { return $hit[0] }
                & $arrow                                   # был раскрыт, пункт просто ниже — вернуть как было
            }
        }
        # прокрутка списка: сначала вверх до упора, потом вниз
        $tree = @(Find-FbdFast -ControlType ([System.Windows.Automation.ControlType]::Tree) | Where-Object { $_.Current.BoundingRectangle.X -gt $right })
        if ($tree.Count -eq 0) { break }
        $tb = $tree[0].Current.BoundingRectangle
        [UmNative]::SetCursorPos([int]($tb.X + $tb.Width / 2), [int]($tb.Y + $tb.Height / 2)) | Out-Null
        $delta = if ($pass -lt 4) { 480 } else { [uint32]4294966816 }                            # вверх, затем вниз
        [UmNative]::mouse_event(0x0800, 0, 0, $delta, [IntPtr]::Zero)
        Start-Sleep -Milliseconds 300
    }
    throw "в списке панели не найден пункт '$Name'" + $(if ($Parent) { " (родитель '$Parent')" } else { '' })
}

# Поставить блок из списка панели в клетку (column, line) и проверить по экрану.
# Точка отпускания — левый верхний угол блока:
#   x = поле.X + sx*column + sx/4,  y = поле.Y + sy*(line - строк_заголовка) - sy/4
# Цель заранее выводится в середину поля: у краёв при перетаскивании поле
# прокручивается само, и блок встаёт не туда.
#   Переменная:  -Item a_real
#   Оператор:    -Item 'Сложение (+)' -Parent 'Арифметические' -TitleRows 1
#   ФБ из словаря: -Item TON -Parent _TON_1 -TitleRows 1  (тащить узел МЕТОДА, не экземпляр)
function Invoke-FbdPlace {
    param([Parameter(Mandatory = $true)][string]$Item, [string]$Parent,
          [Parameter(Mandatory = $true)][int]$Column, [Parameter(Mandatory = $true)][int]$Line,
          [int]$TitleRows = 0, [int]$Pins = 1, $Prog)
    # Второй блок того же экземпляра ФБ ставится (если тащить узел метода), но
    # при сохранении IDE молча теряет ВСЕ связи программы. Не допускаем.
    if ($Prog -and $Parent -and @($Prog.text.Blocks | Where-Object { $_.type -eq 3 -and $_.name -eq "$Parent.$Item" }).Count -gt 0) {
        throw "экземпляр '$Parent' уже стоит на схеме — второй блок того же экземпляра ломает сохранение связей"
    }
    Set-FbdMode -Mode edit | Out-Null
    $v0 = Get-FbdView
    $view = Set-FbdScroll -H ([int]($v0.SX * ($Column + 4) - $v0.W / 2)) -V ([int]($v0.SY * $Line - $v0.H / 2))
    $src = Find-FbdPanelItem -Name $Item -Parent $Parent
    $b = $src.Current.BoundingRectangle
    $dx = [int]($view.X + $view.SX * $Column + $view.SX / 4 - $view.HS)
    $dy = [int]($view.Y + $view.SY * ($Line - $TitleRows) - $view.SY / 4 - $view.VS)
    Invoke-UmDrag -X1 ([int]($b.X + [math]::Min(30, $b.Width / 2))) -Y1 ([int]($b.Y + $b.Height / 2)) -X2 $dx -Y2 $dy
    $type = if ($TitleRows -gt 0) { 4 } else { 0 }
    $probe = [pscustomobject]@{ type = $type; column = $Column; line = $Line; name = $Item; inp_count = $Pins; out_count = $Pins }
    return [bool](Get-FbdRect -Block $probe -View (Get-FbdView))
}

function Invoke-FbdPlaceVar {
    param([Parameter(Mandatory = $true)][string]$Name, [int]$Column, [int]$Line)
    return Invoke-FbdPlace -Item $Name -Column $Column -Line $Line
}

# Сверить сохранённый файл с ожиданием. IDE умеет сохранить схему без связей
# (например, при двух блоках одного экземпляра ФБ) и не сказать об этом.
function Assert-FbdFile {
    param([Parameter(Mandatory = $true)][string]$Path, [int]$Blocks = -1, [int]$Links = -1)
    $j = Read-FbdProg $Path
    $nb = @($j.text.Blocks).Count; $nl = @($j.text.Links).Count
    $ok = ($Blocks -lt 0 -or $nb -eq $Blocks) -and ($Links -lt 0 -or $nl -eq $Links)
    Write-Host ("  в файле блоков {0}{1}, связей {2}{3}" -f $nb, $(if ($Blocks -ge 0) { " (ожидалось $Blocks)" } else { '' }),
                $nl, $(if ($Links -ge 0) { " (ожидалось $Links)" } else { '' }))
    return $ok
}

# ---------------- код на ST и контекстное меню ----------------

# Текст вкладки «Вывод» целиком: это Edit с TextPattern, скриншоты не нужны.
function Get-FbdOutputText {
    $ed = @(Find-FbdFast -ControlType ([System.Windows.Automation.ControlType]::Edit) |
            Where-Object { $r = $_.Current.BoundingRectangle; $r.Y -gt 900 -and $r.Width -gt 1000 })
    if ($ed.Count -eq 0) { throw 'поле «Вывод» не найдено' }
    return $ed[0].GetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern).DocumentRange.GetText(-1)
}

# «Сборка → Редактор → Вывести код на ST» для активной вкладки схемы и текст результата.
# Подменю «Редактор» в UIA часто не видно, поэтому клики по координатам развёрнутого
# окна 2560×1334 (проверены 2026-09-12/13). Строки в ошибках сборки нумеруются так же.
function Get-FbdStCode {
    param([int[]]$Build = @(218, 49), [int[]]$Editor = @(289, 146), [int[]]$Item = @(570, 176))
    Send-UmKeys "{ESC}" 150
    Invoke-UmClick $Build[0] $Build[1] -SleepMs 900
    Invoke-UmClick $Editor[0] $Editor[1] -SleepMs 900
    Invoke-UmClick $Item[0] $Item[1] -SleepMs 1200
    $t = Get-FbdOutputText
    if ($t -notlike '*ST код*') { throw "в «Выводе» нет кода ST — меню не отработало: $t" }
    return $t
}

# Пункты контекстного меню схемы (правый клик) в порядке сверху вниз.
# Активность зависит от того, что выделено: «Инвертировать» — у выделенной связи,
# «Добавить eni-eno» — у ФБ, «Добавить комментарий» — на пустом месте.
$script:FbdMenuItems = @('Изменить', 'Добавить комментарий', 'Добавить eni-eno', 'Удалить eni-eno',
    'Удалить', 'Вырезать', 'Копировать', 'Вставить', 'Вставить аналог', 'Инвертировать',
    'Раскомментировать', 'Закомментировать', 'Автоматически', 'Изменить цвет')

# Выделить объект в точке (X,Y), открыть контекстное меню и выбрать пункт.
# Меню — отдельное окно «Unimod»; пункты в UIA не видны, клик по доле высоты окна.
function Invoke-FbdContextMenu {
    param([Parameter(Mandatory = $true)][int]$X, [Parameter(Mandatory = $true)][int]$Y,
          [Parameter(Mandatory = $true)][string]$Item, [switch]$NoSelect)
    $n = [array]::IndexOf($script:FbdMenuItems, $Item)
    if ($n -lt 0) { throw "нет пункта '$Item' (есть: $($script:FbdMenuItems -join ', '))" }
    Set-FbdMode -Mode edit | Out-Null
    if (-not $NoSelect) { Invoke-UmClick $X $Y -SleepMs 400 }
    [UmNative]::SetCursorPos($X, $Y) | Out-Null; Start-Sleep -Milliseconds 150
    [UmNative]::mouse_event(0x0008, 0, 0, 0, [IntPtr]::Zero); [UmNative]::mouse_event(0x0010, 0, 0, 0, [IntPtr]::Zero)
    Start-Sleep -Milliseconds 700
    $pop = @(Get-UmRoots | Where-Object { $_.Current.Name -eq 'Unimod' -and $_.Current.BoundingRectangle.Height -gt 300 })
    if ($pop.Count -eq 0) { throw 'контекстное меню не открылось' }
    $pb = $pop[0].Current.BoundingRectangle
    $ih = $pb.Height / $script:FbdMenuItems.Count
    Invoke-UmClick ([int]($pb.X + 80)) ([int]($pb.Y + $ih * $n + $ih / 2)) -SleepMs 700
}

# ---------------- правка готовой схемы мышью ----------------

function Invoke-FbdToolButton {
    param([Parameter(Mandatory = $true)][string]$Name)
    $b = @(Find-FbdFast -ControlType ([System.Windows.Automation.ControlType]::Button) -Name $Name)
    if ($b.Count -eq 0) { throw "на панели редактора нет кнопки '$Name'" }
    if (-not $b[0].Current.IsEnabled) { return $false }
    $b[0].GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
    Start-Sleep -Milliseconds 600
    return $true
}

# «отменить  изменения» (в имени два пробела) / «повторить изменения».
function Undo-Fbd { Invoke-FbdToolButton -Name 'отменить  изменения' }
function Redo-Fbd { Invoke-FbdToolButton -Name 'повторить изменения' }

# Удалить блок: выделить кликом по заголовку (у переменной — по телу) и «удалить».
# Связи блока IDE удаляет вместе с ним.
function Remove-FbdBlock {
    param([Parameter(Mandatory = $true)]$Block)
    Set-FbdMode -Mode edit | Out-Null
    $v = Show-FbdCells -C1 $Block.column -L1 ($Block.line - 2) -C2 ($Block.column + 8) -L2 ($Block.line + 2)
    $r = Get-FbdRect -Block $Block -View $v
    if (-not $r) { throw "блок '$($Block.name)' не найден на экране" }
    $y = if ($script:FbdTitleRows[[int]$Block.type]) { $r.Y + 8 } else { $r.Y + [int]($r.H / 2) }
    Invoke-UmClick ([int]($r.X + $r.W / 2)) $y -SleepMs 400
    if (-not (Invoke-FbdToolButton -Name 'удалить')) { throw "блок '$($Block.name)' не выделился — «удалить» неактивна" }
    return (-not (Get-FbdRect -Block $Block -View (Get-FbdView)))
}

# Удалить связь, входящую во вход DstSlot блока Dst: клик по её последнему
# горизонтальному участку (полклетки левее входа) в режиме редактирования.
function Remove-FbdLink {
    param([Parameter(Mandatory = $true)]$Dst, [int]$DstSlot = 0)
    Set-FbdMode -Mode edit | Out-Null
    $v = Show-FbdCells -C1 ($Dst.column - 6) -L1 ($Dst.line - 1) -C2 ($Dst.column + 8) -L2 ($Dst.line + $DstSlot + 1)
    if (-not (Test-FbdWire -Block $Dst -Slot $DstSlot -View $v)) { Write-Host '  провода во входе нет'; return $true }
    $pt = Get-FbdPinPoint -Block $Dst -Slot $DstSlot -View $v
    Clear-FbdSelection -View $v | Out-Null
    Invoke-UmClick ([int]($pt.Left - $v.SX * 0.75)) $pt.Y -SleepMs 400
    if (-not (Invoke-FbdToolButton -Name 'удалить')) { throw 'связь не выделилась — «удалить» неактивна' }
    return (-not (Test-FbdWire -Block $Dst -Slot $DstSlot -View (Get-FbdView)))
}

# Переставить блок перетаскиванием за заголовок (у переменной — за середину) в клетку.
# Смещение точки захвата сохраняется, поэтому цель считается от левого верхнего угла.
function Move-FbdBlock {
    param([Parameter(Mandatory = $true)]$Block, [int]$Column, [int]$Line)
    Set-FbdMode -Mode edit | Out-Null
    $c1 = [math]::Min($Block.column, $Column); $c2 = [math]::Max($Block.column, $Column) + 8
    $l1 = [math]::Min($Block.line, $Line) - 2; $l2 = [math]::Max($Block.line, $Line) + 3
    $v = Show-FbdCells -C1 $c1 -L1 $l1 -C2 $c2 -L2 $l2
    $r = Get-FbdRect -Block $Block -View $v
    if (-not $r) { throw "блок '$($Block.name)' не найден на экране" }
    $gx = [int]($r.X + [math]::Min($r.W / 2, $v.SX * 1.5)); $gy = $r.Y + 6
    $dx = [int](($Column - $Block.column) * $v.SX); $dy = [int](($Line - $Block.line) * $v.SY)
    Invoke-UmDrag -X1 $gx -Y1 $gy -X2 ($gx + $dx) -Y2 ($gy + $dy)
    # перенесённый блок остаётся выделенным красной пунктирной рамкой — детектор её не видит
    Clear-FbdSelection | Out-Null
    $probe = [pscustomobject]@{ type = $Block.type; column = $Column; line = $Line; inp_count = $Block.inp_count; out_count = $Block.out_count }
    return [bool](Get-FbdRect -Block $probe -View (Get-FbdView))
}
