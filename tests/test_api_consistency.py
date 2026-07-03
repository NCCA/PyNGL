"""Conformance suite: every math class implements the shared API contract."""

import numpy as np
import pytest

from ncca.ngl import Mat2, Mat3, Mat4, Quaternion, Vec2, Vec3, Vec4

# Sample constructor args producing a distinctive, invertible value per class.
SAMPLES = {
    Vec2: (1.0, 2.0),
    Vec3: (1.0, 2.0, 3.0),
    Vec4: (1.0, 2.0, 3.0, 4.0),
    Mat2: (2.0, 0.0, 0.0, 3.0),
    Mat3: (2.0, 0.0, 0.0, 0.0, 3.0, 0.0, 0.0, 0.0, 4.0),
    Mat4: (
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
    ),
    Quaternion: (1.0, 0.5, 0.25, 0.125),
}

ALL_CLASSES = list(SAMPLES)


def make(cls):
    return cls(*SAMPLES[cls])


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_default_constructor(cls):
    assert cls() is not None


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_component_constructor(cls):
    assert make(cls) == make(cls)


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_storage_is_float32(cls):
    assert make(cls)._data.dtype == np.float32


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_copy_is_equal_and_independent(cls):
    a = make(cls)
    b = a.copy()
    assert a == b
    assert a is not b
    assert a._data is not b._data


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_to_numpy_is_a_copy(cls):
    a = make(cls)
    arr = a.to_numpy()
    arr[...] = 99.0
    assert a == make(cls)


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_numpy_round_trip(cls):
    a = make(cls)
    assert cls.from_numpy(a.to_numpy()) == a


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_list_round_trip(cls):
    a = make(cls)
    assert cls.from_list(a.to_list()) == a


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_to_tuple(cls):
    a = make(cls)
    t = a.to_tuple()
    assert isinstance(t, tuple)
    assert all(isinstance(v, float) for v in t)


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_hashable(cls):
    a = make(cls)
    assert hash(a) == hash(a.copy())
    assert a in {a.copy()}


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_eval_repr_round_trip(cls):
    a = make(cls)
    assert eval(repr(a)) == a  # noqa: S307


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_len_and_iter(cls):
    a = make(cls)
    assert len(a) > 0
    assert all(isinstance(float(v), float) for v in a)


@pytest.mark.parametrize("cls", [Vec2, Vec3, Vec4])
def test_vectors_normalized_is_pure(cls):
    a = make(cls)
    before = a.copy()
    a.normalized()
    assert a == before


@pytest.mark.parametrize("cls", [Mat2, Mat3, Mat4])
def test_matrices_transposed_is_pure(cls):
    a = make(cls)
    before = a.copy()
    a.transposed()
    a.inverse()
    assert a == before


def test_quaternion_normalized_is_pure():
    q = make(Quaternion)
    before = q.copy()
    q.normalized()
    q.conjugate()
    q.inverse()
    assert q == before
