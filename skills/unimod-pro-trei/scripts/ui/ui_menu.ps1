# Проход по пути в главном меню Unimod PRO 2 за ОДИН вызов.
#
#   .\ui_menu.ps1 -Path "Файл","Архив проекта","Упаковать проект в файл"
#   .\ui_menu.ps1 -Path "Файл" -ListOnly       — открыть и показать пункты
#
# Почему одним вызовом: всплывающее меню Qt закрывается, как только окно теряет
# фокус, а между двумя вызовами PowerShell фокус забирает окно Claude. Поэтому
# «открыть меню» и «выбрать пункт» разными вызовами не работают.
#
# Почему кликом, а не Invoke: у пункта меню есть InvokePattern, но на пункте
# верхнего уровня он не раскрывает выпадающий список. Клик раскрывает.
param(
    [Parameter(Mandatory = $true)][string[]]$Path,
    [switch]$ListOnly,
    [int]$StepSleepMs = 900
)
. "$PSScriptRoot\ui_lib.ps1"

Show-UmWindow | Out-Null
$scale = Get-UmScale

# Сброс: закрываем меню, которое могло остаться открытым от прошлого прогона.
# Иначе первый же клик по пункту верхнего уровня его ЗАКРОЕТ, а не откроет.
Send-UmKeys "{ESC}" 250
Send-UmKeys "{ESC}" 250

function Get-MenuItems {
    return @(Get-UmAllElements -MaxDepth 12 | Where-Object {
        $_.Type -eq 'MenuItem' -and -not $_.OffScreen -and $_.W -gt 0
    })
}

$done = @()
for ($i = 0; $i -lt $Path.Count; $i++) {
    $seg = $Path[$i]
    $items = Get-MenuItems
    # На верхнем уровне берём пункт из строки меню (Y мал), глубже — любой
    # подходящий, которого ещё не проходили.
    $cand = @($items | Where-Object { $_.Name -eq $seg })
    if ($cand.Count -eq 0) { $cand = @($items | Where-Object { $_.Name -like "*$seg*" }) }
    if ($cand.Count -eq 0) {
        "НЕ НАЙДЕН пункт '$seg' после пути [$($done -join ' > ')]"
        # В режиме эмуляции/отладки выпадающий список «Отладка» открывается, но
        # его пункты в UIA не видны (окно popup есть, пустое по имени) — тогда
        # идти клавиатурой: {DOWN}xN + {ENTER}, N считать по снимку меню.
        if ($i -gt 0) { "подсказка: если меню на экране открыто, а пунктов в списке ниже нет — это невидимый для UIA popup, см. known-issues.md" }
        "доступные пункты:"
        $items | ForEach-Object { "   '$($_.Name)' ($($_.X),$($_.Y))" }
        Send-UmKeys "{ESC}" 250; Send-UmKeys "{ESC}" 250
        $global:LASTEXITCODE = 2
        return
    }
    $target = $cand[0]
    # Неактивный (серый) пункт кликается без ошибки, но ничего не делает, а меню
    # остаётся открытым — раньше скрипт в этом случае рапортовал «путь пройден».
    if (-not $target.Element.Current.IsEnabled) {
        "ПУНКТ НЕАКТИВЕН: '$seg' после пути [$($done -join ' > ')]"
        Send-UmKeys "{ESC}" 250; Send-UmKeys "{ESC}" 250
        $global:LASTEXITCODE = 3
        return
    }
    $before = (Get-MenuItems).Count
    $pt = Get-UmClickPoint -Element $target.Element -Scale $scale
    Invoke-UmClick -X $pt.X -Y $pt.Y -SleepMs $StepSleepMs
    # если после клика пунктов не прибавилось — меню, скорее всего, закрылось,
    # а не раскрылось; повторяем клик один раз
    if ((Get-MenuItems).Count -le $before -and $i -lt $Path.Count - 1) {
        Invoke-UmClick -X $pt.X -Y $pt.Y -SleepMs $StepSleepMs
        "   (повторный клик: меню не раскрылось с первого раза)"
    }
    $done += $seg
    "-> '$($target.Name)' ($($pt.X),$($pt.Y))"

    if ($ListOnly -and $i -eq $Path.Count - 1) {
        "пункты после '$seg':"
        Get-MenuItems | Where-Object { $_.Name -ne $seg } |
            ForEach-Object { "   '$($_.Name)' ($($_.X),$($_.Y))" }
        return
    }
}
"путь пройден: $($done -join ' > ')"

# что открылось после последнего шага
Start-Sleep -Milliseconds 600
$wins = @(Get-UmRoots | ForEach-Object { $_.Current.Name } | Where-Object { $_ })
"окна процесса: " + ($wins -join ' | ')
