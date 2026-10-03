#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

FRAMEWORK_ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_PROVIDERS = ("codex", "claude")
SUPPORTED_ROLES = ("primary", "executor", "researcher", "advisor", "fast")
EFFORT_LEVELS = {"none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"}


class ProviderConfigError(ValueError):
    pass


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return None
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value


def _load_yaml_fallback(text: str) -> dict[str, Any]:
    """Parse the small YAML subset used by provider config files.

    Supports nested mappings, scalar values, and lists of scalars. It is only a
    fallback for machines without PyYAML; provider files intentionally avoid
    anchors, inline collections, multiline scalars, and other advanced YAML.
    """
    raw_lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        content = raw.split("#", 1)[0].rstrip()
        if not content.strip():
            continue
        indent = len(content) - len(content.lstrip(" "))
        if indent % 2:
            raise ProviderConfigError("Provider YAML fallback parser requires 2-space indentation.")
        raw_lines.append((indent, content.strip()))

    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-2, root)]
    i = 0
    while i < len(raw_lines):
        indent, token = raw_lines[i]
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ProviderConfigError(f"Invalid YAML indentation near: {token}")
        parent = stack[-1][1]

        if token.startswith("- "):
            if not isinstance(parent, list):
                raise ProviderConfigError(f"List item without list parent near: {token}")
            parent.append(_parse_scalar(token[2:]))
            i += 1
            continue

        if ":" not in token:
            raise ProviderConfigError(f"Expected key/value pair near: {token}")
        key, value = token.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not isinstance(parent, dict):
            raise ProviderConfigError(f"Mapping entry under non-mapping near: {token}")

        if value:
            parent[key] = _parse_scalar(value)
            i += 1
            continue

        # Decide whether the nested container is a list or mapping by peeking.
        next_is_list = False
        if i + 1 < len(raw_lines):
            next_indent, next_token = raw_lines[i + 1]
            next_is_list = next_indent > indent and next_token.startswith("- ")
        child: Any = [] if next_is_list else {}
        parent[key] = child
        stack.append((indent, child))
        i += 1

    return root


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ProviderConfigError(f"Provider config not found: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
    except ModuleNotFoundError:
        data = _load_yaml_fallback(text)
    except Exception as exc:  # PyYAML syntax errors, etc.
        raise ProviderConfigError(f"Invalid YAML in {path}: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ProviderConfigError(f"Provider config root must be a mapping: {path}")
    return data


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge mappings; lists/scalars replace the inherited value."""
    result: dict[str, Any] = dict(base)
    for key, value in override.items():
        existing = result.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            result[key] = deep_merge(existing, value)
        else:
            result[key] = value
    return result


def detect_provider(explicit: str | None = None, env: dict[str, str] | None = None) -> tuple[str | None, str]:
    env = env or dict(os.environ)
    candidate = (explicit or env.get("AI_PROVIDER") or "").strip().lower()
    if candidate:
        if candidate not in SUPPORTED_PROVIDERS:
            raise ProviderConfigError(f"Unsupported provider '{candidate}'. Expected codex or claude.")
        source = "explicit argument" if explicit else "AI_PROVIDER"
        return candidate, source

    claude_markers = (
        "CLAUDECODE",
        "CLAUDE_CODE_ENTRYPOINT",
        "CLAUDE_CODE_SESSION_ID",
        "CLAUDE_CODE_REMOTE",
    )
    codex_markers = (
        "CODEX_HOME",
        "CODEX_SESSION_ID",
        "CODEX_THREAD_ID",
        "CODEX_SANDBOX",
    )
    claude = any(env.get(k) for k in claude_markers)
    codex = any(env.get(k) for k in codex_markers)
    if claude and not codex:
        return "claude", "runtime environment"
    if codex and not claude:
        return "codex", "runtime environment"
    return None, "not detected"


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() or (candidate / ".ai").exists():
            return candidate
    return current


@dataclass(frozen=True)
class EffectiveConfig:
    provider: str
    config: dict[str, Any]
    global_path: Path
    repo_path: Path | None
    sources: tuple[Path, ...]


def validate_config(config: dict[str, Any], provider: str | None = None) -> list[str]:
    errors: list[str] = []
    declared = config.get("provider")
    if provider and declared not in {None, provider}:
        errors.append(f"provider must be '{provider}', found '{declared}'")
    version = config.get("version")
    if version != 1:
        errors.append("version must be 1")

    roles = config.get("roles")
    if not isinstance(roles, dict):
        errors.append("roles must be a mapping")
        return errors

    for role in SUPPORTED_ROLES:
        entry = roles.get(role)
        if not isinstance(entry, dict):
            errors.append(f"roles.{role} must be a mapping")
            continue
        model = entry.get("model")
        if not isinstance(model, str) or not model.strip():
            errors.append(f"roles.{role}.model must be a non-empty string")
        effort = entry.get("effort")
        if effort is not None and (not isinstance(effort, str) or effort.lower() not in EFFORT_LEVELS):
            errors.append(f"roles.{role}.effort '{effort}' is not a recognized effort level")
        for list_key in ("fallbackModels", "fallbackRoles"):
            value = entry.get(list_key)
            if value is not None and (not isinstance(value, list) or not all(isinstance(x, str) for x in value)):
                errors.append(f"roles.{role}.{list_key} must be a list of strings")
        for fallback_role in entry.get("fallbackRoles", []) if isinstance(entry.get("fallbackRoles"), list) else []:
            if fallback_role not in SUPPORTED_ROLES:
                errors.append(f"roles.{role}.fallbackRoles contains unknown role '{fallback_role}'")

    behavior = config.get("behavior", {})
    if not isinstance(behavior, dict):
        errors.append("behavior must be a mapping")
    else:
        advisor = behavior.get("advisor", {})
        if isinstance(advisor, dict):
            threshold = advisor.get("repeatedFailureThreshold")
            if threshold is not None and (not isinstance(threshold, int) or threshold < 1):
                errors.append("behavior.advisor.repeatedFailureThreshold must be an integer >= 1")
            for key in ("completionCheck", "planCheck"):
                value = advisor.get(key)
                if value is not None and value not in {"always", "substantial-only", "off"}:
                    errors.append(f"behavior.advisor.{key} must be always, substantial-only, or off")
        execution = behavior.get("execution", {})
        if isinstance(execution, dict):
            if execution.get("workerScope") not in {None, "bounded", "strict"}:
                errors.append("behavior.execution.workerScope must be bounded or strict")
            if execution.get("parallelMode") not in {None, "plan-only", "off"}:
                errors.append("behavior.execution.parallelMode must be plan-only or off")
            max_agents = execution.get("maxConcurrentAgents")
            if max_agents is not None and (not isinstance(max_agents, int) or max_agents < 1):
                errors.append("behavior.execution.maxConcurrentAgents must be an integer >= 1")
    return errors


def load_effective_config(
    provider: str,
    repo_root: Path | None = None,
    framework_root: Path = FRAMEWORK_ROOT,
) -> EffectiveConfig:
    if provider not in SUPPORTED_PROVIDERS:
        raise ProviderConfigError(f"Unsupported provider: {provider}")
    global_path = framework_root / "providers" / f"{provider}.yml"
    base = load_yaml(global_path)
    repo = (repo_root or find_repo_root()).resolve()
    repo_path = repo / ".ai" / "providers" / f"{provider}.yml"
    sources: list[Path] = [global_path]
    merged = base
    used_repo: Path | None = None
    if repo_path.exists() and repo_path.resolve() != global_path.resolve():
        merged = deep_merge(base, load_yaml(repo_path))
        sources.append(repo_path)
        used_repo = repo_path
    errors = validate_config(merged, provider)
    if errors:
        joined = "\n  - ".join(errors)
        raise ProviderConfigError(f"Invalid effective {provider} provider config:\n  - {joined}")
    return EffectiveConfig(provider, merged, global_path, used_repo, tuple(sources))


def _ordered_role_candidates(config: dict[str, Any], role: str) -> list[tuple[str, str, str | None]]:
    if role not in SUPPORTED_ROLES:
        raise ProviderConfigError(f"Unknown role '{role}'.")
    roles = config["roles"]
    out: list[tuple[str, str, str | None]] = []
    visiting: set[str] = set()

    def visit(r: str) -> None:
        if r in visiting:
            return
        visiting.add(r)
        entry = roles[r]
        effort = entry.get("effort")
        model = entry.get("model")
        if model:
            out.append((r, model, effort))
        for fallback_model in entry.get("fallbackModels", []) or []:
            out.append((r, fallback_model, effort))
        for fallback_role in entry.get("fallbackRoles", []) or []:
            visit(fallback_role)
        visiting.remove(r)

    visit(role)
    seen: set[tuple[str, str | None]] = set()
    deduped: list[tuple[str, str, str | None]] = []
    for item in out:
        identity = (item[1], item[2])
        if identity not in seen:
            seen.add(identity)
            deduped.append(item)
    return deduped



def _native_role_candidates(config: dict[str, Any], role: str) -> list[tuple[str, str, str | None]]:
    """Keep native agent libraries compact: preferred + direct model/role fallbacks.

    Runtime diagnostics can still traverse fallback-role chains recursively, but
    loading every transitive fallback as a named native agent bloats agent
    descriptions/context. A fallback role contributes its preferred model only.
    """
    roles = config["roles"]
    entry = roles[role]
    out: list[tuple[str, str, str | None]] = [(role, entry["model"], entry.get("effort"))]
    for model in entry.get("fallbackModels", []) or []:
        out.append((role, model, entry.get("effort")))
    for fallback_role in entry.get("fallbackRoles", []) or []:
        fallback = roles[fallback_role]
        out.append((fallback_role, fallback["model"], fallback.get("effort")))
    seen: set[tuple[str, str | None]] = set()
    result: list[tuple[str, str, str | None]] = []
    for item in out:
        identity = (item[1], item[2])
        if identity not in seen:
            seen.add(identity)
            result.append(item)
    return result

def resolve_role(
    config: dict[str, Any],
    role: str,
    available_models: Iterable[str] | None = None,
) -> dict[str, Any]:
    candidates = _ordered_role_candidates(config, role)
    available = set(available_models) if available_models is not None else None
    chosen = None
    for candidate in candidates:
        if available is None or candidate[1] in available:
            chosen = candidate
            break
    if chosen is None:
        raise ProviderConfigError(
            f"No available model for role '{role}'. Candidates: " + ", ".join(model for _, model, _ in candidates)
        )
    resolved_role, model, effort = chosen
    requested = config["roles"][role]
    return {
        "requestedRole": role,
        "resolvedRole": resolved_role,
        "model": model,
        "effort": effort,
        "fallbackUsed": (resolved_role != role or model != requested.get("model")),
        "candidates": [
            {"role": r, "model": m, "effort": e} for r, m, e in candidates
        ],
    }


def _toml_quote(value: str) -> str:
    return json.dumps(value)


def _codex_agent_text(name: str, role: str, role_cfg: dict[str, Any], fallback_summary: str) -> str:
    sandbox = "workspace-write" if role == "executor" else "read-only"
    descriptions = {
        "executor": "Bounded implementation worker for explicit coding tasks, edits, and focused validation.",
        "researcher": "Read-only research agent for external docs, APIs, libraries, and evidence gathering.",
        "advisor": "Independent read-only reviewer for plan, repeated-failure, and completion checkpoints.",
        "fast": "Fast read-only agent for low-risk local routing and trivial reversible decisions.",
    }
    instructions = {
        "executor": """Work only on the bounded task delegated by the parent. You may touch directly related files required for the task, but report material scope expansion. Do not make architecture, contract, storage, rollout, or shared-policy decisions; return NEEDS_DECISION. If external evidence is required, return NEEDS_RESEARCH. Finish with COMPLETE, BLOCKED, NEEDS_DECISION, or NEEDS_RESEARCH and include validation performed. BLOCKED must state the blocker, evidence collected, exact prerequisite/input needed, and useful progress already completed.""",
        "researcher": """Gather only the evidence requested by the parent. Prefer authoritative/current documentation when external behavior is version-sensitive. Do not edit repository files. Return concise findings, source references, uncertainty, and any decision that still belongs to the primary agent.""",
        "advisor": """Act as an independent reviewer. Do not implement. Review only the supplied plan/stuck/completion context. Return OK or CONCERN. For CONCERN include Issue, Evidence, Recommendation, and Outcome (NEEDS_DECISION, NEEDS_RESEARCH, BLOCKED, or REVISE_AND_CONTINUE).""",
        "fast": """Handle only low-risk, reversible, local questions such as targeted lookup, file/symbol existence, or mechanical routing. Do not make architecture, contract, security, storage, rollout, or user-impacting decisions. Escalate anything non-trivial to the parent.""",
    }
    lines = [
        f"name = {_toml_quote(name)}",
        f"description = {_toml_quote(descriptions[role])}",
        f"model = {_toml_quote(str(role_cfg['model']))}",
    ]
    if role_cfg.get("effort"):
        lines.append(f"model_reasoning_effort = {_toml_quote(str(role_cfg['effort']))}")
    lines.extend([
        f"sandbox_mode = {_toml_quote(sandbox)}",
        f"developer_instructions = {_toml_quote(instructions[role] + ' Configured fallback chain: ' + fallback_summary + '. Model availability/startup failures are handled by the parent orchestration and are not task failures.')}",
        "",
    ])
    return "\n".join(lines)


def render_codex_native(effective: EffectiveConfig, output: Path, available_models: Iterable[str] | None = None) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    agents_dir = output / "agents"
    agents_dir.mkdir(exist_ok=True)
    written: list[Path] = []
    declarations: list[tuple[str, str, str]] = []

    for role in ("executor", "researcher", "advisor", "fast"):
        all_candidates = _native_role_candidates(effective.config, role)
        if available_models is not None:
            chosen = resolve_role(effective.config, role, available_models)
            candidates = [(chosen["resolvedRole"], chosen["model"], chosen["effort"])]
        else:
            candidates = all_candidates
        fallback_summary = " -> ".join(model for _, model, _ in all_candidates)
        for index, (_resolved_role, model, effort) in enumerate(candidates):
            suffix = "" if index == 0 else f"-fallback-{index}"
            name = f"ai-{role}{suffix}"
            filename = f"{name}.toml"
            role_cfg = {"model": model, "effort": effort}
            path = agents_dir / filename
            path.write_text(_codex_agent_text(name, role, role_cfg, fallback_summary), encoding="utf-8")
            if index == 0:
                next_name = f"ai-{role}-fallback-1" if len(candidates) > 1 else None
                description = f"Company AI framework {role} role."
                if next_name:
                    description += (
                        f" If this agent cannot start because its model is unavailable/unsupported, "
                        f"the parent MUST retry the same task with {next_name}; the parent MUST NOT "
                        f"perform the delegated task itself."
                    )
            else:
                next_name = f"ai-{role}-fallback-{index + 1}" if index + 1 < len(candidates) else None
                description = (
                    f"Fallback {index} for company AI framework {role} role; use when earlier candidate "
                    f"cannot start because its model is unavailable/unsupported."
                )
                if next_name:
                    description += (
                        f" If this fallback also cannot start for model availability, retry {next_name}; "
                        f"do not perform the delegated task in primary."
                    )
                else:
                    description += (
                        " If this final configured fallback cannot start, report the exhausted fallback "
                        "chain explicitly instead of silently doing the delegated task in primary."
                    )
            declarations.append((name, filename, description))
            written.append(path)

    primary_resolved = resolve_role(effective.config, "primary", available_models)
    primary = {"model": primary_resolved["model"], "effort": primary_resolved["effort"]}
    max_agents = effective.config.get("behavior", {}).get("execution", {}).get("maxConcurrentAgents", 4)
    fragment = [
        "# Generated by ~/.ai/scripts/ai.py provider --render-native.",
        "# Merge intentionally; the installer must preserve unrelated Codex config.",
        f"model = {_toml_quote(str(primary['model']))}",
    ]
    if primary.get("effort"):
        fragment.append(f"model_reasoning_effort = {_toml_quote(str(primary['effort']))}")
    fragment.extend([
        "",
        "[agents]",
        "enabled = true",
        f"max_concurrent_threads_per_session = {int(max_agents)}",
        "",
    ])
    for name, filename, description in declarations:
        fragment.extend([
            f"[agents.{name}]",
            f"description = {_toml_quote(description)}",
            f"config_file = {_toml_quote(str((agents_dir / filename).resolve().as_posix()))}",
            "",
        ])
    path = output / "config.fragment.toml"
    path.write_text("\n".join(fragment), encoding="utf-8")
    written.append(path)
    return written

def _claude_agent_text(name: str, role: str, role_cfg: dict[str, Any], fallback_summary: str) -> str:
    tools = {
        "executor": "Read, Write, Edit, Glob, Grep, Bash",
        "researcher": "Read, Glob, Grep, WebFetch, WebSearch",
        "advisor": "Read, Glob, Grep",
        "fast": "Read, Glob, Grep",
    }[role]
    descriptions = {
        "executor": "Bounded implementation worker for explicit coding tasks and focused validation.",
        "researcher": "Read-only researcher for current external docs, APIs, libraries, and vendor behavior.",
        "advisor": "Independent read-only checkpoint reviewer for plans, repeated failures, and completion.",
        "fast": "Low-cost read-only agent for trivial, reversible local routing decisions.",
    }
    bodies = {
        "executor": """Work only on the bounded task delegated by the parent. You may touch directly related files needed to complete it, but report material scope expansion. Never silently decide architecture, contracts, storage, rollout, or shared policy. Return one of COMPLETE, BLOCKED, NEEDS_DECISION, or NEEDS_RESEARCH and include validation performed. BLOCKED must state the blocker, evidence collected, exact prerequisite/input needed, and useful progress already completed.""",
        "researcher": """Research only the question delegated by the parent. Prefer authoritative and current sources for version-sensitive behavior. Do not modify repository files. Return concise findings with source references, limitations, and any unresolved decision that belongs to the primary agent.""",
        "advisor": """Act as an independent reviewer and do not implement. Review only the supplied plan, stuck, or completion context. Return OK or CONCERN. For CONCERN include Issue, Evidence, Recommendation, and Outcome: NEEDS_DECISION, NEEDS_RESEARCH, BLOCKED, or REVISE_AND_CONTINUE.""",
        "fast": """Handle only trivial, reversible, local routing questions. Do not make architecture, contract, security, storage, rollout, or user-impacting decisions. Escalate non-trivial work to the parent.""",
    }
    effort = role_cfg.get("effort") or "medium"
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {descriptions[role]}\n"
        f"tools: {tools}\n"
        f"model: {role_cfg['model']}\n"
        f"effort: {effort}\n"
        "---\n\n"
        f"{bodies[role]}\n\nConfigured fallback chain: {fallback_summary}\n"
    )


def render_claude_native(effective: EffectiveConfig, output: Path, available_models: Iterable[str] | None = None) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    agents_dir = output / "agents"
    agents_dir.mkdir(exist_ok=True)
    written: list[Path] = []
    for role in ("executor", "researcher", "advisor", "fast"):
        all_candidates = _native_role_candidates(effective.config, role)
        if available_models is not None:
            chosen = resolve_role(effective.config, role, available_models)
            candidates = [(chosen["resolvedRole"], chosen["model"], chosen["effort"])]
        else:
            candidates = all_candidates
        fallback_summary = " -> ".join(model for _, model, _ in all_candidates)
        for index, (_resolved_role, model, effort) in enumerate(candidates):
            suffix = "" if index == 0 else f"-fallback-{index}"
            name = f"ai-{role}{suffix}"
            role_cfg = {"model": model, "effort": effort}
            path = agents_dir / f"{name}.md"
            text = _claude_agent_text(name, role, role_cfg, fallback_summary)
            if index > 0:
                text = text.replace(
                    f"description: ",
                    f"description: Fallback {index}; use only when earlier {role} candidate is unavailable. ",
                    1,
                )
            path.write_text(text, encoding="utf-8")
            written.append(path)

    primary_r = resolve_role(effective.config, "primary", available_models)
    advisor_r = resolve_role(effective.config, "advisor", available_models)
    primary = {"model": primary_r["model"], "effort": primary_r["effort"]}
    advisor_cfg = {"model": advisor_r["model"], "effort": advisor_r["effort"]}
    settings = {
        "model": primary["model"],
        "effortLevel": primary.get("effort", "high"),
    }
    fallback_models = effective.config["roles"]["primary"].get("fallbackModels") or []
    if fallback_models:
        settings["fallbackModel"] = fallback_models
    path = output / "settings.fragment.json"
    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    written.append(path)

    native_advisor = effective.config.get("runtime", {}).get("nativeAdvisor", {})
    optional = {
        "advisorModel": advisor_cfg["model"],
        "enabledByFrameworkDefault": bool(native_advisor.get("useWhenAvailable", False)),
        "note": "Framework checkpoints use ai-advisor by default because Claude native advisor receives the full conversation.",
    }
    path = output / "native-advisor.optional.json"
    path.write_text(json.dumps(optional, indent=2) + "\n", encoding="utf-8")
    written.append(path)
    return written

def render_native(effective: EffectiveConfig, output: Path, available_models: Iterable[str] | None = None) -> list[Path]:
    if output.exists():
        shutil.rmtree(output)
    if effective.provider == "codex":
        return render_codex_native(effective, output, available_models)
    return render_claude_native(effective, output, available_models)


def effective_summary(effective: EffectiveConfig) -> dict[str, Any]:
    return {
        "provider": effective.provider,
        "sources": [str(p) for p in effective.sources],
        "roles": {
            role: resolve_role(effective.config, role)
            for role in SUPPORTED_ROLES
        },
        "behavior": effective.config.get("behavior", {}),
        "runtime": effective.config.get("runtime", {}),
    }
