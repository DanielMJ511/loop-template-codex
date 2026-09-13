#!/usr/bin/env python3
"""Read-only preflight before changing the active session's branch."""
import argparse
import subprocess
import sys

REQUIRED = ('.codex/hooks.json', '.codex/hooks/loop.py',
            '.claude/hooks/guard-git-destructive.sh', '.claude/hooks/audit-subagent.sh',
            '.claude/hooks/loop-guard.sh', '.claude/hooks/precompact-checkpoint.sh')


def check(target):
    revision = subprocess.run(['git', 'rev-parse', '--verify', '--end-of-options', target + '^{commit}'],
                              capture_output=True, text=True, check=True).stdout.strip()
    missing = [path for path in REQUIRED if subprocess.run(
        ['git', 'cat-file', '-t', revision + ':' + path], capture_output=True,
        text=True).stdout.strip() != 'blob']
    if missing:
        raise ValueError('Destination lacks hook files: ' + ', '.join(missing) +
                         '. Use a separate worktree; do not switch this active checkout.')
    print('Required hook files exist at ' + revision + '. Review hook changes before switching.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target')
    args = parser.parse_args()
    try:
        check(args.target)
    except (ValueError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
