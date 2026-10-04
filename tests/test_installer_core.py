from __future__ import annotations

import importlib.util
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
