import ctypes

import numpy as np
import pytest

from ncca.ngl import Mat4, Vec4


def test_properties():
    v = Vec4()
    v.x = 2.0
    v.y = 3.0
    v.z = 4.0
    v.w = 5.0
    assert v.x == pytest.approx(2.0)
    assert v.y == pytest.approx(3.0)
    assert v.z == pytest.approx(4.0)
    assert v.w == pytest.approx(5.0)
    with pytest.raises(ValueError):
        v.x = "fail"
    with pytest.raises(ValueError):
        v.y = "fail"
    with pytest.raises(ValueError):
        v.z = "fail"
    with pytest.raises(ValueError):
        v.w = "fail"


def test_ctor():
    v = Vec4()
    assert v.x == pytest.approx(0.0)
    assert v.y == pytest.approx(0.0)
    assert v.z == pytest.approx(0.0)
    assert v.w == pytest.approx(1.0)


def test_user_ctor():
    v = Vec4(2.0, 3.0, 4.0, 5.0)
    assert v.x == pytest.approx(2.0)
    assert v.y == pytest.approx(3.0)
    assert v.z == pytest.approx(4.0)
    assert v.w == pytest.approx(5.0)


def test_ctor_single_value():
    v = Vec4(x=2.0)
    assert v.x == pytest.approx(2.0)
    assert v.y == pytest.approx(0.0)
    assert v.z == pytest.approx(0.0)
    assert v.w == pytest.approx(1.0)

    v = Vec4(y=2.0)
    assert v.x == pytest.approx(0.0)
    assert v.y == pytest.approx(2.0)
    assert v.z == pytest.approx(0.0)
    assert v.w == pytest.approx(1.0)

    v = Vec4(z=2.0)
    assert v.x == pytest.approx(0.0)
    assert v.y == pytest.approx(0.0)
    assert v.z == pytest.approx(2.0)
    assert v.w == pytest.approx(1.0)

    v = Vec4(w=9.2)
    assert v.x == pytest.approx(0.0)
    assert v.y == pytest.approx(0.0)
    assert v.z == pytest.approx(0.0)
    assert v.w == pytest.approx(9.2)


def test_add():
    a = Vec4(1, 2, 3, 4)
    b = Vec4(5, 6, 7, 8)
    c = a + b
    assert c.x == pytest.approx(6.0)
    assert c.y == pytest.approx(8.0)
    assert c.z == pytest.approx(10.0)
    assert c.w == pytest.approx(12.0)


def test_plus_equal():
    a = Vec4(1, 2, 3, 4)
    b = Vec4(5, 6, 7, 8)
    a += b
    assert a.x == pytest.approx(6.0)
    assert a.y == pytest.approx(8.0)
    assert a.z == pytest.approx(10.0)
    assert a.w == pytest.approx(12.0)


def test_sub():
    a = Vec4(1, 2, 3)
    b = Vec4(4, 5, 6, 1.0)  # Include w parameter
    c = a - b
    assert c.x == pytest.approx(-3.0)
    assert c.y == pytest.approx(-3.0)
    assert c.z == pytest.approx(-3.0)
    assert c.w == pytest.approx(0.0)


def test_sub_equals():
    a = Vec4(1, 2, 3)
    b = Vec4(4, 5, 6)
    a -= b
    assert a.x == pytest.approx(-3.0)
    assert a.y == pytest.approx(-3.0)
    assert a.z == pytest.approx(-3.0)
    assert a.w == pytest.approx(0.0)


def test_set():
    a = Vec4()
    a.set(2.5, 0.1, 0.5, 0.2)
    assert a.x == pytest.approx(2.5)
    assert a.y == pytest.approx(0.1)
    assert a.z == pytest.approx(0.5)
    assert a.w == pytest.approx(0.2)
    a = Vec4()
    a.set(1, 2, 3)
    assert a.x == pytest.approx(1.0)
    assert a.y == pytest.approx(2.0)
    assert a.z == pytest.approx(3.0)
    assert a.w == pytest.approx(1.0)
    with pytest.raises(ValueError):
        a.set(1, 2, 3, 4, 5)


def test_error_set():
    with pytest.raises(ValueError):
        a = Vec4()
        a.set("a", 2, 3, 5)


def test_dot():
    a = Vec4(1.0, 2.0, 3.0, 4.0)
    b = Vec4(5.0, 6.0, 7.0, 8.0)
    assert a.dot(b) == pytest.approx(70.0)


def test_length():
    a = Vec4(22, 1, 32, 12)
    assert a.length() == pytest.approx(40.657, rel=1e-3)


def test_length_squared():
    a = Vec4(22, 1, 32, 12)
    assert a.length_squared() == pytest.approx(1653.0, rel=1e-3)


def test_normalize():
    a = Vec4(25.0, 12.2, 0.5, -2.0)
    a.normalize()
    assert a.x == pytest.approx(0.8962, rel=1e-2)
    assert a.y == pytest.approx(0.4373, rel=1e-2)
    assert a.z == pytest.approx(0.0179, rel=1e-2)
    assert a.w == pytest.approx(-0.0716, rel=1e-2)
    with pytest.raises(ZeroDivisionError):
        a = Vec4(0, 0, 0, 0)
        a.normalize()


def test_equal():
    a = Vec4(0.1, 0.2, 0.3, 0.4)
    b = Vec4(0.1, 0.2, 0.3, 0.4)
    assert a == b
    assert a.__eq__(1) == NotImplemented


def test_not_equal():
    a = Vec4(0.3, 0.4, 0.3, 1.0)
    b = Vec4(0.1, 0.2, 0.3, 1.0)
    d = Vec4(1.1, 2.2, 3.3, 4.4)
    assert a != b
    assert a != d

    assert a.__ne__(1) == NotImplemented


def test_negate():
    a = Vec4(0.1, 0.5, -12, 5)
    a = -a
    assert a.x == pytest.approx(-0.1)
    assert a.y == pytest.approx(-0.5)
    assert a.z == pytest.approx(12)
    assert a.w == pytest.approx(-5.0)


def test_get_attr():
    a = Vec4(1, 2, 3, 5)
    assert a.x == pytest.approx(1.0)
    assert a.y == pytest.approx(2.0)
    assert a.z == pytest.approx(3.0)
    assert a.w == pytest.approx(5.0)
    # check to see if we can get non attr
    with pytest.raises(AttributeError):
        a.b

    # check to see that adding an attrib fails
    with pytest.raises(AttributeError):
        a.b = 20.0


def test_mul_scalar():
    a = Vec4(1.0, 1.5, 2.0, 1.0)
    a = a * 2
    assert a.x == pytest.approx(2.0)
    assert a.y == pytest.approx(3.0)
    assert a.z == pytest.approx(4.0)
    assert a.w == pytest.approx(2.0)

    a = Vec4(1.5, 4.2, 2.8, 4.5)
    a = 2 * a
    assert a.x == pytest.approx(3.0)
    assert a.y == pytest.approx(8.4)
    assert a.z == pytest.approx(5.6)
    assert a.w == pytest.approx(9.0)
    with pytest.raises(ValueError):
        a = a * "hello"


def test_matmul():
    a = Vec4(1, 2, 3, 1)
    b = Mat4.rotate_x(45.0)
    c = a @ b
    assert c.x == pytest.approx(1.0)
    assert c.y == pytest.approx(-0.707107)
    assert c.z == pytest.approx(3.535534)
    assert c.w == pytest.approx(1.0)


def test_string():
    a = Vec4(1, 2, 3, 4)
    assert str(a) == "[1,2,3,4]"
    assert repr(a) == "Vec4 [1.0,2.0,3.0,4.0]"


def test_iterable():
    a = Vec4(1, 2, 3, 4)
    b = list(a)
    assert b == [1, 2, 3, 4]
    assert a[0] == 1
    assert a[1] == 2
    assert a[2] == 3
    assert a[3] == 4

    with pytest.raises(IndexError):
        a[5]

    v = []
    v.extend(a)
    assert v == [1, 2, 3, 4]


def test_copy():
    a = Vec4(1, 2, 3, 4)
    b = a.copy()
    assert a == b
    assert a is not b  # Ensure it's a different object


def test_sizeof():
    assert Vec4.sizeof() == 4 * ctypes.sizeof(ctypes.c_float)


def test_division():
    a = Vec4(1.0, 2.0, 3.0, 4.0)
    # test scalar division
    b = a / 2.0
    assert b == Vec4(0.5, 1.0, 1.5, 2.0)
    # test vector division
    c = Vec4(2.0, 2.0, 3.0, 4.0)
    d = a / c
    assert d == Vec4(0.5, 1.0, 1.0, 1.0)
    # test divide by zero
    with pytest.raises(ZeroDivisionError):
        _ = a / 0.0
    with pytest.raises(ZeroDivisionError):
        _ = a / Vec4(0.0, 1.0, 1.0, 1.0)
    with pytest.raises(ValueError):
        _ = a / "hello"


def test_coverage_vec4():
    a = Vec4()
    assert (a == "fail") is False
    with pytest.raises(ValueError):
        a = a * "fail"
    a = 2.0 * a
    assert a.w == pytest.approx(2.0)


def test_hash():
    a = Vec4(1, 2, 3)
    b = Vec4(1, 2, 3)
    assert hash(a) == hash(b)
    c = Vec4(1, 2, 4)
    assert hash(a) != hash(c)
    # hash can be used as a key in a dictionary so test it
    d = {}
    d[a] = "a"
    d[c] = "c"
    assert d[a] == "a"
    assert d[b] == "a"
    assert d[c] == "c"


def test_to_metods():
    a = Vec4(1, 2, 3, 4)
    assert a.to_list() == [1, 2, 3, 4]
    assert np.array_equal(a.to_numpy(), np.array([1, 2, 3, 4]))


def test_outer():
    a = Vec4(1, 2, 3, 4)
    b = Vec4(5, 6, 7, 8)
    m = a.outer(b)
    expected = np.array([[5, 6, 7, 8], [10, 12, 14, 16], [15, 18, 21, 24], [20, 24, 28, 32]])
    assert np.array_equal(m.m, expected)


def test_inner():
    a = Vec4(1, 2, 3, 4)
    b = Vec4(5, 6, 7, 8)
    assert a.inner(b) == pytest.approx(70.0)


def test_null():
    a = Vec4(1, 2, 3, 4)
    a.null()
    assert a == Vec4(0, 0, 0, 0)


def test_cross():
    a = Vec4(1, 2, 3, 0)
    b = Vec4(4, 5, 6, 0)
    c = a.cross(b)
    assert c.x == pytest.approx(-3.0)
    assert c.y == pytest.approx(6.0)
    assert c.z == pytest.approx(-3.0)
    assert c.w == pytest.approx(0.0)
    assert c.w == pytest.approx(0.0)


def test_reflect():
    a = Vec4(1, 0, -1, 0)
    n = Vec4(0, 0, 1, 0)  # Normal pointing up
    r = a.reflect(n)
    assert r.x == pytest.approx(1.0)
    assert r.y == pytest.approx(0.0)
    assert r.z == pytest.approx(1.0)


def test_clamp():
    a = Vec4(-2.0, 0.5, 2.5, 1.5)
    a.clamp(0.0, 1.0)
    assert a.x == pytest.approx(0.0)
    assert a.y == pytest.approx(0.5)
    assert a.z == pytest.approx(1.0)
    assert a.w == pytest.approx(1.0)
