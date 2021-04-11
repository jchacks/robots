import random
from robots.robot.utils import test_circle_to_circles
import numpy as np
from typing import List
from abc import ABC
from robots.robot.utils import Turn, Move
from robots.config import BULLET_RADIUS, MAX_SPEED, ROBOT_RADIUS
from robots.robot.events import *
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


class BattleSpec(object):
    def __init__(self, robots: list, size, rounds) -> None:
        self.robots = robots


@nb.extending.overload(np.clip)
def np_clip(a, a_min, a_max, out=None):
    def np_clip_impl(a, a_min, a_max, out=None):
        shape = a.shape
        if out is None:
            out = np.empty_like(a)
        a = a.flatten()
        for i in range(len(a)):
            if a[i] < a_min:
                out[i] = a_min
            elif a[i] > a_max:
                out[i] = a_max
            else:
                out[i] = a[i]
        out = out.reshape(shape)
        return out
    return np_clip_impl


@nb.njit
def wall_collision_check(size, position):
    min_size = np.array((20, 20), np.float32)
    max_size = size - min_size
    comp = np.less_equal(min_size, position) & np.less_equal(position, max_size)
    return ~(comp[:, 0] & comp[:, 1])


@nb.njit
def update(
    size,
    bounds,
    dead_mask,
    moving,
    base_turning,
    turret_turning,
    radar_turning,
    fire_power,
    energy,
    position,
    speed,
    base_rotation,
    turret_rotation,
    radar_rotation,
    turret_heat,
    bullet_mask,
    bullet_positions,
    bullet_direction,
    bullet_power,
    bullet_owner,
):
    """
    Tick update:
        * Position
        * Speed
        * Rotation
    :param tick: Tick of the simulation
    :return: None
    """
    # Calculate acceleration
    a = np.zeros_like(speed, np.float32)

    sign_move = np.sign(moving)
    sign_speed = np.sign(speed)
    sign = sign_move * sign_speed
    accel_mask = sign > 0
    decel_mask = sign < 0

    a[accel_mask] = 1 * sign_move[accel_mask]
    a[decel_mask] = 2 * sign_move[decel_mask]

    # Only for alive robots
    # Update speed with acceleration and 0 energy cant move
    speed[~dead_mask] = speed[~dead_mask] + a[~dead_mask]
    speed = np.clip(speed, MAX_SPEED[0], MAX_SPEED[1])
    speed[energy == 0.0] = 0.0

    # Calculate velocity vec and apply to center
    base_rotation_rads = base_rotation[~dead_mask] * np.pi
    velocity = np.column_stack((np.sin(base_rotation_rads), np.cos(base_rotation_rads))) * speed[~dead_mask]
    position[~dead_mask] = position[~dead_mask] + velocity

    # Wall collision
    collided = wall_collision_check(size, position)
    collided = collided & (~dead_mask)

    position[:, 0] = np.clip(position[:, 0], bounds[0][0], bounds[1][0])
    position[:, 1] = np.clip(position[:, 1], bounds[0][1], bounds[1][1])
    energy[collided] -= np.maximum(np.abs(speed[collided]) * 0.5 - 1, 0)
    speed[collided] = 0
    collided_robots_idx = np.where(collided)[0]

    # Caclulate rotation (in rads excluding pi)
    base_rotation_speed = (10 - 0.75 * np.abs(speed[~dead_mask])) / 180
    base_rotation_delta = base_rotation_speed * base_turning[~dead_mask]
    base_rotation[~dead_mask] = (base_rotation[~dead_mask] + base_rotation_delta) % 2

    # Turret delta
    # Turret rotation (in rads excluding pi)
    turret_rotation_speed = 20/180
    # TODO add locked turret
    turret_rotation_delta = turret_rotation_speed * turret_turning[~dead_mask] + base_rotation_delta
    turret_rotation[~dead_mask] = (turret_rotation[~dead_mask] + turret_rotation_delta) % 2
    turret_heat[~dead_mask] = np.maximum(0.0, turret_heat[~dead_mask] - 0.1)

    # Radar rotation (in rads excluding pi)
    radar_rotation_speed = 5/180
    # TODO add locked turret
    radar_rotation_delta = radar_rotation_speed * radar_turning[~dead_mask] + turret_rotation_delta
    radar_rotation[~dead_mask] = (radar_rotation[~dead_mask] + radar_rotation_delta) % 2

    # Fire
    fire_mask = (fire_power > 0) & (~dead_mask) & (turret_heat <= 0.0)
    robot_idx = np.where(fire_mask)[0]
    energy[fire_mask] = np.maximum(0.0, energy[fire_mask] - fire_power[fire_mask])

    turret_rotation_rads = turret_rotation[fire_mask] * np.pi
    turret_direction = np.stack((np.sin(turret_rotation_rads), np.cos(turret_rotation_rads)), axis=-1)
    bullet_position = position[fire_mask] + (turret_direction * 28)
    power = fire_power[fire_mask]

    # Assigning bullets to store
    number_bullets = np.sum(fire_mask)
    free_slots = ~bullet_mask
    free_slots[number_bullets:] = False

    bullet_mask[free_slots] = True
    bullet_owner[free_slots] = robot_idx
    bullet_power[free_slots] = power
    bullet_positions[free_slots] = bullet_position
    bullet_direction[free_slots] = turret_direction

    # Move bullets TODO move before the creation of new bullets
    bullet_speeds = np.expand_dims((20 - (3 * bullet_power[bullet_mask])), 1)
    bullet_positions[bullet_mask] += bullet_direction[bullet_mask] * bullet_speeds

    # Collide bullets and robots
    # position[~dead_mask]

    # bullet_idx = np.where(bullet_mask)[0]
    bullet_positions = bullet_positions[bullet_mask]

    where_alive = np.where(~dead_mask)[0]
    # Vectorise this?
    for i, center in zip(where_alive, position[~dead_mask]):
        not_owned = (bullet_owner != i)[bullet_mask]
        colls = test_circle_to_circles(center, ROBOT_RADIUS, bullet_positions[not_owned], BULLET_RADIUS)
        # Update date the masks to just collisions
        colls = colls & not_owned
        bullet_mask[colls] = False
        energy[i] -= np.sum(4 * bullet_power[colls])

        # np.arr with positions of owners who hit
        energy[bullet_owner[colls]] += 3 * bullet_power[colls]

        # Reset bullet data
        bullet_power[colls] = 0
        bullet_owner[colls] = 0
        bullet_positions[colls] = 0
        bullet_direction[colls] = 0

    return collided_robots_idx


class Engine(object):
    """Tracks robots for simulation"""

    def __init__(self, robots) -> None:
        self.size = np.array((400, 400))
        offset = ROBOT_RADIUS + 4
        self.bounds = (np.array([offset, offset]),
                       np.array([self.size[0] - offset, self.size[1] - offset]))

        self.num_robots = num_robots = len(robots)
        self.robots: List[Robot] = robots

        self.bullets: List[tuple] = []
        self.dead_mask = np.zeros((num_robots,), np.bool)

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
        self.position[:] = np.random.random((self.num_robots, 2)) * self.size
        self.base_rotation[:] = np.random.random((self.num_robots, )) * 2

    @ property
    def where_alive(self):
        return np.where(~self.dead_mask)[0]

    def update_data(self):
        self.dead_mask = dead_mask = self.energy < 0.0
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

    def update_robots(self, collided_robots_idx):
        for i, (robot, dead) in enumerate(zip(self.robots, self.dead_mask)):
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
            self.robots[i].on_hit_wall(HitWallEvent())

    def step(self):
        self.update_data()
        print("Running update")
        data = update(
            self.size,
            self.bounds,
            self.dead_mask,
            self.moving,
            self.base_turning,
            self.turret_turning,
            self.radar_turning,
            self.fire_power,
            self.energy,
            self.position,
            self.speed,
            self.base_rotation,
            self.turret_rotation,
            self.radar_rotation,
            self.turret_heat,
            self.bullet_mask,
            self.bullet_positions,
            self.bullet_direction,
            self.bullet_power,
            self.bullet_owner
        )
        print(self.position[0], self.speed)
        self.update_robots(data)


if __name__ == "__main__":
    from robots.renderers import RobotRenderer

    class RandomRobot(Robot):
        def run(self):
            self.moving = Move.FORWARD
            self.base_turning = Turn.LEFT
            if random.randint(0, 1):
                self.fire(random.randint(1, 3))

    eng = Engine([RandomRobot((255, 0, 0)), RandomRobot((0, 255, 0))])
    eng.init()
    for i in range(10000):
        print(i)
        eng.step()
