# distutils: language = c++

cimport cython
from cython.operator cimport dereference as deref, preincrement as inc

cimport robots.engine_c.core
from robots.engine_c.core cimport Vec2, Bullet, Robot, ROBOT_RADIUS, rand_float

from libc.math cimport sin, cos, abs, pi, pow
from libcpp.set cimport set as c_set
from libcpp.vector cimport vector
from libcpp.list cimport list as c_list
from libc.time cimport time,time_t


ctypedef Bullet* BulletPtr


cdef bint test_circle_to_circle(const Vec2 c1, float r1, const Vec2 c2, float r2) :
    return (c1 - c2).pow(2).sum() <= pow((r1 + r2),2)


cdef class PyBullet:
    """
    Needed for rendering bullets.
    Maybe swap to a list of tuples...
    """
    cdef BulletPtr c_bullet

    @property
    def position(self):
        return self.c_bullet.position.x, self.c_bullet.position.y

    @property
    def velocity(self):
        return self.c_bullet.velocity.x, self.c_bullet.velocity.y

    @staticmethod
    cdef PyBullet from_c(Bullet* c_bullet):
        bullet:PyBullet = PyBullet()
        bullet.c_bullet = c_bullet
        return bullet

    def __repr__(self):
        return f"Bullet<{<long>self.c_bullet}>({self.position})"


cdef class PyRobot:
    cdef Robot c_robot

    def __init__(self, base_color, turret_color=None, radar_color=None):
        self.base_color = base_color
        self.turret_color = turret_color if turret_color is not None else base_color
        self.radar_color = radar_color if radar_color is not None else base_color

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
        return self.c_robot.position.x, self.c_robot.position.y

    @property
    def velocity(self):
        return self.c_robot.velocity

    @property
    def acceleration(self):
        return self.c_robot.acceleration()

    @property
    def base_rotation(self):
        return self.c_robot.base_rotation

    @property
    def turret_rotation(self):
        return self.c_robot.turret_rotation

    @property
    def radar_rotation(self):
        return self.c_robot.radar_rotation

    @property
    def energy(self):
        return self.c_robot.energy

    @property
    def energy_pctg(self):
        return self.c_robot.energy/100
    
    @property
    def heat_pctg(self):
        return self.c_robot.heat/(1+3/5)

    def fire(self, float fire_power):
        self.c_robot.fire_power: float = fire_power
        self.c_robot.should_fire:bint = True

    cpdef run(self):
        pass
    
    def __repr__(self):
        return f"PyRobot(energy={self.energy}, position={self.position},velocity={self.velocity}"\
            f",acceleration={self.acceleration},base_rotation={self.base_rotation})"


cdef bint cirle_oob(const Vec2& c,const float r,const Vec2& size):
    # print(c.x,c.y, size.x,size.y, (r < c.x) ,(c.x < size.x - r) ,(r < c.y) ,(c.y < size.x - r))
    return not ((r < c.x) & (c.x < size.x - r) & (r < c.y) & (c.y < size.y - r))


cdef class Engine:
    cdef Vec2 size
    cdef readonly list robots
    cdef readonly set bullets

    def __init__(self, list robots, tuple size=(600,400), rate=-1 ):
        if robots is None:
            raise ValueError()
        self.size:Vec2 = Vec2(size[0], size[1])
        self.robots = robots

    def __cinit__(self):
        self.bullets = set()

    def is_finished(self):
        return False

    cpdef void init_robots(self):
        for py_robot in self.robots:
            ptr_robot: &Robot = &((<PyRobot>py_robot).c_robot)
            ptr_robot.position = Vec2(rand_float(0,600), rand_float(0,400))
            print(py_robot)

    cdef void collide_bullets(self):
        for py_bullet in self.bullets.copy():
            p_bullet: BulletPtr = ((<PyBullet>py_bullet).c_bullet)

            if cirle_oob(p_bullet.position, 3, self.size):
                print(f"Bullet {py_bullet} collided with wall.")
                self.bullets.remove(py_bullet)
                del p_bullet

            for py_robot in self.robots:
                ptr_robot: &Robot = &((<PyRobot>py_robot).c_robot)
                if p_bullet.owner.uid != ptr_robot.uid:
                    if test_circle_to_circle(ptr_robot.position, ROBOT_RADIUS, p_bullet.position, 3):
                        print(f"Bullet collided {py_robot}, {py_bullet}")
                        power: float = p_bullet.power
                        damage: float = 4 * power + ((power >= 1) * 2 * (power - 1))
                        ptr_robot.energy -= damage
                        self.bullets.remove(py_bullet)
                        del p_bullet
                        break
            
    def step(self):
        self.collide_bullets()
        for py_bullet in self.bullets:
            p_bullet : BulletPtr = (<PyBullet>py_bullet).c_bullet
            p_bullet.step()

        for py_robot in self.robots:
            p_robot: &Robot = &(<PyRobot>py_robot).c_robot
            p_robot.step()
            
            if cirle_oob(p_robot.position, 20, self.size):
                print(f"Robot {py_robot} collided with wall.")

            py_robot.run()
            # Need to do robot update here for the bullet to be added to bullets
            if p_robot.should_fire and (p_robot.heat <= 0.0):
                p_bullet: BulletPtr = p_robot.fire()
                self.bullets.add(PyBullet.from_c(p_bullet))

    