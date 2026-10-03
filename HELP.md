# AI Framework Help

Quick operator reference. See `README.md` for full documentation.

## Where things live

```text
~/.ai/AGENTS.md                  shared agent rules
~/.ai/providers/codex.yml       Codex routing defaults
~/.ai/providers/claude.yml      Claude routing defaults
~/.ai/skills/                   reusable workflows
<repo>/.ai/providers/*.yml      optional repository overrides
```

## Role routing

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
python "$env:USERPROFILE\.ai\scripts\ai.py" provider --validate
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

To test fallback selection, repeat `--available-model <model>` with `--role` or `--render-native`.

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

## Installation

Automated installer/update/uninstall is intentionally pending. Provider resolution and native fragment generation are implemented; do not invent installer commands yet. Use `docs/setup-codex.md` / `docs/setup-claude.md` for current manual/native details and `INSTALLER.md` for the installer checklist.
