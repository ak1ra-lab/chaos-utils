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
    Iteratively merge d2 into a shallow copy of d1 using a stack if deepcopy_first is False.
    If deepcopy_first is True (default), make a deep copy of d1 first to avoid sharing
    any nested mutable objects.
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
