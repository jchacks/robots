# distutils: language = c++

cimport cython
cimport robots.engine_c.core
from robots.engine_c.core cimport Vec2, Bullet, Robot, ROBOT_RADIUS

from libc.math cimport sin, cos, abs, pi, pow
from libcpp.set cimport set


cdef bint test_circle_to_circle(const Vec2 c1, float r1, const Vec2 c2, float r2) :
    return (c1 - c2).pow(2).sum() <= pow((r1 + r2),2)


cdef class PyVec2:
    cdef Vec2 c_vec2

    @staticmethod
    cdef from_c(Vec2 c_vec2):
        py_vec2 = PyVec2()
        py_vec2.c_vec2 = c_vec2
        return py_vec2
    
    def __repr__(self):
        return f"Vec2({self.c_vec2.x},{self.c_vec2.y})"

cdef class PyBullet:
    cdef Bullet* c_bullet

    @property
    def uid(self):
        return self.c_bullet.uid
    
    @staticmethod
    cdef PyBullet from_c(Bullet* c_bullet):
        bullet:PyBullet = PyBullet()
        bullet.c_bullet = c_bullet
        return bullet


cdef class PyRobot:
    cdef Robot c_robot

    def __cinit__(self):
        self.c_robot.position:Vec2 = Vec2(1.0,1.0)

    # Writeable props
    @property
    def moving(self):
        return self.c_robot.moving
    @moving.setter
    def moving(self, moving):
        self.c_robot.moving = moving
    
    @property
    def base_turning(self):
        return self.c_robot.base_turning
    @base_turning.setter
    def base_turning(self, base_turning):
        self.c_robot.base_turning = base_turning

    @property
    def turret_turning(self):
        return self.c_robot.turret_turning
    @turret_turning.setter
    def turret_turning(self, turret_turning):
        self.c_robot.turret_turning = turret_turning

    @property
    def radar_turning(self):
        return self.c_robot.radar_turning
    @radar_turning.setter
    def radar_turning(self, radar_turning):
        self.c_robot.radar_turning = radar_turning

    # Readonly props
    @property
    def position(self):
        return PyVec2.from_c(self.c_robot.position)

    @property
    def velocity(self):
        return self.c_robot.velocity

    @property
    def acceleration(self):
        return self.c_robot.acceleration()

    @property
    def base_rotation(self):
        return self.c_robot.base_rotation

    cdef step(self):
        self.c_robot.step()

    cpdef void fire(self, float fire_power):
        self.c_robot.fire_power: float = fire_power
        self.c_robot.should_fire:bint = True

    cpdef run(self):
        pass
    
    def __repr__(self):
        return f"PyRobot(position={self.position},velocity={self.velocity}"\
            f",acceleration={self.acceleration},base_rotation={self.base_rotation})"

cdef class Engine:
    cdef Vec2 size
    cdef readonly list robots
    cdef set[Bullet*] c_bullets

    def __init__(self,tuple size=(600,400), list robots=None):
        if robots is None:
            raise ValueError()
        self.size = Vec2(size[0], size[1])
        self.robots = robots

    cdef void collide_bullets(self):
        for py_robot in self.robots:
            ptr_robot: &Robot = &((<PyRobot>py_robot).c_robot)
            for ptr_bullet in self.c_bullets:
                if ptr_bullet[0].owner[0].uid != ptr_robot[0].uid:
                    if test_circle_to_circle(ptr_robot[0].position, ROBOT_RADIUS, ptr_bullet[0].position, 3):
                        print(f"Bullet collided {py_robot}, {PyBullet.from_c(ptr_bullet)}")
                        power = ptr_bullet[0].power
                        damage: float = 4 * power + ((power >= 1) * 2 * (power - 1))
                        ptr_robot[0].energy -= damage

                        self.c_bullets.erase(ptr_bullet)
                        del ptr_bullet
    
    def step(self):
        self.collide_bullets()
        for py_robot in self.robots:
            robot: Robot = (<PyRobot>py_robot).c_robot
            robot.step()
            py_robot.run()
            # Need to do robot update here for the bullet to be added to bullets
            if robot.should_fire and (robot.heat <= 0.0):
                bullet:&Bullet = robot.fire()
                self.c_bullets.insert(bullet)

            # clip_Vec2(robot.position, 0.0, 0.0, self.size.x, self.size.y)
            
            # robot.heat = max(robot.heat - 0.1, 0.0)

    @property
    def bullets(self):
        return [PyBullet.from_c(ptr_bullet) for ptr_bullet in self.c_bullets]
