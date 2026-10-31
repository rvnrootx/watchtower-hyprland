import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "theme-engine"))

from theme import ThemeEngine, ThemeError


VALID_THEME = """
schema_version: 1
id: batman
name: Batman
description: Test theme
version: "1.0.0"

palette:
  background: "#090B10"
  foreground: "#FFFFFF"
  surface: "#141821"
  surface_alt: "#1D2430"
  primary: "#D6AE45"
  secondary: "#737B8C"
  accent: "#F0C75E"
  border: "#353B48"
  success: "#38C98B"
  warning: "#F5B942"
  danger: "#EF5350"

typography:
  family: Inter
  size: 10
  weight: 500

shape:
  radius: 14
  border_width: 1

effects:
  transparency: 0.88
  blur: true

animation:
  enabled: true
  duration: 220
"""


class ThemeEngineTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

        self.themes = self.root / "themes"
        self.active = self.root / "state" / "active-theme"

        self.engine = ThemeEngine(
            themes_dir=self.themes,
            active_file=self.active,
        )

        self.write_theme("batman", VALID_THEME)

    def tearDown(self):
        self.temp.cleanup()

    def write_theme(self, theme_id, content):
        directory = self.themes / theme_id
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "theme.yaml").write_text(content)

    def test_load_valid_theme(self):
        theme = self.engine.load("batman")
        self.assertEqual(theme["name"], "Batman")

    def test_discover_theme(self):
        themes = self.engine.discover()
        self.assertEqual(len(themes), 1)
        self.assertTrue(themes[0]["valid"])

    def test_preview_does_not_activate(self):
        self.engine.preview("batman")
        self.assertIsNone(self.engine.current())

    def test_apply_theme(self):
        self.engine.apply("batman")
        self.assertEqual(self.engine.current(), "batman")

    def test_invalid_theme_rejected(self):
        self.write_theme(
            "broken",
            "schema_version: 1\nid: broken\n"
        )

        with self.assertRaises(ThemeError):
            self.engine.apply("broken")

    def test_invalid_apply_preserves_previous_theme(self):
        self.engine.apply("batman")

        self.write_theme(
            "broken",
            "schema_version: 1\nid: broken\n"
        )

        with self.assertRaises(ThemeError):
            self.engine.apply("broken")

        self.assertEqual(self.engine.current(), "batman")

    def test_path_traversal_rejected(self):
        with self.assertRaises(ThemeError):
            self.engine.load("../batman")

    def test_manifest_id_must_match_directory(self):
        content = VALID_THEME.replace(
            "id: batman",
            "id: superman"
        )

        self.write_theme("batman", content)

        with self.assertRaises(ThemeError):
            self.engine.load("batman")

    def test_active_state_has_restricted_permissions(self):
        self.engine.apply("batman")

        permissions = self.active.stat().st_mode & 0o777
        self.assertEqual(permissions, 0o600)


if __name__ == "__main__":
    unittest.main()
