import base64
import json
import logging
from pathlib import Path
from typing import Union

import chardet
import tomllib

logger = logging.getLogger(__name__)


def detect_encoding(filepath: Path, num_bytes: int = 4096) -> str:
    with open(filepath, "rb") as f:
        raw_data = f.read(num_bytes)
    result = chardet.detect(raw_data)
    logger.debug("Detected encoding for %s: %s", filepath, result)
    return result.get("encoding")


def iter_filepath_lines(filepath: Path):
    encoding = detect_encoding(filepath)
    with open(filepath, mode="r", encoding=encoding) as f:
        while True:
            line = f.readline()
            if not line:
                break
            yield line


def read_json(filepath: Path) -> Union[dict, list, None]:
    encoding = detect_encoding(filepath)
    with open(filepath, mode="r", encoding=encoding) as f:
        data = json.load(f)

    return data


def save_json(filepath: Path, data: dict, sort_keys: bool = True) -> None:
    with open(filepath, mode="w", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4, sort_keys=sort_keys))


def read_toml(filepath: Path) -> Union[dict, list, None]:
    # This module does not support writing TOML.
    with open(filepath, mode="rb") as f:
        data = tomllib.load(f)

    return data


def b64decode(data: str):
    suffix = "=" * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(data + suffix).decode("utf-8")
