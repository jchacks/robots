import numpy as np

from robots import SignalRobot
from robots.robot.utils import Move, Turn

class OrnsteinUhlenbeckActionNoise:
    def __init__(self, mu, sigma=0.3, theta=.15, dt=1e-2, x0=None):
        self.theta = theta
        self.mu = mu
        self.sigma = sigma
        self.dt = dt
        self.x0 = x0
        self.reset()

    def __call__(self):
        x = self.x_prev + self.theta * (self.mu - self.x_prev) * self.dt + \
            self.sigma * np.sqrt(self.dt) * np.random.normal(size=self.mu.shape)
        self.x_prev = x
        return x

    def reset(self):
        self.x_prev = self.x0 if self.x0 is not None else np.zeros_like(self.mu)

    def __repr__(self):
        return 'OrnsteinUhlenbeckActionNoise(mu={}, sigma={})'.format(self.mu, self.sigma)


class AiRobot(SignalRobot):
    def on_init(self):
        self.call_model = OrnsteinUhlenbeckActionNoise(np.zeros(5))
        self.scans = []

    def do(self, tick):
        scan = self.scans[0]

        data = np.array([
            scan.bearing,
            scan.distance,
            scan.heading,
            scan.velocity,
            *self.position,
            self.bearing,
            self.energy
        ])

        out = self.call_model()

        # Move Robot
        if out.move > 0.1:
            self.moving = Move.FORWARD
        elif out.move < -0.1:
            self.moving = Move.BACK
        else:
            self.moving = Move.NONE
        # Turn Robot
        if out.turn > 0.1:
            self.turning = Turn.RIGHT
        elif out.turn < -0.1:
            self.turning = Turn.LEFT
        else:
            self.turning = Turn.NONE
        # Turn Robot
        if out.gun_turn > 0.1:
            self.gun_turning = Turn.RIGHT
        elif out.gun_turn < -0.1:
            self.gun_turning = Turn.LEFT
        else:
            self.gun_turning = Turn.NONE
        # Turn Robot
        if out.radar_turn > 0.1:
            self.radar_turning = Turn.RIGHT
        elif out.radar_turn < -0.1:
            self.radar_turning = Turn.LEFT
        else:
            self.radar_turning = Turn.NONE

        if out.fire > 0.1:
            self.set_fire(out.fire)

    def on_scanned_robot(self, event):
        self.scans.append(event)

