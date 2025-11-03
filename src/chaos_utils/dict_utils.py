import logging
from collections import deque
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

logger = logging.getLogger(__name__)


def deep_merge(
    d1: dict[str, Any],
    d2: dict[str, Any],
    *,
    deepcopy_first: bool = True,
) -> dict[str, Any]:
    """
    Recursively merge two mappings and return the merged result.

    This function returns a new dict containing the keys from ``d1`` updated by
    the keys from ``d2``. When a key exists in both mappings and both values
    are mapping types (collections.abc.Mapping), the merge is performed
    recursively so nested mappings are merged instead of replaced.

    The merge is implemented iteratively using a stack to avoid recursion
    limits. By default a deep copy of ``d1`` is made first to guarantee that
    the returned mapping shares no nested mutable structures with the original
    ``d1``. To optimize for performance and avoid copying, set
    ``deepcopy_first=False`` which will start from a shallow copy of ``d1``
    instead (note: nested mutable objects from ``d1`` may be shared in that
    case).

    Args:
        d1: The base mapping whose values will be updated.
        d2: The mapping to merge into ``d1``. Values in ``d2`` take precedence
            over values in ``d1`` when keys collide.
        deepcopy_first: If True (default) produce a deep copy of ``d1`` before
            merging. If False, use a shallow copy of ``d1`` which is faster
            but may share nested mutable objects with the original.

    Returns:
        A new dict representing the merged mapping.

    Examples:
        >>> deep_merge({"a": 1, "b": {"x": 1}}, {"b": {"y": 2}})
        {'a': 1, 'b': {'x': 1, 'y': 2}}

    Notes:
        Non-mapping values are replaced by values from ``d2``.
        Sequences and other non-mapping iterables are not merged element-wise.
    """
    merged: dict[str, Any] = deepcopy(d1) if deepcopy_first else d1.copy()
    # stack contains pairs of (target_dict, source_dict)
    stack = deque([(merged, d2)])

    while stack:
        current_d1, current_d2 = stack.pop()

        for k, v in current_d2.items():
            # If both sides are mappings, push the pair to the stack for later merging.
            if (
                isinstance(v, Mapping)
                and k in current_d1
                and isinstance(current_d1[k], Mapping)
            ):
                stack.append((current_d1[k], v))
            else:
                # Otherwise, overwrite or set the value.
                current_d1[k] = v

    return merged
