import numba as nb
import numpy as np

__all__ = [
    "rot_center",
    "scale_image",
    "load_image",
    "test_segment_circle",
    "test_circle_to_circles",
    "test_circles",
]


class Vector(object):
    def __init__(
        self,
        item_shape,
        initial_size=10,
        dtype="float32",
        mask=None,
    ):
        if mask is True:
            self.initial_size = initial_size
            self._mask = np.zeros(initial_size, dtype="bool")
        else:
            self._mask = mask
            self.initial_size = mask.shape[0]

        self.item_shape = item_shape
        self.dtype = dtype
        self._data = np.zeros((initial_size, *item_shape), dtype=self.dtype)

    @property
    def data(self):
        return self._data[self._mask]

    @data.setter
    def data(self, new_data):
        self._data[self._mask] = new_data

    def append(self, item):
        if not (~self._mask).any():
            self._mask = np.concatenate([self._mask, np.zeros(self.initial_size, dtype="bool")])
            self._data = np.concatenate([self._data, np.zeros((self.initial_size, *self.item_shape), dtype=self.dtype)])
        pos = np.argmin(self._mask)
        self._data[pos] = item
        self._mask[pos] = True
        return pos

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        self._mask[key] = False

    def __mul__(self, other):
        return self.data * other

    def __add__(self, other):
        return self.data + other

    def __truediv__(self, other):
        return self.data / other


@nb.njit
def test_segment_circle(start, stop, center, radius):
    """
    Test the collision of a line segment with a circle
    :param start: start of line segment (x,y)
    :param stop: stop of line segment (x,y)
    :param center:
    :param radius:
    :return:
    """
    start = start - center
    stop = stop - center
    a = np.sum((stop - start) ** 2)
    b = 2 * np.sum(start * (stop - start))
    c = np.sum(start ** 2) - radius ** 2
    disc = b ** 2 - 4 * a * c
    if disc <= 0:
        return False
    sqrtdisc = np.sqrt(disc)
    t1 = (-b + sqrtdisc) / (2 * a)
    t2 = (-b - sqrtdisc) / (2 * a)
    if ((0 < t1) and (t1 < 1)) or ((0 < t2) and (t2 < 1)):
        return True
    return False


@nb.njit
def test_circle_circle(c1, c2, r1, r2):
    """
    Test the collision of two circles
    :param c1: Numpy Array (2,) center of circle1
    :param c2: Numpy Array (2,) center of circle2
    :param r1: radius of circle1
    :param r2: radius of circle2
    :return: Boolean value of the test
    """
    return np.sum((c1 - c2) ** 2) <= (r1 + r2) ** 2


@nb.njit
def test_circles(cs, rs):
    """
    Test collision of all circles against each other.
    :param cs: Numpy Array (n,2) of circle centers
    :param rs: Numpy Array (n,) of circle radii
    :return:
    """
    distances = np.sum((np.expand_dims(cs, 1) - np.expand_dims(cs, 0)) ** 2, axis=2)
    radius_diffs = (np.expand_dims(rs, 1) + np.expand_dims(rs, 0)) ** 2
    bool_in = distances <= radius_diffs
    return bool_in ^ np.identity(len(cs), nb.bool_)


@nb.njit
def test_circle_to_circles(c, r, cs, rs):
    """
    Test collision of a 'single' circle to multiple 'other' circles.
    :param c: Center of single circle
    :param r: Radius of single circle
    :param cs: Numpy Array (n,2) of other circles centers
    :param rs: Numpy Array (n,) of other circles radii
    :return: Boolean Array of collisions
    """
    return np.sum((c - cs) ** 2, axis=1) <= (r + rs) ** 2

