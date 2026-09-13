#!/usr/bin/env python3
"""Required loop governance gate. Read-only checks; explicit init/seal subcommands."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import quote

VERSION = 1
CONTROLS = ('ci', 'protection', 'contributions', 'release')
RECORD = 'loop/GOVERNANCE.json'


def run(argv, cwd):
    return subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=True, timeout=60).stdout.strip()


def git(root, *args):
    return run(['git', *args], root)


def identity(root, remote):
    if remote:
        url = git(root, 'remote', 'get-url', remote)
        match = re.fullmatch(r'(?:https://github.com/|git@github.com:)([^/]+/[^/]+?)(?:\.git)?/?', url)
        if not match:
            return {'host': 'unsupported', 'remote': remote, 'url_hash': hashlib.sha256(url.encode()).hexdigest()}
        return {'host': 'github', 'remote': remote, 'repo': match.group(1).lower()}
    return {'host': 'local', 'git_dir': str(Path(git(root, 'rev-parse', '--path-format=absolute', '--git-common-dir')).resolve())}


def safe_file(root, name):
    path = root / name
    if Path(name).is_absolute() or '..' in Path(name).parts or path.is_symlink():
        raise ValueError('Unsafe evidence path: ' + name)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Evidence escapes project: ' + name)
    return path


def fingerprints(root, record):
    names = {'loop/PROFILE.md'}
    for control in record['controls'].values():
        names.update(control.get('paths', []))
    names.update(str(p.relative_to(root)) for p in (root / '.github/workflows').glob('*') if p.is_file())
    return {name: hashlib.sha256(safe_file(root, name).read_bytes()).hexdigest()
            if safe_file(root, name).is_file() else None for name in sorted(names)}


def policy_digest(record):
    value = {k: record[k] for k in ('identity', 'policy', 'controls')}
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def read(root):
    record = json.loads((root / RECORD).read_text())
    if not isinstance(record, dict) or record.get('version') != VERSION:
        raise ValueError('Missing or unsupported governance version')
    if set(record.get('controls', {})) != set(CONTROLS):
        raise ValueError('All four governance controls must be assessed')
    if record.get('policy', {}).get('review') not in ('solo', 'team'):
        raise ValueError('Review policy must be solo or team')
    for name, control in record['controls'].items():
        if control.get('status') not in ('verified', 'gap', 'unverifiable', 'excepted'):
            raise ValueError('Invalid control status: ' + name)
    return record


def fetch(root, repo, endpoint, gh):
    try:
        return json.loads(run([gh, 'api', 'repos/' + repo + '/' + endpoint], root))
    except subprocess.CalledProcessError as error:
        # A ruleset-only protected branch has no classic protection resource.
        if endpoint.endswith('/protection') and 'HTTP 404' in error.stderr:
            return {}
        raise


def protection_ok(protection, rules, policy):
    """Recognize effective classic protection plus active branch rules, never weaken it."""
    pr = protection.get('required_pull_request_reviews') or {}
    checks = protection.get('required_status_checks') or {}
    enforced = (protection.get('enforce_admins') or {}).get('enabled', False)
    approvals = pr.get('required_approving_review_count', 0) if enforced else 0
    has_pr = bool(pr) and enforced
    strict = checks.get('strict', False) and enforced
    required = set(checks.get('contexts', [])) if enforced else set()
    required.update(c['context'] for c in checks.get('checks', []) if enforced)
    no_force = bool(protection) and enforced and not (protection.get('allow_force_pushes') or {}).get('enabled', False)
    no_delete = bool(protection) and enforced and not (protection.get('allow_deletions') or {}).get('enabled', False)
    conversations = (protection.get('required_conversation_resolution') or {}).get('enabled', False) and enforced
    for rule in rules:
        kind, params = rule.get('type'), rule.get('parameters', {})
        if kind == 'pull_request':
            has_pr = True
            approvals = max(approvals, params.get('required_approving_review_count', 0))
            conversations |= params.get('required_review_thread_resolution', False)
        elif kind == 'required_status_checks':
            strict |= params.get('strict_required_status_checks_policy', False)
            required.update(c['context'] for c in params.get('required_status_checks', []))
        elif kind == 'non_fast_forward':
            no_force = True
        elif kind == 'deletion':
            no_delete = True
    return (has_pr and approvals >= (1 if policy['review'] == 'team' else 0)
            and strict and no_force and no_delete and conversations
            and set(policy['required_checks']).issubset(required))


def binding(root, record):
    value = {'identity': record['identity'], 'policy': record['policy'],
             'fingerprints': fingerprints(root, record)}
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def exception_valid(control, unit, configuration):
    approval = control.get('exception', {})
    if not all(isinstance(approval.get(k), str) and approval[k].strip()
               for k in ('reason', 'approved_by', 'approval_reference', 'scope')):
        return False
    if approval.get('configuration') != configuration:
        return False
    if approval['scope'] == 'unit':
        return bool(unit) and approval.get('unit') == unit
    return approval['scope'] == 'configuration' and approval.get('kind') != 'offline'


def check(root, phase='start', unit=None, gh='gh', api=None):
    issues = []
    record = read(root)
    if not (root / 'loop/PROFILE.md').is_file() or not (root / 'loop/PROFILE.md').read_text().strip():
        issues.append('Project profile is missing; run loop-init first')
    actual = identity(root, record['identity'].get('remote'))
    if actual != record['identity']:
        issues.append('Repository identity changed; run loop-governance')
    if record.get('fingerprints') != fingerprints(root, record) or record.get('policy_digest') != policy_digest(record):
        issues.append('Governance evidence or policy is stale; reassess and seal')
    try:
        assessed = datetime.fromisoformat(record['assessed_at'])
        if assessed.tzinfo is None or assessed > datetime.now(timezone.utc):
            raise ValueError()
    except (ValueError, KeyError, TypeError):
        issues.append('Invalid assessment timestamp')
    active = []
    for name, control in record['controls'].items():
        if control['status'] == 'excepted':
            if not exception_valid(control, unit, binding(root, record)):
                issues.append(name + ': exception lacks scoped user approval')
        elif control['status'] != 'verified':
            issues.append(name + ': ' + control['status'])
        else:
            active.append(name)
            if not control.get('evidence'):
                issues.append(name + ': missing assessment evidence')
            if name in ('contributions', 'release'):
                paths = control.get('paths', [])
                if not paths or any(not safe_file(root, p).is_file() or not safe_file(root, p).read_text().strip() for p in paths):
                    issues.append(name + ': missing nonempty policy files')
    if any(name in active for name in ('ci', 'protection')):
        if actual['host'] != 'github':
            issues.append('Hosting controls require explicit exceptions for non-GitHub projects')
        else:
            try:
                query = api or (lambda endpoint: fetch(root, actual['repo'], endpoint, gh))
                metadata = query('')
                branch = metadata['default_branch']
                if record['policy'].get('default_branch') != branch:
                    issues.append('Default branch changed')
                branch_data = query('branches/' + quote(branch, safe=''))
                if 'protection' in active:
                    protection = query('branches/' + quote(branch, safe='') + '/protection') if branch_data.get('protected') else {}
                    rules = query('rules/branches/' + quote(branch, safe=''))
                    if not protection_ok(protection, rules, record['policy']):
                        issues.append('Effective default-branch protection is insufficient')
                if 'ci' in active:
                    required = record['policy'].get('required_checks', [])
                    if not required:
                        issues.append('Required CI check names are missing')
                    sha = git(root, 'rev-parse', 'HEAD') if phase == 'publish' else branch_data['commit']['sha']
                    checks = query('commits/' + sha + '/check-runs?per_page=100')['check_runs']
                    for name in required:
                        matches = [c for c in checks if c['name'] == name and c.get('app', {}).get('slug') == 'github-actions']
                        latest = max(matches, key=lambda c: c['id']) if matches else None
                        if not latest or latest.get('status') != 'completed' or latest.get('conclusion') != 'success':
                            issues.append('Required CI check is not successful at ' + sha + ': ' + name)
            except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as error:
                issues.append('GitHub evidence unavailable: ' + str(error))
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('init', 'seal', 'binding', 'check'))
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--remote', default='origin')
    parser.add_argument('--local', action='store_true')
    parser.add_argument('--review', choices=('solo', 'team'), default='solo')
    parser.add_argument('--phase', choices=('start', 'publish'), default='start')
    parser.add_argument('--unit')
    parser.add_argument('--gh', default=shutil.which('gh') or 'gh')
    args = parser.parse_args()
    try:
        root = Path(git(args.root, 'rev-parse', '--show-toplevel')).resolve()
        target = root / RECORD
        if args.action == 'init':
            if target.exists():
                raise ValueError('Record exists; preserve it and reassess affected controls')
            target.parent.mkdir(parents=True, exist_ok=True)
            value = dict(version=VERSION, identity=identity(root, None if args.local else args.remote),
                         policy={'review': args.review, 'default_branch': 'main', 'required_checks': []},
                         controls={name: {'status': 'gap', 'paths': [], 'evidence': ''} for name in CONTROLS})
            target.write_text(json.dumps(value, indent=2) + '\n')
            print('Governance pending; assess every control with loop-governance')
        elif args.action == 'binding':
            print(binding(root, read(root)))
        elif args.action == 'seal':
            value = read(root)
            value['fingerprints'] = fingerprints(root, value)
            value['policy_digest'] = policy_digest(value)
            value['assessed_at'] = datetime.now(timezone.utc).isoformat()
            target.write_text(json.dumps(value, indent=2) + '\n')
            print('Evidence fingerprinted; readiness still requires check')
        else:
            issues = check(root, args.phase, args.unit, args.gh)
            print(json.dumps({'ready': not issues, 'issues': issues}, indent=2))
            return 1 if issues else 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        print(json.dumps({'ready': False, 'issues': [str(error)]}))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
