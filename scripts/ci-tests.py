#!/usr/bin/env python3
"""Require real tests and both shell implementations in CI."""
import argparse
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def python_tests():
    suite = unittest.TestSuite(unittest.TestLoader().discover(str(ROOT / path))
                               for path in ('tests/codex', 'tests/governance'))
    if suite.countTestCases() == 0:
        raise RuntimeError('No tests discovered')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return result.wasSuccessful() and not result.skipped


def twins():
    for runner, fixture in (('run-guard-tests.sh', 'guard-git-destructive.cases'),
                            ('run-audit-tests.sh', 'audit-subagent.cases')):
        expected = sum(bool(line.strip()) and not line.startswith('#') for line in (ROOT / 'tests' / fixture).read_text().splitlines())
        result = subprocess.run(['sh', 'tests/' + runner], cwd=ROOT, capture_output=True, text=True, timeout=600)
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        lines = [line for line in result.stdout.splitlines() if re.search(r'\bps1=', line)]
        if result.returncode or expected == 0 or len(lines) != expected or any(re.search(r'\bps1=-\s', line) for line in lines):
            raise RuntimeError(runner + ': failed, empty, or a twin did not run')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('suite', choices=('python', 'twins'))
    args = parser.parse_args()
    try:
        sys.exit(0 if (python_tests() if args.suite == 'python' else twins()) else 1)
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
