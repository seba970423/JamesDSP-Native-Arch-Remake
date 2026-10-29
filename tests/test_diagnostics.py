import importlib.util
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("diagnostics", Path(__file__).parents[1] / "scripts/diagnostics.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SchedulingReport(unittest.TestCase):
    def test_rtkit_reset_on_fork_does_not_hide_realtime_policy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = root / "100/task/101"
            task.mkdir(parents=True)
            (root / "100/comm").write_text("jamesdsp\n")
            (task / "comm").write_text("data-loop.0\n")
            policy = os.SCHED_RR | getattr(os, "SCHED_RESET_ON_FORK", 0x40000000)
            with patch.object(os, "sched_getscheduler", return_value=policy), \
                 patch.object(os, "sched_getparam", return_value=SimpleNamespace(sched_priority=20)):
                threads, available = module.collect_threads(root)
            self.assertTrue(available)
            self.assertEqual(threads[0]["policy"], "RR")
            self.assertTrue(threads[0]["realtime"])
            self.assertTrue(threads[0]["reset_on_fork"])

    def test_unavailable_proc_does_not_claim_normal_scheduling(self):
        threads, available = module.collect_threads(Path("/nonexistent-jdsp-test-proc"))
        self.assertEqual(threads, [])
        self.assertFalse(available)


if __name__ == "__main__":
    unittest.main()
