#Requires -Version 5.1
<#
.SYNOPSIS
    CodeAnvil installer for Windows.
.DESCRIPTION
    Installs uv (if missing) and codeanvil via uv tool install.
    Usage: irm https://raw.githubusercontent.com/dramirezbe/codeanvil-gcpds/main/install.ps1 | iex
    Uninstall: .\install.ps1 -Uninstall
#>
[CmdletBinding()]
param(
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'
$ToolName = 'codeanvil'
$Repo = 'https://github.com/dramirezbe/codeanvil-gcpds.git'
$MinPython = '3.10'

function Write-Status($msg) { Write-Host "[$ToolName] $msg" }
function Write-Warn($msg) { Write-Warning "[$ToolName] $msg" }
function Write-Err($msg) { Write-Error "[$ToolName] $msg"; exit 1 }

# ── 1. Check Python ──────────────────────────────────────────────────
$script:PythonVersion = $null

function Test-Python {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
    if (-not $py) {
        Write-Status "No system Python found — uv will download one."
        return
    }

    $ver = & $py.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    & $py.Source -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $script:PythonVersion = $ver
        Write-Status "Python $ver found — will use it."
    } else {
        Write-Status "Python $ver found but too old ($MinPython+ required) — uv will download one."
    }
}

# ── 2. Ensure uv ─────────────────────────────────────────────────────
function Install-Uv {
    if (Get-Command uv -ErrorAction SilentlyContinue) { return }
    Write-Status "uv not found, installing..."
    irm https://astral.sh/uv/install.ps1 | iex
    $uvBin = Join-Path $env:USERPROFILE '.local\bin'
    if ($env:PATH -notlike "*$uvBin*") {
        $env:PATH = "$uvBin;$env:PATH"
    }
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Err "Failed to install uv. Install manually: https://docs.astral.sh/uv/"
    }
    Write-Status "uv installed."
}

# ── 3. Install ────────────────────────────────────────────────────────
function Install-Tool {
    $pyFlag = if ($script:PythonVersion) { @("--python", $script:PythonVersion) } else { @("--python", "3.12") }
    $toolOutput = $null
    try { $toolOutput = uv tool list 2>&1 | Out-String } catch {}
    $isUpgrade = $toolOutput -and ($toolOutput -match "(?m)^$ToolName ")
    if ($isUpgrade) {
        Write-Status "Upgrading $ToolName..."
        uv tool install --force-reinstall @pyFlag "git+$Repo"
    } else {
        Write-Status "Installing $ToolName..."
        uv tool install @pyFlag "git+$Repo"
    }
    if ($LASTEXITCODE -ne 0) { Write-Err "Installation failed." }
    Write-Status "Installed."
    codeanvil --version 2>$null
}

# ── 4. Ensure PATH ───────────────────────────────────────────────────
function Set-UserPath {
    $binDir = Join-Path $env:USERPROFILE '.local\bin'
    $userPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
    if ($userPath -like "*$binDir*") {
        Write-Status "PATH already configured."
        return
    }
    [Environment]::SetEnvironmentVariable('PATH', "$binDir;$userPath", 'User')
    $env:PATH = "$binDir;$env:PATH"
    Write-Status "Added $binDir to user PATH."
}

# ── 5. Verify ─────────────────────────────────────────────────────────
function Test-Install {
    if (Get-Command $ToolName -ErrorAction SilentlyContinue) {
        Write-Status "Verified: $((Get-Command $ToolName).Source)"
    } else {
        Write-Warn "$ToolName not found on PATH after install. Restart your terminal."
    }
}

# ── 6. Uninstall ──────────────────────────────────────────────────────
function Uninstall-Tool {
    Write-Status "Uninstalling $ToolName..."
    uv tool uninstall $ToolName 2>$null
    $binDir = Join-Path $env:USERPROFILE '.local\bin'
    $userPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
    if ($userPath -like "*$binDir*") {
        $cleaned = ($userPath -split ';' | Where-Object { $_ -ne $binDir }) -join ';'
        [Environment]::SetEnvironmentVariable('PATH', $cleaned, 'User')
        Write-Status "Removed $binDir from user PATH."
    }
    Write-Status "Done."
}

# ── Main ──────────────────────────────────────────────────────────────
if ($Uninstall) {
    Uninstall-Tool
} else {
    Test-Python
    Install-Uv
    Install-Tool
    Set-UserPath
    Test-Install
    Write-Status "Ready! Run: codeanvil init; codeanvil create myproject"
}
