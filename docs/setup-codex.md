# Codex Setup

## Global folders

Use two folders:

```text
%USERPROFILE%\.codex   # Codex runtime/config
%USERPROFILE%\.ai      # shared company AI framework
```

## Recommended global Codex instruction file

Create or update:

```text
%USERPROFILE%\.codex\AGENTS.md
```

with content similar to:

```md
# Global Codex Instructions

Use the company AI framework from `%USERPROFILE%\.ai`.

Follow:
- `%USERPROFILE%\.ai\AGENTS.md`
- `%USERPROFILE%\.ai\rules\team-rules.md`
- `%USERPROFILE%\.ai\rules\coding-standards.md`

Use skills from `%USERPROFILE%\.ai\skills`.

Before switching projects or ending meaningful work, run the `session-close` skill.
```

## Initialize a project

From inside a repository:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1"
```

or choose a project type:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1" -Type dotnet
& "$env:USERPROFILE\.ai\init-project.ps1" -Type go
& "$env:USERPROFILE\.ai\init-project.ps1" -Type nextjs
& "$env:USERPROFILE\.ai\init-project.ps1" -Type python
& "$env:USERPROFILE\.ai\init-project.ps1" -Type vb-migration
```
