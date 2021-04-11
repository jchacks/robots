import random
from robots.robot.utils import test_circle_to_circles
import numpy as np
from typing import List
from abc import ABC
from robots.robot.utils import Turn, Move
from robots.config import BULLET_RADIUS, MAX_SPEED, ROBOT_RADIUS
import numba as nb


class Robot(ABC):
    def __init__(self, base_color, turret_color=None, radar_color=None) -> None:
        super(Robot, self).__init__()
        # Attributes are set by engine.
        self.energy = 100
        self.position = None
        self.bearing = None
        self.turret_bearing = None
        self.radar_bearing = None
        self.speed = 0.0
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
        print("pew pew")


class BattleSpec(object):
    def __init__(self, robots: list, size, rounds) -> None:
        self.robots = robots


class Engine(object):
    """Tracks robots for simulation"""

    def __init__(self, robots) -> None:
        self.size = (400, 400)
        offset = ROBOT_RADIUS + 4
        self.bounds = (offset, offset), (self.size[0] - offset, self.size[1] - offset)

        self.num_robots = num_robots = len(robots)
        self.robots: List[Robot] = robots
        self.bullets: List[tuple] = []

        # Desired actions
        self.moving = np.zeros((num_robots, ), np.int8)
        self.base_turning = np.zeros((num_robots, ), np.int8)
        self.turret_turning = np.zeros((num_robots, ), np.int8)
        self.radar_turning = np.zeros((num_robots, ), np.int8)
        self.fire_power = np.zeros((num_robots, ), np.uint8)

        # Physical quantities
        self.energy = np.zeros((num_robots,), np.float32)
        self.position = np.zeros((num_robots, 2), np.float32)
        self.speed = np.zeros((num_robots,), np.float32)
        self.base_rotation = np.zeros((num_robots,), np.float32)
        self.turret_rotation = np.zeros((num_robots,), np.float32)
        self.radar_rotation = np.zeros((num_robots,), np.float32)
        self.turret_heat = np.zeros((num_robots,), np.float32)

        # Bullets
        self.bullet_mask = np.zeros((1000, ), np.bool)
        self.bullet_positions = np.zeros((1000, 2), np.float32)
        self.bullet_direction = np.zeros((1000, 2), np.float32)
        self.bullet_power = np.zeros((1000, ), np.float32)
        self.bullet_owner = np.zeros((1000, ), np.uint8)

    def init(self):
        self.energy[:] = 100
        self.position[:] = np.random.random((self.num_robots, 2)) * self.bounds
        self.base_rotation[:] = np.random.random((self.num_robots, )) * 2

    def update(self):
        """
        Tick update:
            * Position
            * Speed
            * Rotation
        :param tick: Tick of the simulation
        :return: None
        """

        # Update dead
        dead_mask = self.energy < 0.0
        where_alive = np.where(~dead_mask)[0]

        self.speed[dead_mask] = 0.0
        self.moving[dead_mask] = 0
        self.base_turning[dead_mask] = 0
        self.turret_turning[dead_mask] = 0
        self.radar_turning[dead_mask] = 0
        self.fire_power[dead_mask] = 0

        # For each robot update the state
        for i, (robot, dead) in enumerate(zip(self.robots, dead_mask)):
            if not dead:
                # Call the desired action
                robot.run()
                # Assign into arrays the desired actions
                self.moving[i] = robot.moving.value
                self.base_turning[i] = robot.base_turning.value
                self.turret_turning[i] = robot.turret_turning.value
                self.radar_turning[i] = robot.radar_turning.value
                self.fire_power[i] = robot.should_fire * np.clip(robot.fire_power, 0.1, 3.0)
            else:
                robot.dead = True

        # Only for alive robots
        # Update speed with acceleration and 0 energy cant move

        a = np.zeros((self.num_robots,))
        sign_move = np.sign(self.moving)
        sign_speed = np.sign(self.speed)
        sign = sign_move * sign_speed
        accel_mask = sign > 0
        decel_mask = sign < 0
        a[accel_mask] = 1 * sign_move[accel_mask]
        a[decel_mask] = 2 * sign_move[decel_mask]

        self.speed[~dead_mask] = np.clip(self.speed[~dead_mask] + a[~dead_mask], *MAX_SPEED)
        self.speed[self.energy == 0.0] = 0.0

        # Calculate velocity vec and apply to center
        base_rotation_rads = self.base_rotation[~dead_mask] * np.pi
        velocity = np.stack([np.sin(base_rotation_rads), np.cos(base_rotation_rads)], axis=-1) * self.speed[~dead_mask]
        self.position[~dead_mask] = self.position[~dead_mask] + velocity

        # Wall collision
        collided = ~np.all(((20, 20) <= self.position) & (self.position <= np.array(self.size) - (20, 20)), axis=1)
        collided = collided & (~dead_mask)

        self.position = np.clip(self.position, *self.bounds)
        self.energy[collided] -= np.maximum(np.abs(self.speed[collided]) * 0.5 - 1, 0)
        self.speed[collided] = 0
        collided_robots_idx = np.where(collided)[0]

        # Caclulate rotation (in rads excluding pi)
        base_rotation_speed = (10 - 0.75 * abs(velocity)) / 180
        base_rotation_delta = base_rotation_speed * self.base_turning[~dead_mask]
        self.base_rotation[~dead_mask] = (self.base_rotation[~dead_mask] + base_rotation_delta) % 2

        # Turret delta
        # Turret rotation (in rads excluding pi)
        turret_rotation_speed = 20/180
        # TODO add locked turret
        turret_rotation_delta = turret_rotation_speed * self.turret_turning[~dead_mask] + base_rotation_delta
        self.turret_rotation[~dead_mask] = (self.turret_rotation[~dead_mask] + turret_rotation_delta) % 2
        self.turret_heat[~dead_mask] = np.maximum(0.0, self.turret_heat[~dead_mask] - 0.1)

        # Radar rotation (in rads excluding pi)
        radar_rotation_speed = 5/180
        # TODO add locked turret
        radar_rotation_delta = radar_rotation_speed * self.radar_turning[~dead_mask] + turret_rotation_delta
        self.radar_rotation[~dead_mask] = (self.radar_rotation[~dead_mask] + radar_rotation_delta) % 2

        # Fire
        fire_mask = (self.fire_power > 0) & (~dead_mask) & (self.turret_heat <= 0.0)
        robot_idx = np.where(fire_mask)[0]
        self.energy[fire_mask] = np.maximum(0.0, self.energy[fire_mask] - self.fire_power)

        turret_rotation_rads = self.turret_rotation[fire_mask] * np.pi
        turret_direction = np.stack([np.sin(turret_rotation_rads), np.cos(turret_rotation_rads)], axis=-1)
        bullet_position = self.position[fire_mask] + (turret_direction * 28)
        power = self.fire_power[fire_mask]

        # Assigning bullets to store
        number_bullets = np.sum(fire_mask)
        free_slots = ~self.bullet_mask
        free_slots[number_bullets:] = False

        if np.sum(free_slots) < number_bullets:
            raise RuntimeError("Need more bullet slots")

        self.bullet_mask[free_slots] = True
        self.bullet_owner[free_slots] = robot_idx
        self.bullet_power[free_slots] = power
        self.bullet_positions[free_slots] = bullet_position
        self.bullet_direction[free_slots] = turret_direction

        # Move bullets TODO move before the creation of new bullets
        self.bullet_positions[self.bullet_mask] += self.bullet_direction[self.bullet_mask] * \
            (20 - (3 * self.bullet_power[self.bullet_mask]))

        # Collide bullets and robots
        self.position[~dead_mask]

        bullet_idx = np.where(self.bullet_mask)[0]
        bullet_positions = self.bullet_positions[self.bullet_mask]

        # Vectorise this?
        for i, center in zip(where_alive, self.position[~dead_mask]):
            not_owned = (self.bullet_owner != i) & self.bullet_mask
            colls = test_circle_to_circles(center, ROBOT_RADIUS, bullet_positions[not_owned], BULLET_RADIUS)
            # Update date the masks to just collisions
            colls = colls & not_owned
            self.bullet_mask[colls] = False
            self.energy[i] -= np.sum(4 * self.bullet_power[colls])

            # np.arr with positions of owners who hit
            self.energy[self.bullet_owner[colls]] += 3 * self.bullet_power[colls]

            # Reset bullet data
            self.bullet_power[colls] = 0
            self.bullet_owner[colls] = 0
            self.bullet_positions[colls] = 0
            self.bullet_direction[colls] = 0

        for i, (robot, dead) in enumerate(zip(self.robots, dead_mask)):
            if not dead:
                # Assign into objects the outcomes
                robot.energy = self.energy[i]
                robot.position = self.position[i]
                robot.bearing = self.base_rotation[i]
                robot.turret_bearing = self.turret_rotation[i]
                robot.radar_bearing = self.radar_rotation[i]
                robot.speed = self.speed[i]
                robot.should_fire = False

        # Call events
        for i in collided_robots_idx:
            self.robots[i].on_hit_wall()


if __name__ == "__main__":
    class RandomRobot(Robot):
        def run(self):
            self.moving = Move.FORWARD
            self.base_turning = Turn.LEFT
            if random.randint(0, 1):
                self.fire(random.randint(1, 3))

    eng = Engine([RandomRobot((255, 0, 0)), RandomRobot((0, 255, 0))])
    eng.init()
    eng.update()
