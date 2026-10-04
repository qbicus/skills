from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_runtime import (  # noqa: E402
    ProviderConfigError,
    deep_merge,
    detect_profile,
    detect_provider,
    save_profile,
    load_effective_config,
    render_native,
    resolve_role,
    validate_config,
)


class ProviderRuntimeTests(unittest.TestCase):
    def test_deep_merge_replaces_lists_but_merges_maps(self) -> None:
        base = {"roles": {"executor": {"model": "a", "fallbackModels": ["b"]}}, "x": 1}
        override = {"roles": {"executor": {"model": "c", "fallbackModels": ["d"]}}}
        merged = deep_merge(base, override)
        self.assertEqual(merged["roles"]["executor"]["model"], "c")
        self.assertEqual(merged["roles"]["executor"]["fallbackModels"], ["d"])
        self.assertEqual(merged["x"], 1)

    def test_explicit_provider_wins(self) -> None:
        provider, source = detect_provider("codex", {"CLAUDECODE": "1"})
        self.assertEqual(provider, "codex")
        self.assertEqual(source, "explicit argument")

    def test_ai_provider_wins_over_runtime_markers(self) -> None:
        provider, source = detect_provider(None, {"AI_PROVIDER": "claude", "CODEX_HOME": "x"})
        self.assertEqual(provider, "claude")
        self.assertEqual(source, "AI_PROVIDER")

    def test_profile_defaults_to_medium_and_honors_override(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            framework = Path(td)
            profile, source = detect_profile(None, {}, provider="codex", framework_root=framework)
            self.assertEqual(profile, "medium")
            self.assertEqual(source, "default")
            save_profile("codex", "low", framework)
            profile, source = detect_profile(None, {}, provider="codex", framework_root=framework)
            self.assertEqual(profile, "low")
            self.assertEqual(source, "saved profile")
            profile, source = detect_profile(None, {"AI_PROFILE": "high"}, provider="codex", framework_root=framework)
            self.assertEqual(profile, "high")
            self.assertEqual(source, "AI_PROFILE")
            profile, source = detect_profile("medium", {"AI_PROFILE": "high"}, provider="codex", framework_root=framework)
            self.assertEqual(profile, "medium")
            self.assertEqual(source, "explicit argument")

    def test_effective_config_applies_repo_partial_override(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            path = repo / ".ai" / "providers"
            path.mkdir(parents=True)
            (path / "codex.yml").write_text(
                "roles:\n  executor:\n    model: repo-executor\nbehavior:\n  advisor:\n    repeatedFailureThreshold: 3\n",
                encoding="utf-8",
            )
            effective = load_effective_config("codex", repo, ROOT)
            self.assertEqual(effective.config["roles"]["executor"]["model"], "repo-executor")
            self.assertEqual(effective.config["roles"]["primary"]["model"], "gpt-6-astra")
            self.assertEqual(effective.config["behavior"]["advisor"]["repeatedFailureThreshold"], 3)
            self.assertEqual(effective.profile, "medium")
            self.assertEqual(len(effective.sources), 2)

    def test_low_profile_and_profile_specific_repo_override(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            path = repo / ".ai" / "providers"
            path.mkdir(parents=True)
            (path / "codex.yml").write_text(
                "behavior:\n  advisor:\n    repeatedFailureThreshold: 3\n",
                encoding="utf-8",
            )
            (path / "codex.low.yml").write_text(
                "roles:\n  fast:\n    effort: medium\n",
                encoding="utf-8",
            )
            effective = load_effective_config("codex", repo, ROOT, "low")
            self.assertEqual(effective.profile, "low")
            self.assertEqual(effective.config["roles"]["primary"]["model"], "gpt-5.6-sol")
            self.assertEqual(effective.config["roles"]["fast"]["effort"], "medium")
            self.assertEqual(effective.config["behavior"]["advisor"]["repeatedFailureThreshold"], 3)
            self.assertEqual(len(effective.sources), 3)

    def test_role_fallback_model(self) -> None:
        effective = load_effective_config("codex", ROOT, ROOT)
        resolved = resolve_role(effective.config, "executor", ["gpt-6-sol"])
        self.assertEqual(resolved["model"], "gpt-6-sol")
        self.assertTrue(resolved["fallbackUsed"])

    def test_role_fallback_role(self) -> None:
        effective = load_effective_config("codex", ROOT, ROOT)
        resolved = resolve_role(effective.config, "advisor", ["gpt-6-astra"])
        self.assertEqual(resolved["resolvedRole"], "executor")
        self.assertEqual(resolved["model"], "gpt-6-astra")
        self.assertTrue(resolved["fallbackUsed"])

    def test_invalid_threshold(self) -> None:
        effective = load_effective_config("claude", ROOT, ROOT)
        broken = json.loads(json.dumps(effective.config))
        broken["behavior"]["advisor"]["repeatedFailureThreshold"] = 0
        errors = validate_config(broken, "claude")
        self.assertTrue(any("repeatedFailureThreshold" in x for x in errors))

    def test_render_codex_native(self) -> None:
        effective = load_effective_config("codex", ROOT, ROOT)
        with tempfile.TemporaryDirectory() as td:
            written = render_native(effective, Path(td))
            self.assertTrue(any(p.name == "config.fragment.toml" for p in written))
            text = (Path(td) / "agents" / "ai-executor.toml").read_text(encoding="utf-8")
            self.assertIn('model = "gpt-5.6-sol"', text)
            self.assertIn('sandbox_mode = "workspace-write"', text)
            fragment = (Path(td) / "config.fragment.toml").read_text(encoding="utf-8")
            self.assertIn("MUST retry the same task with ai-executor-fallback-1", fragment)
            self.assertIn("MUST NOT perform the delegated task itself", fragment)
            expected_agent = (Path(td) / "agents" / "ai-executor.toml").resolve().as_posix()
            self.assertIn(f'config_file = "{expected_agent}"', fragment)
            self.assertNotIn('config_file = "./agents/', fragment)

    def test_render_with_availability_resolves_transitive_fallback(self) -> None:
        effective = load_effective_config("codex", ROOT, ROOT)
        with tempfile.TemporaryDirectory() as td:
            render_native(effective, Path(td), ["gpt-5.6-sol"])
            text = (Path(td) / "agents" / "ai-fast.toml").read_text(encoding="utf-8")
            self.assertIn('model = "gpt-5.6-sol"', text)

    def test_high_profile_changes_codex_executor_and_advisor(self) -> None:
        effective = load_effective_config("codex", ROOT, ROOT, "high")
        self.assertEqual(effective.config["roles"]["executor"]["model"], "gpt-6-sol")
        self.assertEqual(effective.config["roles"]["advisor"]["effort"], "high")

    def test_render_claude_native(self) -> None:
        effective = load_effective_config("claude", ROOT, ROOT)
        with tempfile.TemporaryDirectory() as td:
            written = render_native(effective, Path(td))
            self.assertTrue(any(p.name == "settings.fragment.json" for p in written))
            text = (Path(td) / "agents" / "ai-advisor.md").read_text(encoding="utf-8")
            self.assertIn("model: sonnet", text)
            self.assertIn("tools: Read, Glob, Grep", text)


if __name__ == "__main__":
    unittest.main()
