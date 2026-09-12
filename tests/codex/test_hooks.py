import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("loop_hook", ROOT / ".codex/hooks/loop.py")
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


class Hooks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="loop hooks ")
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        shutil.copytree(ROOT / ".claude/hooks", self.root / ".claude/hooks")
        shutil.copytree(ROOT / ".codex/hooks", self.root / ".codex/hooks")
        (self.root / "loop/tasks").mkdir(parents=True)
        (self.root / "nested dir").mkdir()
        (self.root / "loop/PROFILE.md").write_text("Max spawns per task: 10\n")
        (self.root / "loop/PLAN.md").write_text("# Plan\n- [ ] T-001 — one\n")
        (self.root / "loop/tasks/T-001.md").write_text("# T-001 — one\nStatus: in progress — attempt 2 of 3\nRoute: full\n")

    def tearDown(self):
        self.tmp.cleanup()

    def payload(self, event, **kw):
        return dict(cwd=str(self.root / "nested dir"), hook_event_name=event,
                    session_id="main", transcript_path="/tmp/main.jsonl", **kw)

    def activate(self):
        return hook.dispatch(self.payload("PreToolUse", tool_input={
            "cmd": f'python3 "{self.root}/.codex/hooks/loop.py" activate'}))

    def test_original_guard_cases_with_codex_cmd(self):
        for line in (ROOT / "tests/guard-git-destructive.cases").read_text().splitlines():
            if not line or line.startswith("#"):
                continue
            expected, command = line.split("|", 1)
            with self.subTest(command=command):
                result = hook.dispatch(self.payload("PreToolUse", tool_input={"cmd": command}))
                denied = result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
                self.assertEqual(denied, expected == "BLOCK")

    def test_shell_argv_and_command_shapes(self):
        for command in (["bash", "-lc", "git stash"], ["git", "stash"], "git stash"):
            with self.subTest(command=command):
                result = hook.dispatch(self.payload("PreToolUse", tool_input={"command": command}))
                self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_guard_applies_without_loop_directory(self):
        shutil.rmtree(self.root / "loop")
        result = hook.dispatch(self.payload("PreToolUse", tool_input={"cmd": "git stash"}))
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_original_audit_cases(self):
        for line in (ROOT / "tests/audit-subagent.cases").read_text().splitlines():
            if not line or line.startswith("#"):
                continue
            role, task, verdict, message = line.split("|", 3)
            if role == "-":
                role = "test-runner"  # Codex's matcher supplies the named custom-agent type.
            with self.subTest(role=role, message=message):
                log = self.root / "loop/AUDIT.log"
                log.unlink(missing_ok=True)
                hook.dispatch(self.payload("SubagentStop", agent_type=role, agent_id="0123456789",
                                           last_assistant_message=message.replace("\\n", "\n")))
                if role not in hook.ROLES:
                    self.assertFalse(log.exists())
                    continue
                columns = [part.strip() for part in log.read_text().split("|")]
                self.assertEqual(columns[1:4], [role, task, verdict])

    def test_unrelated_agent_does_not_log(self):
        hook.dispatch(self.payload("SubagentStop", agent_type="explorer", last_assistant_message="TASK: T-001"))
        self.assertFalse((self.root / "loop/AUDIT.log").exists())

    def test_null_report_is_honest_empty_verdict(self):
        hook.dispatch(self.payload("SubagentStop", agent_type="test-runner", last_assistant_message=None))
        cols = [x.strip() for x in (self.root / "loop/AUDIT.log").read_text().split("|")]
        self.assertEqual(cols[1:4], ["test-runner", "-", "-"])

    def test_parent_checkpoint_retains_counter_and_skips_blocked(self):
        (self.root / "loop/PLAN.md").write_text("- [ ] T-000 — blocked\n- [ ] T-001 — active\n")
        (self.root / "loop/tasks/T-000.md").write_text("Status: blocked after 3 attempts\n")
        self.assertEqual(self.activate(), {})
        hook.dispatch(self.payload("PreCompact"))
        text = (self.root / "loop/HANDOFF.md").read_text()
        self.assertIn("T-001", text)
        self.assertNotIn("T-000", text)
        self.assertIn("attempt 2 of 3", text)
        self.assertIn("Status: active", text)

    def test_child_cannot_overwrite_parent_handoff(self):
        self.activate()
        target = self.root / "loop/HANDOFF.md"
        target.write_text("human-reviewed checkpoint")
        payload = self.payload("PreCompact")
        payload["transcript_path"] = "/tmp/child.jsonl"
        hook.dispatch(payload)
        self.assertEqual(target.read_text(), "human-reviewed checkpoint")

    def test_inactive_session_does_not_checkpoint(self):
        hook.dispatch(self.payload("PreCompact"))
        self.assertFalse((self.root / "loop/HANDOFF.md").exists())

    def test_stop_warning_is_advisory_and_scoped(self):
        self.activate()
        (self.root / "loop/tasks/T-001.md").write_text("Status: blocked after 3 attempts\n")
        result = hook.dispatch(self.payload("Stop"))
        self.assertIn("Blocked", result["systemMessage"])
        self.assertNotIn("decision", result)
        child = self.payload("Stop")
        child["transcript_path"] = "/tmp/child.jsonl"
        self.assertEqual(hook.dispatch(child), {})

    def test_other_session_cannot_take_over(self):
        self.activate()
        other = self.payload("PreToolUse", tool_input={"cmd": f'python3 "{self.root}/.codex/hooks/loop.py" activate'})
        other["session_id"] = "other"
        self.assertEqual(hook.dispatch(other)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(hook.read_state(self.root)["session_id"], "main")

    def test_cli_rejects_missing_hook_receipt(self):
        result = subprocess.run(["python3", str(self.root / ".codex/hooks/loop.py"), "activate"],
                                cwd=self.root, capture_output=True, text=True,
                                env=dict(os.environ, CODEX_THREAD_ID="main"))
        self.assertNotEqual(result.returncode, 0)
        self.activate()
        result = subprocess.run(["python3", str(self.root / ".codex/hooks/loop.py"), "activate"],
                                cwd=self.root, capture_output=True, text=True,
                                env=dict(os.environ, CODEX_THREAD_ID="main"))
        self.assertEqual(result.returncode, 0, result.stderr)
        replay = subprocess.run(["python3", str(self.root / ".codex/hooks/loop.py"), "activate"],
                                cwd=self.root, capture_output=True, text=True,
                                env=dict(os.environ, CODEX_THREAD_ID="main"))
        self.assertNotEqual(replay.returncode, 0, "stale receipt must not pass after hooks are disabled")

    def test_deactivation_preserves_checkpoint(self):
        self.activate()
        result = hook.dispatch(self.payload("PreToolUse", tool_input={
            "cmd": f'python3 "{self.root}/.codex/hooks/loop.py" deactivate'}))
        self.assertEqual(result, {})
        hook.dispatch(self.payload("PreCompact"))
        self.assertFalse((self.root / "loop/HANDOFF.md").exists())

    def test_completed_unit_does_not_replace_handoff(self):
        self.activate()
        (self.root / "loop/PLAN.md").write_text("- [x] T-001 — done\n")
        (self.root / "loop/HANDOFF.md").write_text("Status: consumed\n")
        hook.dispatch(self.payload("PreCompact"))
        self.assertEqual((self.root / "loop/HANDOFF.md").read_text(), "Status: consumed\n")

    def test_malformed_payload_fails_closed(self):
        for data in ("{", "[]", json.dumps(self.payload("PreToolUse", tool_input={})),
                     json.dumps(self.payload("PreToolUse", tool_input={"cmd": 42}))):
            with self.subTest(data=data):
                result = subprocess.run(["python3", str(ROOT / ".codex/hooks/loop.py")], input=data,
                                        capture_output=True, text=True, check=True)
                self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_missing_script_is_visible(self):
        (self.root / ".claude/hooks/audit-subagent.sh").unlink()
        result = subprocess.run(["python3", str(ROOT / ".codex/hooks/loop.py")],
                                input=json.dumps(self.payload("SubagentStop", agent_type="builder")),
                                capture_output=True, text=True, check=True)
        self.assertIn("Loop hook failed", json.loads(result.stdout)["systemMessage"])

    def test_corrupt_session_marker_is_visible(self):
        (self.root / "loop/.codex-session.json").write_text("[]")
        result = subprocess.run(["python3", str(ROOT / ".codex/hooks/loop.py")],
                                input=json.dumps(self.payload("PreCompact")),
                                capture_output=True, text=True, check=True)
        self.assertIn("must contain an object", json.loads(result.stdout)["systemMessage"])


if __name__ == "__main__":
    unittest.main()
