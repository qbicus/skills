# Claude Code Setup

> Windows installer lifecycle support is implemented and live-validated for Claude Code. The installer safely merges framework-owned Claude wiring while preserving unrelated settings and agents. Linux support is implemented but still pending the same live validation pass.

## Global folders

```text
%USERPROFILE%\.claude  # Claude Code runtime/config
%USERPROFILE%\.ai      # shared company AI framework
```

## Shared instructions and skills

`~/.claude/CLAUDE.md` should import or bridge to the framework's:

```text
~/.ai/CLAUDE.md
```

Company-owned skills should remain sourced from:

```text
~/.ai/skills/
```

and be exposed to Claude's skill location without replacing Claude-managed or third-party content.

## Provider routing

Global Claude routing profiles:

```text
~/.ai/providers/claude.yml          # medium/default
~/.ai/providers/claude.low.yml
~/.ai/providers/claude.high.yml
```

Select `low`, `medium`, or `high` with `--profile` or `AI_PROFILE`; `medium` is the default/recommended delegated-role profile. The active primary Claude model remains the model selected for the current Claude session; framework profiles do not override that host/session choice.

Optional repository overrides:

```text
<repo>/.ai/providers/claude.yml                 # applies to every profile
<repo>/.ai/providers/claude.<profile>.yml       # applies only to selected profile
```

Persist the normal Claude profile when desired:

```bash
python ~/.ai/scripts/ai.py provider --provider claude --set-profile medium
```

Inspect the effective routing:

```bash
python ~/.ai/scripts/ai.py provider --provider claude --effective
python ~/.ai/scripts/ai.py provider --provider claude --profile low --effective
python ~/.ai/scripts/ai.py provider --provider claude --profile high --validate
python ~/.ai/scripts/ai.py provider --provider claude --role executor
```

## Native Claude subagents

Claude Code supports custom subagents with per-agent `model`, `effort`, and tool restrictions. The framework renderer produces:

```text
ai-executor
ai-researcher
ai-advisor
ai-fast
```

`primary` remains the owning/main Claude conversation.

Generate global-default native files:

```bash
python ~/.ai/scripts/ai.py provider \
  --provider claude \
  --profile medium \
  --render-native ~/.ai/generated/claude
```

Generate with a repository override:

```bash
python ~/.ai/scripts/ai.py provider \
  --provider claude \
  --profile low \
  --repo /path/to/repo \
  --render-native ~/.ai/generated/claude
```

Output:

```text
settings.fragment.json
native-advisor.optional.json
agents/ai-executor.md
agents/ai-researcher.md
agents/ai-advisor.md
agents/ai-fast.md
```

The installer merges the framework-owned settings from `settings.fragment.json` into `~/.claude/settings.json` and syncs generated framework agents under `~/.claude/agents/`, while preserving unrelated settings/agents. It also preserves an already-correct AiIndex MCP registration instead of rewriting Claude runtime state on every repair.

## Advisor behavior

The framework uses `ai-advisor` for its `plan`, `stuck`, and `complete` checkpoints by default.

This is intentional: Claude's native advisor tool receives the **full conversation** on each consultation, while this framework's agreed checkpoint contract sends compact purpose-specific context. The native advisor remains useful as an optional manual/full-session second opinion and is represented by `native-advisor.optional.json`, but it is not enabled by the framework default.

The provider still records the preferred/current advisor model so the installer or user can opt into native advisor behavior separately.

The portable framework `ai-advisor` model depends on the selected usage profile (Sonnet for low/medium, Opus for high in the current defaults). Claude's native full-session advisor remains optional/manual and separate from this checkpoint routing.

## Tool boundaries

Generated Claude subagents use role-specific tool surfaces:

- `ai-executor`: read/write/edit/search/shell;
- `ai-researcher`: read/search/web, no repository edits;
- `ai-advisor`: read/search only;
- `ai-fast`: read/search only.

These are defense-in-depth boundaries. Shared skill instructions still define what each role may decide.

## Parallel execution

Claude supports concurrent subagents, but framework parallelism remains **plan-controlled only**. Do not use native parallel capability unless the approved plan marks tasks parallel-safe/eligible and parallel execution has been selected.

## Current status

On Windows, the installer now renders/syncs Claude native agents, merges framework-owned settings, preserves unrelated `~/.claude/settings.json` content, and maintains AiIndex MCP registration idempotently.

The main remaining platform limitation is validation rather than design: Linux support exists but has not completed the same live lifecycle test pass as Windows. Claude behavioral E2E coverage can also be expanded separately without blocking the Windows installer lifecycle.

For full usage see `README.md`, `HELP.md`, and `docs/model-routing.md`.
