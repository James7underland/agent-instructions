# Снимок окна Unimod PRO 2 целиком (окно предварительно разворачивается).
#
#   .\ui_shot.ps1 -Out "C:\tmp\shot.png"
#   .\ui_shot.ps1 -Out "C:\tmp\dlg.png" -Region 900,600,600,250
#
# Снимок делается через CopyFromScreen в физических координатах — тех же, что
# отдаёт UIA. Поэтому прямоугольник любого элемента из ui_read/ui_tree можно
# подставлять в -Region без пересчёта.
param(
    [Parameter(Mandatory = $true)][string]$Out,
    [int[]]$Region,
    [switch]$NoFocus
)
. "$PSScriptRoot\ui_lib.ps1"

if (-not $NoFocus) { Show-UmWindow | Out-Null }

if ($Region -and $Region.Count -eq 4) {
    Add-Type -AssemblyName System.Drawing
    $bmp = New-Object System.Drawing.Bitmap($Region[2], $Region[3])
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($Region[0], $Region[1], 0, 0, $bmp.Size)
    $bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
    "saved $Out $($Region[2])x$($Region[3]) from $($Region[0]),$($Region[1])"
} else {
    Save-UmShot -Out $Out
}
