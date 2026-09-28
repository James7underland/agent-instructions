# Штатно закрывает Unimod PRO 2. При штатном закрытии IDE удаляет cache.tmp
# и дописывает settings.ini. Принудительное убийство процесса оставляет cache.tmp.
param([int]$WaitSec = 6)
Get-Process -Name Unimod -ErrorAction SilentlyContinue | ForEach-Object { $_.CloseMainWindow() | Out-Null }
Start-Sleep -Seconds $WaitSec
$left = @(Get-Process -Name Unimod -ErrorAction SilentlyContinue)
if ($left.Count -gt 0) {
    "не закрылось штатно (возможно, висит диалог) — убиваю принудительно"
    $left | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    "не забудь удалить cache.tmp в каталоге проекта"
} else {
    "closed"
}
