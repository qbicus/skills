param(
    [ValidateSet('install','update-repair','uninstall','doctor')]
    [string]$Action = 'install',

    [ValidateSet('codex','claude','both')]
    [string]$Target,

    [ValidateSet('low','medium','high')]
    [string]$Profile,

    [ValidateSet('low','medium','high')]
    [string]$CodexProfile,

    [ValidateSet('low','medium','high')]
    [string]$ClaudeProfile,

    [string]$RepositoryUrl,

    [switch]$Yes,
    [switch]$DryRun,
    [switch]$Verbose,
    [switch]$SkipAiIndex,
    [switch]$SkipGraphify
)

$ErrorActionPreference = 'Stop'
$FrameworkRoot = Join-Path $HOME '.ai'
$MinimumPython = [Version]'3.11'

function Write-Step([string]$Message) {
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Confirm-Install([string]$Prompt) {
    if ($Yes) { return $true }
    $answer = Read-Host "$Prompt [Y/n]"
    return (-not $answer -or $answer -match '^(y|yes)$')
}

function Ensure-Git {
    if (Get-Command git -ErrorAction SilentlyContinue) {
        $env:AI_FRAMEWORK_PREREQ_GIT_ORIGIN = 'pre-existing'
        return
    }
    Write-Step 'Git is missing.'
    if ($DryRun) { Write-Host 'Would install Git using winget.'; $env:AI_FRAMEWORK_PREREQ_GIT_ORIGIN = 'would-install'; return }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw 'Git is required and winget is unavailable. Install Git, then rerun the installer.'
    }
    if (-not (Confirm-Install 'Install Git using winget?')) { throw 'Cancelled.' }
    & winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw "winget Git install failed with exit code $LASTEXITCODE" }
    $gitCandidates = @(
        "$env:ProgramFiles\Git\cmd\git.exe",
        "$env:ProgramFiles\Git\bin\git.exe"
    )
    foreach ($candidate in $gitCandidates) {
        if (Test-Path $candidate) { $env:PATH = "$(Split-Path $candidate);$env:PATH"; break }
    }
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git installation completed but git is not visible in this process.' }
    $env:AI_FRAMEWORK_PREREQ_GIT_ORIGIN = 'installed-by-framework'
}

function Test-PythonExecutable([string]$Executable, [string[]]$PrefixArgs = @()) {
    try {
        $probe = & $Executable @PrefixArgs -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'); print(sys.executable)" 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $probe -or $probe.Count -lt 2) { return $null }
        $version = [Version]$probe[0].Trim()
        if ($version -lt $MinimumPython) { return $null }
        $resolved = $probe[1].Trim()
        if (-not (Test-Path $resolved)) { return $null }
        return [PSCustomObject]@{ Version = $version; Executable = $resolved }
    }
    catch { return $null }
}

function Find-CompatiblePython {
    foreach ($name in @('python','python3')) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) {
            $result = Test-PythonExecutable $cmd.Source
            if ($result) { return $result }
        }
    }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        $result = Test-PythonExecutable $py.Source @('-3')
        if ($result) { return $result }
    }

    $roots = @(
        (Join-Path $env:LocalAppData 'Programs\Python'),
        $env:ProgramFiles,
        ${env:ProgramFiles(x86)}
    ) | Where-Object { $_ -and (Test-Path $_) }
    $candidates = foreach ($base in $roots) {
        Get-ChildItem -Path $base -Filter python.exe -File -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
    }
    foreach ($candidate in ($candidates | Sort-Object -Descending -Unique)) {
        $result = Test-PythonExecutable $candidate
        if ($result) { return $result }
    }
    return $null
}

function Get-LatestWingetPythonId {
    $output = & winget search --query Python.Python --source winget --accept-source-agreements 2>$null | Out-String
    $matches = [regex]::Matches($output, 'Python\.Python\.(?<major>\d+)\.(?<minor>\d+)')
    $items = foreach ($m in $matches) {
        if ([int]$m.Groups['major'].Value -eq 3) {
            [PSCustomObject]@{
                Id = $m.Value
                Version = [Version]("{0}.{1}" -f $m.Groups['major'].Value, $m.Groups['minor'].Value)
            }
        }
    }
    return $items | Sort-Object Version -Descending | Select-Object -First 1
}

function Ensure-Python {
    $found = Find-CompatiblePython
    if ($found) {
        $env:AI_FRAMEWORK_PREREQ_PYTHON_ORIGIN = 'pre-existing'
        $env:AI_FRAMEWORK_PYTHON = $found.Executable
        return $found.Executable
    }

    Write-Step "Compatible Python is missing (minimum $MinimumPython)."
    if ($DryRun) {
        Write-Host 'Would install the latest stable Python available through winget.'
        $env:AI_FRAMEWORK_PREREQ_PYTHON_ORIGIN = 'would-install'
        return $null
    }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw 'Python is required and winget is unavailable. Install current stable Python 3.11+ and rerun the installer.'
    }
    if (-not (Confirm-Install 'Install the latest stable Python using winget?')) { throw 'Cancelled.' }

    $package = Get-LatestWingetPythonId
    if (-not $package) { throw 'Could not determine the latest stable Python package from winget.' }
    Write-Step "Installing $($package.Id)"
    & winget install --id $package.Id -e --source winget --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw "winget Python install failed with exit code $LASTEXITCODE" }

    $found = Find-CompatiblePython
    if (-not $found) { throw 'Python installation completed but a compatible python executable could not be resolved.' }
    $env:AI_FRAMEWORK_PREREQ_PYTHON_ORIGIN = 'installed-by-framework'
    $env:AI_FRAMEWORK_PYTHON = $found.Executable
    return $found.Executable
}

function Ensure-Uv {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        $env:AI_FRAMEWORK_PREREQ_UV_ORIGIN = 'pre-existing'
        return
    }
    $candidate = Join-Path $HOME '.local\bin\uv.exe'
    if (Test-Path $candidate) {
        $env:PATH = "$(Split-Path $candidate);$env:PATH"
        $env:AI_FRAMEWORK_PREREQ_UV_ORIGIN = 'pre-existing'
        return
    }
    Write-Step 'uv is missing.'
    if ($DryRun) { Write-Host 'Would install uv using the official Astral installer.'; $env:AI_FRAMEWORK_PREREQ_UV_ORIGIN = 'would-install'; return }
    if (-not (Confirm-Install 'Install uv using the official Astral installer?')) { throw 'Cancelled.' }
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    if (Test-Path $candidate) { $env:PATH = "$(Split-Path $candidate);$env:PATH" }
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'uv installation completed but uv is not visible in this process.' }
    $env:AI_FRAMEWORK_PREREQ_UV_ORIGIN = 'installed-by-framework'
}

function Resolve-FrameworkSource {
    $localInstaller = $null
    if ($PSScriptRoot) {
        $candidate = Join-Path $PSScriptRoot 'installer\installer.py'
        if (Test-Path $candidate) { $localInstaller = $PSScriptRoot }
    }

    if (Test-Path (Join-Path $FrameworkRoot 'installer\installer.py')) {
        return $FrameworkRoot
    }

    if ($localInstaller) {
        if (Test-Path $FrameworkRoot) {
            $localFull = (Resolve-Path $localInstaller).Path
            $frameworkFull = (Resolve-Path $FrameworkRoot).Path
            if ($localFull -eq $frameworkFull) { return $localInstaller }
        }
        if ($Action -in @('doctor','uninstall')) { return $localInstaller }
        if ($DryRun) {
            Write-Host "Would install framework from local checkout $localInstaller to $FrameworkRoot"
            return $localInstaller
        }
        if (Test-Path $FrameworkRoot) {
            throw "$FrameworkRoot exists but does not contain the installer. Back it up/remove it or use Update / Repair from a valid framework installation."
        }
        Write-Step 'Installing framework from local checkout'
        & git clone $localInstaller $FrameworkRoot
        if ($LASTEXITCODE -ne 0) { throw 'Local framework clone failed.' }
        return $FrameworkRoot
    }

    $repo = $RepositoryUrl
    if (-not $repo) { $repo = $env:AI_FRAMEWORK_REPO_URL }
    if (-not $repo) {
        if ($Action -in @('doctor','uninstall')) {
            throw "No installed framework was found at $FrameworkRoot. Run doctor/uninstall from an installed or local framework checkout."
        }
        throw 'Framework repository URL is required for bootstrap install. Set AI_FRAMEWORK_REPO_URL or pass -RepositoryUrl.'
    }
    if ($DryRun) {
        Write-Host "Would clone $repo to $FrameworkRoot"
        return $FrameworkRoot
    }
    if (Test-Path $FrameworkRoot) {
        throw "$FrameworkRoot already exists but does not contain a valid installer."
    }
    Write-Step 'Cloning framework'
    & git clone $repo $FrameworkRoot
    if ($LASTEXITCODE -ne 0) { throw 'Framework clone failed.' }
    return $FrameworkRoot
}

if ($Action -in @('install','update-repair')) {
    Ensure-Git
    $pythonExe = Ensure-Python
    Ensure-Uv
}
else {
    $foundPython = Find-CompatiblePython
    if (-not $foundPython) {
        throw "Python $MinimumPython or newer is required to run '$Action'. Doctor/uninstall do not install system prerequisites automatically."
    }
    $pythonExe = $foundPython.Executable
    $env:AI_FRAMEWORK_PREREQ_PYTHON_ORIGIN = 'pre-existing'
}
$root = Resolve-FrameworkSource
$installer = Join-Path $root 'installer\installer.py'
if (-not (Test-Path $installer) -and -not $DryRun) { throw "Installer core not found: $installer" }

if (-not $pythonExe) {
    throw 'Dry-run cannot execute the shared installer core because compatible Python is not currently installed. The bootstrap would install Python during a real run.'
}

$argsList = @($installer, $Action)
if ($Target) { $argsList += @('--target', $Target) }
if ($Profile) { $argsList += @('--profile', $Profile) }
if ($CodexProfile) { $argsList += @('--codex-profile', $CodexProfile) }
if ($ClaudeProfile) { $argsList += @('--claude-profile', $ClaudeProfile) }
if ($Yes) { $argsList += '--yes' }
if ($DryRun) { $argsList += '--dry-run' }
if ($Verbose) { $argsList += '--verbose' }
if ($SkipAiIndex) { $argsList += '--skip-aiindex' }
if ($SkipGraphify) { $argsList += '--skip-graphify' }

Write-Step $Action
& $pythonExe @argsList
exit $LASTEXITCODE
