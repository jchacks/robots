from abc import ABC, abstractmethod

from pygame.sprite import OrderedUpdates

from events import *
from parts import *
from utils import Move, LogicalObject


class Robot(LogicalObject, ABC):
    def __init__(self, app, center, bearing=0.0):
        LogicalObject.__init__(self, center, bearing)
        self.app = app
        self.center = np.array(center, np.float64)
        self.bearing = bearing
        self.dead = False
        self._speed = 0.0

        self.draw_bbs = True
        self.radar = Radar(self)
        self.gun = Gun(self)
        self.base = Base(self)

        self.should_fire = False
        self.fire_power = 3

    def on_init(self):
        self.energy = 100
        self._group = OrderedUpdates(self.base, self.gun, self.radar)
        self.commands = False
        self.left_to_move = 0.0
        self.left_to_turn = 0.0
        self.radar.on_init()
        self.gun.on_init()
        self.base.on_init()

    def _do(self):
        if not self.commands:
            self.do()
            self.commands = True

    @abstractmethod
    def do(self):
        pass

    @abstractmethod
    def on_scanned(self, event):
        pass

    @abstractmethod
    def on_hit_robot(self, event):
        pass

    @abstractmethod
    def on_hit_by_bullet(self, event):
        pass

    @property
    def moving(self):
        if self.left_to_move > 0:
            return Move.FORWARD
        elif self.left_to_move < 0:
            return Move.BACK
        else:
            return Move.NONE

    @property
    def turning(self):
        if self.left_to_turn > 0:
            return Turn.LEFT
        elif self.left_to_turn < 0:
            return Turn.RIGHT
        else:
            return Turn.NONE

    def update_logic(self):
        if not self.dead:
            if self.energy < 0.0:
                self.destroy()
            else:
                self._do()

                self._speed = np.clip(self._speed + self.acceleration, -8.0, 8.0)
                self.left_to_move = max(0, self.left_to_move - self._speed)

                self.center = np.clip(self.center + self.velocity, [0, 0], self.app.size)

                self.bearing = self.get_delta_bearing(self.turning.value)
                self.left_to_turn = max(0, self.left_to_turn - self.rotation_speed)

                self.base.delta()
                self.gun.delta()
                self.radar.delta()
                # print(self._speed, self.center, self.rotation, self.gun.rotation, self.radar.rotation)
                if self.should_fire:
                    self._fire(self.fire_power)

        if self.moving is Move.NONE and self.turning is Turn.NONE:
            self.commands = False

    @property
    def velocity(self):
        return self.direction * self._speed

    def destroy(self):
        self.base.clean_up()
        self._group.empty()
        self.dead = True

    def fire(self, firepower):
        self.should_fire = True
        self.fire_power = firepower

    def _fire(self, firepower):
        if self.gun.heat == 0:
            Bullet(self, firepower)
            self.gun.heat = 1 + firepower / 5
            self.energy -= firepower
            self.should_fire = False

    @property
    def rotation_speed(self):
        return (10 - 0.75 * abs(self._speed)) * float(self.turning.value)

    @property
    def acceleration(self):
        if self._speed > 0:
            if self.moving == Move.FORWARD:
                return 1.0
            else:
                return -2.0
        elif self._speed < 0:
            if self.moving == Move.BACK:
                return -1.0
            else:
                return 2.0
        elif self.moving is not Move.NONE:
            return 1.0
        else:
            return 0.0

    def move_forward(self, dist: float):
        self.left_to_move = dist

    def turn_left(self, angle: float):
        self.left_to_turn = angle

    def _draw(self, surface):
        if not self.dead:
            self._group.update()
            self._group.draw(surface)
            self.radar.draw(surface)
            if self.draw_bbs:
                self.base.draw_coll(surface)
                self.draw_debug(surface)
        self.draw()

    def draw_debug(self, surface):
        pygame.draw.circle(surface, (255, 0, 255), self.center.astype(int), 2)
        pygame.draw.line(surface, (255, 0, 255), self.center.astype(int),
                         (self.center + (self.direction * 10)).astype(int), 1)

    def draw(self):
        pass

    def collide_bullets(self):
        events = []
        if not self.dead:
            bases_colls = {bullet: bullet.rect for bullet in Bullet.class_group}
            hits = self.base.coll.collidedictall(bases_colls)
            for bullet, coll in hits:
                if not bullet.robot is self:
                    self.energy -= bullet.damage
                    bullet.robot.energy += 3 * bullet.power
                    bullet.clean_up()
                    events.append(HitByBulletEvent(bullet))
        if events:
            self.on_hit_by_bullet(events)

    # TODO test this removing clipping from
    def collide_wall(self):
        if not self.dead:
            if not self.app.rect.contains(self.base.coll):
                self.center += -self.velocity
                offset = max(self.base.coll.w, self.base.coll.h)
                bounds = (offset, offset), (self.app.size[0] - offset, self.app.size[1] - offset)
                self.center = np.clip(self.center + self.velocity, *bounds)
                self.energy -= max(abs(self._speed) * 0.5 - 1, 0)
                self._speed = 0

    def collide_robots(self):
        if not self.dead:
            bases_colls = {base: base.coll for base in Base.class_group}
            base, coll = self.base.coll.collidedict(bases_colls)
            if not base is self.base:
                self.energy -= 0.6
                base.robot.energy -= 0.6
                norm = (self.center - base.robot.center)
                norm = (norm / np.sum(norm ** 2)) * 10
                self.center = self.center + norm
                base.robot.center = base.robot.center - norm

    def collide_scan(self, robots):
        scanned = []
        if not self.dead:
            for robot in robots:
                if robot is not self and not robot.dead:
                    if self.radar.intersect_scan(robot.base.coll):
                        scanned.append(ScannedRobotEvent(robot))
        if scanned:
            self.on_scanned(scanned)
