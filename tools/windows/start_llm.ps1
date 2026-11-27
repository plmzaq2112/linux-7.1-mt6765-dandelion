param(
    [string]$LlamaDir = "C:\Users\31806\Documents\AI_Project\llama.cpp",
    [string]$ModelRel = "models\qwen2.5-coder-7b-instruct-q4_k_m.gguf",
    [int]$Ctx = 12288,
    [int]$Threads = 4,
    [int]$Port = 8080
)

$Exe = Join-Path $LlamaDir "llama-server.exe"
$Model = Join-Path $LlamaDir $ModelRel
if (-not (Test-Path $Exe)) { Write-Error "llama-server.exe not found at: $Exe (edit -LlamaDir)"; exit 1 }
if (-not (Test-Path $Model)) { Write-Error "Model not found at: $Model"; exit 1 }

Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500

Write-Host "Starting llama-server (Q8+FA, ctx=$Ctx, threads=$Threads, port=$Port)..."
& $Exe -m $Model -ngl 99 -fa on -ctk q8_0 -ctv q8_0 -c $Ctx -t $Threads -b 512 -ub 512 --repeat-penalty 1.1 --parallel 1 --host 127.0.0.1 --port $Port
