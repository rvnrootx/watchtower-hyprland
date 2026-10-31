import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "core/config-manager/config.py"


class ConfigManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name) / "watchtower-config"
        self.env = os.environ.copy()
        self.env["WATCHTOWER_CONFIG_DIR"] = str(self.config_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_cli(self, *args, expected=0):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            expected,
            msg=f"stdout:\\n{result.stdout}\\nstderr:\\n{result.stderr}",
        )
        return result

    def test_defaults_are_valid_without_creating_user_config(self):
        result = self.run_cli("validate")
        self.assertIn("configuration is valid", result.stdout)
        self.assertFalse(self.config_dir.exists())

    def test_get_default_value(self):
        result = self.run_cli("get", "appearance.character")
        self.assertEqual(result.stdout.strip(), "nightwing")

    def test_set_creates_partial_user_override(self):
        self.run_cli("set", "appearance.character", "batman")
        result = self.run_cli("get", "appearance.character")
        self.assertEqual(result.stdout.strip(), "batman")

    def test_local_override_has_highest_precedence(self):
        self.run_cli("set", "appearance.character", "batman")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "config.local.yaml").write_text(
            "appearance:\n  character: flash\n",
            encoding="utf-8",
        )
        result = self.run_cli("get", "appearance.character")
        self.assertEqual(result.stdout.strip(), "flash")

    def test_invalid_value_is_rejected(self):
        result = self.run_cli(
            "set", "appearance.character", "green-lantern", expected=1
        )
        self.assertIn("validation failed", result.stderr.lower())

    def test_unknown_key_is_rejected(self):
        result = self.run_cli("get", "appearance.unknown", expected=1)
        self.assertIn("unknown configuration key", result.stderr.lower())

    def test_init_and_reset(self):
        self.run_cli("init")
        self.assertTrue((self.config_dir / "config.yaml").exists())
        self.run_cli("reset")
        self.assertFalse((self.config_dir / "config.yaml").exists())

    def test_unknown_keys_in_yaml_are_rejected(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "config.yaml").write_text(
            "unexpected_setting: true\n",
            encoding="utf-8",
        )
        result = self.run_cli("validate", expected=1)
        self.assertIn("additional properties", result.stderr.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
