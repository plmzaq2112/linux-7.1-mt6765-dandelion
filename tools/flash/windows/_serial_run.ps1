param(
    [string]$Port = 'COM5',
    [string]$Cmd = '',
    [int]$WaitMs = 5000,
    [int]$PromptTimeoutMs = 20000
)

# Robust serial runner:
#  - waits for a real shell prompt before sending (avoids the "command swallowed
#    while nc still owns the shell" race)
#  - drains stale output
#  - prints the command output

$sp = New-Object System.IO.Ports.SerialPort($Port, 115200, 'None', 8, 'One')
$sp.ReadTimeout = 400
$sp.WriteTimeout = 20000
$sp.Open()
$sp.DtrEnable = $true
$sp.RtsEnable = $true

$enc = [System.Text.Encoding]::GetEncoding(28591)
$buf = New-Object byte[] 65536

function Drain([int]$ms) {
    $ms2 = New-Object System.IO.MemoryStream
    $last = [DateTime]::Now
    while (([DateTime]::Now - $last).TotalMilliseconds -lt $ms) {
        try {
            $r = $sp.Read($buf, 0, $buf.Length)
            if ($r -gt 0) { $ms2.Write($buf, 0, $r); $last = [DateTime]::Now }
        } catch { }
    }
    return $enc.GetString($ms2.ToArray())
}

function SendRaw([string]$s) { $sp.Write($s) }

function WaitPrompt([int]$timeoutMs) {
    $deadline = [DateTime]::Now.AddMilliseconds($timeoutMs)
    while ([DateTime]::Now -lt $deadline) {
        SendRaw "`n"
        $o = Drain 900
        if ($o -match '(~|/) # ') { return $true }
    }
    return $false
}

[void](Drain 500)

if (-not (WaitPrompt $PromptTimeoutMs)) {
    Write-Output "ERROR: shell prompt not found within $PromptTimeoutMs ms (kernel/shell hung?)"
    $sp.Close()
    exit 2
}

if ($Cmd -ne '') {
    SendRaw ($Cmd + "`n")
    $o = Drain $WaitMs
    Write-Output ($o -replace "`r", "<CR>")
}

$sp.Close()
exit 0
