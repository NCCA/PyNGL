import mat3Data  # this is generated from the julia file gen_mat4_tests.jl
import numpy as np
import pytest

from ncca.ngl import Mat3, Mat4, MatrixError, Vec3


def test_ctor():
    m = Mat3()
    ident = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
    assert m.to_list() == pytest.approx(ident)


def test_identity():
    m = Mat3.identity()
    values = m.to_list()
    ident = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
    assert values == pytest.approx(ident)


def test_to_numpy():
    m = Mat3.from_list([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    n = m.to_numpy()
    value = 1
    for c in range(0, 3):
        for r in range(0, 3):
            assert n[c][r] == value
            value += 1


def test_zero():
    m = Mat3.zero()
    values = m.to_list()
    ident = [0.0] * 9
    assert values == pytest.approx(ident)


def test_from_list():
    m = Mat3.from_list([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
    result = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
    assert m.to_list() == pytest.approx(result)
    m = Mat3.from_list([1, 2, 3, 4, 5, 6, 7, 8, 9])
    assert m.to_list() == pytest.approx(result)


def test_not_square():
    with pytest.raises(MatrixError):
        Mat3.from_list([[1.0, 2.0, 3.0, 50], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])

    with pytest.raises(MatrixError):
        Mat3.from_list([[1, 2, 3], [4, 5, 6], [7, 8, 9], []])


def test_transposed():
    a = Mat3.from_list([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    a = a.transposed()
    result = [1, 4, 7, 2, 5, 8, 3, 6, 9]
    assert a.to_list() == pytest.approx(result)


def test_transposed_returns_new():
    m = Mat3(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)
    t = m.transposed()
    assert t.to_list() == [1.0, 4.0, 7.0, 2.0, 5.0, 8.0, 3.0, 6.0, 9.0]
    assert m.to_list()[1] == 2.0  # original untouched


def test_scale():
    a = Mat3.scale(2.0, 3.0, 4.0)
    result = [2.0, 0.0, 0.0, 0.0, 3.0, 0.0, 0.0, 0.0, 4.0]
    assert a.to_list() == pytest.approx(result)


def test_rotate_x():
    a = Mat3.rotate_x(45.0)
    result = [1.0, 0.0, 0.0, 0.0, 0.707107, 0.707107, 0.0, -0.707107, 0.707107]
    assert a.to_list() == pytest.approx(result)


def test_rotate_y():
    a = Mat3.rotate_y(25.0)
    result = [0.906308, 0.0, -0.422618, 0.0, 1.0, 0.0, 0.422618, 0.0, 0.906308]
    assert a.to_list() == pytest.approx(result)


def test_rotate_z():
    a = Mat3.rotate_z(-36.0)
    result = [0.809017, -0.587785, 0.0, 0.587785, 0.809017, 0.0, 0.0, 0.0, 1.0]
    assert a.to_list() == pytest.approx(result)


def test_mult_mat3_mat3():
    t1 = Mat3.rotate_x(45.0)
    t2 = Mat3.rotate_y(35.0)
    test = t1 @ t2
    # fmt: off
    result = [0.8191, 0.4055, -0.405,0.0, 0.707, 0.707,0.5735, -0.5792, 0.5792]
    # fmt: on
    assert test.to_list() == pytest.approx(result, rel=1e-3, abs=1e-3)

    t1 = Mat3.from_list([1, 2, 3, 2, 3, 4, 4, 5, 6])
    test = t1 @ t1
    result = [17, 23, 29, 24, 33, 42, 38, 53, 68]
    assert test.to_list() == pytest.approx(result, rel=1e-3, abs=1e-3)


def test_mult_error():
    with pytest.raises(MatrixError):
        a = Mat3()
        _ = a @ 2
    with pytest.raises(MatrixError):
        a = Mat3()
        _ = a * "a"


def test_mat3_times_mat3():
    for a, b, result in zip(mat3Data.a, mat3Data.b, mat3Data.a_times_b, strict=False):
        m1 = Mat3.from_list(a)
        m2 = Mat3.from_list(b)
        value = m1 @ m2
        assert value.to_list() == pytest.approx(result, rel=1e-4)


def test_mat3_mult_equal():
    for a, b, result in zip(mat3Data.a, mat3Data.b, mat3Data.a_times_b, strict=False):
        m1 = Mat3.from_list(a)
        m2 = Mat3.from_list(b)
        m1 @= m2
        assert m1.to_list() == pytest.approx(result, rel=1e-4)


def test_mat3_mult_vec3():
    v1 = Vec3(1.0, 2.0, 3.0)
    t1 = Mat3.rotate_x(45.0)
    result = t1 @ v1
    assert result.x == pytest.approx(1.0)
    assert result.y == pytest.approx(3.535534)
    assert result.z == pytest.approx(0.707107)


def test_add():
    a = Mat3.from_list([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    b = Mat3.from_list([[2, 2, 2], [3, 3, 3], [4, 4, 4]])
    c = a + b
    result = c.to_list()
    value = [3, 4, 5, 7, 8, 9, 11, 12, 13]
    assert result == pytest.approx(value)


def test_mat3_plus_mat3():
    for a, b, result in zip(mat3Data.a, mat3Data.b, mat3Data.a_plus_b, strict=False):
        m1 = Mat3.from_list(a)
        m2 = Mat3.from_list(b)
        values = m1 + m2
        assert values.to_list() == pytest.approx(result, rel=1e-4)


def test_mat3_plus_equal():
    for a, b, result in zip(mat3Data.a, mat3Data.b, mat3Data.a_plus_b, strict=False):
        m1 = Mat3.from_list(a)
        m2 = Mat3.from_list(b)
        m1 += m2
        assert m1.to_list() == pytest.approx(result, rel=1e-4)


def test_mat3_mult_float():
    a = Mat3.from_list([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    b = a * 2
    result = [2, 4, 6, 8, 10, 12, 14, 16, 18]
    assert b.to_list() == pytest.approx(result)
    with pytest.raises(MatrixError):
        a = a * "hello"


def test_mat3_minus_mat3():
    for a, b, result in zip(mat3Data.a, mat3Data.b, mat3Data.a_minus_b, strict=False):
        m1 = Mat3.from_list(a)
        m2 = Mat3.from_list(b)
        values = m1 - m2
        assert values.to_list() == pytest.approx(result, rel=1e-4)


def test_mat3_minus_equal():
    for a, b, result in zip(mat3Data.a, mat3Data.b, mat3Data.a_minus_b, strict=False):
        m1 = Mat3.from_list(a)
        m2 = Mat3.from_list(b)
        m1 -= m2
        assert m1.to_list() == pytest.approx(result, rel=1e-4)


def test_det():
    for a, result in zip(mat3Data.a, mat3Data.a_det, strict=False):
        m1 = Mat3.from_list(a)
        value = m1.determinant()
        assert value == pytest.approx(result[0])


def test_inverse():
    for a, result in zip(mat3Data.a, mat3Data.a_inv, strict=False):
        m1 = Mat3.from_list(a)
        value = m1.inverse()
        assert value.to_list() == pytest.approx(result)
    with pytest.raises(MatrixError):
        m = Mat3.zero()
        m.inverse()


def test_subscript():
    a = Mat3.from_list([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    assert a[0].tolist() == [1, 2, 3]
    assert a[1].tolist() == [4, 5, 6]
    assert a[2].tolist() == [7, 8, 9]


def test_subscript_set():
    a = Mat3.identity()
    a[0] = [1, 1, 1]
    a[1] = [2, 2, 2]
    a[2] = [3, 3, 3]

    assert a[0].tolist() == [1, 1, 1]
    assert a[1].tolist() == [2, 2, 2]
    assert a[2].tolist() == [3, 3, 3]


def test_strings():
    a = Mat3.identity()
    assert str(a) == "[[1.0, 0.0, 0.0]\n [0.0, 1.0, 0.0]\n [0.0, 0.0, 1.0]]"
    assert repr(a) == "Mat3(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)"


def test_from_mat4():
    m4 = Mat4.identity()
    m3 = Mat3.from_mat4(m4)
    assert m3.to_list() == pytest.approx([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0])


def test_copy():
    m = Mat3.from_list([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    c = m.copy()
    assert c.to_list() == m.to_list()
    assert id(c) != id(m)
    # check that changing the copy doesn't change the original
    c[0][0] = 100
    assert m.to_numpy()[0][0] == 1


def test_to_list():
    m = Mat3.from_list([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    assert m.to_list() == pytest.approx([1, 2, 3, 4, 5, 6, 7, 8, 9])


def test__eq__():
    a = Mat3.identity()
    b = Mat3.identity()
    assert a == b
    assert a != Mat3.zero()
    # Directly test that __eq__ returns NotImplemented
    result = a.__eq__(5)
    assert result == NotImplemented


def test__ne__():
    a = Mat3.identity()
    assert a != Mat3.zero()
    # Directly test that __ne__ returns NotImplemented
    result = a.__ne__(5)
    assert result == NotImplemented


def test_ctor_components():
    m = Mat3(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)
    assert m.to_list() == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]


def test_eval_repr_round_trip():
    m = Mat3.rotate_x(45.0)
    assert eval(repr(m)) == m


def test_hashable():
    m = Mat3.identity()
    assert hash(m) == hash(m.copy())


def test_element_write_through():
    m = Mat3.identity()
    m[1][2] = 0.5
    assert m.to_numpy()[1][2] == np.float32(0.5)


def test_from_numpy():
    m = Mat3.from_numpy(np.arange(9, dtype=np.float32).reshape(3, 3))
    assert m.to_list() == [float(i) for i in range(9)]
