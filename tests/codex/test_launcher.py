"""Exercise registered shell commands, including failures before loop.py starts."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((ROOT / '.codex/hooks.json').read_text())


class Launcher(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='registered hook ')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        shutil.copytree(ROOT / '.codex/hooks', self.root / '.codex/hooks')
        shutil.copytree(ROOT / '.claude/hooks', self.root / '.claude/hooks')
        (self.root / 'nested dir').mkdir()

    def invoke(self, event, env=None, command=None, cwd=None, shell_command="git status"):
        payload = dict(hook_event_name=event, cwd=str(self.root),
                       tool_input={'cmd': shell_command})
        return subprocess.run(['/bin/sh', '-c', command or CONFIG['hooks'][event][0]['hooks'][0]['command']],
                              input=json.dumps(payload), capture_output=True, text=True,
                              cwd=cwd or self.root / 'nested dir', env=env, timeout=25)

    def fallback(self, event, **kwargs):
        result = self.invoke(event, **kwargs)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        if event == 'PreToolUse':
            self.assertEqual(value['hookSpecificOutput']['permissionDecision'], 'deny')
        else:
            self.assertEqual(set(value), {'systemMessage'})
            self.assertIn('unavailable', value['systemMessage'])
        return value

    def test_old_registered_command_reproduces_missing_entrypoint_exit_2(self):
        (self.root / '.codex/hooks/loop.py').unlink()
        result = self.invoke('Stop', command='python3 "$(git rev-parse --show-toplevel)/.codex/hooks/loop.py"')
        self.assertEqual(result.returncode, 2)
        self.assertIn("can't open file", result.stderr)

    def test_missing_entire_adapter_tree(self):
        shutil.rmtree(self.root / '.codex')
        for event in CONFIG['hooks']:
            with self.subTest(event=event):
                self.fallback(event)

    def test_missing_python(self):
        empty_path = self.root / 'empty-bin'
        empty_path.mkdir()
        for event in CONFIG['hooks']:
            self.fallback(event, env=dict(os.environ, PATH=str(empty_path)))

    def test_startup_crash_exit_2_and_invalid_output(self):
        adapter = self.root / '.codex/hooks/loop.py'
        for script in ('raise RuntimeError("broken")', 'raise SystemExit(2)',
                       'print("not json")', 'print("[]")'):
            adapter.write_text(script)
            for event in CONFIG['hooks']:
                with self.subTest(script=script, event=event):
                    self.fallback(event)

    def test_advisory_events_reject_continuation_output(self):
        (self.root / '.codex/hooks/loop.py').write_text('print(\'{"decision":"block","reason":"again"}\')')
        for event in ('Stop', 'SubagentStop', 'PreCompact'):
            self.fallback(event)

    def test_no_git_root(self):
        with tempfile.TemporaryDirectory() as outside:
            self.fallback('Stop', cwd=outside)
            self.fallback('PreToolUse', cwd=outside)

    def test_normal_advisory_and_guard(self):
        self.assertEqual(json.loads(self.invoke('Stop').stdout), {})
        self.assertEqual(json.loads(self.invoke('PreToolUse').stdout), {})
        value = json.loads(self.invoke('PreToolUse', shell_command='git stash').stdout)
        self.assertEqual(value['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertNotIn('unavailable', value['hookSpecificOutput']['permissionDecisionReason'])

    def test_fixture_branch_transition_and_preflight(self):
        git = lambda *args: subprocess.run(['git', '-C', str(self.root), *args], check=True,
                                           capture_output=True, text=True)
        git('config', 'user.name', 'Fixture')
        git('config', 'user.email', 'fixture@example.invalid')
        shutil.copy2(ROOT / '.codex/hooks.json', self.root / '.codex/hooks.json')
        git('add', '.codex', '.claude')
        git('commit', '-qm', 'complete hooks')
        complete = git('rev-parse', 'HEAD').stdout.strip()
        git('rm', '-r', '.codex')
        git('commit', '-qm', 'revision without adapter')
        missing = git('rev-parse', 'HEAD').stdout.strip()
        git('checkout', '--detach', complete)
        helper = ROOT / 'scripts/check-codex-branch.py'
        for ref, expected in ((complete, 0), (missing, 1)):
            result = subprocess.run(['python3', str(helper), ref], cwd=self.root,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, expected, result.stderr)
            self.assertEqual(git('rev-parse', 'HEAD').stdout.strip(), complete)
        git('checkout', '--detach', missing)
        self.fallback('Stop')
        self.fallback('PreToolUse')
        git('checkout', '--detach', complete)
        self.assertEqual(json.loads(self.invoke('Stop').stdout), {})


if __name__ == '__main__':
    unittest.main()
