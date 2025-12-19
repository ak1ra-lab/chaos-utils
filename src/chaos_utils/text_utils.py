import base64
import json
import logging
from pathlib import Path
from typing import Union

import chardet
import tomllib

logger = logging.getLogger(__name__)


def detect_encoding(filepath: Path, num_bytes: int = 4096) -> str:
    """
    Detect the character encoding of a file.

    This helper reads up to ``num_bytes`` of the file in binary mode and
    uses :mod:`chardet` to guess an encoding. It returns the string name of
    the detected encoding (for example ``"utf-8"``) or ``None`` if the
    detector could not determine an encoding.

    Args:
        filepath: Path to the file to probe.
        num_bytes: Maximum number of bytes to read from the start of the
            file for detection (defaults to 4096).

    Returns:
        The name of the detected encoding, or ``None`` if unknown.
    """
    with open(filepath, "rb") as f:
        raw_data = f.read(num_bytes)
    result = chardet.detect(raw_data)
    logger.debug("Detected encoding for %s: %s", filepath, result)

    # If confidence is low, try UTF-8 first as it's most common
    encoding = result.get("encoding")
    confidence = result.get("confidence", 0)

    if confidence < 0.9 and encoding and encoding.lower() not in ["utf-8", "ascii"]:
        try:
            raw_data.decode("utf-8")
            logger.debug(
                "Low confidence (%s), validated UTF-8 for %s", confidence, filepath
            )
            return "utf-8"
        except UnicodeDecodeError:
            pass

    return encoding


def iter_filepath_lines(filepath: Path):
    """
    Yield lines from ``filepath`` using a detected encoding.

    This generator will open the file with the encoding guessed by
    :func:`detect_encoding` and yield each line as a string. Useful for
    processing files with unknown encodings safely.

    Args:
        filepath: Path to the file to read.

    Yields:
        Lines from the file as unicode strings (with trailing newline if
        present).
    """
    encoding = detect_encoding(filepath)
    with open(filepath, mode="r", encoding=encoding) as f:
        while True:
            line = f.readline()
            if not line:
                break
            yield line


def read_json(filepath: Path) -> Union[dict, list, None]:
    """
    Read and parse JSON from ``filepath`` using detected encoding.

    Args:
        filepath: Path to a JSON file.

    Returns:
        The parsed JSON object (typically a ``dict`` or ``list``). If the
        file is empty or cannot be parsed a JSONDecodeError will propagate.
    """
    encoding = detect_encoding(filepath)
    with open(filepath, mode="r", encoding=encoding) as f:
        data = json.load(f)

    return data


def save_json(filepath: Path, data: dict, sort_keys: bool = True) -> None:
    """
    Serialize ``data`` to a JSON file using UTF-8 encoding.

    The output file is written with indentation and UTF-8 encoding. By
    default keys are sorted to produce stable output.

    Args:
        filepath: Path where the JSON will be written.
        data: A JSON-serializable Python object (commonly a ``dict``).
        sort_keys: If True, sort dictionary keys in the output for
            deterministic result.
    """
    with open(filepath, mode="w", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4, sort_keys=sort_keys))


def read_toml(filepath: Path) -> Union[dict, list, None]:
    """
    Read TOML data from ``filepath``.

    This uses the stdlib :mod:`tomllib` (Python 3.11+) to parse the file.
    Note that writing TOML is not supported by this helper — use a TOML
    library that supports serialization if you need to write TOML files.

    Args:
        filepath: Path to the TOML file.

    Returns:
        The parsed TOML data (typically a dict).
    """
    # This module does not support writing TOML.
    with open(filepath, mode="rb") as f:
        data = tomllib.load(f)

    return data


def b64decode(data: str):
    """
    Decode a URL-safe Base64-encoded string into a UTF-8 string.

    The helper will add the required padding characters (``=``) if they are
    missing from the input before decoding.

    Args:
        data: A base64 (URL-safe) encoded string. Padding may be omitted.

    Returns:
        The decoded Unicode string.

    Raises:
        binascii.Error: If the input is not valid base64.
    """
    suffix = "=" * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(data + suffix).decode("utf-8")
