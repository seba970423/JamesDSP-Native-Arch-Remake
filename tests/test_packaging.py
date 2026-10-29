import hashlib
from pathlib import Path
import re
import subprocess
import unittest


class PackagingInputs(unittest.TestCase):
    def test_local_sources_resolve_like_makepkg_and_have_valid_checksums(self):
        root = Path(__file__).parents[1]
        command = 'source "$1"; printf "%s\\0" "${source[@]}"; printf "\\1"; printf "%s\\0" "${sha256sums[@]}"'
        result = subprocess.check_output(['bash', '-c', command, 'metadata', str(root / 'PKGBUILD')])
        sources, hashes = (part.rstrip(b'\0').decode().split('\0') for part in result.split(b'\1'))
        self.assertEqual(len(sources), len(hashes))
        for source, checksum in zip(sources, hashes):
            if source.startswith('https://'):
                self.assertTrue(source.startswith('https://github.com/Audio4Linux/JDSP4Linux/releases/download/'))
                self.assertRegex(checksum, r'^[0-9a-f]{64}$')
                continue
            if 'git+https://' in source:
                self.assertRegex(source, r'#commit=[0-9a-f]{40}$')
                continue
            # makepkg resolves a local source by its basename in startdir.
            filename = source.split('::', 1)[0] if '::' in source else source.rsplit('/', 1)[-1]
            path = root / filename
            self.assertTrue(path.is_file(), source + ' is not resolvable by makepkg')
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), checksum, source)

    def test_binary_install_has_no_compilation_or_source_download(self):
        root = Path(__file__).parents[1]
        package = (root / 'PKGBUILD').read_text()
        self.assertNotIn('qmake6 ', package)
        self.assertNotIn('git+', package)
        self.assertNotIn('\nbuild()', package)
        self.assertIn('native-engines-x86_64.tar.xz', package)
        self.assertIn('jamesdsp-pipewire_', package)
        self.assertNotIn('libpulse', package)


if __name__ == '__main__':
    unittest.main()
