# Общая библиотека управления GUI Unimod PRO 2 через UI Automation.
# Подключать точкой:  . "$PSScriptRoot\ui_lib.ps1"
#
# Правила, зашитые здесь намеренно:
#  * окно Unimod ВСЕГДА разворачивается на весь экран (SW_MAXIMIZE), никаких
#    фиксированных MoveWindow — иначе нижние панели не попадают в снимок;
#  * масштаб DPI вычисляется в рантайме, а не берётся константой;
#  * фокус и действие делаются в одном вызове, иначе фокус уводит чужое окно.

Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes, System.Windows.Forms, System.Drawing

$sig = @'
using System;using System.Text;using System.Runtime.InteropServices;
public class UmNative{
 [StructLayout(LayoutKind.Sequential)] public struct RECT{public int L,T,R,B;}
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int n);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, IntPtr pid);
 [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint a, uint b, bool c);
 [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
 [StructLayout(LayoutKind.Sequential)] public struct PT{public int X,Y;}
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern bool GetCursorPos(out PT p);
 [DllImport("user32.dll")] public static extern bool GetPhysicalCursorPos(out PT p);
 [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint dx,uint dy,uint d,IntPtr e);
 [DllImport("kernel32.dll", CharSet=CharSet.Unicode)] public static extern int GetShortPathName(string lng, StringBuilder shrt, int cch);
}
'@
if (-not ("UmNative" -as [type])) { Add-Type -TypeDefinition $sig }

# Процесс PowerShell сам по себе НЕ DPI-aware: до первого обращения к UIA
# GetWindowRect отдаёт логические координаты (1721x927 вместо 2582x1390 при 150%),
# и снимок получается обрезанным. После первого UIA-вызова процесс становится
# DPI-aware сам — отсюда «плавающий» размер снимков. Включаем явно и сразу.
if (-not ("UmDpi" -as [type])) {
    Add-Type -TypeDefinition 'using System.Runtime.InteropServices;public class UmDpi{[DllImport("user32.dll")] public static extern bool SetProcessDPIAware();}'
}
[UmDpi]::SetProcessDPIAware() | Out-Null

$SW_MAXIMIZE = 3

# Qt отдаёт бесконечность для скрытых элементов — приводим к -1, а не падаем.
function ConvertTo-UmInt {
    param([double]$V)
    if ([double]::IsNaN($V) -or [double]::IsInfinity($V)) { return -1 }
    if ($V -gt 2147483000 -or $V -lt -2147483000) { return -1 }
    return [int]$V
}

function Get-UmProcess {
    $p = @(Get-Process -Name Unimod -ErrorAction SilentlyContinue |
           Where-Object { $_.MainWindowHandle -ne 0 })
    if ($p.Count -eq 0) { return $null }
    return $p[0]
}

if (-not ("UmEnum" -as [type])) {
    Add-Type -TypeDefinition @'
using System;using System.Text;using System.Runtime.InteropServices;
public class UmEnum{
 public delegate bool EP(IntPtr h,IntPtr l);
 [DllImport("user32.dll")] static extern bool EnumWindows(EP f,IntPtr l);
 [DllImport("user32.dll")] static extern int GetWindowText(IntPtr h,StringBuilder s,int n);
 [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
 [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
 public static IntPtr FindByPrefix(uint pid,string prefix){IntPtr res=IntPtr.Zero;EnumWindows((h,l)=>{uint p;GetWindowThreadProcessId(h,out p);if(p==pid&&IsWindowVisible(h)){var sb=new StringBuilder(256);GetWindowText(h,sb,256);if(sb.ToString().StartsWith(prefix)){res=h;return false;}}return true;},IntPtr.Zero);return res;}
}
'@
}

# Handle ГЛАВНОГО окна IDE. Process.MainWindowHandle для этого не годится:
# пока открыто выпадающее меню, Windows считает главным окном сам popup
# (заголовок 'Unimod', класс Qt5152QWindowPopupDropShadowSaveBits) — тогда
# Show-UmWindow «разворачивает» меню, а Save-UmShot снимает его вместо окна.
function Get-UmMainHandle {
    $p = Get-UmProcess
    if ($null -eq $p) { throw "Unimod не запущен" }
    $h = [UmEnum]::FindByPrefix([uint32]$p.Id, 'Unimod PRO 2')
    if ($h -eq [IntPtr]::Zero) { $h = [IntPtr]$p.MainWindowHandle }
    return $h
}

# Разворачивает окно на весь экран и выводит на передний план.
# Возвращает handle. Вызывать перед ЛЮБЫМ действием.
function Show-UmWindow {
    $h = Get-UmMainHandle
    $fg = [UmNative]::GetForegroundWindow()
    $t1 = [UmNative]::GetWindowThreadProcessId($fg, [IntPtr]::Zero)
    $t2 = [UmNative]::GetCurrentThreadId()
    [UmNative]::AttachThreadInput($t1, $t2, $true) | Out-Null
    # Сначала SW_RESTORE, потом SW_MAXIMIZE. Без restore система считает окно
    # уже развёрнутым и повторный maximize игнорирует — так бывает после
    # модальных диалогов, и окно остаётся уменьшенным.
    [UmNative]::ShowWindow($h, 9) | Out-Null              # SW_RESTORE
    Start-Sleep -Milliseconds 150
    [UmNative]::ShowWindow($h, $SW_MAXIMIZE) | Out-Null   # всегда на весь экран
    [UmNative]::SetForegroundWindow($h) | Out-Null
    [UmNative]::AttachThreadInput($t1, $t2, $false) | Out-Null
    Start-Sleep -Milliseconds 600
    return $h
}

# ВСЕ окна верхнего уровня процесса Unimod.
# Важно: выпадающие меню, диалоги и всплывающие подсказки Qt — это отдельные
# окна верхнего уровня, а не дети главного окна. Если обходить только главное,
# пункты открытого меню и кнопки диалогов просто не найдутся.
function Get-UmRoots {
    $p = Get-UmProcess
    if ($null -eq $p) { throw "Unimod не запущен" }
    $cond = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ProcessIdProperty, $p.Id)
    $desktop = [System.Windows.Automation.AutomationElement]::RootElement
    $found = $desktop.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)
    $res = New-Object System.Collections.ArrayList
    foreach ($e in $found) { [void]$res.Add($e) }
    return $res
}

# Главное окно (первое из окон процесса).
function Get-UmRoot {
    $all = Get-UmRoots
    if ($all.Count -eq 0) { return $null }
    foreach ($e in $all) {
        if ($e.Current.Name -like 'Unimod PRO 2*') { return $e }
    }
    return $all[0]
}

# Масштаб между координатами UIA (физические пиксели) и координатами SetCursorPos.
# Меряем эмпирически: ставим курсор и сравниваем логическую позицию с физической.
# Сравнивать ширину окна из GetWindowRect бесполезно — у развёрнутого окна рамка
# выходит за экран, и получается мусорный коэффициент вроде 0.99.
function Get-UmScale {
    $save = New-Object UmNative+PT
    [UmNative]::GetCursorPos([ref]$save) | Out-Null
    [UmNative]::SetCursorPos(1000, 500) | Out-Null
    Start-Sleep -Milliseconds 60
    $log = New-Object UmNative+PT
    $phys = New-Object UmNative+PT
    [UmNative]::GetCursorPos([ref]$log) | Out-Null
    $okPhys = [UmNative]::GetPhysicalCursorPos([ref]$phys)
    [UmNative]::SetCursorPos($save.X, $save.Y) | Out-Null
    if (-not $okPhys -or $log.X -eq 0) { return 1.0 }
    return [math]::Round($phys.X / $log.X, 4)
}

# Центр элемента в координатах, пригодных для SetCursorPos (логических).
function Get-UmClickPoint {
    param($Element, [double]$Scale)
    $b = $Element.Current.BoundingRectangle
    return @{ X = [int]([math]::Round(($b.X + $b.Width / 2) / $Scale))
              Y = [int]([math]::Round(($b.Y + $b.Height / 2) / $Scale)) }
}

function Invoke-UmClick {
    param([int]$X, [int]$Y, [int]$SleepMs = 600)
    [UmNative]::SetCursorPos($X, $Y) | Out-Null
    Start-Sleep -Milliseconds 150
    [UmNative]::mouse_event(0x0002, 0, 0, 0, [IntPtr]::Zero)   # LEFTDOWN
    [UmNative]::mouse_event(0x0004, 0, 0, 0, [IntPtr]::Zero)   # LEFTUP
    Start-Sleep -Milliseconds $SleepMs
}

function Send-UmKeys {
    param([string]$Keys, [int]$SleepMs = 500)
    [System.Windows.Forms.SendKeys]::SendWait($Keys)
    Start-Sleep -Milliseconds $SleepMs
}

# Обход дерева UIA. Возвращает плоский список с глубиной.
function Get-UmElements {
    param($Root, [int]$MaxDepth = 8, [int]$Limit = 4000)
    $walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
    $res = New-Object System.Collections.ArrayList
    $stack = New-Object System.Collections.Stack
    $stack.Push(@($Root, 0))
    while ($stack.Count -gt 0 -and $res.Count -lt $Limit) {
        $item = $stack.Pop()
        $el = $item[0]; $depth = $item[1]
        try { $cur = $el.Current } catch { continue }
        # у скрытых/офскрин элементов Qt отдаёт BoundingRectangle = бесконечность
        $b = $cur.BoundingRectangle
        [void]$res.Add([pscustomobject]@{
            Depth = $depth
            Type  = ($cur.ControlType.ProgrammaticName -replace '^ControlType\.', '')
            Name  = $cur.Name
            AutomationId = $cur.AutomationId
            X = (ConvertTo-UmInt $b.X)
            Y = (ConvertTo-UmInt $b.Y)
            W = (ConvertTo-UmInt $b.Width)
            H = (ConvertTo-UmInt $b.Height)
            OffScreen = ([double]::IsInfinity($b.X) -or $cur.IsOffscreen)
            Element = $el
        })
        if ($depth -ge $MaxDepth) { continue }
        $kids = New-Object System.Collections.ArrayList
        try {
            $c = $walker.GetFirstChild($el)
            while ($null -ne $c) { [void]$kids.Add($c); $c = $walker.GetNextSibling($c) }
        } catch { }
        for ($i = $kids.Count - 1; $i -ge 0; $i--) { $stack.Push(@($kids[$i], $depth + 1)) }
    }
    return $res
}

# Все элементы всех окон процесса (главное окно + меню + диалоги).
function Get-UmAllElements {
    param([int]$MaxDepth = 8)
    $res = New-Object System.Collections.ArrayList
    foreach ($r in Get-UmRoots) {
        try { $wn = $r.Current.Name } catch { continue }
        foreach ($e in (Get-UmElements -Root $r -MaxDepth $MaxDepth)) {
            $e | Add-Member -NotePropertyName Window -NotePropertyValue $wn -Force
            [void]$res.Add($e)
        }
    }
    return $res
}

# Поиск по части имени и (необязательно) типу — по всем окнам процесса.
function Find-UmElement {
    param($Root, [string]$Name, [string]$Type, [int]$MaxDepth = 8)
    $all = if ($null -ne $Root) { Get-UmElements -Root $Root -MaxDepth $MaxDepth }
           else { Get-UmAllElements -MaxDepth $MaxDepth }
    $hit = $all | Where-Object {
        (-not $Name -or ($_.Name -and $_.Name -like "*$Name*")) -and
        (-not $Type -or $_.Type -eq $Type)
    }
    return $hit
}

# Действие над элементом: Invoke, если поддержан, иначе клик по центру.
function Invoke-UmElement {
    param($Item, [double]$Scale, [int]$SleepMs = 700)
    $el = $Item.Element
    $pattern = $null
    try {
        $pattern = $el.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
    } catch { }
    if ($null -ne $pattern) {
        $pattern.Invoke()
        Start-Sleep -Milliseconds $SleepMs
        return "invoked"
    }
    $pt = Get-UmClickPoint -Element $el -Scale $Scale
    Invoke-UmClick -X $pt.X -Y $pt.Y -SleepMs $SleepMs
    return "clicked $($pt.X),$($pt.Y)"
}

# Снимок всего окна Unimod (в физических пикселях, окно развёрнуто).
function Save-UmShot {
    param([string]$Out)
    $h = Get-UmMainHandle
    $r = New-Object UmNative+RECT
    [UmNative]::GetWindowRect($h, [ref]$r) | Out-Null
    $scale = Get-UmScale
    $x = [int]($r.L * $scale); $y = [int]($r.T * $scale)
    $w = [int](($r.R - $r.L) * $scale); $ht = [int](($r.B - $r.T) * $scale)
    $bmp = New-Object System.Drawing.Bitmap($w, $ht)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($x, $y, 0, 0, $bmp.Size)
    $bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
    return "saved $Out ${w}x${ht}"
}

# Закрепить окно IDE поверх остальных окон. Без этого чужое окно (например,
# Claude) перехватывает фокус, и синтетические клики уходят мимо IDE.
# В конце работы обязательно снять: Set-UmTopmost -Off
function Set-UmTopmost {
    param([switch]$Off)
    if (-not ("UmTop" -as [type])) {
        Add-Type -TypeDefinition 'using System;using System.Runtime.InteropServices;public class UmTop{[DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h,IntPtr a,int x,int y,int cx,int cy,uint f);}'
    }
    $h = Get-UmMainHandle
    $after = if ($Off) { [IntPtr](-2) } else { [IntPtr](-1) }   # HWND_NOTOPMOST / HWND_TOPMOST
    [UmTop]::SetWindowPos($h, $after, 0, 0, 0, 0, 0x0013) | Out-Null   # NOMOVE|NOSIZE|NOACTIVATE
    if ($Off) { "окно откреплено" } else { "окно закреплено поверх остальных" }
}

# Вернуть окну IDE настоящий фокус (нужен для SendKeys и главного меню).
# Возвращает $true, если получилось.
function Confirm-UmFocus {
    param([int]$Tries = 6)
    if (-not ("UmFg" -as [type])) {
        Add-Type -TypeDefinition 'using System;using System.Runtime.InteropServices;public class UmFg{[DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();}'
    }
    for ($i = 0; $i -lt $Tries; $i++) {
        $h = Show-UmWindow
        Start-Sleep -Milliseconds 250
        if ([UmFg]::GetForegroundWindow() -eq $h) { return $true }
    }
    return $false
}

# Перетаскивание мышью: зажать в (X1,Y1), провести шагами, отпустить в (X2,Y2).
# Именно так в редакторе FBD блок переносится из панели на схему и двигается
# по ней. Одиночные клики для этого не работают.
function Invoke-UmDrag {
    param([int]$X1, [int]$Y1, [int]$X2, [int]$Y2, [int]$Steps = 20, [int]$StepMs = 35)
    [UmNative]::SetCursorPos($X1, $Y1) | Out-Null
    Start-Sleep -Milliseconds 250
    [UmNative]::mouse_event(0x0002, 0, 0, 0, [IntPtr]::Zero)      # LEFTDOWN
    Start-Sleep -Milliseconds 250
    for ($i = 1; $i -le $Steps; $i++) {
        [UmNative]::SetCursorPos([int]($X1 + ($X2 - $X1) * $i / $Steps),
                                 [int]($Y1 + ($Y2 - $Y1) * $i / $Steps)) | Out-Null
        Start-Sleep -Milliseconds $StepMs
    }
    Start-Sleep -Milliseconds 300
    [UmNative]::mouse_event(0x0004, 0, 0, 0, [IntPtr]::Zero)      # LEFTUP
    Start-Sleep -Milliseconds 800
}

# Координаты в редакторе FBD — в fbd_lib.ps1 (калибровка по полосам прокрутки,
# без зашитых констант).
