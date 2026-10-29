import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


git_progress = module('git_progress')
download = module('download')
logged = module('run_logged')


class Progress(unittest.TestCase):
    def test_git_object_transfer_shows_percentage_and_reported_speed(self):
        line = git_progress.progress_line('Receiving objects: 42% (42/100), 2.00 MiB | 1.25 MiB/s')
        self.assertIn('42%', line)
        self.assertIn('1.25 MiB/s', line)
        self.assertIn('[########------------]', line)

    def test_git_flags_survive_global_directory_option(self):
        self.assertEqual(git_progress.with_progress(['-C', '/tmp/tree', 'fetch', '-q', 'origin']),
                         ['-C', '/tmp/tree', 'fetch', '--progress', 'origin'])
        self.assertIsNone(git_progress.with_progress(['rev-parse', 'HEAD']))

    def test_submodule_progress_is_forced(self):
        result = git_progress.with_progress(['-c', 'protocol.file.allow=always', 'submodule', 'update', '--init'])
        self.assertIn('--progress', result)

    def test_fragmented_git_output_and_failure_status(self):
        with tempfile.TemporaryDirectory() as temp:
            fake = Path(temp) / 'git'
            fake.write_text('#!' + sys.executable + '\nimport os,sys\n'
                'assert "--progress" in sys.argv\n'
                'os.write(2,b"Receiving objects: 50% (5/10), 1.0 MiB | ")\n'
                'os.write(2,b"2.0 MiB/s\\rReceiving objects: 100% (10/10), 2.0 MiB | 2.0 MiB/s\\n")\n'
                'sys.exit(7)\n')
            fake.chmod(0o755)
            env = dict(os.environ, JDSP_REAL_GIT=str(fake), JDSP_PROGRESS_TTY='0')
            result = subprocess.run([sys.executable, str(ROOT/'scripts/git_progress.py'), 'clone', 'example'],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 7)
            self.assertIn('50%', result.stderr)
            self.assertIn('100%', result.stderr)
            self.assertIn('2.0 MiB/s', result.stderr)

    def test_quiet_runner_logs_noise_and_reports_heartbeats(self):
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / 'build.log'
            code = 'import time; print("compiler noise",flush=True); print("@@JDSP_STEP@@Patching|1|2",flush=True); time.sleep(.2)'
            result = subprocess.run([sys.executable, str(ROOT/'scripts/run_logged.py'), '--label', 'Packaging',
                '--log', str(log), '--interval', '.05', '--', sys.executable, '-c', code],capture_output=True,text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('compiler noise', result.stdout)
            self.assertIn('compiler noise', log.read_text())
            self.assertIn('50%', result.stdout)
            self.assertIn('still running', result.stdout)

    def test_download_percentage_speed_and_checksum(self):
        with tempfile.TemporaryDirectory() as temp:
            source, target = Path(temp)/'source', Path(temp)/'target'
            source.write_bytes(b'payload' * 10000)
            output = io.StringIO()
            expected = hashlib.sha256(source.read_bytes()).hexdigest()
            download.download(source.as_uri(), target, expected, output)
            self.assertEqual(target.read_bytes(), source.read_bytes())
            self.assertIn('100%', output.getvalue())
            self.assertIn('/s', output.getvalue())
            cached = io.StringIO()
            download.download(source.as_uri(), target, expected, cached)
            self.assertIn('cached and verified', cached.getvalue())

    def test_bad_download_does_not_replace_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            source, target = Path(temp)/'source', Path(temp)/'target'
            source.write_bytes(b'bad payload')
            target.write_bytes(b'previous version')
            with self.assertRaises(RuntimeError):
                download.download(source.as_uri(), target, '0'*64, io.StringIO())
            self.assertEqual(target.read_bytes(), b'previous version')
            self.assertFalse(Path(str(target)+'.part').exists())

    def test_stage_progress_uses_completed_steps(self):
        self.assertIn('75%', logged.stage_line('@@JDSP_STEP@@Patching|3|4'))
        self.assertIsNone(logged.stage_line('@@JDSP_STEP@@Patching|5|4'))


if __name__ == '__main__':
    unittest.main()
