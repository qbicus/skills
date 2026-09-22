param(
    [switch]$DryRun,
    [ValidateSet("base", "dotnet", "vb-migration", "go", "nextjs", "python")]
    [string]$Type = "base",
    [switch]$WithCodexHooks,
    [switch]$WithGraphifyClaude,
    [string]$Repo
)

$scriptPath = Join-Path $PSScriptRoot "repo-init.py"
$argsList = @($scriptPath, "--type", $Type)

if ($DryRun) { $argsList += "--dry-run" }
if ($WithCodexHooks) { $argsList += "--with-codex-hooks" }
if ($WithGraphifyClaude) { $argsList += "--with-graphify-claude" }
if ($Repo) { $argsList += @("--repo", $Repo) }

python @argsList
exit $LASTEXITCODE
