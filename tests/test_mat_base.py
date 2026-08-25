"""Tests for the shared MatrixBase behaviour in ncca.ngl.mat_base.

MatrixBase is abstract (SIZE is set by subclasses), so these tests exercise
its common API through a concrete subclass (Mat3). They target the branches
not already covered by the per-type Mat2/Mat3/Mat4 suites: construction and
operator error paths, the from_numpy shape handling, and sizeof().
"""

import numpy as np
import pytest

from ncca.ngl import Mat3
from ncca.ngl.mat_base import MatrixError


def test_constructor_rejects_wrong_component_count():
    with pytest.raises(MatrixError, match="requires 0 or 9 components"):
        Mat3(1.0, 2.0, 3.0)


def test_from_numpy_accepts_flat_array():
    flat = np.arange(9, dtype=np.float32)

    m = Mat3.from_numpy(flat)

    assert m.to_list() == pytest.approx(list(range(9)))


def test_from_numpy_rejects_wrong_shape():
    with pytest.raises(MatrixError, match="requires shape"):
        Mat3.from_numpy(np.zeros((2, 2), dtype=np.float32))


def test_sizeof_returns_byte_count():
    # 3 * 3 float32 values, 4 bytes each.
    assert Mat3.sizeof() == 36


def test_rmul_scales_from_the_left():
    m = Mat3.identity()

    result = 2.0 * m

    assert result.to_list() == (m * 2.0).to_list()
    assert result[0][0] == pytest.approx(2.0)


def test_truediv_rejects_non_scalar():
    with pytest.raises(MatrixError, match="only scale by scalars"):
        Mat3.identity() / Mat3.identity()


def test_add_rejects_non_matrix():
    with pytest.raises(MatrixError, match="can only add"):
        Mat3.identity() + 5


def test_sub_rejects_non_matrix():
    with pytest.raises(MatrixError, match="can only subtract"):
        Mat3.identity() - 5
