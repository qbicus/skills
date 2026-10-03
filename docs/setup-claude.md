# Claude Code Setup

> Automated installation/update/uninstall is still pending. The runtime adapter and native Claude fragments are implemented; the installer will merge them safely into Claude Code without replacing unrelated settings or agents.

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

Global Claude routing policy:

```text
~/.ai/providers/claude.yml
```

Optional repository override:

```text
<repo>/.ai/providers/claude.yml
```

Inspect the effective routing:

```bash
python ~/.ai/scripts/ai.py provider --provider claude --effective
python ~/.ai/scripts/ai.py provider --provider claude --validate
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
  --render-native ~/.ai/generated/claude
```

Generate with a repository override:

```bash
python ~/.ai/scripts/ai.py provider \
  --provider claude \
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

The installer will eventually merge `settings.fragment.json` into `~/.claude/settings.json` and sync the generated agents under `~/.claude/agents/`, while preserving unrelated settings/agents.

## Advisor behavior

The framework uses `ai-advisor` for its `plan`, `stuck`, and `complete` checkpoints by default.

This is intentional: Claude's native advisor tool receives the **full conversation** on each consultation, while this framework's agreed checkpoint contract sends compact purpose-specific context. The native advisor remains useful as an optional manual/full-session second opinion and is represented by `native-advisor.optional.json`, but it is not enabled by the framework default.

The provider still records the preferred/current advisor model so the installer or user can opt into native advisor behavior separately.

Current Claude documentation also states that Fable is temporarily unavailable as a native advisor selection. The provider therefore uses `opus` for the current advisor role while retaining `preferredWhenAvailable: fable` as policy metadata.

## Tool boundaries

Generated Claude subagents use role-specific tool surfaces:

- `ai-executor`: read/write/edit/search/shell;
- `ai-researcher`: read/search/web, no repository edits;
- `ai-advisor`: read/search only;
- `ai-fast`: read/search only.

These are defense-in-depth boundaries. Shared skill instructions still define what each role may decide.

## Parallel execution

Claude supports concurrent subagents, but framework parallelism remains **plan-controlled only**. Do not use native parallel capability unless the approved plan marks tasks parallel-safe/eligible and parallel execution has been selected.

## Current limitation

The native files are generated but are not automatically merged into `~/.claude/settings.json` or `~/.claude/agents/` yet. That safe install/update/uninstall work belongs to `INSTALLER.md`.

For full usage see `README.md`, `HELP.md`, and `docs/model-routing.md`.
