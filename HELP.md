# AI Framework Help

Quick operator reference. See `README.md` for full documentation.

## Where things live

```text
~/.ai/AGENTS.md                  shared agent rules
~/.ai/providers/codex.yml       Codex medium/default routing
~/.ai/providers/codex.low.yml   Codex lower-usage profile
~/.ai/providers/codex.high.yml  Codex quality-first profile
~/.ai/providers/claude.yml      Claude medium/default routing
~/.ai/providers/claude.low.yml  Claude lower-usage profile
~/.ai/providers/claude.high.yml Claude quality-first profile
~/.ai/skills/                   reusable workflows
<repo>/.ai/providers/*.yml      optional repository overrides
```

## Role routing

The main `primary` model is the model selected in the active Codex/Claude session. Framework low/medium/high profiles control delegated roles and their fallbacks; they do not override the host/session model.


```text
primary     planning / architecture / material decisions / final ownership
executor    bounded implementation / edits / focused tests
researcher  external docs / API / library / vendor research
advisor     independent plan / stuck / completion review
fast        trivial low-risk routing
```

Override active provider only when needed:

```powershell
$env:AI_PROVIDER = "codex"
```

```bash
export AI_PROVIDER=claude
```

Usage profile defaults to `medium`. Override temporarily with:

```powershell
$env:AI_PROFILE = "low"
```

or per command:

```powershell
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider codex --profile high --effective
```

Persist the usual profile for a provider:

```powershell
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider codex --set-profile low
```

`low` conserves usage, `medium` is recommended/default, and `high` favors quality for difficult work.

## Main skills

| Skill | Use for | Typical explicit request |
|---|---|---|
| `new-feature` | Full gated feature delivery | `Use new-feature for <feature>.` |
| `nf-spec` | Feature specification | `Use nf-spec to draft/revise specs.md.` |
| `nf-design` | Implementation design | `Use nf-design from the approved spec.` |
| `nf-tasks` | Execution task plan | `Use nf-tasks from the approved design.` |
| `nf-avalonia` | Avalonia support inside NF | Usually activated by `new-feature` |
| `advisor` | Independent checkpoint | `Use advisor in plan|stuck|complete mode.` |
| `decision` | Durable decision log | `Use decision to record why we chose X.` |
| `parallel-exec` | Approved parallel-safe tasks | `Use parallel-exec for approved batch P2.` |
| `debug` | Logs-first root-cause debugging | `Use debug; inspect logs before edits.` |
| `code-review` | Review/fix current changes | `Use code-review on the current diff.` |
| `modernize-eval` | Modernization assessment | `Use modernize-eval on this system.` |
| `modernize-plan` | Approved modernization plan | `Use modernize-plan from the evaluation.` |
| `session-close` | End-of-session handoff | `Use session-close before we stop.` |
| `tas-01-*` | Per-repo architecture analysis | See architecture skills README |
| `tas-02-*` | Group projects/platforms | See architecture skills README |
| `tas-03-*` | Normalize architecture entities | See architecture skills README |
| `tas-04-*` | Generate TAS documents | See architecture skills README |

Claude Code exposes installed skills through `/name` commands. Natural-language `Use the <name> skill...` is portable across clients.

### `repo-init`

Use when onboarding a new/existing repository to the framework. It inspects first, preserves existing project configuration, scaffolds missing framework files, sets up AiIndex/Graphify repository intelligence as appropriate, updates generated-data ignore rules, asks before broad full/rebuild indexing, and verifies the result.

Recommended prompt:

```text
Use repo-init to initialize this existing repository for our AI framework.
Set up Graphify, AiIndex, repo-local configuration and gitignore entries as appropriate.
Preserve all existing config and code.
Inspect first, show me the planned changes, then proceed.
```

## New feature flow

```text
nf-spec -> approve
nf-design -> advisor:plan if substantial -> approve
nf-tasks -> approve
execute sequentially OR explicitly approved parallel-exec
advisor:stuck when same failure threshold is reached
advisor:complete before substantial feature is declared done
```

Spec records:

```yaml
substantial: true|false
```

## Advisor defaults

```text
Repeated same failure threshold: 2
Plan check: substantial work only
Completion check: substantial work only
```

Manual examples:

```text
Use advisor in plan mode on this design.
Use advisor in stuck mode; the same error happened twice.
Use advisor in complete mode before we mark this done.
```

## Worker outcomes

```text
COMPLETE
BLOCKED
NEEDS_DECISION
NEEDS_RESEARCH
```

Workers are `bounded`: directly related files are allowed; material architecture/contract/storage/rollout decisions are escalated.

## Parallel rule

No automatic fan-out. `parallel-exec` runs only when an approved plan explicitly marks work parallel-safe/eligible and parallel execution is selected.

## Framework helper

```powershell
python "$env:USERPROFILE\.ai\scripts\ai.py" help
python "$env:USERPROFILE\.ai\scripts\ai.py" skills
python "$env:USERPROFILE\.ai\scripts\ai.py" provider
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --effective
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --profile low --effective
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --profile high --validate
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider codex --set-profile medium
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --role executor
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --diagnose
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --get behavior.advisor.repeatedFailureThreshold
```


### Render native role agents

```powershell
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider codex --render-native "$env:USERPROFILE\.ai\generated\codex"
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --provider claude --render-native "$env:USERPROFILE\.ai\generated\claude"
```

Add `--repo <repo-root>` to include repository overrides. Generated role agents are `ai-executor`, `ai-researcher`, `ai-advisor`, and `ai-fast`; `primary` remains the owning thread.

To test fallback selection, repeat `--available-model <model>` with `--role` or `--render-native`. For normal profile changes use the installer's **Change profiles** action so native files are regenerated/re-synced automatically; `--profile low|medium|high` remains useful for one-off helper diagnostics/rendering.

## Project init

Interactive:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1"
```

Typed/non-interactive:

```powershell
& "$env:USERPROFILE\.ai\init-project.ps1" -Type dotnet -NonInteractive
```

Supported type examples:

```text
dotnet
go
nextjs
python
vb-migration
```

Useful flags/actions:

```text
-DryRun
-WithCodexHooks
-WithGraphifyClaude
-Action update
-Action reinit
-Action dry-run
```

## Repository intelligence

```text
AiIndex  -> semantic/fuzzy/behavior discovery
Graphify -> callers/dependencies/structure/blast radius
Mixed    -> AiIndex first, Graphify second
```

Preferred AiIndex MCP tools:

```text
init_project
index_status
index_project
search_code
```

## Installation / lifecycle

Fresh Windows bootstrap:

```powershell
irm https://raw.githubusercontent.com/qbicus/skills/main/install.ps1 | iex
```

Existing Windows install / maintenance console:

```powershell
& "$env:USERPROFILE\.ai\install.ps1"
```

Menu: Install, Update / Repair, Change profiles, Check for updates, Uninstall, Doctor, Preview changes, Exit. Use Up/Down, Space, Enter, and Esc.

Windows non-interactive examples:

```powershell
& "$env:USERPROFILE\.ai\install.ps1" doctor
& "$env:USERPROFILE\.ai\install.ps1" install -Target codex -Profile low -Yes
& "$env:USERPROFILE\.ai\install.ps1" update-repair -Target both -Yes
& "$env:USERPROFILE\.ai\install.ps1" change-profile -Target codex -Profile medium -Yes
& "$env:USERPROFILE\.ai\install.ps1" check-updates
& "$env:USERPROFILE\.ai\install.ps1" uninstall -Target claude -Yes
```

Linux non-interactive examples:

```bash
~/.ai/install.sh doctor
~/.ai/install.sh install --target codex --profile low --yes
~/.ai/install.sh update-repair --target both --yes
~/.ai/install.sh change-profile --target codex --profile medium --yes
~/.ai/install.sh check-updates
~/.ai/install.sh uninstall --target claude --yes
```

`Update / Repair` preserves the active profile by default. Use `Change profiles` for deliberate low/medium/high changes. AiIndex is not re-downloaded when the installed runtime is healthy and current. Existing Graphify tooling/integration is preserved.

Canonical repository: `https://github.com/qbicus/skills.git`. See `README.md` and `INSTALLER.md`.

## Python prerequisite policy

The AI framework itself runs Python scripts. Bootstrap therefore requires Python 3.11+ as a first-class prerequisite. Existing compatible Python is used as-is. If missing, Windows installs the highest stable Python 3.x package exposed by `winget`; Linux installs the current Python package exposed by the detected distribution package manager. Git and `uv` are handled similarly when missing.

Uninstall deliberately leaves Python, Git, and `uv` installed because they are shared system/developer prerequisites.


Doctor and uninstall are intentionally non-mutating with respect to system prerequisites: they require an existing compatible Python runtime and never install Git, Python, or uv.
