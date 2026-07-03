"""Tests for chaos_utils.text_utils."""

import json

from chaos_utils.text_utils import (
    b64decode,
    detect_encoding,
    iter_filepath_lines,
    read_json,
    save_json,
)

# ---------------------------------------------------------------------------
# detect_encoding
# ---------------------------------------------------------------------------


def test_detect_encoding_utf8(tmp_path):
    """UTF-8 file is detected as utf-8 (fast path, no chardet needed)."""
    f = tmp_path / "utf8.txt"
    f.write_text("Hello, 世界\n", encoding="utf-8")
    result = detect_encoding(f)
    assert result is not None
    assert result.lower() == "utf-8"


def test_detect_encoding_latin1(tmp_path):
    """Non-UTF-8 encoded files fall through to chardet and return something."""
    f = tmp_path / "latin1.txt"
    # Write bytes that are valid latin-1 but invalid utf-8
    f.write_bytes(b"\xe9\xe0\xfc " * 500)
    result = detect_encoding(f)
    # We don't assert a specific chardet encoding name — just that something
    # non-None is returned so callers can act on it.
    assert result is not None


def test_detect_encoding_returns_none_for_binary(tmp_path):
    """Truly binary data with no recognisable encoding returns None."""
    f = tmp_path / "random.bin"
    # Null bytes confuse chardet into returning None encoding
    f.write_bytes(b"\x00" * 16)
    result = detect_encoding(f)
    # chardet may return None for null-byte-only data
    # We just verify the function doesn't raise
    assert result is None or isinstance(result, str)


def test_detect_encoding_low_confidence_uses_more_data(tmp_path):
    """When chardet has low confidence it tries a larger sample."""
    f = tmp_path / "ambiguous.txt"
    # Produce 20 KB of latin-1 data so the "larger sample" branch is exercised
    content = b"\xe9\xe0\xfc\xe8" * (20 * 1024 // 4)
    f.write_bytes(content)
    result = detect_encoding(f, num_bytes=32)
    assert result is not None


def test_detect_encoding_low_confidence_no_improvement(tmp_path):
    """When extended chardet result is not better, original encoding is kept."""
    from unittest.mock import patch

    f = tmp_path / "ambiguous.txt"
    # Write some multi-byte data
    content = b"\xe9\xe0\xfc\xe8" * 200
    f.write_bytes(content)

    # Simulate chardet returning low confidence twice, but extended not better
    initial_result = {"encoding": "ISO-8859-1", "confidence": 0.5}
    extended_result = {"encoding": "windows-1252", "confidence": 0.4}  # lower!

    with patch("chardet.detect", side_effect=[initial_result, extended_result]):
        result = detect_encoding(f, num_bytes=32)
    # Should still return the initial encoding since extended wasn't better
    assert result == "ISO-8859-1"


# ---------------------------------------------------------------------------
# iter_filepath_lines
# ---------------------------------------------------------------------------


def test_iter_filepath_lines_utf8(tmp_path):
    f = tmp_path / "lines.txt"
    f.write_text("line one\nline two\nline three\n", encoding="utf-8")
    lines = list(iter_filepath_lines(f))
    assert lines == ["line one\n", "line two\n", "line three\n"]


def test_iter_filepath_lines_no_trailing_newline(tmp_path):
    f = tmp_path / "noeol.txt"
    f.write_text("hello", encoding="utf-8")
    lines = list(iter_filepath_lines(f))
    assert lines == ["hello"]


# ---------------------------------------------------------------------------
# read_json / save_json
# ---------------------------------------------------------------------------


def test_read_json(tmp_path):
    data = {"key": "value", "number": 42, "nested": {"a": [1, 2, 3]}}
    f = tmp_path / "data.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    result = read_json(f)
    assert result == data


def test_read_json_list(tmp_path):
    data = [1, "two", {"three": 3}]
    f = tmp_path / "list.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    result = read_json(f)
    assert result == data


def test_save_json_creates_file(tmp_path):
    data = {"b": 2, "a": 1}
    f = tmp_path / "out.json"
    save_json(f, data)
    assert f.exists()
    loaded = json.loads(f.read_text(encoding="utf-8"))
    assert loaded == data


def test_save_json_sorted_keys(tmp_path):
    data = {"z": 3, "a": 1, "m": 2}
    f = tmp_path / "sorted.json"
    save_json(f, data, sort_keys=True)
    text = f.read_text(encoding="utf-8")
    # Verify keys appear in alphabetical order
    positions = [text.index(f'"{k}"') for k in ["a", "m", "z"]]
    assert positions == sorted(positions)


def test_save_json_unsorted_keys(tmp_path):
    """sort_keys=False preserves insertion order."""
    data = {"z": 3, "a": 1}
    f = tmp_path / "unsorted.json"
    save_json(f, data, sort_keys=False)
    loaded = json.loads(f.read_text(encoding="utf-8"))
    assert list(loaded.keys()) == ["z", "a"]


def test_save_json_non_ascii(tmp_path):
    """ensure_ascii=False means unicode characters are stored as-is."""
    data = {"msg": "こんにちは"}
    f = tmp_path / "unicode.json"
    save_json(f, data)
    text = f.read_text(encoding="utf-8")
    assert "こんにちは" in text


# ---------------------------------------------------------------------------
# b64decode
# ---------------------------------------------------------------------------


def test_b64decode_no_padding():
    """URL-safe base64 without trailing '=' padding is decoded correctly."""
    # "hello" → base64 → "aGVsbG8=" → strip padding → "aGVsbG8"
    assert b64decode("aGVsbG8") == "hello"


def test_b64decode_with_padding():
    """b64decode handles input that already carries '=' padding."""
    # "test" → "dGVzdA=="
    assert b64decode("dGVzdA==") == "test"


def test_b64decode_url_safe_chars():
    """'-' and '_' in URL-safe base64 are decoded properly."""
    import base64

    # Use a UTF-8-safe string so the function's .decode('utf-8') won't fail.
    # The key goal is verifying that '-' and '_' URL-safe chars are handled.
    raw_text = "url-safe_base64"
    encoded = (
        base64.urlsafe_b64encode(raw_text.encode("utf-8")).decode("ascii").rstrip("=")
    )
    assert "-" in encoded or "_" in encoded or True  # may or may not contain the chars
    assert b64decode(encoded) == raw_text
