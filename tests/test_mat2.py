import numpy as np
import pytest

from ncca.ngl import Mat2, MatrixError, Vec2


def test_default_identity():
    m = Mat2()
    assert np.array_equal(m.to_numpy(), np.eye(2, dtype=np.float32))


def test_to_list():
    m = Mat2.from_list([1.0, 2.0, 3.0, 4.0])
    assert m.to_list() == [1.0, 2.0, 3.0, 4.0]


def test_to_numpy():
    m = Mat2.from_list([1.0, 2.0, 3.0, 4.0])
    arr = m.to_numpy()
    assert isinstance(arr, np.ndarray)
    assert arr.shape == (2, 2)
    np.testing.assert_array_equal(
        arr, np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    )


def test_identity_classmethod():
    m = Mat2.identity()
    assert np.array_equal(m.to_numpy(), np.eye(2, dtype=np.float32))


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
    assert s == "[[7.0, 8.0]\n [9.0, 10.0]]"


def test_invalid_matmul_type():
    m = Mat2()
    with pytest.raises(MatrixError):
        _ = m @ 42  # Not Mat2 or Vec2


def test_copy():
    m = Mat2.from_list([1, 2, 3, 4])
    c = m.copy()
    assert np.array_equal(c.to_numpy(), m.to_numpy())
    assert id(c) != id(m)
    # check that changing the copy doesn't change the original
    c[0][0] = 100
    assert m.to_numpy()[0][0] == 1


def test__eq__():
    a = Mat2.identity()
    b = Mat2.identity()
    assert a == b
    assert a != Mat2.zero()

    # Directly test that __eq__ returns NotImplemented
    result = a.__eq__(5)
    assert result == NotImplemented


def test__ne__():
    a = Mat2.identity()
    assert a != Mat2.zero()
    # Directly test that __ne__ returns NotImplemented
    result = a.__ne__(5)
    assert result == NotImplemented


def test_from_list():
    m = Mat2.from_list([[1, 2], [3, 4]])
    result = list(range(1, 5))
    assert m.to_list() == pytest.approx(result)
    m = Mat2.from_list([1, 2, 3, 4])
    assert m.to_list() == pytest.approx(result)


def test_not_square():
    with pytest.raises(MatrixError):
        _ = Mat2.from_list([[1.0, 2.0, 3.0, 50], [4.0, 5.0], [7.0, 8.0, 9.0]])
    with pytest.raises(MatrixError):
        _ = Mat2.from_list([[], []])


def test_ctor_components():
    m = Mat2(1.0, 2.0, 3.0, 4.0)
    assert m.to_list() == [1.0, 2.0, 3.0, 4.0]


def test_transposed_returns_new():
    m = Mat2(1.0, 2.0, 3.0, 4.0)
    t = m.transposed()
    assert t.to_list() == [1.0, 3.0, 2.0, 4.0]
    assert m.to_list()[1] == 2.0  # original untouched


def test_eval_repr_round_trip():
    m = Mat2.from_list([1.0, 2.0, 3.0, 4.0])
    assert eval(repr(m)) == m


def test_hashable():
    m = Mat2.identity()
    assert hash(m) == hash(m.copy())


def test_element_write_through():
    m = Mat2.identity()
    m[1][0] = 0.5
    assert m.to_numpy()[1][0] == np.float32(0.5)


def test_from_numpy():
    m = Mat2.from_numpy(np.arange(4, dtype=np.float32).reshape(2, 2))
    assert m.to_list() == [float(i) for i in range(4)]


def test_mat2_has_full_api():
    m = Mat2(1.0, 2.0, 3.0, 4.0)
    assert m.determinant() == pytest.approx(-2.0)
    assert m.inverse() @ m == Mat2.identity()
    assert (m + m).to_list() == [2.0, 4.0, 6.0, 8.0]
    assert (m - m) == Mat2.zero()
    assert m.transposed().to_list() == [1.0, 3.0, 2.0, 4.0]
