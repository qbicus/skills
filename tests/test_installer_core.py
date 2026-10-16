from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from unittest import mock
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "installer" / "installer.py"
spec = importlib.util.spec_from_file_location("company_ai_installer", MODULE_PATH)
installer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(installer)


class InstallerCoreTests(unittest.TestCase):
    def test_toml_top_level_round_trip(self):
        text = 'service_tier = "default"\nmodel = "old"\n\n[features]\nmulti_agent = false\n'
        self.assertEqual(installer.toml_get_top(text, "model"), '"old"')
        text = installer.toml_set_top(text, "model", '"new"')
        self.assertEqual(installer.toml_get_top(text, "model"), '"new"')
        text = installer.toml_set_top(text, "model", None)
        self.assertIsNone(installer.toml_get_top(text, "model"))
        self.assertIn('service_tier = "default"', text)

    def test_toml_section_key_preserves_other_sections(self):
        text = '[features]\njs_repl = false\n\n[desktop]\nfoo = true\n'
        text = installer.toml_set_section_key(text, "features", "multi_agent", "true")
        self.assertEqual(installer.toml_get_section_key(text, "features", "multi_agent"), "true")
        self.assertIn("[desktop]", text)
        self.assertIn("foo = true", text)

    def test_remove_owned_codex_sections_preserves_unrelated(self):
        text = '''[agents.ai-fast]\nfoo = true\n\n[mcp_servers.aiindex]\ncommand = "x"\n\n[mcp_servers.other]\ncommand = "y"\n'''
        cleaned = installer.remove_codex_owned_sections(text)
        self.assertNotIn("agents.ai-fast", cleaned)
        self.assertNotIn("mcp_servers.aiindex", cleaned)
        self.assertIn("mcp_servers.other", cleaned)

    def test_extract_codex_fragment(self):
        frag = '''model = "m"\nmodel_reasoning_effort = "low"\n\n[agents]\nenabled = true\nmax_concurrent_threads_per_session = 2\n\n[agents.ai-fast]\ndescription = "x"\n'''
        top, sections, root = installer.extract_codex_fragment(frag)
        self.assertEqual(top["model"], '"m"')
        self.assertEqual(root["enabled"], "true")
        self.assertIn("[agents.ai-fast]", sections)

    def test_managed_markdown_preserves_user_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "AGENTS.md"
            p.write_text("user content\n", encoding="utf-8")
            installer.managed_markdown(p, "framework content", False)
            text = p.read_text(encoding="utf-8")
            self.assertIn("user content", text)
            self.assertIn("framework content", text)
            installer.remove_managed_markdown(p, False)
            self.assertEqual(p.read_text(encoding="utf-8").strip(), "user content")

    def test_default_state_has_prerequisites(self):
        state = installer.default_state()
        self.assertIn("prerequisites", state)
        self.assertEqual(state["prerequisites"], {})


    def test_framework_semver_comparison(self):
        self.assertTrue(installer.newer_framework_version("0.1.0", "0.2.0"))
        self.assertFalse(installer.newer_framework_version("0.2.0", "0.2.0"))
        self.assertFalse(installer.newer_framework_version("1.0.0", "0.9.0"))

    def test_framework_version_url_from_repo(self):
        cfg = {"frameworkRepositoryUrl": "https://github.com/qbicus/skills.git", "frameworkBranch": "main"}
        self.assertEqual(
            installer.framework_version_url(cfg),
            "https://raw.githubusercontent.com/qbicus/skills/main/version.json",
        )

    def test_wire_skills_adopts_existing_canonical_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "framework"
            skill = root / "skills" / "debug"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# debug\n", encoding="utf-8")
            codex = Path(tmp) / "codex"
            link = codex / "skills" / "debug"
            link.parent.mkdir(parents=True)
            link.symlink_to(skill, target_is_directory=True)
            state = {"managedSkills": {"codex": [], "claude": []}, "links": []}
            old_root = installer.FRAMEWORK_ROOT
            try:
                installer.FRAMEWORK_ROOT = root
                with mock.patch.dict(os.environ, {"CODEX_HOME": str(codex)}):
                    installer.wire_skills("codex", state, False)
                self.assertEqual(state["managedSkills"]["codex"], ["debug"])
                self.assertIn(str(link), state["links"])
            finally:
                installer.FRAMEWORK_ROOT = old_root

    def test_wire_skills_repairs_wrong_target_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "framework"
            skill = root / "skills" / "debug"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# debug\n", encoding="utf-8")
            wrong = Path(tmp) / "wrong"
            wrong.mkdir()
            codex = Path(tmp) / "codex"
            link = codex / "skills" / "debug"
            link.parent.mkdir(parents=True)
            link.symlink_to(wrong, target_is_directory=True)
            state = {"managedSkills": {"codex": [], "claude": []}, "links": []}
            old_root = installer.FRAMEWORK_ROOT
            try:
                installer.FRAMEWORK_ROOT = root
                with mock.patch.dict(os.environ, {"CODEX_HOME": str(codex)}):
                    installer.wire_skills("codex", state, False)
                self.assertEqual(link.resolve(), skill.resolve())
            finally:
                installer.FRAMEWORK_ROOT = old_root


    def test_wire_skills_migrates_exact_legacy_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "framework"
            skill = root / "skills" / "debug"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: debug\n---\n# debug\n", encoding="utf-8")
            codex = Path(tmp) / "codex"
            legacy = codex / "skills" / "debug"
            legacy.mkdir(parents=True)
            (legacy / "SKILL.md").write_text((skill / "SKILL.md").read_text(encoding="utf-8"), encoding="utf-8")
            state = {"managedSkills": {"codex": [], "claude": []}, "links": []}
            old_root = installer.FRAMEWORK_ROOT
            try:
                installer.FRAMEWORK_ROOT = root
                with mock.patch.dict(os.environ, {"CODEX_HOME": str(codex)}):
                    installer.wire_skills("codex", state, False)
                self.assertTrue(legacy.is_symlink())
                self.assertEqual(legacy.resolve(), skill.resolve())
            finally:
                installer.FRAMEWORK_ROOT = old_root

    def test_wire_skills_refuses_modified_legacy_copy_with_clear_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "framework"
            skill = root / "skills" / "debug"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: debug\n---\n# current\n", encoding="utf-8")
            codex = Path(tmp) / "codex"
            legacy = codex / "skills" / "debug"
            legacy.mkdir(parents=True)
            (legacy / "SKILL.md").write_text("---\nname: debug\n---\n# old or edited\n", encoding="utf-8")
            state = {"managedSkills": {"codex": [], "claude": []}, "links": []}
            old_root = installer.FRAMEWORK_ROOT
            try:
                installer.FRAMEWORK_ROOT = root
                with mock.patch.dict(os.environ, {"CODEX_HOME": str(codex)}):
                    with self.assertRaisesRegex(RuntimeError, "Legacy framework skill copy detected"):
                        installer.wire_skills("codex", state, False)
            finally:
                installer.FRAMEWORK_ROOT = old_root

    def test_codex_detection_accepts_chatgpt_command(self):
        with mock.patch.object(installer, "which", side_effect=lambda name: "/usr/bin/chatgpt" if name == "chatgpt" else None), \
             mock.patch.object(installer, "command_version", return_value="chatgpt 1.2.3"):
            detected, detail = installer.client_detected("codex")
        self.assertTrue(detected)
        self.assertIn("chatgpt", detail)

    def test_aiindex_dry_run_preserves_correct_linux_shim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "framework"
            bin_dir = root / "bin"
            bin_dir.mkdir(parents=True)
            cli = bin_dir / "aiindex"
            cli.write_text("x", encoding="utf-8")
            home = Path(tmp) / "home"
            shim = home / ".local" / "bin" / "aiindex"
            shim.parent.mkdir(parents=True)
            shim.symlink_to(cli)
            old_root = installer.FRAMEWORK_ROOT
            try:
                installer.FRAMEWORK_ROOT = root
                with mock.patch.object(Path, "home", return_value=home), \
                     mock.patch("builtins.print") as print_mock:
                    installer.ensure_aiindex_cli_path({}, True)
                output = "\n".join(" ".join(str(a) for a in call.args) for call in print_mock.call_args_list)
                self.assertIn("would preserve existing AiIndex link", output)
            finally:
                installer.FRAMEWORK_ROOT = old_root

    def test_aiindex_current_version_skips_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            (bin_dir / "aiindex").write_text("x", encoding="utf-8")
            (bin_dir / "aiindex-mcp").write_text("x", encoding="utf-8")
            state = {"aiIndex": {"version": "aiindex-2026.09.22"}}
            release = {
                "tag_name": "aiindex-2026.09.22",
                "assets": [
                    {"name": "aiindex-linux-x64.tar.gz", "browser_download_url": "x"},
                    {"name": "SHA256SUMS", "browser_download_url": "y"},
                ],
            }
            old_root = installer.FRAMEWORK_ROOT
            try:
                installer.FRAMEWORK_ROOT = root
                with mock.patch.object(installer, "latest_aiindex_release", return_value=release), \
                     mock.patch.object(installer, "platform_rid", return_value=("linux-x64", "tar.gz")), \
                     mock.patch.object(installer, "download") as download_mock:
                    mcp, info = installer.install_aiindex({"aiIndexReleaseApiUrl": "x"}, state, False, False)
                self.assertEqual(info["status"], "current")
                self.assertTrue(mcp.exists())
                download_mock.assert_not_called()
            finally:
                installer.FRAMEWORK_ROOT = old_root

    def test_aiindex_can_preserve_older_healthy_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            (bin_dir / "aiindex").write_text("x", encoding="utf-8")
            (bin_dir / "aiindex-mcp").write_text("x", encoding="utf-8")
            state = {"aiIndex": {"version": "aiindex-2026.09.22", "asset": "old"}}
            release = {
                "tag_name": "aiindex-2026.10.16",
                "assets": [
                    {"name": "aiindex-linux-x64.tar.gz", "browser_download_url": "x"},
                    {"name": "SHA256SUMS", "browser_download_url": "y"},
                ],
            }
            old_root = installer.FRAMEWORK_ROOT
            try:
                installer.FRAMEWORK_ROOT = root
                with mock.patch.object(installer, "latest_aiindex_release", return_value=release), \
                     mock.patch.object(installer, "platform_rid", return_value=("linux-x64", "tar.gz")), \
                     mock.patch.object(installer, "download") as download_mock:
                    _, info = installer.install_aiindex({"aiIndexReleaseApiUrl": "x"}, state, False, False, allow_update=False)
                self.assertEqual(info["status"], "update-available")
                self.assertEqual(info["version"], "aiindex-2026.09.22")
                download_mock.assert_not_called()
            finally:
                installer.FRAMEWORK_ROOT = old_root


if __name__ == "__main__":
    unittest.main()
