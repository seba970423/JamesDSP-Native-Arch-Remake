import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).parents[1]


class DependencyBootstrap(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.bin = self.base / 'bin'
        self.bin.mkdir()
        self.trace = self.base / 'trace'
        self.state = self.base / 'installed'
        self.env = dict(os.environ, PATH=str(self.bin), JDSP_TEST_BIN=str(self.bin),
                        JDSP_TEST_TRACE=str(self.trace), JDSP_TEST_STATE=str(self.state))
        self.write_command('pacman', r'''
printf '%q ' pacman "$@" >> "$JDSP_TEST_TRACE"
printf '\n' >> "$JDSP_TEST_TRACE"
case $1 in
  -T)
    [[ ${JDSP_TEST_QUERY_ERROR:-0} != 1 ]] || exit 1
    [[ ! -f $JDSP_TEST_STATE ]] || exit 0
    printf '%s\n' base-devel python fakeroot
    exit 127
    ;;
  -S)
    [[ ${JDSP_TEST_DECLINE:-0} != 1 ]] || exit 1
    : > "$JDSP_TEST_STATE"
    for executable in python3 makepkg; do
      printf '#!/bin/bash\nexit 0\n' > "$JDSP_TEST_BIN/$executable"
      /bin/chmod +x "$JDSP_TEST_BIN/$executable"
    done
    ;;
  -U) exit 0 ;;
  *) exit 99 ;;
esac
''')
        self.write_command('sudo', r'''
printf '%q ' sudo "$@" >> "$JDSP_TEST_TRACE"
printf '\n' >> "$JDSP_TEST_TRACE"
exec "$@"
''')

    def write_command(self, name, body):
        path = self.bin / name
        path.write_text('#!/bin/bash\n' + body)
        path.chmod(0o755)

    def run_bootstrap(self, mode='install', suffix='printf "READY\\n"', env=None):
        code = ('exec 3>&1 4>&2; source "$1"; '
                'jdsp_ensure_dependencies "$2" python fakeroot python; ' + suffix)
        return subprocess.run(['/bin/bash', '-euc', code, 'bootstrap',
            str(ROOT / 'scripts/dependencies.sh'), mode], env=env or self.env,
            text=True, capture_output=True)

    def calls(self):
        return [shlex.split(line) for line in self.trace.read_text().splitlines()] if self.trace.exists() else []

    def test_missing_python_and_packaging_tools_are_offered_before_use(self):
        self.assertFalse((self.bin / 'python3').exists())
        self.assertFalse((self.bin / 'makepkg').exists())
        result = self.run_bootstrap()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('READY', result.stdout)
        self.assertTrue((self.bin / 'python3').is_file())
        self.assertTrue((self.bin / 'makepkg').is_file())
        self.assertEqual(self.calls(), [
            ['pacman', '-T', 'base-devel', 'python', 'fakeroot'],
            ['sudo', 'pacman', '-S', '--needed', 'base-devel', 'python', 'fakeroot'],
            ['pacman', '-S', '--needed', 'base-devel', 'python', 'fakeroot'],
            ['pacman', '-T', 'base-devel', 'python', 'fakeroot']])

    def test_declining_pacman_stops_before_later_steps(self):
        result = self.run_bootstrap(env=dict(self.env, JDSP_TEST_DECLINE='1'))
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('READY', result.stdout)
        self.assertIn('Installation stopped', result.stderr)
        self.assertFalse((self.bin / 'python3').exists())
        self.assertFalse(self.state.exists())

    def test_existing_dependencies_do_not_prompt_for_installation(self):
        self.state.touch()
        self.write_command('python3', 'exit 0\n')
        self.write_command('makepkg', 'exit 0\n')
        result = self.run_bootstrap()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), [['pacman', '-T', 'base-devel', 'python', 'fakeroot']])

    def test_dry_run_lists_missing_packages_without_installing(self):
        result = self.run_bootstrap('dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Nothing was installed', result.stdout)
        self.assertEqual(len(self.calls()), 1)
        self.assertFalse(self.state.exists())

    def test_query_error_does_not_trigger_installation(self):
        result = self.run_bootstrap(env=dict(self.env, JDSP_TEST_QUERY_ERROR='1'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Dependency check failed', result.stderr)
        self.assertNotIn('READY', result.stdout)
        self.assertEqual(len(self.calls()), 1)

    def test_su_fallback_preserves_paths_with_spaces(self):
        (self.bin / 'sudo').unlink()
        self.write_command('su', r'''
printf '%q ' su "$@" >> "$JDSP_TEST_TRACE"
printf '\n' >> "$JDSP_TEST_TRACE"
exec /bin/bash "$@"
''')
        package = str(self.base / 'package cache/jamesdsp.pkg.tar.zst')
        result = self.run_bootstrap(suffix='jdsp_run_pacman -U ' + shlex.quote(package))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls()[-1], ['pacman', '-U', package])
        self.assertTrue(any(call[0] == 'su' for call in self.calls()))

    def test_installer_dry_run_works_without_python_or_makepkg(self):
        (self.bin / 'pacman').unlink()
        (self.bin / 'dirname').symlink_to(shutil.which('dirname'))
        result = subprocess.run(['/bin/bash', str(ROOT / 'install.sh'), '--dry-run'],
                                env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('kernel detection would run after pacman installs Python', result.stdout)
        self.assertFalse(self.trace.exists())


if __name__ == '__main__':
    unittest.main()
