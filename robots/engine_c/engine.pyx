# distutils: language = c++

cimport cython
cimport robots.engine_c.core
from robots.engine_c.core cimport Vec2, Bullet, Robot

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
    def owner_uid(self):
        return self.c_bullet.owner_uid
    
    @property
    def uid(self):
        return self.c_bullet.uid
    
    @property
    def owner_uid(self):
        return self.c_bullet.owner_uid

    @staticmethod
    cdef PyBullet from_c(Bullet* c_bullet):
        bullet:PyBullet = PyBullet()
        bullet.c_bullet = c_bullet
        return bullet


cdef class PyRobot:
    cdef Robot c_robot

    def __cinit__(self):
        self.c_robot.position:Vec2 = Vec2(1.0,1.0)

    @property
    def position(self):
        return PyVec2.from_c(self.c_robot.position)

    cdef step(self):
        self.c_robot.step()

    def fire(self):
        self.c_robot.fire()

    def run(self):
        pass

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
        for i in range(len(self.robots)):
            robot = self.robots[i]
            # for bullet in self.c_bullets:
            #     # if bullet.ptr_owner[0] != robot:
            #     #     if test_circle_to_circle(robot.position, ROBOT_RADIUS, bullet.position, 3):
            #     #         power = ptr_bullet[0].power
            #     #         damage: float = 4 * power + ((power >= 1) * 2 * (power - 1))
            #     #         robot.energy -= damage

            #     #         self.bullets.erase(ptr_bullet)
            #     #         free(ptr_bullet)
            #     pass
            # #print(f"{<unsigned long>ptr_bullet[0].position.x}")
    
    def step(self):
        self.collide_bullets()
        for py_robot in self.robots:
            robot: Robot = (<PyRobot>py_robot).c_robot

            # Need to do robot update here for the bullet to be added to bullets
            robot.step()
            # if robot.should_fire and (robot.heat <= 0.0):
            #     bullet:&Bullet = robot.fire()
            #     # print(f"{<unsigned long>ptr_bullet}")
            #     self.c_bullets.insert(bullet)

            # clip_Vec2(robot.position, 0.0, 0.0, self.size.x, self.size.y)
            
            # robot.heat = max(robot.heat - 0.1, 0.0)

    def get_bullets(self):
        return None
        for b in self.bullets:
            print(b) 

    @property
    def bullets(self):
        return [PyBullet.from_c(bullet) for bullet in self.c_bullets]
