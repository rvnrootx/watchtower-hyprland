#!/usr/bin/env python3
"""Watchtower configuration manager."""

from __future__ import annotations

import argparse
import copy
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULTS_FILE = ROOT / "core/config-manager/defaults/config.yaml"
SCHEMA_FILE = ROOT / "core/config-manager/schema/config.schema.json"


def config_directory() -> Path:
    override = os.environ.get("WATCHTOWER_CONFIG_DIR")
    if override:
        return Path(override).expanduser()

    xdg_config = Path(
        os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
    ).expanduser()
    return xdg_config / "watchtower"


def read_yaml(path: Path, *, required: bool = False) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Configuration file not found: {path}")
        return {}

    try:
        with path.open("r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping at the top level: {path}")

    return data


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)

    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)

    return result


def load_schema() -> dict[str, Any]:
    import json

    with SCHEMA_FILE.open("r", encoding="utf-8") as stream:
        schema = json.load(stream)

    jsonschema.validators.validator_for(schema).check_schema(schema)
    return schema


def load_effective_config() -> dict[str, Any]:
    defaults = read_yaml(DEFAULTS_FILE, required=True)
    user_dir = config_directory()

    user_config = read_yaml(user_dir / "config.yaml")
    local_config = read_yaml(user_dir / "config.local.yaml")

    return deep_merge(deep_merge(defaults, user_config), local_config)


def validation_errors(config: dict[str, Any]) -> list[str]:
    schema = load_schema()
    validator = jsonschema.validators.validator_for(schema)(schema)

    errors = sorted(
        validator.iter_errors(config),
        key=lambda error: list(map(str, error.absolute_path)),
    )

    return [
        f"{'.'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
        for error in errors
    ]


def validate_config(config: dict[str, Any]) -> None:
    errors = validation_errors(config)
    if errors:
        raise ValueError("Configuration validation failed:\n  - " + "\n  - ".join(errors))


def atomic_write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    temporary_path = Path(temporary_name)

    try:
        os.fchmod(fd, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            yaml.safe_dump(
                data,
                stream,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
            )
            stream.flush()
            os.fsync(stream.fileno())

        os.replace(temporary_path, path)
    except Exception:
        try:
            temporary_path.unlink(missing_ok=True)
        finally:
            raise


def get_dotted_value(data: dict[str, Any], dotted_key: str) -> Any:
    current: Any = data

    for part in dotted_key.split("."):
        if not part or not isinstance(current, dict) or part not in current:
            raise KeyError(f"Unknown configuration key: {dotted_key}")
        current = current[part]

    return current


def set_dotted_value(
    data: dict[str, Any], dotted_key: str, value: Any
) -> None:
    parts = dotted_key.split(".")
    if not all(parts):
        raise KeyError(f"Invalid configuration key: {dotted_key}")

    current: Any = data
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            raise KeyError(f"Unknown configuration key: {dotted_key}")
        current = current[part]

    final_key = parts[-1]
    if not isinstance(current, dict) or final_key not in current:
        raise KeyError(f"Unknown configuration key: {dotted_key}")

    current[final_key] = value


def command_show(_: argparse.Namespace) -> int:
    config = load_effective_config()
    validate_config(config)
    print(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), end="")
    return 0


def command_validate(_: argparse.Namespace) -> int:
    validate_config(load_effective_config())
    print("Watchtower configuration is valid.")
    return 0


def command_get(args: argparse.Namespace) -> int:
    config = load_effective_config()
    validate_config(config)
    value = get_dotted_value(config, args.key)

    if isinstance(value, str):
        print(value)
    elif isinstance(value, bool):
        print(str(value).lower())
    elif value is None:
        print("null")
    elif isinstance(value, (int, float)):
        print(value)
    else:
        print(yaml.safe_dump(value, allow_unicode=True, sort_keys=False).rstrip())

    return 0


def set_layer_value(data: dict[str, Any], dotted_key: str, value: Any) -> None:
    parts = dotted_key.split(".")
    if not all(parts):
        raise KeyError(f"Invalid configuration key: {dotted_key}")

    current = data
    for part in parts[:-1]:
        existing = current.get(part)
        if existing is None:
            current[part] = {}
        elif not isinstance(existing, dict):
            raise KeyError(f"Cannot create nested key below: {part}")
        current = current[part]

    current[parts[-1]] = value


def command_set(args: argparse.Namespace) -> int:
    user_dir = config_directory()
    effective = load_effective_config()

    # Confirm the key exists in the supported configuration.
    get_dotted_value(effective, args.key)

    try:
        value = yaml.safe_load(args.value)
    except yaml.YAMLError as exc:
        raise ValueError(f"Could not parse the supplied YAML value: {exc}") from exc

    def ensure_json_compatible(item: Any) -> None:
        if item is None or isinstance(item, (str, int, float, bool)):
            return
        if isinstance(item, list):
            for child in item:
                ensure_json_compatible(child)
            return
        if isinstance(item, dict):
            if not all(isinstance(key, str) for key in item):
                raise ValueError("Configuration mapping keys must be strings.")
            for child in item.values():
                ensure_json_compatible(child)
            return
        raise ValueError(f"Unsupported configuration value type: {type(item).__name__}")

    ensure_json_compatible(value)

    local_path = user_dir / "config.local.yaml"
    user_path = user_dir / "config.yaml"
    local_config = read_yaml(local_path)
    user_config = read_yaml(user_path)

    # If the key already exists in the local layer, update that layer.
    # Otherwise, write it to the normal user configuration layer.
    try:
        get_dotted_value(local_config, args.key)
        target_path = local_path
        target_config = local_config
    except KeyError:
        target_path = user_path
        target_config = user_config

    set_layer_value(target_config, args.key, value)

    # Validate the result with the updated layer and the other existing layer.
    defaults = read_yaml(DEFAULTS_FILE, required=True)
    if target_path == local_path:
        candidate = deep_merge(deep_merge(defaults, user_config), target_config)
    else:
        candidate = deep_merge(deep_merge(defaults, target_config), local_config)

    validate_config(candidate)
    atomic_write_yaml(target_path, target_config)

    print(f"Updated {args.key}")
    return 0


def command_init(_: argparse.Namespace) -> int:
    user_path = config_directory() / "config.yaml"
    if user_path.exists():
        raise FileExistsError(
            f"{user_path} already exists. Use 'reset' first if you intend to replace it."
        )

    defaults = read_yaml(DEFAULTS_FILE, required=True)
    validate_config(defaults)
    atomic_write_yaml(user_path, defaults)
    print(f"Created user configuration: {user_path}")
    return 0


def command_reset(_: argparse.Namespace) -> int:
    user_dir = config_directory()
    removed = []

    for filename in ("config.yaml", "config.local.yaml"):
        path = user_dir / filename
        if path.exists():
            path.unlink()
            removed.append(filename)

    if removed:
        print("Removed: " + ", ".join(removed))
    else:
        print("No user configuration files to reset.")

    print("Watchtower will now use its built-in defaults.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="watchtower-config",
        description="Manage Watchtower configuration.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("show", help="Show the effective configuration")
    subparsers.add_parser("validate", help="Validate the effective configuration")

    get_parser = subparsers.add_parser("get", help="Read a configuration value")
    get_parser.add_argument("key", help="Dotted key, e.g. appearance.character")

    set_parser = subparsers.add_parser("set", help="Set a configuration value")
    set_parser.add_argument("key", help="Existing dotted configuration key")
    set_parser.add_argument("value", help="Value parsed as a YAML scalar or collection")

    subparsers.add_parser("init", help="Create a user configuration from defaults")
    subparsers.add_parser("reset", help="Remove user and local override configuration")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    commands = {
        "show": command_show,
        "validate": command_validate,
        "get": command_get,
        "set": command_set,
        "init": command_init,
        "reset": command_reset,
    }

    try:
        return commands[args.command](args)
    except (OSError, ValueError, KeyError, jsonschema.ValidationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
