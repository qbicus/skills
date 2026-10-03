#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from provider_runtime import (  # noqa: E402
    ProviderConfigError,
    SUPPORTED_ROLES,
    detect_provider,
    effective_summary,
    find_repo_root,
    load_effective_config,
    render_native,
    resolve_role,
    validate_config,
)


def print_help() -> None:
    print("Company AI Framework")
    print()
    print("Usage: ai <command> [args]")
    print()
    print("Commands:")
    print("  help       Show this help")
    print("  skills     Print the installed framework skill catalog")
    print("  provider   Inspect/validate/render provider-aware model routing")
    print("  repo-init  Initialize/update repository AI framework files")
    print()
    print("Provider examples:")
    print("  ai provider")
    print("  ai provider --effective")
    print("  ai provider --validate")
    print("  ai provider --role executor")
    print("  ai provider --provider claude --render-native ./out/claude")
    print()
    print(f"Full documentation: {ROOT / 'README.md'}")
    print(f"Quick reference:    {ROOT / 'HELP.md'}")


def print_skills() -> int:
    skill_list = ROOT / "skills" / "SKILL-LIST.md"
    if not skill_list.exists():
        print(f"Skill catalog not found: {skill_list}", file=sys.stderr)
        return 1
    print(skill_list.read_text(encoding="utf-8"))
    return 0


def provider_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ai provider", add_help=True)
    p.add_argument("--provider", choices=["codex", "claude"], help="Override provider detection")
    p.add_argument("--repo", type=Path, help="Repository root used for .ai/provider overrides")
    p.add_argument("--effective", action="store_true", help="Print the effective merged config summary")
    p.add_argument("--validate", action="store_true", help="Validate effective provider config")
    p.add_argument("--role", choices=SUPPORTED_ROLES, help="Resolve one role and show its fallback chain")
    p.add_argument("--get", dest="get_path", help="Print one dotted effective-config value, e.g. behavior.advisor.repeatedFailureThreshold")
    p.add_argument("--diagnose", action="store_true", help="Show read-only runtime/client wiring diagnostics")
    p.add_argument(
        "--available-model",
        action="append",
        default=None,
        help="Treat only this model as available (repeat to test fallback/native rendering)",
    )
    p.add_argument("--render-native", type=Path, help="Render client-native agent/config fragments to a directory")
    p.add_argument("--json", action="store_true", help="Emit JSON where applicable")
    return p


def _get_dotted(data: dict, dotted: str):
    current = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            raise ProviderConfigError(f"Config path not found: {dotted}")
        current = current[part]
    return current


def _print_diagnostics(provider: str, effective, repo_root: Path) -> None:
    home = Path.home()
    print(f"Provider: {provider}")
    print(f"Repository: {repo_root}")
    print(f"CLI executable: {shutil.which(provider) or 'not found on PATH'}")
    print("Config sources:")
    for path in effective.sources:
        print(f"  - {path}")
    if provider == "codex":
        client_home = Path(os.environ.get("CODEX_HOME", home / ".codex"))
        config = client_home / "config.toml"
        agents = client_home / "agents"
    else:
        client_home = home / ".claude"
        config = client_home / "settings.json"
        agents = client_home / "agents"
    print(f"Client home: {client_home} ({'exists' if client_home.exists() else 'missing'})")
    print(f"Client config: {config} ({'exists' if config.exists() else 'missing'})")
    print(f"Client agents: {agents} ({'exists' if agents.exists() else 'missing'})")
    for role in ("executor", "researcher", "advisor", "fast"):
        suffix = ".toml" if provider == "codex" else ".md"
        native = agents / f"ai-{role}{suffix}"
        print(f"  ai-{role:10}: {'installed' if native.exists() else 'not installed'}")
    repo_override = repo_root / ".ai" / "providers" / f"{provider}.yml"
    print(f"Repo override: {repo_override} ({'active' if repo_override.exists() else 'none'})")


def provider_command(argv: list[str]) -> int:
    args = provider_parser().parse_args(argv)
    try:
        provider, source = detect_provider(args.provider)
        if provider is None:
            print("Provider could not be detected automatically.", file=sys.stderr)
            print("Use --provider codex|claude or set AI_PROVIDER.", file=sys.stderr)
            return 2
        repo_root = (args.repo or find_repo_root()).resolve()
        effective = load_effective_config(provider, repo_root, ROOT)

        if args.get_path:
            value = _get_dotted(effective.config, args.get_path)
            if args.json or isinstance(value, (dict, list)):
                print(json.dumps(value, indent=2))
            elif isinstance(value, bool):
                print("true" if value else "false")
            else:
                print(value)

        if args.diagnose:
            _print_diagnostics(provider, effective, repo_root)

        if args.validate:
            errors = validate_config(effective.config, provider)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print(f"OK: effective {provider} provider config is valid")

        if args.role:
            resolved = resolve_role(effective.config, args.role, args.available_model)
            if args.json:
                print(json.dumps(resolved, indent=2))
            else:
                print(f"Requested role: {resolved['requestedRole']}")
                print(f"Resolved role:  {resolved['resolvedRole']}")
                print(f"Model:          {resolved['model']}")
                print(f"Effort:         {resolved['effort']}")
                print(f"Fallback used:  {'yes' if resolved['fallbackUsed'] else 'no'}")
                print("Candidates:")
                for candidate in resolved["candidates"]:
                    print(f"  - {candidate['role']}: {candidate['model']} ({candidate['effort']})")

        if args.render_native:
            written = render_native(effective, args.render_native.resolve(), args.available_model)
            print(f"Rendered {provider} native wiring to: {args.render_native.resolve()}")
            for path in written:
                print(f"  {path}")

        if args.effective:
            summary = effective_summary(effective)
            if args.json:
                print(json.dumps(summary, indent=2))
            else:
                print(f"Provider: {provider} ({source})")
                print(f"Repository: {repo_root}")
                print("Config sources:")
                for path in effective.sources:
                    print(f"  - {path}")
                print("Roles:")
                for role, resolved in summary["roles"].items():
                    marker = " (fallback)" if resolved["fallbackUsed"] else ""
                    print(f"  {role:10} -> {resolved['model']} / {resolved['effort']}{marker}")
                advisor = summary["behavior"].get("advisor", {})
                execution = summary["behavior"].get("execution", {})
                print("Behavior:")
                print(f"  repeated failure threshold: {advisor.get('repeatedFailureThreshold')}")
                print(f"  plan check:                 {advisor.get('planCheck')}")
                print(f"  completion check:           {advisor.get('completionCheck')}")
                print(f"  worker scope:               {execution.get('workerScope')}")
                print(f"  parallel mode:              {execution.get('parallelMode')}")

        if not any((args.validate, args.role, args.render_native, args.effective, args.get_path, args.diagnose)):
            print("Provider-aware routing")
            print(f"  Active provider:  {provider} ({source})")
            print(f"  Codex defaults:   {ROOT / 'providers' / 'codex.yml'}")
            print(f"  Claude defaults:  {ROOT / 'providers' / 'claude.yml'}")
            print(f"  Repo override:    {repo_root / '.ai' / 'providers' / (provider + '.yml')}")
            print("  Explicit override: AI_PROVIDER or --provider")
            print(f"  Details:          {ROOT / 'docs' / 'model-routing.md'}")
            print("  Use --effective, --validate, --role, or --render-native for more detail.")
        return 0
    except ProviderConfigError as exc:
        print(f"Provider configuration error: {exc}", file=sys.stderr)
        return 2


def main() -> int:
    if len(sys.argv) < 2:
        print_help()
        return 0

    cmd = sys.argv[1].lower()
    args = sys.argv[2:]

    if cmd in {"help", "-h", "--help"}:
        print_help()
        return 0
    if cmd == "skills":
        return print_skills()
    if cmd in {"provider", "providers"}:
        return provider_command(args)
    if cmd == "repo-init":
        return subprocess.call([sys.executable, str(ROOT / "scripts" / "repo-init.py"), *args])

    print(f"Unknown command: {cmd}", file=sys.stderr)
    print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
