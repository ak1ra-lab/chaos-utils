from chaos_utils.dict_utils import deep_merge


def test_basic_merge():
    """Test merging of flat dictionaries."""
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 3, "c": 4}
    expected = {"a": 1, "b": 3, "c": 4}

    result = deep_merge(d1, d2)
    assert result == expected
    # Original dict should not be modified
    assert d1 == {"a": 1, "b": 2}


def test_nested_merge():
    """Test merging of nested dictionaries."""
    d1 = {"a": 1, "b": {"x": 1, "y": 2}}
    d2 = {"b": {"y": 3, "z": 4}, "c": 5}
    expected = {"a": 1, "b": {"x": 1, "y": 3, "z": 4}, "c": 5}

    result = deep_merge(d1, d2)
    assert result == expected


def test_empty_dicts():
    """Test merging with empty dictionaries."""
    d1 = {"a": 1}
    d2 = {}
    assert deep_merge(d1, d2) == {"a": 1}
    assert deep_merge({}, d1) == {"a": 1}
    assert deep_merge({}, {}) == {}


def test_deepcopy_behavior():
    """Test deepcopy_first parameter behavior."""
    nested = {"x": 1}
    d1 = {"a": nested}
    d2 = {"b": 2}

    # With deepcopy_first=True (default)
    result1 = deep_merge(d1, d2)
    nested["x"] = 999
    assert result1["a"]["x"] == 1  # Should not be affected

    # With deepcopy_first=False
    result2 = deep_merge(d1, d2, deepcopy_first=False)
    nested["x"] = 777
    assert result2["a"]["x"] == 777  # Should be affected


def test_different_value_types():
    """Test merging dictionaries with different value types."""
    d1 = {"str": "original", "int": 1, "list": [1, 2], "dict": {"a": 1}}
    d2 = {"str": "new", "int": 2, "list": [3, 4], "dict": {"b": 2}}

    result = deep_merge(d1, d2)
    assert result["str"] == "new"
    assert result["int"] == 2
    assert result["list"] == [3, 4]
    assert result["dict"] == {"a": 1, "b": 2}


def test_overwrite_behavior():
    """Test overwriting behavior when merging."""
    d1 = {"a": {"x": 1, "y": 2}, "b": [1, 2], "c": 1}
    d2 = {"a": {"y": 3, "z": 4}, "b": "new", "d": 4}

    result = deep_merge(d1, d2)
    assert result["a"] == {"x": 1, "y": 3, "z": 4}  # Merged
    assert result["b"] == "new"  # Overwritten
    assert result["c"] == 1  # Unchanged
    assert result["d"] == 4  # Added
