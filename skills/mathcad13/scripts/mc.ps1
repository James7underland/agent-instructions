<#
.SYNOPSIS
  Mathcad 13 COM driver: open a worksheet, set inputs, recalculate, report errors/values, save/export.

.DESCRIPTION
  Mathcad 13 is a 32-bit COM server (Mathcad.Application). When started from 64-bit PowerShell this
  script relaunches itself in 32-bit PowerShell (SysWOW64), waits with a timeout and prints JSON.
  Region properties are read with late binding (InvokeMember) because early binding returns empty values.

.EXAMPLE
  mc.ps1 -Action info
  mc.ps1 -Path calc.xmcd -Regions                      # errors per region
  mc.ps1 -Path calc.xmcd -Get "y,M" -SaveAs out.xmcd   # values + recalculated copy (results inside)
  mc.ps1 -Path calc.xmcd -Set "L=3.5;v=[1,2,3]" -Get Smax
  mc.ps1 -Path calc.xmcd -SaveAs report.rtf            # export: .xmcd .xmcdz .rtf .htm/.html .mcd(v11) .xmct
  mc.ps1 -Action new -SaveAs empty.xmcd [-Template "...\template\Normal.xmct"]
#>
param(
  [ValidateSet('run', 'info', 'new')][string]$Action = 'run',
  [string]$Path = '',
  [string]$Set = '',
  [string]$Get = '',
  [switch]$Regions,
  [switch]$Xml,
  [string]$SaveAs = '',
  [string]$Format = '',
  [string]$Template = '',
  [string]$Json = '',
  [int]$Timeout = 300,
  [switch]$Visible,
  [switch]$NoRecalc,
  [string]$Meta = '',
  [string]$ArgsFile = ''
)

$ErrorActionPreference = 'Stop'

function Find-McadDir {
  # same order as find_mathcad.py: env MATHCAD13_DIR -> COM LocalServer32 -> Uninstall entry -> default folders
  $cands = @()
  if ($env:MATHCAD13_DIR) { $cands += $env:MATHCAD13_DIR }
  $clsid = (Get-ItemProperty 'Registry::HKEY_CLASSES_ROOT\Mathcad.Application\CLSID' -ErrorAction SilentlyContinue).'(default)'
  if ($clsid) {
    foreach ($k in @('WOW6432Node\CLSID', 'CLSID')) {
      $srv = (Get-ItemProperty "Registry::HKEY_CLASSES_ROOT\$k\$clsid\LocalServer32" -ErrorAction SilentlyContinue).'(default)'
      if ($srv -and $srv -match '^\s*"?(.+?\.exe)') { $cands += (Split-Path $Matches[1]) }
    }
  }
  foreach ($u in @('HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
                   'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*')) {
    Get-ItemProperty $u -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -match '^Mathcad 13\b' -and $_.InstallLocation } |
      ForEach-Object { $cands += $_.InstallLocation }
  }
  foreach ($b in @(${env:ProgramFiles(x86)}, $env:ProgramFiles)) { if ($b) { $cands += (Join-Path $b 'Mathsoft\Mathcad 13') } }
  foreach ($c in $cands) { if (Test-Path -LiteralPath (Join-Path $c 'mathcad.exe')) { return $c.TrimEnd('\') } }
  return ''
}
$McadDir = Find-McadDir

function Resolve-Full([string]$p) {
  if (-not $p) { return '' }
  return $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($p)
}

function Get-AutomationPids([datetime]$Since = [datetime]::MinValue) {
  # COM-launched instances have "-Embedding" on the command line; exited processes can still be listed
  # while someone holds a handle, so keep only the ones that are really alive
  @(Get-CimInstance Win32_Process -Filter "Name='mathcad.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match '(?i)embedding|automation' -and $_.CreationDate -ge $Since } | ForEach-Object { [int]$_.ProcessId } |
    Where-Object { $pr = Get-Process -Id $_ -ErrorAction SilentlyContinue; $pr -and -not $pr.HasExited })
}

# ---------------------------------------------------------------- 64-bit parent: relaunch as 32-bit
if ([IntPtr]::Size -eq 8 -and -not $ArgsFile) {
  $tmp = Join-Path ([IO.Path]::GetTempPath()) ('mc_' + [guid]::NewGuid().ToString('N'))
  $opt = [ordered]@{
    Action = $Action; Path = (Resolve-Full $Path); Set = $Set; Get = $Get; Regions = [bool]$Regions
    Xml = [bool]$Xml; SaveAs = (Resolve-Full $SaveAs); Format = $Format; Template = (Resolve-Full $Template)
    Visible = [bool]$Visible; NoRecalc = [bool]$NoRecalc; Meta = $Meta; OutFile = "$tmp.out.json"
  }
  $opt | ConvertTo-Json | Set-Content "$tmp.args.json" -Encoding UTF8
  $launched = Get-Date
  $ps32 = Join-Path $env:WINDIR 'SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
  $proc = Start-Process $ps32 -PassThru -WindowStyle Hidden -RedirectStandardError "$tmp.err.txt" `
    -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -ArgsFile `"$tmp.args.json`""
  # The child writes its JSON atomically and then cleans up its own Mathcad server (which sometimes
  # hangs on shutdown); return as soon as the result exists instead of waiting for that cleanup.
  $deadline = (Get-Date).AddSeconds($Timeout)
  while (-not (Test-Path "$tmp.out.json") -and -not $proc.HasExited -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 100 }
  if (Test-Path "$tmp.out.json") {
    $out = Get-Content "$tmp.out.json" -Raw -Encoding UTF8
    # the child keeps running a few seconds to make sure its Mathcad server is gone; no need to wait
  } elseif ($proc.HasExited) {
    $err = ''
    if (Test-Path "$tmp.err.txt") { $err = [string](Get-Content "$tmp.err.txt" -Raw) }
    $out = [ordered]@{ ok = $false; error = "32-bit child produced no output"; stderr = $err } | ConvertTo-Json
  } else {
    try { $proc.Kill() } catch {}
    Get-AutomationPids -Since $launched | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
    $out = [ordered]@{ ok = $false; error = "timeout after $Timeout s (Mathcad killed; a modal dialog or endless calculation?)" } | ConvertTo-Json
  }
  Remove-Item "$tmp.args.json", "$tmp.out.json", "$tmp.err.txt" -ErrorAction SilentlyContinue
  [Console]::OutputEncoding = [Text.Encoding]::UTF8
  if ($Json) { Set-Content -Path (Resolve-Full $Json) -Value $out -Encoding UTF8 }
  $out
  return
}

# ---------------------------------------------------------------- 32-bit worker
if ($ArgsFile) {
  $o = Get-Content $ArgsFile -Raw -Encoding UTF8 | ConvertFrom-Json
} else {
  $o = [pscustomobject]@{ Action = $Action; Path = (Resolve-Full $Path); Set = $Set; Get = $Get; Regions = [bool]$Regions
    Xml = [bool]$Xml; SaveAs = (Resolve-Full $SaveAs); Format = $Format; Template = (Resolve-Full $Template)
    Visible = [bool]$Visible; NoRecalc = [bool]$NoRecalc; Meta = $Meta; OutFile = (Resolve-Full $Json) }
}

$BF = [Reflection.BindingFlags]
function P($obj, [string]$name) { [System.__ComObject].InvokeMember($name, $BF::GetProperty, $null, $obj, $null) }
function SetP($obj, [string]$name, $v) { [void][System.__ComObject].InvokeMember($name, $BF::SetProperty, $null, $obj, @($v)) }
function M($obj, [string]$name, [object[]]$a) { [System.__ComObject].InvokeMember($name, $BF::InvokeMethod, $null, $obj, $a) }
function ErrText($e) { if ($e.Exception.InnerException) { $e.Exception.InnerException.Message } else { $e.Exception.Message } }

$script:msgMap = $null
function Get-MessageText([string]$code) {
  if ($null -eq $script:msgMap) {
    $script:msgMap = @{}
    try {
      [xml]$mx = Get-Content (Join-Path $McadDir 'messages\messages_EN.xml') -Raw -Encoding UTF8
      foreach ($m in $mx.messages.message) { if ($m.short_name) { $script:msgMap[[string]$m.short_name] = [string]$m.text } }
    } catch {}
  }
  if ($script:msgMap.ContainsKey($code)) { return $script:msgMap[$code] }
  return ''
}

# GetValue/SetValue expect Greek letters as "\" + the Latin key of the Symbol font (σ -> \s, φ -> \f)
# (built from code points: this file is read as ANSI by PowerShell 5.1, and @{} is case-insensitive)
$script:greek = New-Object 'System.Collections.Generic.Dictionary[char,string]'
$lower = 'abgdezhqiklmnxoprVstufcyw'   # U+03B1 alpha .. U+03C9 omega (U+03C2 final sigma = V)
$upper = 'ABGDEZHQIKLMNXOPR?STUFCYW'   # U+0391 Alpha .. U+03A9 Omega (U+03A2 unassigned)
for ($n = 0; $n -lt 25; $n++) {
  $script:greek[[char](0x3B1 + $n)] = '\' + $lower[$n]
  if ($upper[$n] -ne '?') { $script:greek[[char](0x391 + $n)] = '\' + $upper[$n] }
}
$script:greek[[char]0x3D5] = '\j'; $script:greek[[char]0x3D1] = '\J'   # phi / theta symbol variants
function Convert-Name([string]$name) {
  $sb = New-Object System.Text.StringBuilder
  foreach ($ch in $name.ToCharArray()) {
    if ($script:greek.ContainsKey($ch)) { [void]$sb.Append($script:greek[$ch]) } else { [void]$sb.Append($ch) }
  }
  $sb.ToString()
}

function Convert-Value($v) {
  if ($null -eq $v) { return $null }
  $t = [string]$v.Type
  switch ($t) {
    'Numeric' { return [ordered]@{ type = 'num'; re = [double]$v.Real; im = [double]$v.Imag; text = [string]$v.AsString } }
    'String' { return [ordered]@{ type = 'str'; value = [string]$v.Value } }
    'Matrix' {
      $rows = [int]$v.Rows; $cols = [int]$v.Cols; $data = @()
      for ($r = 0; $r -lt $rows; $r++) {
        $row = @()
        for ($c = 0; $c -lt $cols; $c++) {
          $e = $v.GetElement($r, $c)
          if ([string]$e.Type -eq 'Numeric' -and [double]$e.Imag -eq 0) { $row += [double]$e.Real }
          else { $row += , (Convert-Value $e) }
        }
        $data += , $row
      }
      return [ordered]@{ type = 'matrix'; rows = $rows; cols = $cols; data = $data }
    }
    default { return [ordered]@{ type = $t; text = [string]$v.AsString } }
  }
}

function Convert-Input($s) {
  $s = $s.Trim()
  try { $j = $s | ConvertFrom-Json } catch { return $s }   # bare word -> string
  if ($j -is [array]) {
    if ($j.Count -gt 0 -and $j[0] -is [array]) {            # [[..],[..]] -> 2-D double array (row-major input)
      $a = New-Object 'double[,]' $j.Count, $j[0].Count
      for ($r = 0; $r -lt $j.Count; $r++) { for ($c = 0; $c -lt $j[0].Count; $c++) { $a[$r, $c] = [double]$j[$r][$c] } }
      return , $a
    }
    return , ([double[]]$j)
  }
  if ($j -is [string]) { return $j }
  return [double]$j
}

function Get-FormatCode([string]$fmt, [string]$file) {
  $map = @{ xmcd = 18; xmcdz = 19; htm = 3; html = 3; rtf = 16; mcd = 17; mcd11 = 17; xmct = 15; mathml = 2; mml = 2; mcd2001 = 8; mcd2001i = 11; mcd12 = 12; xmcd12 = 13 }
  if ($fmt) { if ($fmt -match '^\d+$') { return [int]$fmt }; return $map[$fmt.ToLower()] }
  $ext = [IO.Path]::GetExtension($file).TrimStart('.').ToLower()
  if ($map.ContainsKey($ext)) { return $map[$ext] }
  return 0
}

$script:tStart = Get-Date
$res = [ordered]@{ ok = $false; action = $o.Action }
$mc = $null; $ws = $null
$regionTypes = @{ 0 = 'text'; 1 = 'math'; 2 = 'bitmap'; 3 = 'metafile'; 4 = 'ole' }
try {
  $t0 = Get-Date
  $mc = New-Object -ComObject Mathcad.Application
  try { $mc.SetOption(0, $false) } catch {}      # mcShowMessageBoxes = false
  if ($o.Visible) { $mc.Visible = $true }
  try {                                           # exact PID of the COM server, so the parent can clean it up
    Add-Type -Namespace McNative -Name Win -MemberDefinition '[DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(System.IntPtr hWnd, out uint pid);'
    $mpid = [uint32]0
    [void][McNative.Win]::GetWindowThreadProcessId([IntPtr][int](P $mc 'HWND'), [ref]$mpid)
    $res.mathcad_pid = [int]$mpid
  } catch {}
  $res.version = [string]$mc.Version
  $res.start_s = [math]::Round(((Get-Date) - $t0).TotalSeconds, 2)

  if ($o.Action -eq 'info') {
    $res.fullName = [string]$mc.FullName
    $res.install_dir = $McadDir
    $res.defaultFilePath = [string]$mc.DefaultFilePath
    $res.ok = $true
  } else {
    if ($o.Action -eq 'new') {
      if ($o.Template) { $ws = M $mc.Worksheets 'AddFromTemplate' @($o.Template) } else { $ws = $mc.Worksheets.Add() }
    } else {
      if (-not (Test-Path -LiteralPath $o.Path)) { throw "File not found: $($o.Path)" }
      if ($o.Path -match '\.mcdx$') { throw "Mathcad Prime file (.mcdx): Mathcad 13 cannot open Prime worksheets" }
      $t0 = Get-Date
      $ws = $mc.Worksheets.Open($o.Path)
      $res.open_s = [math]::Round(((Get-Date) - $t0).TotalSeconds, 2)
    }
    $res.worksheet = [string]$ws.FullName

    if ($o.Set) {
      $res.set = [ordered]@{}
      $pairs = New-Object System.Collections.ArrayList
      if ($o.Set.Trim().StartsWith('{')) {
        $jo = $o.Set | ConvertFrom-Json
        foreach ($pr in $jo.PSObject.Properties) { [void]$pairs.Add(@($pr.Name, ($pr.Value | ConvertTo-Json -Compress))) }
      } else {
        foreach ($part in ($o.Set -split ';')) {
          if (-not $part.Trim()) { continue }
          $kv = $part -split '=', 2
          [void]$pairs.Add(@($kv[0].Trim(), $kv[1]))
        }
      }
      foreach ($p in $pairs) {
        try { $ws.SetValue((Convert-Name $p[0]), (Convert-Input $p[1])); $res.set[$p[0]] = 'ok' } catch { $res.set[$p[0]] = 'ERROR: ' + (ErrText $_) }
      }
    }

    if (-not $o.NoRecalc) {
      $t0 = Get-Date
      $ws.Recalculate()
      $res.recalc_s = [math]::Round(((Get-Date) - $t0).TotalSeconds, 2)
    }

    # region scan (always count errors; full list with -Regions)
    $regs = $ws.Regions
    $n = [int]$regs.Count
    $res.region_count = $n
    $list = @(); $errs = @(); $counts = @{}
    for ($k = 0; $k -lt $n; $k++) {
      $r = $regs.Item($k)
      $info = [ordered]@{ i = $k }
      try {
        $tp = [int](P $r 'Type')
        $info.type = $regionTypes[$tp]
        $info.tag = [string](P $r 'Tag')
        $info.x = [int](P $r 'X'); $info.y = [int](P $r 'Y')
        $counts[$info.type] = 1 + [int]$counts[$info.type]
        if ($tp -eq 1) {
          $mi = P $r 'MathInterface'
          $he = [bool](P $mi 'HasError')
          $info.error = $he
          if ($he) {
            $raw = [string](P $mi 'ErrorMsg')
            $code = ($raw -split "`t")[0]
            $info.error_code = $code
            $info.error_text = Get-MessageText $code
            $info.error_raw = $raw
          }
          if ($o.Xml -or $he) { $info.xml = ([string](P $mi 'XML')) -replace '\s*\r?\n\s*', '' }
          if ($he) { $errs += $info }
        }
      } catch { $info.scan_error = ErrText $_ }
      $list += $info
    }
    $res.region_types = $counts
    $res.error_count = $errs.Count
    $res.errors = $errs
    if ($o.Regions) { $res.regions = $list }

    if ($o.Get) {
      $res.values = [ordered]@{}
      foreach ($name in ($o.Get -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })) {
        try { $res.values[$name] = Convert-Value ($ws.GetValue((Convert-Name $name))) } catch { $res.values[$name] = [ordered]@{ type = 'error'; error = (ErrText $_) } }
      }
    }

    $mdObj = $null
    try { $mdObj = P $ws 'Metadata' } catch {}   # not $meta: PowerShell names are case-insensitive (-Meta param)
    if ($mdObj -and $o.Meta) {                # -Meta "Title=...;Author=..." (Title Author Company Description Keywords RevisedBy)
      foreach ($part in ($o.Meta -split ';')) {
        $kv = $part -split '=', 2
        if ($kv.Count -eq 2) { try { SetP $mdObj $kv[0].Trim() $kv[1] } catch { $res.meta_error = ErrText $_ } }
      }
    }
    if ($mdObj) {
      $res.metadata = [ordered]@{}
      foreach ($f in 'Title', 'Author', 'Company', 'Description', 'Keywords', 'RevisedBy', 'Revision') {
        try { $res.metadata[$f] = [string](P $mdObj $f) } catch {}
      }
    }

    if ($o.SaveAs) {
      $code = Get-FormatCode $o.Format $o.SaveAs
      $dir = Split-Path -Parent $o.SaveAs
      if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
      $ws.SaveAs($o.SaveAs, $code)
      $res.saved = [ordered]@{ path = $o.SaveAs; format = $code; exists = (Test-Path -LiteralPath $o.SaveAs) }
      if ($res.saved.exists) { $res.saved.bytes = (Get-Item -LiteralPath $o.SaveAs).Length }
    }
    $res.ok = $true
  }
} catch {
  $res.error = ErrText $_
} finally {
  $t0 = Get-Date
  if ($ws) { try { $ws.Close(2) } catch {} }          # mcDiscardChanges
  $res.close_s = [math]::Round(((Get-Date) - $t0).TotalSeconds, 2)
  Start-Sleep -Milliseconds 300                        # Quit right after Close sometimes leaves mathcad.exe alive
  $t0 = Get-Date
  if ($mc) {
    try { $mc.Quit(2) } catch {}
    try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($mc) } catch {}
  }
  $res.quit_s = [math]::Round(((Get-Date) - $t0).TotalSeconds, 2)
}
$res.total_s = [math]::Round(((Get-Date) - $script:tStart).TotalSeconds, 2)

$outJson = $res | ConvertTo-Json -Depth 20
if ($o.OutFile) {                                      # write + rename so the parent never reads a partial file
  Set-Content -Path "$($o.OutFile).part" -Value $outJson -Encoding UTF8
  Move-Item -Force "$($o.OutFile).part" $o.OutFile
}
if (-not $ArgsFile) { [Console]::OutputEncoding = [Text.Encoding]::UTF8; $outJson }

# Mathcad normally exits ~2 s after Quit but sometimes hangs on shutdown: kill our own server if needed
if ($res.mathcad_pid) {
  $deadline = (Get-Date).AddSeconds(4)
  do { $pr = Get-Process -Id $res.mathcad_pid -ErrorAction SilentlyContinue; $alive = $pr -and -not $pr.HasExited; if ($alive) { Start-Sleep -Milliseconds 200 } }
  while ($alive -and (Get-Date) -lt $deadline)
  if ($alive) { Stop-Process -Id $res.mathcad_pid -Force -ErrorAction SilentlyContinue }
}
if ($ArgsFile) { [Environment]::Exit(0) }             # only in the relaunched child, never in a user's session
