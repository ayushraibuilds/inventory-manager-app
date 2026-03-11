import os
from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values


ENV_FILE = Path(__file__).resolve().with_name(".env")


@lru_cache(maxsize=1)
def get_dotenv_values() -> dict[str, str]:
    if not ENV_FILE.exists():
        return {}
    return {
        key: str(value)
        for key, value in dotenv_values(ENV_FILE).items()
        if value is not None
    }


def get_env_value(key: str, default: str = "") -> str:
    runtime_value = os.getenv(key)
    if runtime_value not in (None, ""):
        return runtime_value
    return str(get_dotenv_values().get(key, default) or default)


def get_merged_env() -> dict[str, str]:
    merged = dict(get_dotenv_values())
    merged.update(os.environ)
    return merged
