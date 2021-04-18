
from dataclasses import dataclass
from robots.robot.utils import *
import random
from robots.engine.utils import test_circle_to_circles, test_circles
import numpy as np
from robots.robot.utils import Turn, Move
from robots.config import *
from robots.robot.events import *
import time


class RobotData(object):
    def __init__(self, robot):
        self.robot = robot

        # Physical quantities
        self.energy = 0
        self.alive = False
        self.velocity = 0.0
        self.position = None
        self.base_rotation = None
        self.turret_rotation = 0
        self.radar_rotation = 0
        self.turret_heat = 0

        self.base_rotation_velocity = 0.0
        self.turret_rotation_velocity = 0.0
        self.radar_rotation_velocity = 0.0


    def flush_state(self):
        """Push read only values back to the Robot class"""
        self.robot.energy = self.energy
        self.robot.position = self.position
        self.robot.velocity = self.velocity
        self.robot.turret_heat = self.turret_heat

        self.robot.base_rotation_velocity = self.base_rotation_velocity
        self.robot.turret_rotation_velocity = self.turret_rotation_velocity
        self.robot.radar_rotation_velocity = self.radar_rotation_velocity

        self.robot.bearing = self.base_rotation
        self.robot.turret_bearing = self.turret_rotation
        self.robot.radar_bearing = self.radar_rotation


@dataclass
class Bullet:
    robot_data: RobotData
    position: np.ndarray
    velocity: float
    power: int

    def __hash__(self) -> int:
        return id(self)


def acceleration(r):
    if r.velocity > 0.0:
        if r.robot.moving == Move.FORWARD:
            return 1.0
        else:
            return -2.0
    elif r.velocity < 0.0:
        if r.robot.moving == Move.BACK:
            return -1.0
        else:
            return 2.0
    elif r.robot.moving is not Move.NONE:
        return 1.0
    else:
        return 0.0


class Engine(object):
    def __init__(self, robots, size, bullet_self_collisions=True, rate=-1):
        self.robots = robots
        self.size = size

        # Collision settings
        self.bullet_self_collisions = bullet_self_collisions
        self.robot_collisions = True

        # Stores
        self.data = None
        self.bullets = set()
        self.interval = 1/rate
        self.next_sim = 0
        offset = ROBOT_RADIUS + 4
        self.bounds = (offset, offset), (self.size[0] - offset, self.size[1] - offset)

    def set_rate(self, rate):
        self.interval = 1/rate

    def init(self):
        self.data = [RobotData(robot) for robot in self.robots]
        self.bullets.clear()
        for r in self.data:
            r.position = np.random.random(2) * self.size
            r.base_rotation = random.random() * 360
            r.turret_rotation = r.base_rotation
            r.radar_rotation = r.base_rotation
            r.energy = 100
            r.alive = True
        self.flush_robot_state()

    def run(self):
        while not self.is_finished():
            if time.time() > self.next_sim:
                self.next_sim = time.time() + self.interval
                self.step()

    def step(self):
        self.update_robots()
        self.flush_robot_state()

    def add_bullet(self, robot_data, position, velocity, power):
        self.bullets.add(Bullet(robot_data, position, velocity, power))

    def is_finished(self):
        return sum(r.alive for r in self.data) <= 1

    def flush_robot_state(self):
        for data in self.data:
            data.flush_state()

    def update_robots(self):
        robots = np.array([r for r in self.data if r.alive])
        cs = np.stack([r.position for r in self.data if r.alive])
        rs = np.ones(len(cs)) * ROBOT_RADIUS
        wall_colisions = ~np.all(((20, 20) <= cs) & (cs <= np.array(self.size) - (20, 20)), 1)
        for r in robots[wall_colisions]:
            r.energy -= max(abs(r.velocity) * 0.5 - 1, 0)
            r.velocity = 0.0
            r.position = np.clip(r.position + r.velocity, *self.bounds)

        # Robot to Robot collisions
        for i, r1 in enumerate(robots):
            colls = test_circle_to_circles(r1.position, ROBOT_RADIUS, cs, rs)
            colls = np.delete(robots, i)[np.delete(colls, i)]
            for r2 in colls:
                r1.energy -= 0.6
                r2.energy -= 0.6
                norm = r1.position - r2.position
                if np.sum(norm) == 0:
                    norm = np.array([0.0, 1.0])
                norm = (norm / np.sum(norm ** 2)) * 15
                r1.position = r1.position + norm
                r2.position = r2.position - norm
                r1.velocity = 0
                r2.velocity = 0

                r1.robot.on_hit_robot(HitRobotEvent(r2.robot))
                r2.robot.on_hit_robot(HitRobotEvent(r1.robot))

        # COLLIDE SCANS HERE

        bullets = list(self.bullets)
        if len(bullets) > 1:
            cs = np.array([b.position for b in bullets])
            where = np.argwhere(np.any(test_circles(cs, np.array([3])), 0))
            to_remove = [bullets[idx] for idx in where.flatten().tolist()]
            self.bullets.difference_update(to_remove)

        for bullet in self.bullets:
            bullet.position += bullet.velocity

        # Collide bullets
        for i, r in enumerate(robots):
            events = []
            bullets = [(b, b.position) for b in self.bullets if b.robot_data is not r]
            if bullets:
                bs, cs = zip(*bullets)
                bs, cs = np.stack(bs), np.stack(cs)

                colls = test_circle_to_circles(r.position, ROBOT_RADIUS, cs, 3)
                for bullet in bs[colls]:
                    # Damage calculation
                    damage = 4 * bullet.power
                    if bullet.power > 1:
                        damage += 2 * (bullet.power - 1)
                    r.energy -= damage
                    bullet.robot_data.energy += 3 * bullet.power
                    self.bullets.remove(bullet)
                    events.append(HitByBulletEvent(damage))
                if events:
                    r.robot.on_hit_by_bullet(events)

        for i, r in enumerate(robots):
            # Update robots actions
            base_rotation_rads = r.base_rotation * np.pi / 180
            direction = np.array([np.sin(base_rotation_rads), np.cos(base_rotation_rads)])
            r.velocity = np.clip(r.velocity + acceleration(r), -8.0, 8.0)
            r.position = r.position + (r.velocity * direction)

            r.base_rotation_velocity = (10 - 0.75 * abs(r.velocity)) * r.robot.base_turning.value
            r.base_rotation = (r.base_rotation + r.base_rotation_velocity) % 360

            # TODO add locked turret
            turret_rotation_rads = r.turret_rotation * np.pi / 180
            r.turret_rotation_velocity = 20 * r.robot.turret_turning.value + r.base_rotation_velocity
            r.turret_rotation = (r.turret_rotation + r.turret_rotation_velocity) % 360
            r.turret_heat = np.maximum(0.0, r.turret_heat - 0.1)

            # TODO add locked radar
            r.radar_rotation_velocity = 5 * r.robot.radar_turning.value + r.turret_rotation_velocity
            r.radar_rotation = (r.radar_rotation + r.radar_rotation_velocity) % 360

            # Should fire and can fire
            if r.robot.should_fire and (r.turret_heat <= 0.0):
                fire_power = r.robot.fire_power
                r.turret_heat = 1 + fire_power / 5
                r.energy = np.maximum(0.0, r.energy - fire_power)
                r.robot.should_fire = False
                turret_direction = np.array([np.sin(turret_rotation_rads), np.cos(turret_rotation_rads)])
                bullet_position = r.position + (turret_direction * 30)
                self.add_bullet(r,
                                bullet_position,
                                turret_direction * (20 - (3 * fire_power)),
                                max(min(MAX_POWER, fire_power), MIN_POWER))

        for r in self.data:
            r.turret_heat = max(r.turret_heat - 0.1, 0)
            if r.energy > 0:
                r.robot.run()
            else:
                r.alive = False
