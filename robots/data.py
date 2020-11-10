import numpy as np

from robots.robot.utils import Vector


class BulletData(object):
    def __init__(self):
        self.centers = Vector((2,), mask=True)
        self.radii = Vector((1,), mask=self.centers._mask)
        self.velocity = Vector((2,), mask=self.centers._mask)
        self.power = Vector((1,), mask=self.centers._mask)
        self.robot = Vector((1,), dtype="int16", mask=self.centers._mask)

    def add_bullet(self, owner, power, bearing):
        speed = 20 - (3 * power)
        rads = np.pi * bearing / 180
        return np.stack([speed * np.sin(rads), speed * np.cos(rads)], axis=-1)

    @property
    def damage(self):
        damage = 4 * self.power
        damage[self.power > 1] += 2 * (self.power - 1)
        return damage

    def step(self):
        pass

    def reset(self):
        pass
