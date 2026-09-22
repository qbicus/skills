<#
.SYNOPSIS
Initializes or updates the current repository with the shared AI framework project files.

.DESCRIPTION
Run this script from inside an existing or new project repository after cloning the
shared framework to %USERPROFILE%\.ai. It creates missing AGENTS.md, CLAUDE.md,
and .ai project files without overwriting existing files.

If project AI files already exist, interactive mode shows the detected setup and asks
whether to update/repair missing files, re-init safely, preview, or cancel.

If -Type, -Action, or -NonInteractive is provided, the script runs without prompts.

Use -WithGraphifyClaude to install Graphify's Claude project integration and then
normalize the generated CLAUDE.md Graphify section to the shared AiIndex/Graphify
routing policy.

.EXAMPLES
  & "$env:USERPROFILE\.ai\init-project.ps1"
  & "$env:USERPROFILE\.ai\init-project.ps1" -Type dotnet
  & "$env:USERPROFILE\.ai\init-project.ps1" -Type go
  & "$env:USERPROFILE\.ai\init-project.ps1" -Type nextjs
  & "$env:USERPROFILE\.ai\init-project.ps1" -Type python
  & "$env:USERPROFILE\.ai\init-project.ps1" -Type vb-migration -WithCodexHooks
  & "$env:USERPROFILE\.ai\init-project.ps1" -Type dotnet -WithGraphifyClaude
  & "$env:USERPROFILE\.ai\init-project.ps1" -Type dotnet -WithCodexHooks -WithGraphifyClaude
  & "$env:USERPROFILE\.ai\init-project.ps1" -DryRun
  & "$env:USERPROFILE\.ai\init-project.ps1" -Type dotnet -Action update -NonInteractive
#>

param(
    [switch]$DryRun,
    [ValidateSet("", "base", "dotnet", "vb-migration", "go", "nextjs", "python")]
    [string]$Type = "",
    [ValidateSet("", "update", "reinit", "dry-run", "cancel")]
    [string]$Action = "",
    [switch]$WithCodexHooks,
    [switch]$WithGraphifyClaude,
    [string]$Repo,
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"

$frameworkRoot = $PSScriptRoot
$repoInitScript = Join-Path $frameworkRoot "scripts\repo-init.py"

if (-not (Test-Path $repoInitScript)) {
    Write-Error "Could not find repo-init.py at: $repoInitScript"
    exit 1
}

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
}

if (-not $pythonCommand) {
    Write-Error "Python was not found. Install Python or make sure 'python'/'py' is available in PATH."
    exit 1
}

$argsList = @($repoInitScript)

if (-not [string]::IsNullOrWhiteSpace($Type)) { $argsList += @("--type", $Type) }
if (-not [string]::IsNullOrWhiteSpace($Action)) { $argsList += @("--action", $Action) }
if ($DryRun) { $argsList += "--dry-run" }
if ($WithCodexHooks) { $argsList += "--with-codex-hooks" }
if ($WithGraphifyClaude) { $argsList += "--with-graphify-claude" }
if ($Repo) { $argsList += @("--repo", $Repo) }
if ($NonInteractive) { $argsList += "--non-interactive" }

Write-Host "AI framework: $frameworkRoot"
Write-Host "Target folder:  $(if ($Repo) { $Repo } else { (Get-Location).Path })"
if ([string]::IsNullOrWhiteSpace($Type) -and [string]::IsNullOrWhiteSpace($Action) -and -not $NonInteractive) {
    Write-Host "Mode:           interactive prompt"
} else {
    Write-Host "Template type:  $(if ([string]::IsNullOrWhiteSpace($Type)) { 'base' } else { $Type })"
    Write-Host "Action:         $(if ([string]::IsNullOrWhiteSpace($Action)) { 'update' } else { $Action })"
    Write-Host "Codex hooks:    $(if ($WithCodexHooks) { 'enabled' } else { 'disabled' })"
    Write-Host "Graphify Claude:$(if ($WithGraphifyClaude) { ' enabled' } else { ' disabled' })"
}

& $pythonCommand.Source @argsList
exit $LASTEXITCODE
