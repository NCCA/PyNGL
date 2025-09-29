import pytest

from ncca.ngl import Mat4, Quaternion


def test_quaternion():
    q = Quaternion()
    assert q.s == pytest.approx(1.0)
    assert q.x == pytest.approx(0.0)
    assert q.y == pytest.approx(0.0)
    assert q.z == pytest.approx(0.0)
    q = Quaternion(0.2, 0.0, 1.0, 0.0)
    assert q.s == pytest.approx(0.2)
    assert q.x == pytest.approx(0.0)
    assert q.y == pytest.approx(1.0)
    assert q.z == pytest.approx(0.0)


def test_from_mat4():
    test = Quaternion.from_mat4(Mat4.rotate_x(45.0))
    assert test.s == pytest.approx(0.92388, rel=1e-3)
    assert test.x == pytest.approx(0.38268, rel=1e-3)
    assert test.y == pytest.approx(0.0)
    assert test.z == pytest.approx(0.0)
    test = Quaternion.from_mat4(Mat4.rotate_y(45.0))
    assert test.s == pytest.approx(0.92388, rel=1e-3)
    assert test.x == pytest.approx(0.0)
    assert test.y == pytest.approx(0.38268, rel=1e-3)
    assert test.z == pytest.approx(0.0)
    test = Quaternion.from_mat4(Mat4.rotate_z(45.0))
    assert test.s == pytest.approx(0.92388, rel=1e-3)
    assert test.x == pytest.approx(0.0)
    assert test.y == pytest.approx(0.0)
    assert test.z == pytest.approx(0.38268, rel=1e-3)

    # The following tests add coverage for each of the paths in the code
    # +2.179450 [-0.344124i,+0.688247j,-0.344124k]
    matrix = Mat4.from_list(list(range(1, 17)))

    quat = Quaternion.from_mat4(matrix)
    assert quat.s == pytest.approx(2.179450)
    assert quat.x == pytest.approx(-0.344123, rel=1e-3)
    assert quat.y == pytest.approx(0.688247)
    assert quat.z == pytest.approx(-0.34412, rel=1e-3)

    # +1.802776 [+0.000000i,+0.000000j,+0.000000k]
    # +0.000000 [+2.236068i,+0.223607j,+0.223607k]
    matrix = Mat4.from_list([-1.0, 1, 1, 1, 1, -10, 1, 1, 1, 1, -10, 1, 1, 1, 1, 1])

    quat = Quaternion.from_mat4(matrix)
    assert quat.s == pytest.approx(0)
    assert quat.x == pytest.approx(2.236068)
    assert quat.y == pytest.approx(0.223607)
    assert quat.z == pytest.approx(0.223607)
    # +0.185695i,+2.692582j,+0.185695k
    matrix = Mat4.from_list([-20.0, 1, 1, 1, 1, -10, 1, 1, 1, 1, -18, 1, 1, 1, 1, 1])

    quat = Quaternion.from_mat4(matrix)
    assert quat.s == pytest.approx(0)
    assert quat.x == pytest.approx(0.185695, rel=1e-3)
    assert quat.y == pytest.approx(2.692582, rel=1e-3)
    assert quat.z == pytest.approx(0.185695, rel=1e-3)

    # +0.000000 +0.208514i,+0.208514j,+2.397916k
    matrix = Mat4.from_list([-20.0, 1, 1, 1, 1, -10, 1, 1, 1, 1, -8, 1, 1, 1, 1, 1])

    quat = Quaternion.from_mat4(matrix)
    assert quat.s == pytest.approx(0)
    assert quat.x == pytest.approx(0.208514, rel=1e-3)
    assert quat.y == pytest.approx(0.208514, rel=1e-3)
    assert quat.z == pytest.approx(2.397916, rel=1e-3)


def test_addition():
    a = Quaternion(0.5, 1.0, 0.0, 0.0)
    b = Quaternion(0.2, 0.0, 1.0, 0.0)
    c = a + b
    assert c.s == pytest.approx(0.7)
    assert c.x == pytest.approx(1.0, rel=1e-3)
    assert c.y == pytest.approx(1.0, rel=1e-3)
    assert c.z == pytest.approx(0.0, rel=1e-3)


def test_plus_equal():
    a = Quaternion(0.5, 1.0, 0.0, 0.0)
    b = Quaternion(0.2, 0.0, 1.0, 0.0)
    a += b
    assert a.s == pytest.approx(0.7)
    assert a.x == pytest.approx(1.0, rel=1e-3)
    assert a.y == pytest.approx(1.0, rel=1e-3)
    assert a.z == pytest.approx(0.0, rel=1e-3)


def test_subtraction():
    a = Quaternion(0.5, 1.0, 0.0, 0.0)
    b = Quaternion(0.2, 0.0, 1.0, 0.0)
    c = a - b
    assert c.s == pytest.approx(0.3)
    assert c.x == pytest.approx(1.0, rel=1e-3)
    assert c.y == pytest.approx(-1.0, rel=1e-3)
    assert c.z == pytest.approx(0.0, rel=1e-3)


def test_minus_equal():
    a = Quaternion(0.5, 1.0, 0.0, 0.0)
    b = Quaternion(0.2, 0.0, 1.0, 0.0)
    a -= b
    assert a.s == pytest.approx(0.3)
    assert a.x == pytest.approx(1.0, rel=1e-3)
    assert a.y == pytest.approx(-1.0, rel=1e-3)
    assert a.z == pytest.approx(0.0, rel=1e-3)


# from https://www.wolframalpha.com/input/?i=quaternion+-Sin%5BPi%5D%2B3i%2B4j%2B3k+multiplied+by+-1j%2B3.9i%2B4-3k
# (-sin(π) + 3i + 4j + 3k) × (4 + 3.9i -1j -3k)
# 1.3 + 3 i + 36.7 j - 6.6 k


def test_multiply():
    a = Quaternion(0.0, 3.0, 4.0, 3.0)
    b = Quaternion(4.0, 3.9, -1.0, -3.0)
    c = a * b
    # 1.3000000000000007, 3.0, 36.7, -6.600000000000001 from Julia Quat package
    assert c.s == pytest.approx(1.3, rel=1e-3)
    assert c.x == pytest.approx(3.0, rel=1e-3)
    assert c.y == pytest.approx(36.7, rel=1e-3)
    assert c.z == pytest.approx(-6.6, rel=1e-3)


def test_str_repr():
    quat = Quaternion(1.0, 2.0, 3.0, 4.0)
    assert str(quat) == "Quaternion(1.0, [2.0, 3.0, 4.0])"
    assert repr(quat) == "Quaternion(1.0, [2.0, 3.0, 4.0])"
