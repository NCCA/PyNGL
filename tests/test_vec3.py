import ctypes
from typing import cast

import numpy as np
import pytest

from ncca.ngl import Mat3, Vec2, Vec3


def test_properties():
    v = Vec3()
    v.x = 2.0
    v.y = 3.0
    v.z = 4.0
    assert v.x == pytest.approx(2.0)
    assert v.y == pytest.approx(3.0)
    assert v.z == pytest.approx(4.0)
    with pytest.raises(ValueError):
        v.x = "fail"
    with pytest.raises(ValueError):
        v.y = "fail"
    with pytest.raises(ValueError):
        v.z = "fail"


def test_ctor():
    v = Vec3()
    assert v.x == pytest.approx(0.0)
    assert v.y == pytest.approx(0.0)
    assert v.z == pytest.approx(0.0)


def test_user_ctor():
    v = Vec3(2.0, 3.0, 4.0)
    assert v.x == pytest.approx(2.0)
    assert v.y == pytest.approx(3.0)
    assert v.z == pytest.approx(4.0)


def test_ctor_single_value():
    v = Vec3(x=2.0)
    assert v.x == pytest.approx(2.0)
    assert v.y == pytest.approx(0.0)
    assert v.z == pytest.approx(0.0)

    v = Vec3(y=2.0)
    assert v.x == pytest.approx(0.0)
    assert v.y == pytest.approx(2.0)
    assert v.z == pytest.approx(0.0)

    v = Vec3(z=2.0)
    assert v.x == pytest.approx(0.0)
    assert v.y == pytest.approx(0.0)
    assert v.z == pytest.approx(2.0)


def test_ctor_too_many_args():
    with pytest.raises(ValueError):
        Vec3(1, 2, 3, 4)


def test_add():
    a = Vec3(1, 2, 3)
    b = Vec3(4, 5, 6)
    c = a + b
    assert c.x == pytest.approx(5)
    assert c.y == pytest.approx(7)
    assert c.z == pytest.approx(9)

    # negative test
    a = Vec3(1, 2, 3)
    b = Vec3(-4, -5, -6)
    c = a + b
    assert c.x == pytest.approx(-3)
    assert c.y == pytest.approx(-3)
    assert c.z == pytest.approx(-3)


def test_plus_equals():
    a = Vec3(1, 2, 3)
    b = Vec3(4, 5, 6)
    a += b
    assert a.x == pytest.approx(5)
    assert a.y == pytest.approx(7)
    assert a.z == pytest.approx(9)


def test_sub():
    a = Vec3(1, 2, 3)
    b = Vec3(4, 5, 6)
    c = a - b
    assert c.x == pytest.approx(-3)
    assert c.y == pytest.approx(-3)
    assert c.z == pytest.approx(-3)


def test_sub_equals():
    a = Vec3(1, 2, 3)
    b = Vec3(4, 5, 6)
    a -= b
    assert a.x == pytest.approx(-3)
    assert a.y == pytest.approx(-3)
    assert a.z == pytest.approx(-3)


def test_set():
    a = Vec3()
    a.set(2.5, 0.1, 0.5)
    assert a.x == pytest.approx(2.5)
    assert a.y == pytest.approx(0.1)
    assert a.z == pytest.approx(0.5)
    with pytest.raises(ValueError):
        a.set(2, 3, 4, 5)


def test_error_set():
    with pytest.raises(ValueError):
        a = Vec3()
        a.set(2, 3, "hello")


def test_dot():
    a = Vec3(1.0, 2.0, 3.0)
    b = Vec3(4.0, 5.0, 6.0)
    assert a.dot(b) == pytest.approx(32.0)


def test_length():
    a = Vec3(22, 1, 32)
    assert a.length() == pytest.approx(38.845, rel=1e-2)


def test_length_squared():
    a = Vec3(22, 1, 32)
    assert a.length_squared() == pytest.approx(1509, rel=1e-2)


def test_normalize():
    a = Vec3(22.3, 0.5, 10.0)
    a = a.normalized()
    assert a.x == pytest.approx(0.912266, rel=1e-2)
    assert a.y == pytest.approx(0.0204544, rel=1e-2)
    assert a.z == pytest.approx(0.409088, rel=1e-2)
    with pytest.raises(ZeroDivisionError):
        a = Vec3(0, 0, 0)
        a.normalized()


def test_equal():
    a = Vec3(0.1, 0.2, 0.3)
    b = Vec3(0.1, 0.2, 0.3)
    assert a == b
    assert a.__eq__(1) == NotImplemented


def test_not_equal():
    a = Vec3(0.3, 0.4, 0.3)
    b = Vec3(0.1, 0.2, 0.3)
    assert a != b
    a = Vec3(0.3, 0.4, 0.3)
    b = Vec3(0.3, 0.2, 0.3)
    assert a != b
    a = Vec3(0.3, 0.2, 0.3)
    b = Vec3(0.3, 0.4, 0.3)
    assert a != b
    a = Vec3(0.3, 0.4, 0.3)
    b = Vec3(0.3, 0.4, 0.5)
    assert a != b
    c = Vec3(1, 2, 3)
    d = Vec3(4, 5, 6)
    assert c != d
    assert a.__ne__(1) == NotImplemented


def test_inner():
    a = Vec3(1.0, 2.0, 3.0)
    b = Vec3(3.0, 4.0, 5.0)
    inner = a.inner(b)
    assert inner == pytest.approx(26.0)


def test_negate():
    a = Vec3(0.1, 0.5, -12)
    a = -a
    assert a.x == pytest.approx(-0.1)
    assert a.y == pytest.approx(-0.5)
    assert a.z == pytest.approx(12.0)


def test_reflect():
    N = Vec3(0, 1, 0)
    a = Vec3(2, 2, 0)
    a = a.normalized()
    ref = a.reflected(N)
    assert ref.x == pytest.approx(0.707, rel=1e-2)
    assert ref.y == pytest.approx(-0.707, rel=1e-2)
    assert ref.z == pytest.approx(0.0, rel=1e-2)


def test_clamp():
    a = Vec3(0.1, 5.0, 1.7)
    a = a.clamped(0.5, 1.8)
    assert a.x == pytest.approx(0.5)
    assert a.y == pytest.approx(1.8)
    assert a.z == pytest.approx(1.7)


def test_outer():
    a = Vec3(1.0, 2.0, 3.0)
    b = Vec3(3.0, 4.0, 5.0)
    outer = a.outer(b)
    result = [3, 4, 5, 6, 8, 10, 9, 12, 15]
    value = outer.to_list()
    assert result == pytest.approx(value)


def test_null():
    a = Vec3(2, 3, 5)
    a.set(0.0, 0.0, 0.0)
    assert a.x == pytest.approx(0.0)
    assert a.y == pytest.approx(0.0)
    assert a.z == pytest.approx(0.0)


def test_cross():
    a = Vec3(0.0, 1.0, 0.0)
    b = Vec3(-1.0, 0.0, 0.0)
    c = a.cross(b)
    assert c.x == pytest.approx(0.0)
    assert c.y == pytest.approx(0.0)
    assert c.z == pytest.approx(1.0)
    assert c == Vec3(0.0, 0.0, 1.0)


def test_mul_scalar():
    a = Vec3(1.0, 1.5, 2.0)
    a = a * 2
    assert a.x == pytest.approx(2.0)
    assert a.y == pytest.approx(3.0)
    assert a.z == pytest.approx(4.0)

    a = Vec3(1.5, 4.2, 2.8)
    a = 2 * a
    assert a.x == pytest.approx(3.0)
    assert a.y == pytest.approx(8.4)
    assert a.z == pytest.approx(5.6)

    with pytest.raises(ValueError):
        a = a * "hello"


def test_get_attr():
    a = Vec3(1, 2, 3)
    assert a.x == pytest.approx(1.0)
    assert a.y == pytest.approx(2.0)
    assert a.z == pytest.approx(3.0)

    # check to see if we can get non attr
    with pytest.raises(AttributeError):
        a.b
    # check to see that adding an attrib fails
    with pytest.raises(AttributeError):
        a.b = 20.0


def test_matmul():
    a = Vec3(1, 2, 3)
    b = Mat3.rotate_x(45.0)
    c = a @ b
    assert c.x == pytest.approx(1.0)
    assert c.y == pytest.approx(-0.707107, rel=1e-2)
    assert c.z == pytest.approx(3.535534, rel=1e-2)


def test_string():
    a = Vec3(1, 2, 3)
    assert str(a) == "[1.0, 2.0, 3.0]"
    assert repr(a) == "Vec3(1.0, 2.0, 3.0)"


def test_iterable():
    a = Vec3(1, 2, 3)
    b = list(a)
    assert b == [1, 2, 3]
    assert a[0] == 1
    assert a[1] == 2
    assert a[2] == 3
    with pytest.raises(IndexError):
        a[3]

    v = []
    v.extend(a)
    assert v == [1, 2, 3]


def test_copy():
    a = Vec3(1, 2, 3)
    b = a.copy()
    assert a == b
    assert a is not b  # Ensure it's a different object
    b.x = 10
    assert a != b
    assert a.x == 1
    assert b.x == 10


def test_sizeof():
    assert Vec3.sizeof() == 3 * ctypes.sizeof(ctypes.c_float)


def test_division():
    a = Vec3(1.0, 2.0, 3.0)
    # test scalar division
    b = a / 2.0
    assert b == Vec3(0.5, 1.0, 1.5)
    # test vector division
    c = Vec3(2.0, 2.0, 3.0)
    d = a / c
    assert d == Vec3(0.5, 1.0, 1.0)
    # test divide by zero
    with pytest.raises(ZeroDivisionError):
        _ = a / 0.0
    with pytest.raises(ZeroDivisionError):
        _ = a / Vec3(0.0, 1.0, 1.0)
    with pytest.raises(ValueError):
        _ = a / "hello"


def test_hash():
    a = Vec3(1, 2, 3)
    b = Vec3(1, 2, 3)
    assert hash(a) == hash(b)
    c = Vec3(1, 2, 4)
    assert hash(a) != hash(c)
    # hash can be used as a key in a dictionary so test it
    d = {}
    d[a] = "a"
    d[c] = "c"
    assert d[a] == "a"
    assert d[b] == "a"
    assert d[c] == "c"


def test_to_metods():
    a = Vec3(1, 2, 3)
    assert a.to_list() == [1, 2, 3]
    assert np.array_equal(a.to_numpy(), np.array([1, 2, 3]))
    assert a.to_tuple() == (1, 2, 3)


def test_unknown_component_kwarg():
    with pytest.raises(ValueError, match="Unknown component name"):
        Vec3(invalid_component=1.0)


def test_add_incompatible_type():
    a = Vec3(1, 2, 3)
    b = cast(Vec3, Vec2(1, 2))
    with pytest.raises(ValueError, match="Can only add Vec3 to Vec3"):
        _ = a + b


def test_iadd_incompatible_type():
    a = Vec3(1, 2, 3)
    b = cast(Vec3, Vec2(1, 2))
    with pytest.raises(ValueError, match="Can only add Vec3 to Vec3"):
        a += b


def test_sub_incompatible_type():
    a = Vec3(1, 2, 3)
    b = cast(Vec3, Vec2(1, 2))
    with pytest.raises(ValueError, match="Can only subtract Vec3 from Vec3"):
        _ = a - b


def test_isub_incompatible_type():
    a = Vec3(1, 2, 3)
    b = cast(Vec3, Vec2(1, 2))
    with pytest.raises(ValueError, match="Can only subtract Vec3 from Vec3"):
        a -= b


def test_dot_incompatible_type():
    a = Vec3(1, 2, 3)
    b = cast(Vec3, Vec2(1, 2))
    with pytest.raises(ValueError, match="Can only compute dot product with Vec3"):
        _ = a.dot(b)


def test_normalized_returns_new():
    v = Vec3(3.0, 0.0, 0.0)
    n = v.normalized()
    assert n == Vec3(1.0, 0.0, 0.0)
    assert v == Vec3(3.0, 0.0, 0.0)  # original untouched


def test_clamped_returns_new():
    v = Vec3(-2.0, 0.5, 9.0)
    c = v.clamped(0.0, 1.0)
    assert c == Vec3(0.0, 0.5, 1.0)
    assert v == Vec3(-2.0, 0.5, 9.0)


def test_lerp():
    a = Vec3(0.0, 0.0, 0.0)
    b = Vec3(2.0, 4.0, 6.0)
    assert a.lerp(b, 0.5) == Vec3(1.0, 2.0, 3.0)


def test_from_numpy_round_trip():
    import numpy as np

    v = Vec3.from_numpy(np.array([1.0, 2.0, 3.0]))
    assert v == Vec3(1.0, 2.0, 3.0)
    assert v.to_numpy().dtype == np.float32


def test_eval_repr_round_trip():
    v = Vec3(1.5, 2.5, 3.5)
    assert eval(repr(v)) == v


def test_dtype_is_float32():
    import numpy as np

    assert Vec3(1.0, 2.0, 3.0)._data.dtype == np.float32
