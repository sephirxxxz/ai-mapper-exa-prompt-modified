from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class HarnessContractTests(unittest.TestCase):
    def test_codex_and_claude_contracts_require_context_mode_and_one_fixed_plan(self) -> None:
        for path in (ROOT / "SKILL.md", ROOT / ".claude" / "agents" / "ai-mapper.md"):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn("ctx_doctor", text)
                self.assertIn("40", text)
                self.assertIn("ctx_purge(confirm:true, scope:\"project\")", text)
                self.assertNotIn("Elsewhere", text)
                self.assertNotIn("Obsidian", text)

    def test_codex_metadata_names_the_agent_and_stays_implicitly_discoverable(self) -> None:
        text = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn('display_name: "AI Mapper Agent"', text)
        self.assertIn('allow_implicit_invocation: true', text)
        self.assertIn("$ai-mapper-agent", text)

    def test_claude_slash_command_uses_the_shared_cli_contract(self) -> None:
        text = (ROOT / ".claude" / "commands" / "ai-mapper.md").read_text(encoding="utf-8")
        self.assertIn("$ARGUMENTS", text)
        self.assertIn("ai-mapper-agent", text)
        self.assertIn("Context Mode", text)

    def test_rating_rubric_is_present_and_contains_no_removed_integrations(self) -> None:
        rubric = ROOT / "references" / "rating-rubric.md"
        self.assertTrue(rubric.is_file())
        text = rubric.read_text(encoding="utf-8")
        for rating in ("`A`", "`B`", "`C`", "`暂不跟进`"):
            self.assertIn(rating, text)
        self.assertNotIn("Elsewhere", text)
        self.assertNotIn("Obsidian", text)


if __name__ == "__main__":
    unittest.main()
