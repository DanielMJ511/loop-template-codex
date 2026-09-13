import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / '.claude/skills/loop-governance/scripts/governance.py'
spec = importlib.util.spec_from_file_location('governance', SCRIPT)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


class Governance(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        subprocess.run(['git', '-C', str(self.root), 'remote', 'add', 'origin', 'https://github.com/owner/project.git'], check=True)
        (self.root / 'loop').mkdir()
        for name in ('PROFILE.md', 'CONTRIBUTING.md', 'RELEASES.md', 'PR.md'):
            (self.root / name).write_text('Measured project policy\n')
        (self.root / 'loop/PROFILE.md').write_text('Measured profile\n')
        self.record = {'version': 1, 'identity': g.identity(self.root, 'origin'),
                       'policy': {'review': 'solo', 'default_branch': 'main', 'required_checks': ['CI']},
                       'controls': {name: {'status': 'verified', 'paths': [], 'evidence': 'Reviewed actual policy'} for name in g.CONTROLS}}
        self.record['controls']['contributions']['paths'] = ['CONTRIBUTING.md', 'PR.md']
        self.record['controls']['release']['paths'] = ['RELEASES.md']
        self.protection = dict(enforce_admins={'enabled': True}, required_pull_request_reviews={'required_approving_review_count': 0},
                               required_status_checks={'strict': True, 'contexts': ['CI']},
                               required_conversation_resolution={'enabled': True})
        self.responses = {'': {'default_branch': 'main'}, 'branches/main': {'protected': True, 'commit': {'sha': 'abc'}},
                          'branches/main/protection': self.protection, 'rules/branches/main': [],
                          'commits/abc/check-runs?per_page=100': {'check_runs': [dict(id=1, name='CI', app={'slug': 'github-actions'}, status='completed', conclusion='success')]}}
        self.save()

    def save(self):
        self.record['assessed_at'] = datetime.now(timezone.utc).isoformat()
        self.record['fingerprints'] = g.fingerprints(self.root, self.record)
        self.record['policy_digest'] = g.policy_digest(self.record)
        (self.root / g.RECORD).write_text(json.dumps(self.record))

    def check(self, **kwargs):
        return g.check(self.root, api=lambda endpoint: self.responses[endpoint], **kwargs)

    def test_verified_solo_passes(self):
        self.assertEqual(self.check(), [])

    def test_team_requires_independent_approval(self):
        self.record['policy']['review'] = 'team'
        self.save()
        self.assertTrue(self.check())
        self.protection['required_pull_request_reviews']['required_approving_review_count'] = 1
        self.assertEqual(self.check(), [])

    def test_protection_drift(self):
        for key in ('enforce_admins', 'required_pull_request_reviews', 'required_status_checks', 'required_conversation_resolution'):
            before = copy.deepcopy(self.protection)
            self.protection.pop(key)
            self.assertTrue(self.check(), key)
            self.protection.update(before)

    def test_ci_skipped_empty_wrong_source_and_failure_block(self):
        checks = self.responses['commits/abc/check-runs?per_page=100']['check_runs']
        for conclusion in ('skipped', 'neutral', 'failure', None):
            checks[0]['conclusion'] = conclusion
            self.assertTrue(self.check())
        checks[0]['conclusion'] = 'success'
        checks[0]['app']['slug'] = 'other'
        self.assertTrue(self.check())
        checks.clear()
        self.assertTrue(self.check())

    def test_latest_rerun_must_pass(self):
        checks = self.responses['commits/abc/check-runs?per_page=100']['check_runs']
        checks.append(dict(checks[0], id=2, conclusion='failure'))
        self.assertTrue(self.check())

    def test_network_failure_is_unverifiable(self):
        def fail(endpoint):
            raise OSError('network unavailable')
        self.assertTrue(g.check(self.root, api=fail))

    def test_wrong_identity_blocks(self):
        self.record['identity']['repo'] = 'someone/else'
        self.save()
        self.assertTrue(self.check())

    def test_changed_policy_file_and_workflow_invalidate(self):
        (self.root / 'CONTRIBUTING.md').write_text('changed')
        self.assertTrue(self.check())
        self.save()
        (self.root / '.github/workflows').mkdir(parents=True)
        (self.root / '.github/workflows/ci.yml').write_text('new workflow')
        self.assertTrue(self.check())

    def test_seal_never_promotes_gap(self):
        self.record['controls']['ci']['status'] = 'gap'
        self.save()
        self.assertTrue(self.check())

    def test_missing_corrupt_and_unknown_records_cli_fail(self):
        for text in ('{', '[]', '{"version":99}'):
            (self.root / g.RECORD).write_text(text)
            result = subprocess.run(['python3', str(SCRIPT), 'check', '--root', str(self.root)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)['ready'])
        (self.root / g.RECORD).unlink()
        result = subprocess.run(['python3', str(SCRIPT), 'check', '--root', str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)

    def test_local_project_needs_bound_approved_exceptions(self):
        self.record['identity'] = g.identity(self.root, None)
        self.save()
        self.assertTrue(self.check())
        for name in ('ci', 'protection'):
            self.record['controls'][name].update(status='excepted', exception={'reason': 'local-only fixture', 'kind': 'local-only',
                'approved_by': 'fixture user', 'approval_reference': 'fixture-message-1', 'scope': 'configuration',
                'configuration': g.binding(self.root, self.record)})
        self.save()
        self.assertEqual(self.check(), [])
        (self.root / 'RELEASES.md').write_text('changed')
        self.save()
        self.assertTrue(self.check(), 'resealing must not renew approval')

    def test_offline_exception_is_unit_bounded(self):
        for name in ('ci', 'protection'):
            self.record['controls'][name].update(status='excepted', exception={'reason': 'offline', 'kind': 'offline',
                'approved_by': 'fixture user', 'approval_reference': 'fixture-message-2', 'scope': 'unit', 'unit': 'U-1',
                'configuration': g.binding(self.root, self.record)})
        self.save()
        self.assertEqual(self.check(unit='U-1'), [])
        self.assertTrue(self.check(unit='U-2'))
        self.assertTrue(self.check())

    def test_exception_without_approval_fails(self):
        self.record['controls']['ci'].update(status='excepted', exception={'scope': 'configuration'})
        self.save()
        self.assertTrue(self.check())

    def test_empty_policy_file_blocks(self):
        (self.root / 'RELEASES.md').write_text('')
        self.save()
        self.assertTrue(self.check())

    def test_publish_uses_head_checks(self):
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '--allow-empty', '-qm', 'fixture'], check=True)
        head = g.git(self.root, 'rev-parse', 'HEAD')
        self.responses['commits/' + head + '/check-runs?per_page=100'] = {'check_runs': []}
        self.assertTrue(self.check(phase='publish'))
        self.responses['commits/' + head + '/check-runs?per_page=100'] = self.responses['commits/abc/check-runs?per_page=100']
        self.assertEqual(self.check(phase='publish'), [])

    def test_classic_protection_absent_is_not_api_outage(self):
        with patch.object(g, 'run', side_effect=subprocess.CalledProcessError(1, ['gh'], stderr='Not Found (HTTP 404)')):
            self.assertEqual(g.fetch(self.root, 'owner/project', 'branches/main/protection', 'gh'), {})
        for message in ('Forbidden (HTTP 403)', 'network unavailable'):
            with patch.object(g, 'run', side_effect=subprocess.CalledProcessError(1, ['gh'], stderr=message)):
                with self.assertRaises(subprocess.CalledProcessError):
                    g.fetch(self.root, 'owner/project', 'branches/main/protection', 'gh')

    def test_ruleset_only_protection(self):
        self.responses['branches/main/protection'] = {}
        self.responses['rules/branches/main'] = [
            {'type': 'pull_request', 'parameters': {'required_approving_review_count': 0, 'required_review_thread_resolution': True}},
            {'type': 'required_status_checks', 'parameters': {'strict_required_status_checks_policy': True, 'required_status_checks': [{'context': 'CI'}]}},
            {'type': 'non_fast_forward'}, {'type': 'deletion'}]
        self.assertEqual(self.check(), [])

    def test_init_preserves_existing_record(self):
        before = (self.root / g.RECORD).read_bytes()
        result = subprocess.run(['python3', str(SCRIPT), 'init', '--root', str(self.root)], capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual((self.root / g.RECORD).read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
