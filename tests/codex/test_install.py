import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("installer", ROOT / "scripts/install-codex.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class Install(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="loop install ")
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def snapshot(self):
        return {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob("*")
                if path.is_file() and ".git" not in path.relative_to(self.root).parts}

    def test_install_and_reinstall_preserve_state(self):
        for name in ("PROFILE.md", "LESSONS.md", "STATE.md", "PLAN.md", "HANDOFF.md", "AUDIT.log", "tasks/T-001.md"):
            self.write("loop/" + name, "earned state: " + name)
        self.write(".codex/config.toml", 'model = "existing-model"\n')
        installer.install(self.root)
        first = self.snapshot()
        installer.install(self.root)
        self.assertEqual(self.snapshot(), first)
        self.assertEqual((self.root / "loop/LESSONS.md").read_text(), "earned state: LESSONS.md")
        self.assertEqual((self.root / ".codex/config.toml").read_text(), 'model = "existing-model"\n')

    def test_customization_collision_writes_nothing(self):
        self.write(".agents/skills/retro/SKILL.md", "project-specific retro")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Conflicting file"):
            installer.install(self.root)
        self.assertEqual(self.snapshot(), before)

    def test_merge_existing_hooks_and_keep_backup(self):
        original = {"description": "mine", "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo my-hook"}]}]}}
        self.write(".codex/hooks.json", json.dumps(original))
        installer.install(self.root)
        merged = json.loads((self.root / ".codex/hooks.json").read_text())
        self.assertEqual(merged["description"], "mine")
        self.assertIn(original["hooks"]["Stop"][0], merged["hooks"]["Stop"])
        self.assertEqual(len(merged["hooks"]["Stop"]), 2)
        self.assertEqual(json.loads((self.root / ".codex/hooks.json.before-loop").read_text()), original)

    def test_conflicting_hook_writes_nothing(self):
        self.write(".codex/hooks.json", json.dumps({"hooks": {"Stop": [{"hooks": [{"command": "custom .codex/hooks/loop.py"}]}]}}))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Conflicting existing loop hook"):
            installer.install(self.root)
        self.assertEqual(self.snapshot(), before)

    def test_symlink_parent_rejected(self):
        (self.root / "outside").mkdir()
        (self.root / ".codex").symlink_to(self.root / "outside", target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            installer.install(self.root)
        self.assertEqual(list((self.root / "outside").iterdir()), [])

    def test_dry_run_writes_nothing(self):
        installer.install(self.root, dry_run=True)
        self.assertEqual(self.snapshot(), {})

    def test_dangling_backup_symlink_rejected_before_writes(self):
        self.write(".codex/hooks.json", '{"hooks": {}}')
        backup = self.root / ".codex/hooks.json.before-loop"
        backup.symlink_to(self.root / "unrelated")
        with self.assertRaisesRegex(ValueError, "symlink"):
            installer.install(self.root)
        self.assertFalse((self.root / "unrelated").exists())
        self.assertFalse((self.root / ".claude").exists())


if __name__ == "__main__":
    unittest.main()
