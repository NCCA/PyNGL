import numpy as np
import pytest

from ncca.ngl import Mat2, Vec2


def test_default_identity():
    m = Mat2()
    assert np.array_equal(m.m, np.eye(2, dtype=np.float64))


def test_get_matrix():
    m = Mat2.from_list([1.0, 2.0, 3.0, 4.0])
    assert m.get_matrix() == [1.0, 3.0, 2.0, 4.0]


def test_to_numpy():
    m = Mat2.from_list([1.0, 2.0, 3.0, 4.0])
    arr = m.to_numpy()
    assert isinstance(arr, np.ndarray)
    assert arr.shape == (2, 2)
    np.testing.assert_array_equal(arr, np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32))


def test_identity_classmethod():
    m = Mat2.identity()
    assert np.array_equal(m.m, np.eye(2, dtype=np.float64))


def test_matrix_multiplication():
    a = Mat2.from_list([1, 2, 3, 4])
    b = Mat2.from_list([2, 0, 1, 2])
    result = a @ b

    assert isinstance(result, Mat2)
    assert result == Mat2.from_list([2, 4, 7, 10])


def test_vector_transformation():
    m = Mat2.from_list([1, 2, 3, 4])
    v = Vec2(5, 6)
    result = m @ v
    assert isinstance(result, Vec2)
    assert result.x == 5 * 1 + 6 * 2
    assert result.y == 5 * 3 + 6 * 4


def test_str_representation():
    m = Mat2.from_list([7, 8, 9, 10])
    s = str(m)
    assert s == "Mat2([7.0, 8.0], [9.0, 10.0])"


def test_invalid_matmul_type():
    m = Mat2()
    with pytest.raises(ValueError):
        _ = m @ 42  # Not Mat2 or Vec2


def test_copy():
    m = Mat2.from_list([1, 2, 3, 4])
    c = m.copy()
    assert np.array_equal(c.m, m.m)
    assert id(c) != id(m)
    # check that changing the copy doesn't change the original
    c.m[0][0] = 100
    assert m.m[0][0] == 1
