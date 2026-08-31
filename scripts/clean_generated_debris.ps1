param(
    [switch]$RemoveUpstreamStage
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$tasksRoot = (Resolve-Path -LiteralPath (Join-Path $repoRoot 'tasks')).Path
$separator = [System.IO.Path]::DirectorySeparatorChar
$transientNames = @('__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache')

$targets = Get-ChildItem -LiteralPath $repoRoot -Recurse -Directory -Force |
    Where-Object { $transientNames -contains $_.Name } |
    Sort-Object { $_.FullName.Length } -Descending

foreach ($target in $targets) {
    if (-not (Test-Path -LiteralPath $target.FullName)) {
        continue
    }
    $resolved = (Resolve-Path -LiteralPath $target.FullName).Path
    if (-not $resolved.StartsWith($repoRoot + $separator, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove path outside repository root: $resolved"
    }
    Remove-Item -LiteralPath $resolved -Recurse -Force
    Write-Output "removed transient directory: $resolved"
}

if ($RemoveUpstreamStage) {
    $stage = Join-Path $repoRoot '.upstream_stage'
    if (Test-Path -LiteralPath $stage) {
        $resolvedStage = (Resolve-Path -LiteralPath $stage).Path
        $stageParent = (Split-Path -Parent $resolvedStage)
        if (-not $stageParent.Equals($repoRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
            -not (Split-Path -Leaf $resolvedStage).Equals('.upstream_stage', [System.StringComparison]::Ordinal)) {
            throw "Refusing unsafe staging removal: $resolvedStage"
        }
        Remove-Item -LiteralPath $resolvedStage -Recurse -Force
        Write-Output "removed upstream staging directory: $resolvedStage"
    }
}
