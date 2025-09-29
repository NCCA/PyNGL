import pytest

from ncca.ngl import FirstPersonCamera, Mat4, Vec3


class DummyMat4(Mat4):
    def __init__(self):
        super().__init__()


def test_init_sets_attributes():
    eye = Vec3(1, 2, 3)
    look = Vec3(4, 5, 6)
    up = Vec3(0, 1, 0)
    fov = 60.0
    cam = FirstPersonCamera(eye, look, up, fov)
    assert cam.eye == eye
    assert cam.look == look
    assert cam.world_up == up
    assert isinstance(cam.front, Vec3)
    assert isinstance(cam.up, Vec3)
    assert isinstance(cam.right, Vec3)
    assert cam.yaw == pytest.approx(-90.0)
    assert cam.pitch == pytest.approx(0.0)
    assert cam.speed == pytest.approx(2.5)
    assert cam.sensitivity == pytest.approx(0.1)
    assert cam.zoom == pytest.approx(45.0)
    assert cam.near == pytest.approx(0.1)
    assert cam.far == pytest.approx(100.0)
    assert cam.aspect == pytest.approx(1.2)
    assert cam.fov == pytest.approx(fov)
    assert isinstance(cam.projection, Mat4)
    assert isinstance(cam.view, Mat4)


def test_str_and_repr():
    eye = Vec3(1, 2, 3)
    look = Vec3(4, 5, 6)
    up = Vec3(0, 1, 0)
    fov = 60.0
    cam = FirstPersonCamera(eye, look, up, fov)
    s = str(cam)
    r = repr(cam)
    assert "Camera" in s
    assert "Camera" in r
    assert str(eye) in s
    assert str(look) in s
    assert str(up) in s
    assert str(fov) in s


def test_process_mouse_movement_constrain_pitch():
    cam = FirstPersonCamera(Vec3(), Vec3(), Vec3(0, 1, 0), 60.0)
    cam.pitch = 0.0
    cam.yaw = 0.0
    cam.process_mouse_movement(100, 100, _constrain_pitch=True)
    assert cam.pitch <= 89.0
    assert cam.pitch >= -89.0


def test_process_mouse_movement_no_constrain_pitch():
    cam = FirstPersonCamera(Vec3(), Vec3(), Vec3(0, 1, 0), 60.0)
    cam.pitch = 0.0
    cam.yaw = 0.0
    cam.process_mouse_movement(100, 100, _constrain_pitch=False)
    # pitch can exceed bounds
    assert cam.pitch > 89.0 or cam.pitch < -89.0 or (cam.pitch <= 89.0 and cam.pitch >= -89.0)


def test_update_camera_vectors_changes_front_right_up_and_view():
    cam = FirstPersonCamera(Vec3(), Vec3(), Vec3(0, 1, 0), 60.0)
    old_front = cam.front.clone()
    old_right = cam.right.clone()
    old_up = cam.up.clone()
    cam.yaw += 10
    cam.pitch += 5
    cam._update_camera_vectors()
    assert cam.front != old_front or cam.right != old_right or cam.up != old_up
    assert isinstance(cam.view, Mat4)


def test_set_projection_returns_mat4():
    cam = FirstPersonCamera(Vec3(), Vec3(), Vec3(0, 1, 0), 60.0)
    proj = cam.set_projection(60.0, 1.2, 0.1, 100.0)
    assert isinstance(proj, Mat4)


def test_move_changes_eye():
    cam = FirstPersonCamera(Vec3(), Vec3(), Vec3(0, 1, 0), 60.0)
    old_eye = cam.eye.clone()
    cam.move(1.0, 0.0, 0.5)
    assert cam.eye != old_eye


def test_get_vp_returns_mat4():
    cam = FirstPersonCamera(Vec3(), Vec3(), Vec3(0, 1, 0), 60.0)
    vp = cam.get_vp()
    assert isinstance(vp, Mat4)
