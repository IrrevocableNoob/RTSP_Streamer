import pytest

from rtsp_streamer.grid import grid_dimensions


@pytest.mark.parametrize(
    "n,dim",
    [
        (1, (1, 1)),
        (2, (1, 2)),
        (3, (2, 2)),
        (4, (2, 2)),
        (5, (2, 3)),
        (6, (2, 3)),
        (7, (3, 3)),
        (9, (3, 3)),
        (10, (3, 4)),
        (12, (3, 4)),
        (13, (4, 4)),
        (16, (4, 4)),
    ],
)
def test_grid_dimensions(n, dim):
    assert grid_dimensions(n) == dim


def test_zero_or_negative_is_empty():
    assert grid_dimensions(0) == (0, 0)
    assert grid_dimensions(-3) == (0, 0)


def test_above_max_clamps_to_sixteen_layout():
    assert grid_dimensions(20) == (4, 4)
