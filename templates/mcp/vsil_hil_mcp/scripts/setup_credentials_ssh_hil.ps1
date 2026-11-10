<#
.SYNOPSIS
  Windows companion of setup_credentials_ssh_hil.sh — run ON THE WINDOWS TARGET,
  in an elevated (Administrator) PowerShell. Analogous to the Linux remote step:
  it creates a login-locked agent user, grants it admin (Windows "sudo"), creates
  a workspace, and installs the vsil_hil_mcp agent public keys into OpenSSH.

.DESCRIPTION
  UNTESTED / BEST-EFFORT — review before running. Windows differs from Linux:
    * no rrsync, so the deploy key canNOT be restricted to write-only rsync; both
      keys are installed as plain keys. The forced-command confinement that the
      Linux target gets does not apply here.
    * rsync on Windows needs cwRsync or WSL for code_sync to work.
    * an admin account's keys live in C:\ProgramData\ssh\administrators_authorized_keys
      with strict ACLs (Administrators + SYSTEM only), handled below.
  Unlike the .sh (host-run, SSHes in), this script runs on the target itself.
  Generate the keys on the host first (ssh-keygen, see the .sh), then pass the two
  .pub contents here.

.PARAMETER AgentUser   Agent account to create (default: codeanvil).
.PARAMETER DeployPub   Full text of deploy_ed25519.pub.
.PARAMETER ExecPub     Full text of exec_ed25519.pub.
.PARAMETER Workspace   Agent workspace dir (default: C:\codeanvil\workspace).

.EXAMPLE
  .\setup_credentials_ssh_hil.ps1 -DeployPub "ssh-ed25519 AAAA... deploy" -ExecPub "ssh-ed25519 AAAA... exec"
#>
[CmdletBinding()]
param(
  [string]$AgentUser = "codeanvil",
  [Parameter(Mandatory)][string]$DeployPub,
  [Parameter(Mandatory)][string]$ExecPub,
  [string]$Workspace = "C:\codeanvil\workspace"
)

$ErrorActionPreference = "Stop"

# must be elevated
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
      ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  throw "Run this in an elevated (Administrator) PowerShell."
}
foreach ($k in @($DeployPub, $ExecPub)) {
  if ($k -notmatch '^ssh-ed25519 [A-Za-z0-9+/]+={0,2}( .+)?$') { throw "unexpected public key format: $k" }
}

# 1. agent user — no interactive password (key-only); never expires
if (-not (Get-LocalUser -Name $AgentUser -ErrorAction SilentlyContinue)) {
  New-LocalUser -Name $AgentUser -NoPassword -AccountNeverExpires `
    -Description "CodeAnvil HIL agent (key-only)" | Out-Null
}
# 2. admin ("sudo"): add to the local Administrators group
if (-not (Get-LocalGroupMember -Group "Administrators" -Member $AgentUser -ErrorAction SilentlyContinue)) {
  Add-LocalGroupMember -Group "Administrators" -Member $AgentUser
}

# 3. workspace
New-Item -ItemType Directory -Force -Path $Workspace | Out-Null

# 4. OpenSSH authorized keys for an admin account: administrators_authorized_keys
#    with ACLs restricted to Administrators + SYSTEM (OpenSSH refuses it otherwise).
$akPath = Join-Path $env:ProgramData "ssh\administrators_authorized_keys"
New-Item -ItemType Directory -Force -Path (Split-Path $akPath) | Out-Null
$existing = (Test-Path $akPath) ? (Get-Content -Raw -Path $akPath) : ""
foreach ($k in @($DeployPub.Trim(), $ExecPub.Trim())) {
  if ($existing -notmatch [regex]::Escape($k)) { Add-Content -Path $akPath -Value $k }
}
# lock down ACLs
icacls $akPath /inheritance:r | Out-Null
icacls $akPath /grant "Administrators:F" "SYSTEM:F" | Out-Null

# 5. ensure the OpenSSH server is present/running (best-effort)
$svc = Get-Service sshd -ErrorAction SilentlyContinue
if ($null -eq $svc) {
  Write-Warning "OpenSSH Server (sshd) not installed. Install it: Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0, then Start-Service sshd; Set-Service sshd -StartupType Automatic"
} elseif ($svc.Status -ne "Running") {
  Start-Service sshd
}

Write-Host "OK: '$AgentUser' ready — admin, workspace $Workspace, deploy+exec keys installed." -ForegroundColor Green
Write-Host "Caveats: no rrsync write-only restriction on Windows; rsync needs cwRsync/WSL for code_sync." -ForegroundColor Yellow
Write-Host "On the HOST, add the target to .codeanvil/project.yaml with os: windows." -ForegroundColor Cyan
