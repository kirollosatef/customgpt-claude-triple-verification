# CustomGPT Triple Verification — Windows PowerShell Installer
# Usage: .\install.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " CustomGPT Triple Verification Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Node.js
Write-Host "[1/4] Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    $major = [int]($nodeVersion -replace 'v(\d+)\..*', '$1')
    if ($major -lt 18) {
        Write-Host "ERROR: Node.js >= 18 required (found $nodeVersion)" -ForegroundColor Red
        Write-Host "Download from: https://nodejs.org" -ForegroundColor Gray
        exit 1
    }
    Write-Host "  Node.js $nodeVersion detected" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Node.js not found. Install from https://nodejs.org" -ForegroundColor Red
    exit 1
}

# Step 2: Check Claude Code
Write-Host "[2/4] Checking Claude Code..." -ForegroundColor Yellow
try {
    $claudeVersion = claude --version 2>&1
    Write-Host "  Claude Code detected" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Claude Code CLI not found in PATH" -ForegroundColor Yellow
    Write-Host "  Install from: https://claude.ai/code" -ForegroundColor Gray
}

# Step 3: Determine plugin directory
Write-Host "[3/4] Installing plugin..." -ForegroundColor Yellow
$pluginSource = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path $pluginSource)) {
    $pluginSource = $PSScriptRoot | Split-Path -Parent
}

# Create Claude plugins directory if needed
$claudeDir = Join-Path $env:USERPROFILE ".claude"
if (-not (Test-Path $claudeDir)) {
    New-Item -ItemType Directory -Path $claudeDir -Force | Out-Null
}

$pluginsDir = Join-Path $claudeDir "plugins"
if (-not (Test-Path $pluginsDir)) {
    New-Item -ItemType Directory -Path $pluginsDir -Force | Out-Null
}

$targetDir = Join-Path $pluginsDir "customgpt-triple-verification"

# Copy plugin files (or create symlink for development)
if (Test-Path $targetDir) {
    Write-Host "  Plugin directory already exists, updating..." -ForegroundColor Yellow
    Remove-Item -Path $targetDir -Recurse -Force
}

# Use directory junction for development, copy for distribution
$scriptDir = Split-Path -Parent $PSScriptRoot
Copy-Item -Path $scriptDir -Destination $targetDir -Recurse -Force
Write-Host "  Plugin installed to: $targetDir" -ForegroundColor Green

# Step 4: Run verification
Write-Host "[4/4] Running verification..." -ForegroundColor Yellow
try {
    $verifyScript = Join-Path $targetDir "install" "verify.mjs"
    node $verifyScript
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " Installation Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Open any project with Claude Code" -ForegroundColor White
    Write-Host "  2. The triple verification hooks are now active" -ForegroundColor White
    Write-Host "  3. Try: 'Create a Python file with a TODO'" -ForegroundColor White
    Write-Host "  4. Check audit logs in .claude/triple-verify-audit/" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "WARNING: Verification failed, but plugin is installed" -ForegroundColor Yellow
    Write-Host "  Error: $_" -ForegroundColor Gray
}
