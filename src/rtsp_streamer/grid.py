"""Auto-fit grid geometry: map a stream count to (rows, cols).

Breakpoints follow the design spec:
    1 -> 1x1, 2 -> 1x2, 3-4 -> 2x2, 5-6 -> 2x3,
    7-9 -> 3x3, 10-12 -> 3x4, 13-16 -> 4x4.
Counts above 16 clamp to the 4x4 layout; zero or negative is empty.
"""
from __future__ import annotations

# (max_count_inclusive, (rows, cols)) in ascending order.
_BREAKPOINTS = [
    (1, (1, 1)),
    (2, (1, 2)),
    (4, (2, 2)),
    (6, (2, 3)),
    (9, (3, 3)),
    (12, (3, 4)),
    (16, (4, 4)),
]


def grid_dimensions(count: int) -> tuple[int, int]:
    if count <= 0:
        return (0, 0)
    for threshold, dims in _BREAKPOINTS:
        if count <= threshold:
            return dims
    return _BREAKPOINTS[-1][1]
