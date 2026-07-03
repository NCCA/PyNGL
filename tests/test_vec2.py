import ctypes
import math

import numpy as np
import pytest

from ncca.ngl import Vec2


def test_init():
    v = Vec2(1.0, 2.0)
    assert v.x == pytest.approx(1.0)
    assert v.y == pytest.approx(2.0)
    v = Vec2()
    assert v.x == pytest.approx(0.0)
    assert v.y == pytest.approx(0.0)


def test_iter():
    v = Vec2(1.0, 2.0)
    assert list(v) == [1.0, 2.0]


def test_copy():
    v1 = Vec2(1.0, 2.0)
    v2 = v1.copy()
    assert v1 == v2
    assert v1 is not v2


def test_getitem():
    v = Vec2(1.0, 2.0)
    assert v[0] == pytest.approx(1.0)
    assert v[1] == pytest.approx(2.0)
    with pytest.raises(IndexError):
        v[2]


def test_validate_and_set():
    v = Vec2()
    v.x = 1.0
    assert v.x == pytest.approx(1.0)
    with pytest.raises(ValueError):
        v.y = "hello"


def test_add():
    v1 = Vec2(1.0, 2.0)
    v2 = Vec2(3.0, 4.0)
    v3 = v1 + v2
    assert v3.x == pytest.approx(4.0)
    assert v3.y == pytest.approx(6.0)


def test_iadd():
    v1 = Vec2(1.0, 2.0)
    v2 = Vec2(3.0, 4.0)
    v1 += v2
    assert v1.x == pytest.approx(4.0)
    assert v1.y == pytest.approx(6.0)


def test_sub():
    v1 = Vec2(1.0, 2.0)
    v2 = Vec2(3.0, 4.0)
    v3 = v1 - v2
    assert v3.x == pytest.approx(-2.0)
    assert v3.y == pytest.approx(-2.0)


def test_isub():
    v1 = Vec2(1.0, 2.0)
    v2 = Vec2(3.0, 4.0)
    v1 -= v2
    assert v1.x == pytest.approx(-2.0)
    assert v1.y == pytest.approx(-2.0)


def test_eq():
    v1 = Vec2(1.0, 2.0)
    v2 = Vec2(1.0, 2.0)
    assert v1 == v2
    v3 = Vec2(2.0, 2.0)
    assert v1 != v3
    assert (v1 == "hello") is False


def test_neq():
    v1 = Vec2(1.0, 2.0)
    v2 = Vec2(1.0, 3.0)
    assert v1 != v2
    v3 = Vec2(2.0, 2.0)
    assert v1 != v3
    v4 = Vec2(3.0, 4.0)
    assert v1 != v4
    assert (v1 != 1) is True


def test_neq_not_implemented():
    v = Vec2(1, 2)
    assert v.__ne__(2) is NotImplemented


def test_neg():
    v1 = Vec2(1.0, 2.0)
    v2 = -v1
    assert v2.x == pytest.approx(-1.0)
    assert v2.y == pytest.approx(-2.0)
    v3 = Vec2(2.5, -2.0)
    assert v3.x == pytest.approx(2.5)
    assert v3.y == pytest.approx(-2.0)


def test_set():
    v = Vec2()
    v.set(1.0, 2.0)
    assert v.x == pytest.approx(1.0)
    assert v.y == pytest.approx(2.0)
    with pytest.raises(ValueError):
        v.set("a", "b")
    with pytest.raises(ValueError):
        v.set(1, 2, 3)


def test_dot():
    v1 = Vec2(1.0, 2.0)
    v2 = Vec2(3.0, 4.0)
    assert v1.dot(v2) == pytest.approx(11.0)


def test_length():
    v = Vec2(3.0, 4.0)
    assert v.length() == pytest.approx(5.0)


def test_length_squared():
    v = Vec2(3.0, 4.0)
    assert v.length_squared() == pytest.approx(25.0)


def test_inner():
    v1 = Vec2(1.0, 2.0)
    v2 = Vec2(3.0, 4.0)
    assert v1.inner(v2) == pytest.approx(11.0)


def test_null():
    v = Vec2(1.0, 2.0)
    v.set(0.0, 0.0)
    assert v.x == pytest.approx(0.0)
    assert v.y == pytest.approx(0.0)


def test_cross():
    v1 = Vec2(1.0, 2.0)
    v2 = Vec2(3.0, 4.0)
    assert v1.cross(v2) == pytest.approx(-2.0)


def test_normalize():
    v = Vec2(3.0, 4.0)
    v = v.normalized()
    assert math.isclose(v.length(), 1.0)
    v = Vec2(0.0, 0.0)
    with pytest.raises(ZeroDivisionError):
        v.normalized()


def test_reflect():
    v = Vec2(1.0, -1.0)
    n = Vec2(0.0, 1.0)
    r = v.reflected(n)
    assert r.x == pytest.approx(1.0)
    assert r.y == pytest.approx(1.0)


def test_clamp():
    v = Vec2(1.5, -1.5)
    v = v.clamped(0.0, 1.0)
    assert v.x == pytest.approx(1.0)
    assert v.y == pytest.approx(0.0)


def test_repr():
    v = Vec2(1.0, 2.0)
    assert repr(v) == "Vec2(1.0, 2.0)"


def test_truediv():
    v = Vec2(2.0, 4.0)
    v2 = v / 2.0
    assert v2.x == pytest.approx(1.0)
    assert v2.y == pytest.approx(2.0)
    with pytest.raises(ValueError):
        _ = v / "a"


def test_div():
    v = Vec2(2.0, 4.0)
    v2 = v / 2.0
    assert v2.x == pytest.approx(1.0)
    assert v2.y == pytest.approx(2.0)
    with pytest.raises(ZeroDivisionError):
        _ = v / 0.0
    with pytest.raises(ZeroDivisionError):
        _ = v / Vec2(0.0, 0.0)

    v3 = v / Vec2(2.0, 2.0)
    result = v2 / v3
    print(result)
    assert result.x == pytest.approx(1.0)
    assert result.y == pytest.approx(1.0)


def test_str():
    v = Vec2(1.0, 2.0)
    assert str(v) == "[1.0, 2.0]"


def test_mul():
    v = Vec2(1.0, 2.0)
    v2 = v * 2.0
    assert v2.x == pytest.approx(2.0)
    assert v2.y == pytest.approx(4.0)
    with pytest.raises(ValueError):
        _ = v * "a"


def test_rmul():
    v = Vec2(1.0, 2.0)
    v2 = 2.0 * v
    assert v2.x == pytest.approx(2.0)
    assert v2.y == pytest.approx(4.0)


def test_matmul():
    from ncca.ngl import Mat2

    v = Vec2(1.0, 2.0)
    m = Mat2.from_list([1.0, 2.0, 3.0, 4.0])
    r = v @ m
    assert r.x == pytest.approx(7.0)
    assert r.y == pytest.approx(10.0)


def test_sizeof():
    assert Vec2.sizeof() == 2 * ctypes.sizeof(ctypes.c_float)


def test_hash():
    a = Vec2(1, 2)
    b = Vec2(1, 2)
    assert hash(a) == hash(b)
    c = Vec2(1, 3)
    assert hash(a) != hash(c)
    # hash can be used as a key in a dictionary so test it
    d = {}
    d[a] = "a"
    d[c] = "c"
    assert d[a] == "a"
    assert d[b] == "a"
    assert d[c] == "c"


def test_to_metods():
    a = Vec2(1, 2)
    assert a.to_list() == [1, 2]
    assert np.array_equal(a.to_numpy(), np.array([1, 2]))


def test_truediv_vec2():
    v1 = Vec2(2.0, 4.0)
    v2 = Vec2(2.0, 2.0)
    result = v1 / v2
    assert result.x == pytest.approx(1.0)
    assert result.y == pytest.approx(2.0)
    with pytest.raises(ZeroDivisionError):
        _ = v1 / Vec2(0.0, 1.0)


def test_outer():
    v1 = Vec2(1.0, 2.0)
    v2 = Vec2(3.0, 4.0)
    result = v1.outer(v2)
    n = result.to_numpy()
    assert n[0, 0] == pytest.approx(3.0)
    assert n[0, 1] == pytest.approx(4.0)
    assert n[1, 0] == pytest.approx(6.0)
    assert n[1, 1] == pytest.approx(8.0)


def test_normalized_returns_new():
    v = Vec2(3.0, 0.0)
    n = v.normalized()
    assert n == Vec2(1.0, 0.0)
    assert v == Vec2(3.0, 0.0)  # original untouched


def test_clamped_returns_new():
    v = Vec2(-2.0, 9.0)
    c = v.clamped(0.0, 1.0)
    assert c == Vec2(0.0, 1.0)
    assert v == Vec2(-2.0, 9.0)


def test_lerp():
    a = Vec2(0.0, 0.0)
    b = Vec2(2.0, 4.0)
    assert a.lerp(b, 0.5) == Vec2(1.0, 2.0)


def test_from_numpy_round_trip():
    v = Vec2.from_numpy(np.array([1.0, 2.0]))
    assert v == Vec2(1.0, 2.0)
    assert v.to_numpy().dtype == np.float32


def test_eval_repr_round_trip():
    v = Vec2(1.5, 2.5)
    assert eval(repr(v)) == v


def test_dtype_is_float32():
    assert Vec2(1.0, 2.0)._data.dtype == np.float32
