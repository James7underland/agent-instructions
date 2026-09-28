# Выводит главное окно Unimod PRO 2 на передний план.
# Нужно перед отправкой горячих клавиш (Ctrl+S, F9).
$sig = @'
using System;using System.Runtime.InteropServices;
public class UmFocus{
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int n);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, IntPtr pid);
 [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint a, uint b, bool c);
 [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
 public delegate bool EP(IntPtr h,IntPtr l);
 [DllImport("user32.dll")] static extern bool EnumWindows(EP f,IntPtr l);
 [DllImport("user32.dll")] static extern int GetWindowText(IntPtr h,System.Text.StringBuilder s,int n);
 [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
 [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
 public static IntPtr FindByPrefix(uint pid,string prefix){IntPtr res=IntPtr.Zero;EnumWindows((h,l)=>{uint p;GetWindowThreadProcessId(h,out p);if(p==pid&&IsWindowVisible(h)){var sb=new System.Text.StringBuilder(256);GetWindowText(h,sb,256);if(sb.ToString().StartsWith(prefix)){res=h;return false;}}return true;},IntPtr.Zero);return res;}
}
'@
if (-not ("UmFocus" -as [type])) { Add-Type -TypeDefinition $sig }

$p = @(Get-Process -Name Unimod -ErrorAction Stop | Where-Object { $_.MainWindowHandle -ne 0 })[0]
# главное окно ищем по заголовку: при открытом меню MainWindowHandle — это popup
$h = [UmFocus]::FindByPrefix([uint32]$p.Id, 'Unimod PRO 2')
if ($h -eq [IntPtr]::Zero) { $h = [IntPtr]$p.MainWindowHandle }
$fg = [UmFocus]::GetForegroundWindow()
$t1 = [UmFocus]::GetWindowThreadProcessId($fg, [IntPtr]::Zero)
$t2 = [UmFocus]::GetCurrentThreadId()
[UmFocus]::AttachThreadInput($t1, $t2, $true) | Out-Null
[UmFocus]::ShowWindow($h, 3) | Out-Null   # SW_MAXIMIZE: окно всегда на весь экран,
                                          # иначе нижние панели не попадают в снимок
[UmFocus]::SetForegroundWindow($h) | Out-Null
[UmFocus]::AttachThreadInput($t1, $t2, $false) | Out-Null
Start-Sleep -Milliseconds 800
"focused"
