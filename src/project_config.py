from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "project.json"


@lru_cache(maxsize=1)
def load_project_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def config_value(name: str):
    config = load_project_config()
    if name not in config:
        raise KeyError(f"Missing project configuration value: {name}")
    return config[name]
