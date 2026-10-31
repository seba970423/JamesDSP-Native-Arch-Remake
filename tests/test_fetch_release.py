"""No-network tests for release selection and checksum handling."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from fetch_release import version_tuple, release_asset, package_asset_name, expected_hash


class ReleaseTests(unittest.TestCase):
    def test_versions(self):
        self.assertEqual(version_tuple("v0.2.3"), (0, 2, 3))
        self.assertEqual(version_tuple("0.10.1"), (0, 10, 1))
        with self.assertRaises(ValueError):
            version_tuple("v0.2.3-rc1")

    def test_package_names(self):
        self.assertEqual(package_asset_name("v0.2.3", "rt"),
                         "jamesdsp-native-arch-0.2.3-rt-x86_64.pkg.tar.zst")
        with self.assertRaises(ValueError):
            package_asset_name("v0.2.3", "debug")

    def test_checksums(self):
        name = package_asset_name("v0.2.3", "standard")
        line = "a" * 64 + "  " + name
        self.assertEqual(expected_hash(line, name), "a" * 64)
        with self.assertRaises(ValueError):
            expected_hash(line + "\n" + line, name)
        with self.assertRaises(ValueError):
            expected_hash("a" * 64 + "  different-name", name)

    def test_asset_urls(self):
        name = package_asset_name("v0.2.3", "rt")
        url = "https://github.com/seba970423/JamesDSP-Native-Arch-Remake/releases/download/v0.2.3/" + name
        release = {"tag_name": "v0.2.3", "assets": [{"name": name, "browser_download_url": url}]}
        self.assertEqual(release_asset(release, name), url)
        release["assets"].append({"name": name, "browser_download_url": url})
        with self.assertRaises(ValueError):
            release_asset(release, name)
        release["assets"] = [{"name": name, "browser_download_url": "https://example.com/bad"}]
        with self.assertRaises(ValueError):
            release_asset(release, name)


if __name__ == "__main__":
    unittest.main()
