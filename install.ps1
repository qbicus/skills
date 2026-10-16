param(
    [Parameter(Position = 0)]
    [ValidateSet('install','update-repair','change-profile','check-updates','uninstall','doctor')]
    [string]$Action,

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
    [switch]$SkipAiIndex,
    [switch]$SkipGraphify,
    [switch]$SkipFrameworkUpdate,
    [switch]$NoAiIndexUpdate,

    [ValidateSet('framework','aiindex','both')]
    [string]$Apply,
    [switch]$JsonOutput
)

$script:VerboseRequested = $PSBoundParameters.ContainsKey('Verbose') -or $VerbosePreference -eq 'Continue'

$ErrorActionPreference = 'Stop'
$FrameworkRoot = Join-Path $HOME '.ai'
$MinimumPython = [Version]'3.11'
$DefaultRepositoryUrl = 'https://github.com/qbicus/skills.git'
$script:InteractiveMode = -not $PSBoundParameters.ContainsKey('Action')

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

function Resolve-FrameworkSource([string]$RequestedAction, [bool]$RequestedDryRun) {
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
        if ($RequestedAction -in @('doctor','uninstall','check-updates','change-profile')) { return $localInstaller }
        if ($RequestedDryRun) {
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
    if (-not $repo) { $repo = $DefaultRepositoryUrl }
    if ($RequestedAction -in @('doctor','uninstall','check-updates','change-profile') -and -not (Test-Path $FrameworkRoot)) {
        throw "No installed framework was found at $FrameworkRoot. Install the framework first."
    }
    if ($RequestedDryRun) {
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

function Get-VersionInfo {
    $framework = '?'
    $aiIndex = '?'
    $paths = @()
    if ($PSScriptRoot) { $paths += (Join-Path $PSScriptRoot 'version.json') }
    $paths += (Join-Path $FrameworkRoot 'version.json')
    foreach ($path in $paths | Select-Object -Unique) {
        if (Test-Path $path) {
            try {
                $v = Get-Content $path -Raw | ConvertFrom-Json
                if ($v.framework) { $framework = [string]$v.framework }
                if ($v.aiIndex) { $aiIndex = [string]$v.aiIndex }
                break
            } catch { }
        }
    }
    $statePath = Join-Path $FrameworkRoot 'local\installer-state.json'
    if (Test-Path $statePath) {
        try {
            $state = Get-Content $statePath -Raw | ConvertFrom-Json
            if ($state.frameworkVersion) { $framework = [string]$state.frameworkVersion }
            if ($state.aiIndex.version) { $aiIndex = [string]$state.aiIndex.version }
        } catch { }
    }
    return [PSCustomObject]@{ Framework = $framework; AiIndex = $aiIndex }
}

function Show-Banner {
    $v = Get-VersionInfo
    $ai = if ($v.AiIndex -and $v.AiIndex -ne '?') { ($v.AiIndex -replace '^aiindex-', '') } else { '?' }
    Write-Host '    _    ___   _____                                            _' -ForegroundColor Cyan
    Write-Host '   / \  |_ _| |  ___| __ __ _ _ __ ___   _____      _____  _ __| | __' -ForegroundColor Cyan
    Write-Host '  / _ \  | |  | |_ | ''__/ _` | ''_ ` _ \ / _ \ \ /\ / / _ \| ''__| |/ /' -ForegroundColor Cyan
    Write-Host ' / ___ \ | |  |  _|| | | (_| | | | | | |  __/\ V  V / (_) | |  |   <' -ForegroundColor Cyan
    Write-Host '/_/   \_\___| |_|  |_|  \__,_|_| |_| |_|\___| \_/\_/ \___/|_|  |_|\_\' -ForegroundColor Cyan
    Write-Host ''
    Write-Host "AI Framework v$($v.Framework)" -ForegroundColor White -NoNewline
    Write-Host "  [AiIndex $ai]" -ForegroundColor DarkGray
    Write-Host ''
}

function Read-SingleSelect([string]$Title, [string[]]$Options, [int]$DefaultIndex = 0, [switch]$AllowBack) {
    $index = [Math]::Max(0, [Math]::Min($DefaultIndex, $Options.Count - 1))
    while ($true) {
        Clear-Host
        Show-Banner
        Write-Host $Title -ForegroundColor Yellow
        Write-Host ''
        for ($i = 0; $i -lt $Options.Count; $i++) {
            if ($i -eq $index) { Write-Host "> $($Options[$i])" -ForegroundColor Green }
            else { Write-Host "  $($Options[$i])" }
        }
        Write-Host ''
        Write-Host 'Up/Down Navigate   Enter Select' -ForegroundColor DarkGray -NoNewline
        if ($AllowBack) { Write-Host '   Esc Back' -ForegroundColor DarkGray } else { Write-Host '' }
        $key = [Console]::ReadKey($true)
        switch ($key.Key) {
            'UpArrow'   { $index = ($index - 1 + $Options.Count) % $Options.Count }
            'DownArrow' { $index = ($index + 1) % $Options.Count }
            'Enter'     { return $index }
            'Escape'    { if ($AllowBack) { return -1 } }
        }
    }
}

function Read-MultiSelect([string]$Title, [string[]]$Options, [bool[]]$Selected, [switch]$AllowBack) {
    $index = 0
    while ($true) {
        Clear-Host
        Show-Banner
        Write-Host $Title -ForegroundColor Yellow
        Write-Host ''
        for ($i = 0; $i -lt $Options.Count; $i++) {
            $mark = if ($Selected[$i]) { '[x]' } else { '[ ]' }
            $line = "$mark $($Options[$i])"
            if ($i -eq $index) { Write-Host "> $line" -ForegroundColor Green }
            else { Write-Host "  $line" }
        }
        Write-Host ''
        Write-Host 'Up/Down Move   Space Toggle   Enter Continue' -ForegroundColor DarkGray -NoNewline
        if ($AllowBack) { Write-Host '   Esc Back' -ForegroundColor DarkGray } else { Write-Host '' }
        $key = [Console]::ReadKey($true)
        switch ($key.Key) {
            'UpArrow'   { $index = ($index - 1 + $Options.Count) % $Options.Count }
            'DownArrow' { $index = ($index + 1) % $Options.Count }
            'Spacebar'  { $Selected[$index] = -not $Selected[$index] }
            'Enter' {
                if ($Selected -contains $true) { return $Selected }
            }
            'Escape' { if ($AllowBack) { return $null } }
        }
    }
}

function Get-LocalProfiles {
    $path = Join-Path $FrameworkRoot 'local\provider-profiles.json'
    $result = @{ codex = 'medium'; claude = 'medium' }
    if (Test-Path $path) {
        try {
            $data = Get-Content $path -Raw | ConvertFrom-Json
            if ($data.profiles.codex) { $result.codex = [string]$data.profiles.codex }
            if ($data.profiles.claude) { $result.claude = [string]$data.profiles.claude }
        } catch { }
    }
    return $result
}

function Convert-SelectionToTarget([bool[]]$Selection) {
    if ($Selection[0] -and $Selection[1]) { return 'both' }
    if ($Selection[0]) { return 'codex' }
    return 'claude'
}

function Invoke-CoreAction {
    param(
        [string]$SelectedAction,
        [string]$SelectedTarget,
        [string]$SelectedProfile,
        [string]$SelectedCodexProfile,
        [string]$SelectedClaudeProfile,
        [bool]$RequestedDryRun = $false,
        [bool]$RequestedYes = $false,
        [bool]$RequestedSkipFrameworkUpdate = $false,
        [bool]$RequestedNoAiIndexUpdate = $false,
        [string]$Apply,
        [bool]$JsonOutput = $false,
        [bool]$Capture = $false
    )

    $oldDryRun = $script:DryRun
    $oldYes = $script:Yes
    $script:DryRun = $RequestedDryRun
    $script:Yes = $RequestedYes
    try {
        if ($SelectedAction -in @('install','update-repair')) {
            Ensure-Git
            $pythonExe = Ensure-Python
            Ensure-Uv
        } else {
            $foundPython = Find-CompatiblePython
            if (-not $foundPython) {
                throw "Python $MinimumPython or newer is required to run '$SelectedAction'."
            }
            $pythonExe = $foundPython.Executable
            $env:AI_FRAMEWORK_PREREQ_PYTHON_ORIGIN = 'pre-existing'
        }

        $root = Resolve-FrameworkSource $SelectedAction $RequestedDryRun
        $installer = Join-Path $root 'installer\installer.py'
        if (-not (Test-Path $installer) -and -not $RequestedDryRun) { throw "Installer core not found: $installer" }
        if (-not $pythonExe) { throw 'Preview cannot execute the installer core because compatible Python is not currently installed.' }

        $argsList = @($installer, $SelectedAction)
        if ($SelectedTarget) { $argsList += @('--target', $SelectedTarget) }
        if ($SelectedProfile) { $argsList += @('--profile', $SelectedProfile) }
        if ($SelectedCodexProfile) { $argsList += @('--codex-profile', $SelectedCodexProfile) }
        if ($SelectedClaudeProfile) { $argsList += @('--claude-profile', $SelectedClaudeProfile) }
        if ($RequestedYes) { $argsList += '--yes' }
        if ($RequestedDryRun) { $argsList += '--dry-run' }
        if ($script:VerboseRequested) { $argsList += '--verbose' }
        if ($SkipAiIndex) { $argsList += '--skip-aiindex' }
        if ($SkipGraphify) { $argsList += '--skip-graphify' }
        if ($RequestedSkipFrameworkUpdate) { $argsList += '--skip-framework-update' }
        if ($RequestedNoAiIndexUpdate) { $argsList += '--no-aiindex-update' }
        if ($Apply) { $argsList += @('--apply', $Apply) }
        if ($JsonOutput) { $argsList += '--json-output' }

        if (-not $Capture) { Write-Step $SelectedAction }
        if ($Capture) {
            $output = & $pythonExe @argsList 2>&1
            if ($LASTEXITCODE -ne 0) { throw ($output | Out-String) }
            return ($output -join "`n")
        }
        & $pythonExe @argsList | ForEach-Object { Write-Host $_ }
        $exitCode = $LASTEXITCODE
        return $exitCode
    }
    finally {
        $script:DryRun = $oldDryRun
        $script:Yes = $oldYes
    }
}

function Pause-ForMenu([string]$Message = 'Press Enter to return to menu') {
    Write-Host ''
    Write-Host $Message -ForegroundColor DarkGray
    while ([Console]::ReadKey($true).Key -ne 'Enter') { }
}

function Get-InstalledClientDefaults {
    $result = [bool[]]@($false, $false)
    $statePath = Join-Path $FrameworkRoot 'local\installer-state.json'
    if (Test-Path $statePath) {
        try {
            $state = Get-Content $statePath -Raw | ConvertFrom-Json
            foreach ($client in @($state.installedClients)) {
                if ($client -eq 'codex') { $result[0] = $true }
                if ($client -eq 'claude') { $result[1] = $true }
            }
        } catch { }
    }
    if (-not ($result -contains $true)) {
        if (Test-Path (Join-Path $HOME '.codex')) { $result[0] = $true }
        if (Test-Path (Join-Path $HOME '.claude')) { $result[1] = $true }
    }
    if (-not ($result -contains $true)) { $result[0] = $true }
    return $result
}


function Select-Clients([string]$Title, [bool[]]$Defaults = @($true, $false)) {
    return Read-MultiSelect $Title @('Codex','Claude') ([bool[]]@($Defaults[0], $Defaults[1])) -AllowBack
}

function Select-Profile([string]$Client, [string]$Current = 'medium') {
    $options = @('Low (usage-saving)','Medium (recommended)','High (quality-first)')
    $default = switch ($Current) { 'low' {0}; 'high' {2}; default {1} }
    $idx = Read-SingleSelect "$Client profile" $options $default -AllowBack
    if ($idx -lt 0) { return $null }
    return @('low','medium','high')[$idx]
}

function Show-OperationResult([int]$Code) {
    if ($Code -eq 0) { Write-Host ''; Write-Host 'Completed successfully.' -ForegroundColor Green }
    else { Write-Host ''; Write-Host "Operation returned exit code $Code." -ForegroundColor Yellow }
    Pause-ForMenu
}

function Invoke-InstallFlow([bool]$Preview = $false) {
    $selection = Select-Clients $(if ($Preview) { 'Preview Install - select clients' } else { 'Install - select clients' })
    if ($null -eq $selection) { return }
    $target = Convert-SelectionToTarget $selection
    $codexP = $null; $claudeP = $null
    if ($selection[0]) { $codexP = Select-Profile 'Codex' 'medium'; if (-not $codexP) { return } }
    if ($selection[1]) { $claudeP = Select-Profile 'Claude' 'medium'; if (-not $claudeP) { return } }

    Clear-Host; Show-Banner
    Write-Host $(if ($Preview) { 'Preview Install' } else { 'Ready to install' }) -ForegroundColor Yellow
    Write-Host ''
    if ($selection[0]) { Write-Host "Codex   $codexP" }
    if ($selection[1]) { Write-Host "Claude  $claudeP" }
    Write-Host ''
    Write-Host 'Components: AI Framework, skills, AiIndex CLI/MCP, Graphify, native wiring' -ForegroundColor DarkGray
    if (-not $Preview) {
        $confirm = Read-SingleSelect 'Continue?' @('Install','Cancel') 0 -AllowBack
        if ($confirm -ne 0) { return }
    }
    $code = Invoke-CoreAction -SelectedAction 'install' -SelectedTarget $target -SelectedCodexProfile $codexP -SelectedClaudeProfile $claudeP -RequestedDryRun $Preview -RequestedYes $true
    Show-OperationResult $code
}

function Get-UpdateStatusObject {
    try {
        $raw = Invoke-CoreAction -SelectedAction 'check-updates' -JsonOutput $true -Capture $true
        return $raw | ConvertFrom-Json
    } catch {
        return $null
    }
}

function Invoke-RepairFlow([bool]$Preview = $false) {
    $profiles = Get-LocalProfiles
    $labels = @("Codex ($($profiles.codex))", "Claude ($($profiles.claude))")
    $selection = Read-MultiSelect $(if ($Preview) { 'Preview Update / Repair - select clients' } else { 'Update / Repair - select clients' }) $labels (Get-InstalledClientDefaults) -AllowBack
    if ($null -eq $selection) { return }
    $target = Convert-SelectionToTarget $selection

    $status = Get-UpdateStatusObject
    $skipFw = $true
    $noAiUpdate = $true
    if ($status) {
        $available = @()
        if ($status.framework.updateAvailable) { $available += "Framework $($status.framework.current) -> $($status.framework.latest)" }
        if ($status.aiIndex.updateAvailable) { $available += "AiIndex $($status.aiIndex.current) -> $($status.aiIndex.latest)" }
        if ($available.Count -gt 0) {
            $idx = Read-SingleSelect "Updates are available:`n$($available -join "`n")`n`nInclude available updates in this repair?" @('Yes - update and repair','No - repair only') 0 -AllowBack
            if ($idx -lt 0) { return }
            if ($idx -eq 0) { $skipFw = $false; $noAiUpdate = $false }
        }
    }

    $code = Invoke-CoreAction -SelectedAction 'update-repair' -SelectedTarget $target -RequestedDryRun $Preview -RequestedYes $true -RequestedSkipFrameworkUpdate $skipFw -RequestedNoAiIndexUpdate $noAiUpdate
    Show-OperationResult $code
}

function Invoke-ChangeProfileFlow([bool]$Preview = $false) {
    $profiles = Get-LocalProfiles
    $labels = @("Codex (current: $($profiles.codex))", "Claude (current: $($profiles.claude))")
    $selection = Read-MultiSelect $(if ($Preview) { 'Preview Change profiles - select clients' } else { 'Change profiles - select clients' }) $labels (Get-InstalledClientDefaults) -AllowBack
    if ($null -eq $selection) { return }
    $target = Convert-SelectionToTarget $selection
    $codexP = $null; $claudeP = $null
    if ($selection[0]) { $codexP = Select-Profile 'Codex' $profiles.codex; if (-not $codexP) { return } }
    if ($selection[1]) { $claudeP = Select-Profile 'Claude' $profiles.claude; if (-not $claudeP) { return } }
    $code = Invoke-CoreAction -SelectedAction 'change-profile' -SelectedTarget $target -SelectedCodexProfile $codexP -SelectedClaudeProfile $claudeP -RequestedDryRun $Preview -RequestedYes $true
    Show-OperationResult $code
}

function Invoke-CheckUpdatesFlow {
    Clear-Host; Show-Banner
    Write-Host 'Checking for updates...' -ForegroundColor Yellow
    $status = Get-UpdateStatusObject
    if (-not $status) {
        Write-Host 'Could not retrieve update status.' -ForegroundColor Red
        Pause-ForMenu
        return
    }
    Clear-Host; Show-Banner
    Write-Host 'Check for updates' -ForegroundColor Yellow
    Write-Host ''
    $fwState = if ($status.framework.error) { "unknown - $($status.framework.error)" } elseif ($status.framework.updateAvailable) { "$($status.framework.current) -> $($status.framework.latest) UPDATE AVAILABLE" } else { "$($status.framework.current) current" }
    $aiState = if ($status.aiIndex.error) { "unknown - $($status.aiIndex.error)" } elseif (-not $status.aiIndex.healthy) { "$($status.aiIndex.current) -> $($status.aiIndex.latest) REPAIR NEEDED" } elseif ($status.aiIndex.updateAvailable) { "$($status.aiIndex.current) -> $($status.aiIndex.latest) UPDATE AVAILABLE" } else { "$($status.aiIndex.current) current" }
    Write-Host "Framework  $fwState" -ForegroundColor $(if ($status.framework.updateAvailable) {'Yellow'} else {'Green'})
    Write-Host "AiIndex    $aiState" -ForegroundColor $(if ($status.aiIndex.updateAvailable -or -not $status.aiIndex.healthy) {'Yellow'} else {'Green'})

    $options = @(); $keys = @(); $defaults = @()
    if ($status.framework.updateAvailable) { $options += 'Framework'; $keys += 'framework'; $defaults += $true }
    if ($status.aiIndex.updateAvailable -or -not $status.aiIndex.healthy) { $options += $(if ($status.aiIndex.healthy) {'AiIndex'} else {'AiIndex (repair)'}); $keys += 'aiindex'; $defaults += $true }
    if ($options.Count -eq 0) { Pause-ForMenu; return }
    $selection = Read-MultiSelect 'Select updates to apply' $options ([bool[]]$defaults) -AllowBack
    if ($null -eq $selection) { return }
    $chosen = @()
    for ($i=0; $i -lt $selection.Count; $i++) { if ($selection[$i]) { $chosen += $keys[$i] } }
    $apply = if ($chosen.Count -eq 2) { 'both' } else { $chosen[0] }
    $code = Invoke-CoreAction -SelectedAction 'check-updates' -Apply $apply -RequestedYes $true
    Show-OperationResult $code
}

function Invoke-UninstallFlow([bool]$Preview = $false) {
    $profiles = Get-LocalProfiles
    $labels = @("Codex ($($profiles.codex))", "Claude ($($profiles.claude))")
    $selection = Read-MultiSelect $(if ($Preview) { 'Preview Uninstall - select clients' } else { 'Uninstall - select clients' }) $labels (Get-InstalledClientDefaults) -AllowBack
    if ($null -eq $selection) { return }
    $target = Convert-SelectionToTarget $selection
    Clear-Host; Show-Banner
    Write-Host $(if ($Preview) {'Preview Uninstall'} else {'Ready to uninstall'}) -ForegroundColor Yellow
    Write-Host ''
    Write-Host 'Will remove framework-owned client wiring, generated agents and managed skill links.'
    Write-Host 'Will preserve Python, Git, uv, unrelated settings/skills, repo overrides and .ai-index data.' -ForegroundColor DarkGray
    if (-not $Preview) {
        Write-Host ''
        $confirm = Read-SingleSelect 'Continue?' @('Uninstall','Cancel') 1 -AllowBack
        if ($confirm -ne 0) { return }
    }
    $code = Invoke-CoreAction -SelectedAction 'uninstall' -SelectedTarget $target -RequestedDryRun $Preview -RequestedYes $true
    Show-OperationResult $code
}

function Invoke-DoctorFlow {
    Clear-Host; Show-Banner
    $code = Invoke-CoreAction -SelectedAction 'doctor'
    Pause-ForMenu
}

function Invoke-PreviewFlow {
    $idx = Read-SingleSelect 'Preview which operation?' @('Install','Update / Repair','Change profiles','Uninstall') 0 -AllowBack
    switch ($idx) {
        0 { Invoke-InstallFlow $true }
        1 { Invoke-RepairFlow $true }
        2 { Invoke-ChangeProfileFlow $true }
        3 { Invoke-UninstallFlow $true }
    }
}

function Start-InteractiveInstaller {
    while ($true) {
        $idx = Read-SingleSelect 'AI Framework Installer' @(
            'Install',
            'Update / Repair',
            'Change profiles',
            'Check for updates',
            'Uninstall',
            'Doctor',
            'Preview changes',
            'Exit'
        ) 0
        switch ($idx) {
            0 { Invoke-InstallFlow }
            1 { Invoke-RepairFlow }
            2 { Invoke-ChangeProfileFlow }
            3 { Invoke-CheckUpdatesFlow }
            4 { Invoke-UninstallFlow }
            5 { Invoke-DoctorFlow }
            6 { Invoke-PreviewFlow }
            7 { Clear-Host; return }
        }
    }
}

if ($script:InteractiveMode) {
    Start-InteractiveInstaller
    exit 0
}

$code = Invoke-CoreAction -SelectedAction $Action -SelectedTarget $Target -SelectedProfile $Profile -SelectedCodexProfile $CodexProfile -SelectedClaudeProfile $ClaudeProfile -RequestedDryRun ([bool]$DryRun) -RequestedYes ([bool]$Yes) -RequestedSkipFrameworkUpdate ([bool]$SkipFrameworkUpdate) -RequestedNoAiIndexUpdate ([bool]$NoAiIndexUpdate) -Apply $Apply -JsonOutput ([bool]$JsonOutput)
exit $code
