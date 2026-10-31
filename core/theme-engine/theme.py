#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import tempfile

from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]

THEMES_DIR = Path(
    os.environ.get("WATCHTOWER_THEMES_DIR", ROOT / "themes")
).expanduser()

ACTIVE_FILE = Path(
    os.environ.get(
        "WATCHTOWER_ACTIVE_THEME_FILE",
        Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
        / "watchtower"
        / "active-theme",
    )
).expanduser()

SCHEMA_FILE = Path(__file__).parent / "schema" / "theme.schema.json"

THEME_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")


class ThemeError(Exception):
    pass


class ThemeEngine:

    def __init__(
        self,
        themes_dir: Path = THEMES_DIR,
        active_file: Path = ACTIVE_FILE,
    ):
        self.themes_dir = Path(themes_dir)
        self.active_file = Path(active_file)
        self.runtime_file = self.active_file.with_name("active-theme.json")

        try:
            self.schema = json.loads(SCHEMA_FILE.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise ThemeError(f"Cannot load theme schema: {exc}") from exc

        self.validator = Draft202012Validator(self.schema)

    def theme_path(self, theme_id: str) -> Path:
        if not THEME_ID_PATTERN.fullmatch(theme_id):
            raise ThemeError(f"Invalid theme identifier: {theme_id}")

        path = self.themes_dir / theme_id / "theme.yaml"

        if not path.is_file():
            raise ThemeError(f"Theme not found: {theme_id}")

        return path

    def load(self, theme_id: str) -> dict[str, Any]:
        path = self.theme_path(theme_id)

        try:
            with path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            raise ThemeError(f"Invalid YAML in {theme_id}: {exc}") from exc
        except OSError as exc:
            raise ThemeError(f"Cannot read {theme_id}: {exc}") from exc

        if not isinstance(data, dict):
            raise ThemeError(f"{theme_id}: theme manifest must be a YAML object")

        errors = sorted(
            self.validator.iter_errors(data),
            key=lambda error: list(error.absolute_path),
        )

        if errors:
            details = []
            for error in errors:
                location = ".".join(str(part) for part in error.absolute_path)
                details.append(f"{location or 'root'}: {error.message}")

            raise ThemeError(
                f"Theme '{theme_id}' failed validation:\n  - "
                + "\n  - ".join(details)
            )

        if data["id"] != theme_id:
            raise ThemeError(
                f"Theme directory '{theme_id}' does not match manifest ID "
                f"'{data['id']}'"
            )

        return data

    def discover(self) -> list[dict[str, Any]]:
        results = []

        if not self.themes_dir.is_dir():
            raise ThemeError(f"Themes directory does not exist: {self.themes_dir}")

        for directory in sorted(self.themes_dir.iterdir()):
            if not directory.is_dir() or directory.is_symlink():
                continue

            if not THEME_ID_PATTERN.fullmatch(directory.name):
                continue

            manifest = directory / "theme.yaml"

            if not manifest.is_file():
                continue

            try:
                theme = self.load(directory.name)
                results.append({
                    "id": directory.name,
                    "name": theme["name"],
                    "valid": True,
                    "error": None,
                })
            except ThemeError as exc:
                results.append({
                    "id": directory.name,
                    "name": directory.name,
                    "valid": False,
                    "error": str(exc),
                })

        return results

    def current(self) -> str | None:
        if not self.active_file.exists():
            return None

        try:
            value = self.active_file.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise ThemeError(f"Cannot read active theme state: {exc}") from exc

        if not value:
            return None

        if not THEME_ID_PATTERN.fullmatch(value):
            raise ThemeError("Active theme state contains an invalid identifier")

        return value

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None

        try:
            fd, temp_name = tempfile.mkstemp(
                prefix=f".{path.name}.",
                dir=path.parent,
                text=True,
            )
            temp_path = Path(temp_name)
            os.fchmod(fd, stat.S_IRUSR | stat.S_IWUSR)

            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())

            os.replace(temp_path, path)
            temp_path = None

            dir_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)

        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def export_active(self) -> dict[str, Any]:
        active = self.current()
        theme = self.load(active) if active else None

        document = {
            "schema_version": 1,
            "active_theme": active,
            "theme": theme,
        }

        self._atomic_write(
            self.runtime_file,
            json.dumps(document, indent=2) + chr(10),
        )

        return document

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None

        try:
            fd, temp_name = tempfile.mkstemp(
                prefix=f".{path.name}.",
                dir=path.parent,
                text=True,
            )
            temp_path = Path(temp_name)
            os.fchmod(fd, stat.S_IRUSR | stat.S_IWUSR)

            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())

            os.replace(temp_path, path)
            temp_path = None

            dir_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)

        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def export_active(self) -> dict[str, Any]:
        active = self.current()
        theme = self.load(active) if active else None

        document = {
            "schema_version": 1,
            "active_theme": active,
            "theme": theme,
        }

        self._atomic_write(
            self.runtime_file,
            json.dumps(document, indent=2) + chr(10),
        )

        return document

    def apply(self, theme_id: str) -> None:
        # Validate before modifying either state file.
        theme = self.load(theme_id)

        old_state = (
            self.active_file.read_bytes()
            if self.active_file.exists()
            else None
        )
        old_runtime = (
            self.runtime_file.read_bytes()
            if self.runtime_file.exists()
            else None
        )

        document = {
            "schema_version": 1,
            "active_theme": theme_id,
            "theme": theme,
        }

        try:
            self._atomic_write(self.active_file, theme_id + chr(10))
            self._atomic_write(
                self.runtime_file,
            json.dumps(document, indent=2) + chr(10),
            )

        except (OSError, UnicodeError) as exc:
            # Restore the previous state if either write fails.
            try:
                if old_state is None:
                    self.active_file.unlink(missing_ok=True)
                else:
                    self._atomic_write(
                        self.active_file,
                        old_state.decode("utf-8"),
                    )

                if old_runtime is None:
                    self.runtime_file.unlink(missing_ok=True)
                else:
                    self._atomic_write(
                        self.runtime_file,
                        old_runtime.decode("utf-8"),
                    )

            except (OSError, UnicodeError) as rollback_error:
                raise ThemeError(
                    f"Activation failed: {exc}. "
                    f"Rollback failed: {rollback_error}"
                ) from rollback_error

            raise ThemeError(f"Could not activate theme: {exc}") from exc

    def preview(self, theme_id: str) -> dict[str, Any]:
        return self.load(theme_id)


def command_list(engine: ThemeEngine) -> int:
    themes = engine.discover()
    active = engine.current()

    print("\nWatchtower Character Themes\n")

    if not themes:
        print("No theme manifests found.")
        return 0

    for theme in themes:
        if not theme["valid"]:
            print(f"  ! {theme['id']} — INVALID")
            print(f"      {theme['error'].splitlines()[0]}")
            continue

        marker = "●" if theme["id"] == active else "○"
        status = " (active)" if theme["id"] == active else ""

        print(f"  {marker} {theme['name']}{status}")

    print(f"\nTotal: {len(themes)}")
    return 0


def command_current(engine: ThemeEngine) -> int:
    active = engine.current()

    if active is None:
        print("No character theme has been activated.")
        return 0

    try:
        theme = engine.load(active)
    except ThemeError:
        print(f"Active theme: {active} (currently invalid or unavailable)")
        return 1

    print(f"Active theme: {theme['name']} ({active})")
    return 0


def command_validate(engine: ThemeEngine, theme_id: str | None) -> int:
    if theme_id:
        theme_ids = [theme_id]
    else:
        theme_ids = [
            item["id"] for item in engine.discover()
        ]

    if not theme_ids:
        print("No themes found.")
        return 1

    failures = 0

    for identifier in theme_ids:
        try:
            theme = engine.load(identifier)
            print(f"[ OK ] {theme['name']} ({identifier})")
        except ThemeError as exc:
            failures += 1
            print(f"[FAIL] {identifier}")
            print(f"       {exc}")

    print(f"\nValidated: {len(theme_ids) - failures}/{len(theme_ids)}")

    return 1 if failures else 0


def command_preview(engine: ThemeEngine, theme_id: str) -> int:
    theme = engine.preview(theme_id)

    print(f"\n{theme['name']}")
    print(f"{theme['description']}")
    print(f"Version: {theme['version']}")

    print("\nPalette")

    for key, value in theme["palette"].items():
        print(f"  {key:<14} {value}")

    print("\nTypography")
    for key, value in theme["typography"].items():
        print(f"  {key:<14} {value}")

    print("\nShape")
    for key, value in theme["shape"].items():
        print(f"  {key:<14} {value}")

    print("\nEffects")
    for key, value in theme["effects"].items():
        print(f"  {key:<14} {value}")

    print("\nAnimation")
    for key, value in theme["animation"].items():
        print(f"  {key:<14} {value}")

    print("\nPreview only — active theme was not changed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Watchtower Character Theme Engine"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List available themes")
    subparsers.add_parser("current", help="Show the active theme")

    validate = subparsers.add_parser("validate", help="Validate theme manifests")
    validate.add_argument("theme", nargs="?", help="Optional theme ID")

    preview = subparsers.add_parser("preview", help="Preview a theme")
    preview.add_argument("theme")

    apply = subparsers.add_parser("apply", help="Activate a theme")
    apply.add_argument("theme")

    subparsers.add_parser(
        "export",
        help="Export the active theme as runtime JSON",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        engine = ThemeEngine()

        if args.command == "list":
            return command_list(engine)

        if args.command == "current":
            return command_current(engine)

        if args.command == "validate":
            return command_validate(engine, args.theme)

        if args.command == "preview":
            return command_preview(engine, args.theme)

        if args.command == "apply":
            engine.apply(args.theme)
            print(f"Activated theme: {args.theme}")
            return 0

        if args.command == "export":
            document = engine.export_active()
            print(f"Exported active theme: {document['active_theme'] or 'none'}")
            print(f"Runtime file: {engine.runtime_file}")
            return 0

        return 2

    except ThemeError as exc:
        print(f"Theme Engine error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
