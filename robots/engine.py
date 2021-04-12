
from dataclasses import dataclass
from robots.robot.utils import *
import random
from robots.robot.utils import test_circle_to_circles
import numpy as np
from typing import List
from abc import ABC
from robots.robot.utils import Turn, Move
from robots.config import *
from robots.robot.events import *


class Robot(ABC):
    def __init__(self, base_color, turret_color=None, radar_color=None) -> None:
        # Attributes are set by engine.
        self.energy = 100
        self.position = None
        self.bearing = None
        self.turret_bearing = None
        self.radar_bearing = None
        self.velocity = 0.0
        self.dead = False

        # Set by user and read by engine.
        self.base_color = base_color
        self.turret_color = turret_color if turret_color is not None else base_color
        self.radar_color = radar_color if radar_color is not None else base_color

        self.should_fire = False
        self.fire_power = 3
        self.moving = Move.NONE
        self.base_turning = Turn.NONE
        self.turret_turning = Turn.NONE
        self.radar_turning = Turn.NONE

    def run(self):
        pass

    def fire(self, power):
        self.fire_power = power
        print("pew pew")

    def on_battle_ended(self, event: BattleEndedEvent):
        pass

    def on_bullet_hit_bullet(self, event: BulletHitBulletEvent):
        pass

    def on_bullet_hit(self, event: BulletHitEvent):
        pass

    def on_bullet_missed(self, event: BulletMissedEvent):
        pass

    def on_custom_event(self, event: CustomEvent):
        pass

    def on_death(self, event: DeathEvent):
        pass

    def on_hit_by_bullet(self, event: List[HitByBulletEvent]):
        pass

    def on_hit_robot(self, event: HitRobotEvent):
        pass

    def on_hit_wall(self, event: HitWallEvent):
        pass

    def on_key(self, event: KeyEvent):
        pass

    def on_message(self, event: MessageEvent):
        pass

    def on_paint(self, event: PaintEvent):
        pass

    def on_robot_death(self, event: RobotDeathEvent):
        pass

    def on_round_ended(self, event: RoundEndedEvent):
        pass

    def on_scanned_robot(self, event: List[ScannedRobotEvent]):
        pass

    def on_skipped_turn(self, event: SkippedTurnEvent):
        pass

    def on_status(self, event: StatusEvent):
        pass

    def on_win(self, event: WinEvent):
        pass


class RobotData(object):
    def __init__(self, robot):
        self.robot = robot
        self.moving = Move.NONE
        self.base_turning = Turn.NONE
        self.turret_turning = Turn.NONE
        self.radar_turning = Turn.NONE
        self.fire_power = 0

        # Physical quantities
        self.energy = 0
        self.alive = False
        self.velocity = 0.0
        self.position = None
        self.base_rotation = None
        self.turret_rotation = 0
        self.radar_rotation = 0
        self.turret_heat = 0


@dataclass
class Bullet:
    robot: Robot
    position: np.ndarray
    velocity: float
    power: int


def acceleration(r):
    if r.velocity > 0.0:
        if r.moving == Move.FORWARD:
            return 1.0
        else:
            return -2.0
    elif r.velocity < 0.0:
        if r.moving == Move.BACK:
            return -1.0
        else:
            return 2.0
    elif r.moving is not Move.NONE:
        print("Shouldnt happen", r.moving, r.velocity)
        return 1.0
    else:
        return 0.0


class Engine(object):
    def __init__(self, robots, size):
        self.data = [RobotData(robot) for robot in robots]
        self.bullets = set()
        self.size = size
        offset = ROBOT_RADIUS + 4
        self.bounds = (offset, offset), (size[0] - offset, size[1] - offset)

    def init(self):
        for r in self.data:
            r.position = np.random.random(2) * self.size
            r.base_rotation = np.random.random(1) * 2
            r.energy = 100
            r.alive = True

    def add_bullet(self, robot, position, velocity, power):
        self.bullets.add(Bullet(robot, position, velocity, power))

    def update(self):
        robots = np.array([r for r in self.data if r.alive])
        cs = np.stack([r.position for r in self.data if r.alive])
        rs = np.ones(len(cs)) * ROBOT_RADIUS
        wall_colisions = ~np.all(((20, 20) <= cs) & (cs <= np.array(self.size) - (20, 20)), 1)
        for r in robots[wall_colisions]:
            r.energy -= max(abs(r.velocity) * 0.5 - 1, 0)
            r.velocity = 0.0
            r.position = np.clip(r.position + r.velocity, *self.bounds)

        for i, r1 in enumerate(robots):
            colls = test_circle_to_circles(r1.position, ROBOT_RADIUS, cs, rs)
            colls = np.delete(robots, i)[np.delete(colls, i)]
            for r2 in colls:
                r1.energy -= 0.6
                r2.energy -= 0.6
                norm = r1.center - r2.center
                if np.sum(norm) == 0:
                    norm = np.array([0.0, 1.0])
                norm = (norm / np.sum(norm ** 2)) * 15
                r1.center = r1.center + norm
                r2.center = r2.center - norm
                r1._speed = 0
                r2._speed = 0

                r1.robot.on_hit_robot(HitRobotEvent(r2.robot))
                r2.robot.on_hit_robot(HitRobotEvent(r1.robot))

        # COLLIDE SCANS HERE

        bullets = list(self.bullets)
        if len(bullets) > 1:
            cs = np.array([b.center for b in bullets])
            rs = np.array([b.radius for b in bullets])
            where = np.argwhere(np.any(test_circles(cs, rs), 0))
            to_remove = [bullets[idx] for idx in where.flatten().tolist()]
            self.bullets.difference_update(to_remove)

        for bullet in self.bullets.copy():
            bullet.position += bullet.velocity

        # Collide bullets
        for i, r in enumerate(robots):
            events = []
            bullets = [(b, b.center, b.radius) for b in self.bullets if b.robot is not r]
            if bullets:
                bs, cs, rs = zip(*bullets)
                bs, cs, rs = np.stack(bs), np.stack(cs), np.stack(rs)

                colls = test_circle_to_circles(r.center, r.radius, cs, rs)
                for bullet in bs[colls]:
                    # Damage calculation
                    damage = 4 * bullet.power 
                    if bullet.power > 1:
                        damage += 2 * (bullet.power - 1)

                    r.energy -= bullet.damage
                    bullet.robot += 3 * bullet.power
                    self.bullets.remove(bullet)
                    events.append(HitByBulletEvent(bullet))
                if events:
                    r.robot.on_hit_by_bullet(events)


        for i, r in enumerate(robots):
            r.velocity = np.clip(r.velocity + acceleration(r), -8.0, 8.0)
            r.position = r.position + r.velocity

            base_rotation_delta = ((10 - 0.75 * abs(r.velocity)) / 180) * r.base_turning.value
            r.base_rotation = (r.base_rotation + base_rotation_delta) % 2

            turret_rotation_velocity = 20/180
            # TODO add locked turret
            turret_rotation_delta = turret_rotation_velocity * r.turret_turning.value + base_rotation_delta
            r.turret_rotation = (r.turret_rotation + turret_rotation_delta) % 2
            r.turret_heat = np.maximum(0.0, r.turret_heat - 0.1)

            radar_rotation_velocity = 5/180
            # TODO add locked radar
            radar_rotation_delta = radar_rotation_velocity * r.radar_turning.value + turret_rotation_delta
            r.radar_rotation = (r.radar_rotation + radar_rotation_delta) % 2

            # Should fire and can fire
            if (r.fire_power > 0) and (r.turret_heat <= 0.0):
                r.energy = np.maximum(0.0, r.energy - r.fire_power)
                turret_rotation_rads = r.turret_rotation * np.pi
                turret_direction = np.concatenate([np.sin(turret_rotation_rads), np.cos(turret_rotation_rads)])
                bullet_position = r.position + (turret_direction * 28)
                self.add_bullet(r,
                                bullet_position,
                                turret_direction * (20 - (3 * r.fire_power)),
                                max(min(MAX_POWER, r.fire_power), MIN_POWER))


if __name__ == "__main__":
    class RandomRobot(Robot):
        def run(self):
            self.moving = Move.FORWARD
            self.base_turning = Turn.LEFT
            if random.randint(0, 1):
                self.fire(random.randint(1, 3))

    battle = Engine([
        RandomRobot((255, 0, 0)),
        RandomRobot((0, 255, 0))],
        (400, 400))
    battle.init()
    battle.update()
    print(battle.data)
