import gzip
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("kernel_info", Path(__file__).parents[1] / "scripts/kernel_info.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class KernelDetection(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value if isinstance(value, bytes) else value.encode())

    def detect(self):
        return module.detect_kernel(self.root, "test-rt-bore")

    def test_rt_active(self):
        self.write("sys/kernel/realtime", "1\n")
        self.assertEqual(self.detect()["patch_profile"], "rt")

    def test_rt_from_running_config(self):
        self.write("proc/config.gz", gzip.compress(b"CONFIG_PREEMPT_RT=y\n"))
        self.assertTrue(self.detect()["preempt_rt"])

    def test_full_preempt_is_not_rt(self):
        self.write("boot/config-test-rt-bore", "CONFIG_PREEMPT=y\n# CONFIG_PREEMPT_RT is not set\n")
        self.assertEqual(self.detect()["patch_profile"], "standard")
        self.assertIn("full", self.detect()["model"])

    def test_dynamic_preempt_is_not_rt(self):
        self.write("boot/config-test-rt-bore", "CONFIG_PREEMPT_DYNAMIC=y\n")
        self.assertFalse(self.detect()["preempt_rt"])

    def test_unreadable_or_missing_is_standard(self):
        self.assertEqual(self.detect()["patch_profile"], "standard")
        self.assertIsNone(self.detect()["preempt_rt"])

    def test_kernel_name_is_not_evidence(self):
        self.assertIsNone(self.detect()["preempt_rt"])

    def test_runtime_zero_overrides_config(self):
        self.write("sys/kernel/realtime", "0")
        self.write("boot/config-test-rt-bore", "CONFIG_PREEMPT_RT=y\n")
        self.assertFalse(self.detect()["preempt_rt"])

    def test_corrupt_gzip_falls_back(self):
        self.write("proc/config.gz", b"not gzip")
        self.write("boot/config-test-rt-bore", "CONFIG_PREEMPT_RT=y\n")
        self.assertTrue(self.detect()["preempt_rt"])


if __name__ == "__main__":
    unittest.main()
