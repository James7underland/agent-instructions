# Чтение содержимого интерфейса Unimod PRO 2: деревья, таблицы, поля, вкладки.
#
#   .\ui_read.ps1                       — обзор: окна, вкладки, деревья, кнопки
#   .\ui_read.ps1 -What tree            — узлы деревьев проекта и конфигурации
#   .\ui_read.ps1 -What table           — заголовки и ячейки таблиц (словарь)
#   .\ui_read.ps1 -What buttons         — кнопки панелей с именами
#   .\ui_read.ps1 -What edit            — поля ввода и их значения
#   .\ui_read.ps1 -What all -MaxDepth 14
param(
    [ValidateSet('overview', 'tree', 'table', 'buttons', 'edit', 'tabs', 'all')]
    [string]$What = 'overview',
    [int]$MaxDepth = 12,
    [switch]$NoFocus
)
. "$PSScriptRoot\ui_lib.ps1"

if (-not $NoFocus) { Show-UmWindow | Out-Null }
$all = @(Get-UmAllElements -MaxDepth $MaxDepth | Where-Object { -not $_.OffScreen })

function Show-Group([string]$Title, $Items) {
    "=== $Title ($($Items.Count)) ==="
    foreach ($e in $Items) {
        $nm = if ($e.Name) { $e.Name } else { '<без имени>' }
        "  {0}{1} [{2}] ({3},{4})" -f (' ' * $e.Depth), $nm, $e.Type, $e.X, $e.Y
    }
}

switch ($What) {
    'tree'    { Show-Group "Узлы деревьев" @($all | Where-Object { $_.Type -in 'TreeItem', 'Tree' }) }
    'table'   { Show-Group "Таблицы: заголовки и ячейки" @($all | Where-Object { $_.Type -in 'Header', 'HeaderItem', 'DataItem', 'DataGrid', 'Table' }) }
    'buttons' { Show-Group "Кнопки" @($all | Where-Object { $_.Type -eq 'Button' -and $_.Name }) }
    'edit'    {
        "=== Поля ввода ==="
        foreach ($e in @($all | Where-Object { $_.Type -in 'Edit', 'Document' })) {
            $v = ''
            try {
                $p = $e.Element.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
                $v = $p.Current.Value
            } catch { }
            "  '{0}' [{1}] ({2},{3}) = '{4}'" -f $e.Name, $e.Type, $e.X, $e.Y, $v
        }
    }
    'tabs'    { Show-Group "Вкладки" @($all | Where-Object { $_.Type -in 'TabItem', 'Tab' }) }
    'all'     { Show-Group "Все элементы" $all }
    default   {
        "окна процесса: " + ((Get-UmRoots | ForEach-Object { "'" + $_.Current.Name + "'" }) -join ' | ')
        "элементов видимых: $($all.Count)"
        "типы: " + (($all | Group-Object Type | Sort-Object Count -Descending |
                     ForEach-Object { "$($_.Name)=$($_.Count)" }) -join ', ')
        Show-Group "Вкладки" @($all | Where-Object { $_.Type -eq 'TabItem' })
        Show-Group "Узлы деревьев" @($all | Where-Object { $_.Type -eq 'TreeItem' })
        Show-Group "Кнопки с именами" @($all | Where-Object { $_.Type -eq 'Button' -and $_.Name -and $_.X -ge 0 })
    }
}
