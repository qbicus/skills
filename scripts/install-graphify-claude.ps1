param(
    [Parameter(Mandatory = $false)]
    [string]$RepoPath = "."
)

$ErrorActionPreference = "Stop"

function Get-FullPath {
    param([string]$Path)

    return [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Path).Path)
}

$repo = Get-FullPath $RepoPath
$claudeFile = Join-Path $repo "CLAUDE.md"

if (-not (Get-Command graphify -ErrorAction SilentlyContinue)) {
    throw "Graphify is not available on PATH. Install it first, then rerun this script."
}

Write-Host "Repository : $repo"
Write-Host "Installing Graphify Claude integration..."

Push-Location $repo
try {
    & graphify claude install

    if ($LASTEXITCODE -ne 0) {
        throw "graphify claude install failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $claudeFile)) {
    throw "Graphify completed, but CLAUDE.md was not found at: $claudeFile"
}

# Keep Graphify's installer responsible for hooks/settings, but normalize only the
# generated CLAUDE.md section so our AiIndex/Graphify routing remains consistent.
$replacement = @'
## graphify

This project has a knowledge graph at `graphify-out/` with god nodes, community structure, and cross-file relationships.

Follow the repository-intelligence routing rules from the shared global framework.

Rules:

- Use Graphify when the question is primarily structural, including:
  - callers and callees;
  - dependency paths;
  - imports and references;
  - inheritance or implementation relationships;
  - architectural relationships;
  - impact or blast-radius analysis;
  - paths between known symbols or concepts.
- For semantic or behavioral discovery such as "where is the code that does X?", use AiIndex first when it is available.
- For mixed questions, use AiIndex to discover relevant files, symbols, or concepts first, then use Graphify to trace or verify their structural relationships.
- When Graphify is appropriate and `graphify-out/graph.json` exists, query the existing graph instead of rebuilding it.
- Use `graphify query "<question>"` for broader structural traversal.
- Use `graphify path "<A>" "<B>"` for relationships between known concepts or symbols.
- Use `graphify explain "<concept>"` for focused structural explanations.
- If `graphify-out/wiki/index.md` exists, use it for broad graph navigation rather than reading the raw graph.
- Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review or when query/path/explain do not provide enough context.
- After modifying code, run `graphify update .` to keep the graph current.
'@

$content = [System.IO.File]::ReadAllText($claudeFile)

# Graphify currently writes a "## graphify" section. Replace that section up to the
# next level-2 heading, or to end-of-file when it is the final section.
$pattern = '(?ms)^## graphify\s*$.*?(?=^##\s+|\z)'

if ($content -match $pattern) {
    $updated = [System.Text.RegularExpressions.Regex]::Replace(
        $content,
        $pattern,
        ($replacement.TrimEnd() + [Environment]::NewLine + [Environment]::NewLine),
        1
    )
}
else {
    # This fallback keeps the script useful if Graphify changes its installer and
    # no longer writes the section, while still making the intended routing explicit.
    if ($content.Length -gt 0 -and -not $content.EndsWith([Environment]::NewLine)) {
        $content += [Environment]::NewLine
    }

    $updated =
        $content +
        [Environment]::NewLine +
        $replacement.TrimEnd() +
        [Environment]::NewLine
}

# Write UTF-8 without BOM for predictable cross-platform repository diffs.
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($claudeFile, $updated, $utf8NoBom)

Write-Host ""
Write-Host "Graphify Claude integration installed."
Write-Host "Normalized routing section in: $claudeFile"
Write-Host "Graphify hooks/settings remain managed by Graphify."
