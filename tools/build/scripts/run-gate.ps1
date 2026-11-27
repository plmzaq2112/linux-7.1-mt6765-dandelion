param(
    [string]$Profile = "kernel_dtbs",
    [string]$ExtraArgs = ""
)

$Root = Split-Path -Parent $PSScriptRoot
$CfgPath = Join-Path $Root ".ai\build_profiles.json"
if (-not (Test-Path $CfgPath)) { Write-Error "Missing $CfgPath"; exit 2 }

$Profiles = Get-Content $CfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
$Prop = $Profiles.PSObject.Properties[$Profile]
if (-not $Prop) {
    $Avail = ($Profiles.PSObject.Properties.Name) -join ", "
    Write-Error "Unknown profile '$Profile'. Available: $Avail"
    exit 2
}

$P = $Prop.Value
$Cwd = if ($P.cwd) { $P.cwd } else { "/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline" }
$Cmd = if ($ExtraArgs.Trim()) { "$($P.cmd) $($ExtraArgs.Trim())" } else { "$($P.cmd)" }

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = $utf8NoBom
[Console]::OutputEncoding = $utf8NoBom

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$BashScript = "set -o pipefail`ncd '$Cwd' || exit 1`n$Cmd 2>&1`n"
$Out = $BashScript | wsl -d Ubuntu-26.04 bash -c "tr -d '\r' | bash -s"
$Code = $LASTEXITCODE
$sw.Stop()

if ($Code -eq 0) {
    Write-Output ("[GATE PASS] profile={0} time={1:N1}s" -f $Profile, $sw.Elapsed.TotalSeconds)
    exit 0
}

Write-Output ("[GATE FAIL] profile={0} exit={1} time={2:N1}s" -f $Profile, $Code, $sw.Elapsed.TotalSeconds)
$Diags = $Out | Where-Object { $_ -match "(?i)(error:|warning:|Error \d+|FAILED:|ninja: build stopped|undefined reference|No such file)" }
if ($Diags) {
    $Diags | Select-Object -First 40
} else {
    $Out | Select-Object -Last 30
}
exit $Code
