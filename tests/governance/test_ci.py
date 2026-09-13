import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('ci_tests', ROOT / 'scripts/ci-tests.py')
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)


class CI(unittest.TestCase):
    def test_skipped_twin_is_failure_even_on_exit_zero(self):
        result = subprocess.CompletedProcess([], 0, stdout='sh=allow ps1=- want=allow\nOK\n', stderr='')
        with patch.object(ci.subprocess, 'run', return_value=result):
            with self.assertRaises(RuntimeError):
                ci.twins()

    def test_empty_twin_suite_is_failure(self):
        with patch.object(ci.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, stdout='OK\n', stderr='')):
            with self.assertRaises(RuntimeError):
                ci.twins()

    def test_failed_twin_runner_is_failure(self):
        with patch.object(ci.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, stdout='', stderr='failed')):
            with self.assertRaises(RuntimeError):
                ci.twins()

    def test_empty_python_discovery_is_failure(self):
        with patch.object(ci.unittest.TestLoader, 'discover', return_value=unittest.TestSuite()):
            with self.assertRaises(RuntimeError):
                ci.python_tests()


if __name__ == '__main__':
    unittest.main()
