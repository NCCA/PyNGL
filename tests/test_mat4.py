import mat4Data as mat4Data  # this is generated from the julia file gen_mat4_tests.jl
import numpy as np
import pytest

from ncca.ngl import Mat3, Mat4, MatrixError, Vec4


def test_ctor():
    m = Mat4()
    # fmt: off
    ident = [1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0]
    # fmt: on
    assert m.to_list() == pytest.approx(ident)


def test_translate():
    m = Mat4.translate(1, 2, 3)
    # fmt: off
    ident = [1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                1.0, 2.0, 3.0, 1.0]
    # fmt: on
    assert m.to_list() == pytest.approx(ident)


def test_identity():
    m = Mat4.identity()
    # fmt: off
    ident = [1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0]
    # fmt: on
    assert m.to_list() == pytest.approx(ident)


def test_zero():
    m = Mat4.zero()
    values = m.to_list()
    ident = [0.0] * 16
    assert values == pytest.approx(ident)


def test_to_numpy():
    m = Mat4.from_list([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]])
    n = m.to_numpy()
    value = 1
    for c in range(0, 4):
        for r in range(0, 4):
            assert n[c][r] == value
            value += 1


def test_from_list():
    m = Mat4.from_list([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]])
    result = list(range(1, 17))
    assert m.to_list() == pytest.approx(result)
    m = Mat4.from_list([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
    assert m.to_list() == pytest.approx(result)


def test_not_square():
    with pytest.raises(MatrixError):
        _ = Mat4.from_list([[1.0, 2.0, 3.0, 50], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
    with pytest.raises(MatrixError):
        _ = Mat4.from_list([[], [], [], []])


def test_transposed():
    m = Mat4.from_list([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]])
    m = m.transposed()
    values = m.to_list()
    result = [1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15, 4, 8, 12, 16]
    assert values == pytest.approx(result)


def test_transposed_returns_new():
    m = Mat4(
        1.0,
        2.0,
        3.0,
        4.0,
        5.0,
        6.0,
        7.0,
        8.0,
        9.0,
        10.0,
        11.0,
        12.0,
        13.0,
        14.0,
        15.0,
        16.0,
    )
    t = m.transposed()
    result = [1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15, 4, 8, 12, 16]
    assert t.to_list() == pytest.approx(result)
    assert m.to_list()[1] == 2.0  # original untouched


def test_scale():
    a = Mat4.scale(2.0, 3.0, 4.0)
    value = a.to_list()
    # fmt: off
    result = [2.0,0.0,0.0,0.0,0.0,3.0,0.0,0.0,0.0,0.0,4.0,0.0,0.0,0.0,0.0,1.0]
    # fmt: on
    assert value == pytest.approx(result)


def test_rotate_x():
    a = Mat4.rotate_x(45.0)
    value = a.to_list()
    # fmt: off
    result = [1.0,0.0,0.0,0.0,
                0.0,0.707107,0.707107,0.0,
                0.0,-0.707107,0.707107,0.0,
                0.0,0.0,0.0,1.0]

    # fmt: on
    assert value == pytest.approx(result)


def test_rotate_y():
    a = Mat4.rotate_y(25.0)
    value = a.to_list()
    # fmt: off
    result = [0.906308,0.0,-0.422618,0.0,
                0.0,1.0,0.0,0.0,
                0.422618,0.0,0.906308,0.0,
                0.0,0.0,0.0,1.0]

    #         # fmt: on
    assert value == pytest.approx(result)


def test_rotate_z():
    a = Mat4.rotate_z(-36.0)
    value = a.to_list()
    # fmt: off
    result = [0.809,-0.5877,0.0,0.0,
                0.5877, 0.809, 0.0, 0.0,
                0.0,0.0,1.0, 0.0,
                0.0, 0.0,0.0,1.0,]
    # fmt: on
    assert value == pytest.approx(result, abs=1e-3)


def test_mat4_times_mat4():
    for a, b, result in zip(mat4Data.a, mat4Data.b, mat4Data.a_times_b, strict=False):
        m1 = Mat4.from_list(a)
        m2 = Mat4.from_list(b)
        value = m1 @ m2
        assert value.to_list() == pytest.approx(result)


def test_rotate_mat4_mat4():
    t1 = Mat4.rotate_x(45.0)
    t2 = Mat4.rotate_y(35.0)
    test = t1 @ t2
    # fmt: off
    result=[0.819152,0.405580,-0.405580,0.0,
            0.0,0.707107,0.707107,0.0,
            0.573577,-0.579228,0.579228,0.0,
            0.0,0.0,0.0,1.0]
    # fmt: on
    value = test.to_list()
    assert value == pytest.approx(result, abs=1e-3)
    test = t1 @ t2
    value = test.to_list()
    assert value == pytest.approx(result, abs=1e-3)


def test_mult_error():
    with pytest.raises(MatrixError):
        a = Mat4()
        _ = a @ 2


def test_mult_mat4_equal():
    for a, b, result in zip(mat4Data.a, mat4Data.b, mat4Data.a_times_b, strict=False):
        m1 = Mat4.from_list(a)
        m2 = Mat4.from_list(b)
        m1 @= m2
        assert m1.to_list() == pytest.approx(result)


def test_mat4_mult_vec4():
    test = Vec4(1.0, 2.0, 3.0, 1.0)
    t1 = Mat4.rotate_x(45.0)
    test = t1 @ test
    assert test.x == pytest.approx(1.0)
    assert test.y == pytest.approx(3.535534)
    assert test.z == pytest.approx(0.707107)
    assert test.w == pytest.approx(1.0)


def test_mat4_plus_mat4():
    for a, b, result in zip(mat4Data.a, mat4Data.b, mat4Data.a_plus_b, strict=False):
        m1 = Mat4.from_list(a)
        m2 = Mat4.from_list(b)
        values = m1 + m2
        assert values.to_list() == pytest.approx(result)


def test_mat4_plus_equal():
    for a, b, result in zip(mat4Data.a, mat4Data.b, mat4Data.a_plus_b, strict=False):
        m1 = Mat4.from_list(a)
        m2 = Mat4.from_list(b)
        m1 += m2
        assert m1.to_list() == pytest.approx(result)


def test_mat4_minus_mat4():
    for a, b, result in zip(mat4Data.a, mat4Data.b, mat4Data.a_minus_b, strict=False):
        m1 = Mat4.from_list(a)
        m2 = Mat4.from_list(b)
        values = m1 - m2
        assert values.to_list() == pytest.approx(result, rel=1e-4)


def test_mat4_minus_equal():
    for a, b, result in zip(mat4Data.a, mat4Data.b, mat4Data.a_minus_b, strict=False):
        m1 = Mat4.from_list(a)
        m2 = Mat4.from_list(b)
        m1 -= m2
        assert m1.to_list() == pytest.approx(result, rel=1e-4)


def test_det():
    for a, result in zip(mat4Data.a, mat4Data.a_det, strict=False):
        m1 = Mat4.from_list(a)
        value = m1.determinant()
        assert value == pytest.approx(result[0])


def test_inverse():
    for a, result in zip(mat4Data.a, mat4Data.a_inv, strict=False):
        m1 = Mat4.from_list(a)
        value = m1.inverse()
        assert value.to_list() == pytest.approx(result, rel=1e-4)
    with pytest.raises(MatrixError):
        m1 = Mat4.zero()
        m1.inverse()


def test_subscript():
    a = Mat4.from_list([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]])
    assert a[0].tolist() == [1, 2, 3, 4]
    assert a[1].tolist() == [5, 6, 7, 8]
    assert a[2].tolist() == [9, 10, 11, 12]
    assert a[3].tolist() == [13, 14, 15, 16]


def test_subscript_set():
    a = Mat4()
    a[0] = [1, 2, 3, 4]
    a[1] = [5, 6, 7, 8]
    a[2] = [9, 10, 11, 12]
    a[3] = [13, 14, 15, 16]
    assert a.to_list() == pytest.approx(
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    )


def test_mult():
    a = Mat4.from_list([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]])
    b = a * 2
    result = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32]
    assert b.to_list() == pytest.approx(result)
    with pytest.raises(MatrixError):
        a = a * "hello"


def test_strings():
    a = Mat4.identity()
    assert (
        str(a)
        == "[[1.0, 0.0, 0.0, 0.0]\n [0.0, 1.0, 0.0, 0.0]\n [0.0, 0.0, 1.0, 0.0]\n [0.0, 0.0, 0.0, 1.0]]"
    )
    assert repr(a) == (
        "Mat4(1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, "
        "0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)"
    )


def test_ngl():
    t1 = Mat4.rotate_x(45.0)
    t2 = Mat4.rotate_y(35.0)
    test = t2 @ t1
    result = Mat4.from_list(
        [
            0.819152,
            0,
            -0.573577,
            0,
            0.40558,
            0.707107,
            0.579228,
            0,
            0.40558,
            -0.707107,
            0.579228,
            0,
            0,
            0,
            0,
            1,
        ]
    )
    assert test.to_list() == pytest.approx(result.to_list(), abs=1e-3)


def test_copy():
    m = Mat4.from_list([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]])
    c = m.copy()
    assert c.to_list() == m.to_list()
    assert id(c) != id(m)
    # check that changing the copy doesn't change the original
    c[0][0] = 100
    assert m.to_numpy()[0][0] == 1


def test__eq__():
    a = Mat4.identity()
    b = Mat4.identity()
    assert a == b
    assert a != Mat4.zero()
    # Directly test that __eq__ returns NotImplemented
    result = a.__eq__(5)
    assert result == NotImplemented


def test__ne__():
    a = Mat4.identity()
    assert a != Mat4.zero()
    # Directly test that __ne__ returns NotImplemented
    result = a.__ne__(5)
    assert result == NotImplemented


def test_ctor_components():
    m = Mat4(
        1.0,
        2.0,
        3.0,
        4.0,
        5.0,
        6.0,
        7.0,
        8.0,
        9.0,
        10.0,
        11.0,
        12.0,
        13.0,
        14.0,
        15.0,
        16.0,
    )
    assert m.to_list() == [
        1.0,
        2.0,
        3.0,
        4.0,
        5.0,
        6.0,
        7.0,
        8.0,
        9.0,
        10.0,
        11.0,
        12.0,
        13.0,
        14.0,
        15.0,
        16.0,
    ]


def test_eval_repr_round_trip():
    m = Mat4.rotate_x(45.0)
    assert eval(repr(m)) == m


def test_hashable():
    m = Mat4.identity()
    assert hash(m) == hash(m.copy())


def test_element_write_through():
    m = Mat4.identity()
    m[1][2] = 0.5
    assert m.to_numpy()[1][2] == np.float32(0.5)


def test_from_numpy():
    m = Mat4.from_numpy(np.arange(16, dtype=np.float32).reshape(4, 4))
    assert m.to_list() == [float(i) for i in range(16)]


def test_from_mat3_places_upper_left_block():
    mat3 = Mat3(2.0, 0.0, 0.0, 0.0, 3.0, 0.0, 0.0, 0.0, 4.0)

    m = Mat4.from_mat3(mat3)

    assert m.to_list() == pytest.approx(
        [
            2.0,
            0.0,
            0.0,
            0.0,
            0.0,
            3.0,
            0.0,
            0.0,
            0.0,
            0.0,
            4.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
        ]
    )
