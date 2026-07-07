import numpy as np
import pytest

from ncca.ngl import Mat4, Quaternion, Vec3


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


def test_subtraction():
    a = Quaternion(0.5, 1.0, 0.0, 0.0)
    b = Quaternion(0.2, 0.0, 1.0, 0.0)
    c = a - b
    assert c.s == pytest.approx(0.3)
    assert c.x == pytest.approx(1.0, rel=1e-3)
    assert c.y == pytest.approx(-1.0, rel=1e-3)
    assert c.z == pytest.approx(0.0, rel=1e-3)


# from https://www.wolframalpha.com/input/?i=quaternion+-Sin%5BPi%5D%2B3i%2B4j%2B3k+multiplied+by+-1j%2B3.9i%2B4-3k
# (-sin(π) + 3i + 4j + 3k) × (4 + 3.9i -1j -3k)
# 1.3 + 3 i + 36.7 j - 6.6 k


def test_multiply():
    a = Quaternion(0.0, 3.0, 4.0, 3.0)
    b = Quaternion(4.0, 3.9, -1.0, -3.0)
    c = a @ b
    # 1.3000000000000007, 3.0, 36.7, -6.600000000000001 from Julia Quat package
    assert c.s == pytest.approx(1.3, rel=1e-3)
    assert c.x == pytest.approx(3.0, rel=1e-3)
    assert c.y == pytest.approx(36.7, rel=1e-3)
    assert c.z == pytest.approx(-6.6, rel=1e-3)


def test_str_repr():
    quat = Quaternion(1.0, 2.0, 3.0, 4.0)
    assert str(quat) == "Quaternion(1.0, [2.0, 3.0, 4.0])"
    assert repr(quat) == "Quaternion(1.0, 2.0, 3.0, 4.0)"


def test_from_axis_angle():
    axis = Vec3(1.0, 0.0, 0.0)
    angle = np.pi / 2.0
    # from_axis angle works in degrees
    quat = Quaternion.from_axis_angle(axis, np.degrees(angle))
    assert quat.s == pytest.approx(np.cos(angle / 2.0), rel=1e-3)
    assert quat.x == pytest.approx(np.sin(angle / 2.0), rel=1e-3)
    assert quat.y == pytest.approx(0.0, rel=1e-3)
    assert quat.z == pytest.approx(0.0, rel=1e-3)


def test_mult_vec3():
    # Rotating (0, 0, 1) by 90 degrees about the Y axis should give (1, 0, 0).
    axis = Vec3(0.0, 1.0, 0.0)
    angle = 90.0
    quat = Quaternion.from_axis_angle(axis, angle)
    vec = Vec3(0.0, 0.0, 1.0)
    result = quat * vec
    assert result.x == pytest.approx(1.0, abs=1e-6)
    assert result.y == pytest.approx(0.0, abs=1e-6)
    assert result.z == pytest.approx(0.0, abs=1e-6)


def test_matmul_product():
    a = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 90.0)
    b = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), -90.0)
    assert a @ b == Quaternion(1.0, 0.0, 0.0, 0.0)


def test_mul_quaternion_raises():
    with pytest.raises(TypeError):
        Quaternion() * Quaternion()


def test_inverse():
    q = Quaternion.from_axis_angle(Vec3(1.0, 0.0, 0.0), 30.0)
    assert q @ q.inverse() == Quaternion(1.0, 0.0, 0.0, 0.0)


def test_slerp_endpoints():
    a = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 0.0)
    b = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 90.0)
    assert a.slerp(b, 0.0) == a
    assert a.slerp(b, 1.0) == b


def test_to_mat4_round_trip():
    q = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 45.0)
    assert Quaternion.from_mat4(q.to_mat4()) == q


def test_contract():
    q = Quaternion(1.0, 0.5, 0.25, 0.125)
    assert eval(repr(q)) == q


def test_matmul_rejects_non_quaternion():
    with pytest.raises(TypeError, match="requires a Quaternion"):
        Quaternion() @ 5


def test_mul_rejects_unsupported_type():
    with pytest.raises(TypeError, match="cannot multiply Quaternion"):
        Quaternion() * "not a quaternion"


def test_rmul_rejects_unsupported_type():
    with pytest.raises(TypeError, match="cannot multiply"):
        "not a quaternion" * Quaternion()


def test_rmul_scalar_matches_mul():
    q = Quaternion(1.0, 2.0, 3.0, 4.0)
    assert 2.0 * q == q * 2.0


def test_truediv_rejects_non_scalar():
    with pytest.raises(TypeError, match="cannot divide Quaternion"):
        Quaternion() / "not a scalar"


def test_getitem_out_of_range_raises():
    q = Quaternion()
    with pytest.raises(IndexError):
        q[4]
    with pytest.raises(IndexError):
        q[-1]


def test_normalized_zero_length_raises():
    q = Quaternion(0.0, 0.0, 0.0, 0.0)
    with pytest.raises(ZeroDivisionError):
        q.normalized()


def test_inverse_zero_quaternion_raises():
    q = Quaternion(0.0, 0.0, 0.0, 0.0)
    with pytest.raises(ZeroDivisionError):
        q.inverse()


def test_dot():
    a = Quaternion(1.0, 0.0, 0.0, 0.0)
    b = Quaternion(0.0, 1.0, 0.0, 0.0)
    assert a.dot(b) == pytest.approx(0.0)
    assert a.dot(a) == pytest.approx(1.0)


def test_slerp_takes_shortest_path_for_opposite_hemisphere():
    a = Quaternion(1.0, 0.0, 0.0, 0.0)
    b = Quaternion(-1.0, 0.0, 0.0, 0.0)  # negative dot with a

    result = a.slerp(b, 0.0)

    assert result == a


def test_slerp_near_identical_quaternions_uses_linear_interpolation():
    a = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 10.0)
    b = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 10.0001)

    result = a.slerp(b, 0.5)

    assert result.length() == pytest.approx(1.0, abs=1e-4)


def test_set_updates_all_components():
    q = Quaternion()
    q.set(0.5, 1.0, 2.0, 3.0)
    assert q == Quaternion(0.5, 1.0, 2.0, 3.0)


def test_from_list_wrong_length_raises():
    with pytest.raises(ValueError, match="requires 4 values"):
        Quaternion.from_list([1.0, 2.0, 3.0])


def test_from_numpy_wrong_shape_raises():
    with pytest.raises(ValueError, match="requires shape"):
        Quaternion.from_numpy(np.zeros(3))


def test_equal_with_non_quaternion_is_not_implemented():
    assert (Quaternion() == "not a quaternion") is False


def test_not_equal_with_non_quaternion_is_true():
    assert Quaternion() != "not a quaternion"


def test_component_setter_rejects_non_numeric():
    q = Quaternion()
    with pytest.raises(ValueError, match="need float or int"):
        q.x = "not a number"


def test_component_setter_accepts_numeric():
    q = Quaternion()
    q.x = 0.5
    assert q.x == pytest.approx(0.5)
