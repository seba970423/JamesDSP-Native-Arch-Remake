import io
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).parents[1]


class LogLocation(unittest.TestCase):
    def test_visible_home_logs_and_existing_log_migration(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / 'home with spaces'
            old = Path(temp) / 'custom state/jamesdsp-native-arch/logs'
            old.mkdir(parents=True)
            (old / 'old-install.log').write_text('previous failure')
            (old / 'same.log').write_text('old copy')
            visible = home / 'jamesdsp-native-arch-logs'
            visible.mkdir(parents=True)
            (visible / 'same.log').write_text('keep this version')
            result = subprocess.run(['bash', '-euc',
                'source "$1"; jdsp_setup_logs; printf "%s\\n" "$JDSP_LOG_DIR"',
                'logs', str(ROOT / 'scripts/logs.sh')],
                env=dict(os.environ, HOME=str(home), XDG_STATE_HOME=str(Path(temp) / 'custom state')),
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), str(visible))
            self.assertEqual((visible / 'old-install.log').read_text(), 'previous failure')
            self.assertEqual((visible / 'same.log').read_text(), 'keep this version')
            self.assertEqual((old / 'old-install.log').read_text(), 'previous failure')


@unittest.skipUnless(shutil.which('pacman'), 'Requires pacman to query real package archives')
class PackageDiscovery(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.commands = self.base / 'bin'
        self.commands.mkdir()
        (self.base / 'db').mkdir()
        config = self.base / 'pacman.conf'
        config.write_text('[options]\nArchitecture = auto\n')
        real_pacman = shutil.which('pacman')
        self.write_command('pacman', 'exec ' + shlex.quote(real_pacman) +
            ' --config ' + shlex.quote(str(config)) +
            ' --dbpath ' + shlex.quote(str(self.base / 'db')) + ' "$@"\n')

    def write_command(self, name, code):
        path = self.commands / name
        path.write_text('#!/bin/bash\n' + code)
        path.chmod(0o755)

    def package(self, name):
        directory = self.base / 'package cache with spaces'
        directory.mkdir(exist_ok=True)
        path = directory / (name + '-0.2.0-2-x86_64.pkg.tar.gz')
        metadata = ('pkgname = ' + name + '\npkgver = 0.2.0-2\n'
                    'pkgdesc = Regression fixture\narch = x86_64\n'
                    'builddate = 1793270000\nsize = 0\nlicense = GPL\n').encode()
        with tarfile.open(path, 'w:gz') as archive:
            info = tarfile.TarInfo('.PKGINFO')
            info.size = len(metadata)
            archive.addfile(info, io.BytesIO(metadata))
        return path

    def discover(self):
        return subprocess.run(['bash', '-euc', 'source "$1"; jdsp_find_package',
            'package', str(ROOT / 'scripts/package.sh')],
            env=dict(os.environ, PATH=str(self.commands) + os.pathsep + os.environ['PATH']),
            capture_output=True, text=True)

    def test_selects_main_archive_after_debug_package_using_real_pacman(self):
        debug = self.package('jamesdsp-native-arch-debug')
        main = self.package('jamesdsp-native-arch')
        self.write_command('makepkg', 'cat <<\'PACKAGES\'\n' + str(debug) + '\n' + str(main) + '\nPACKAGES\n')
        result = self.discover()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(main))

    def test_corrupt_archive_stops_before_installation(self):
        corrupt = self.base / 'corrupt.pkg.tar.gz'
        corrupt.write_text('not a package')
        self.write_command('makepkg', 'printf "%s\\n" ' + shlex.quote(str(corrupt)) + '\n')
        result = self.discover()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Could not inspect prepared package', result.stderr)
        self.assertEqual(result.stdout, '')

    def test_package_list_failure_does_not_return_a_candidate(self):
        self.write_command('makepkg', 'exit 23\n')
        result = self.discover()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Could not list', result.stderr)
        self.assertEqual(result.stdout, '')

    def test_dependency_dry_run_queries_real_pacman(self):
        result = subprocess.run(['bash', '-euc',
            'source "$1"; jdsp_ensure_dependencies dry-run python fakeroot',
            'dependencies', str(ROOT / 'scripts/dependencies.sh')],
            env=dict(os.environ, PATH=str(self.commands) + os.pathsep + os.environ['PATH']),
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('base-devel', result.stdout)
        self.assertIn('python', result.stdout)
        self.assertIn('Nothing was installed', result.stdout)


if __name__ == '__main__':
    unittest.main()
