from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["bash", str(ROOT / script), *args], text=True, capture_output=True, check=False)


class InstallScriptTests(unittest.TestCase):
    def test_install_rejects_unknown_target_without_changing_configuration(self) -> None:
        result = run_script("scripts/install.sh", "--unsupported")

        self.assertEqual(result.returncode, 2)
        self.assertIn("Usage", result.stderr)

    def test_install_dry_run_requires_context_mode_but_never_edits_global_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = run_script("scripts/install.sh", "--codex", "--root", temp, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Context Mode", result.stdout)
            self.assertIn("does not modify global", result.stdout)
            self.assertFalse((Path(temp) / ".venv").exists())

    def test_uninstall_preserves_runs_without_explicit_purge(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runs = root / "runs" / "sample"
            runs.mkdir(parents=True)
            (root / ".local-harness").mkdir()
            (root / ".ai-mapper-project").write_text(str(root.resolve()) + "\n", encoding="utf-8")
            (root / "SKILL.md").write_text("agent marker\n", encoding="utf-8")

            result = run_script("scripts/uninstall.sh", "--root", temp, "--yes")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(runs.exists())
            self.assertFalse((root / ".local-harness").exists())

    def test_codex_install_creates_a_discoverable_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config_root = Path(temp)

            result = run_script("scripts/install.sh", "--codex", "--config-root", temp)

            installed = config_root / "codex" / "skills" / "ai-mapper-agent" / "SKILL.md"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(installed.is_file())

    def test_installed_launcher_runs_outside_the_repository(self) -> None:
        with tempfile.TemporaryDirectory() as config_temp, tempfile.TemporaryDirectory() as work_temp:
            config_root = Path(config_temp)
            installed = run_script("scripts/install.sh", "--both", "--config-root", config_temp)
            self.assertEqual(installed.returncode, 0, installed.stderr)

            for launcher in (
                config_root / "codex" / "bin" / "ai-mapper-agent",
                config_root / "claude" / "bin" / "ai-mapper-agent",
            ):
                with self.subTest(launcher=launcher):
                    result = subprocess.run(
                        [str(launcher), "--help"], cwd=work_temp, text=True, capture_output=True, check=False
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("execute-query", result.stdout)

    def test_claude_install_creates_agent_and_slash_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config_root = Path(temp)

            result = run_script("scripts/install.sh", "--claude", "--config-root", temp)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((config_root / "claude" / "agents" / "ai-mapper.md").is_file())
            self.assertTrue((config_root / "claude" / "commands" / "ai-mapper.md").is_file())

    def test_uninstall_rejects_an_unmarked_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "runs").mkdir()

            result = run_script(
                "scripts/uninstall.sh",
                "--root",
                temp,
                "--yes",
                "--purge-data",
                "--confirm-root",
                str(root.resolve()),
            )

            self.assertEqual(result.returncode, 2)
            self.assertTrue((root / "runs").is_dir())

    def test_uninstall_removes_only_the_managed_harness_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "agent"
            (source / ".claude" / "agents").mkdir(parents=True)
            (source / ".claude" / "commands").mkdir(parents=True)
            shutil.copy2(ROOT / "SKILL.md", source / "SKILL.md")
            shutil.copy2(ROOT / ".claude" / "agents" / "ai-mapper.md", source / ".claude" / "agents" / "ai-mapper.md")
            shutil.copy2(ROOT / ".claude" / "commands" / "ai-mapper.md", source / ".claude" / "commands" / "ai-mapper.md")
            source.joinpath(".ai-mapper-project").write_text(str(source.resolve()) + "\n", encoding="utf-8")

            installed = run_script("scripts/install.sh", "--both", "--root", str(source), "--config-root", str(base))
            self.assertEqual(installed.returncode, 0, installed.stderr)
            uninstalled = run_script(
                "scripts/uninstall.sh",
                "--both",
                "--root",
                str(source),
                "--config-root",
                str(base),
                "--yes",
            )
            self.assertEqual(uninstalled.returncode, 0, uninstalled.stderr)
            self.assertFalse((base / "codex" / "skills" / "ai-mapper-agent").exists())
            self.assertFalse((base / "codex" / "bin" / "ai-mapper-agent").exists())
            self.assertFalse((base / "claude" / "agents" / "ai-mapper.md").exists())
            self.assertFalse((base / "claude" / "bin" / "ai-mapper-agent").exists())


if __name__ == "__main__":
    unittest.main()
