# distutils: language = c++

cimport cython
from cython.operator cimport dereference as deref, preincrement as inc

cimport robots.engine_c.core
from robots.engine_c.core cimport Vec2, Bullet, Robot, ROBOT_RADIUS, rand_float, rand_seed

from libc.math cimport sin, cos, abs, pi, pow, pi
from libcpp.set cimport set as c_set
from libcpp.vector cimport vector
from libcpp.list cimport list as c_list
from libc.time cimport time,time_t
from cpython.ref cimport PyObject


ctypedef Bullet* BulletPtr
ctypedef Robot* RobotPtr

rand_seed()

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

    def __cinit__(self):
        self.c_robot = Robot()
        self.c_robot.scripted_robot = <PyObject*>self

    def __init__(self, base_color, turret_color=None, radar_color=None):
        self.base_color = base_color
        self.turret_color = turret_color if turret_color is not None else base_color
        self.radar_color = radar_color if radar_color is not None else base_color
    
    def init(self,*args, **kwargs):
        pass

    def stop(self):
        self.moving = 0
        self.base_turning = 0
        self.turret_turning = 0

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
    def speed(self):
        return self.c_robot.speed

    @property
    def acceleration(self):
        return self.c_robot.get_acceleration()

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
    
    cpdef on_hit_robot(self, robot):
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(energy={self.energy}, position={self.position},speed={self.speed}"\
            f",acceleration={self.acceleration},base_rotation={self.base_rotation})"


cdef bint cirle_oob(const Vec2& c,const float r,const Vec2& size):
    return not ((r < c.x) & (c.x < size.x - r) & (r < c.y) & (c.y < size.y - r))


cdef class Engine:
    cdef Vec2 size
    cdef readonly list robots
    cdef readonly set bullets

    def __init__(self, list robots, tuple size=(600,400), rate=-1 ):
        self.size:Vec2 = Vec2(size[0], size[1])
        self.robots = robots
        # Cleaned in init
        self.bullets = set()

    def is_finished(self) -> bool:
        alive: int = 0
        for py_robot in self.robots:
            p_robot: &Robot = &(<PyRobot>py_robot).c_robot
            if p_robot.energy > 0:
                alive += 1
        return alive <= 1

    cpdef init(self, robot_kwargs=None):
        self.bullets.clear()

        robot_kwargs = {} if robot_kwargs is None else robot_kwargs
        for py_robot in self.robots:
            ptr_robot: &Robot = &((<PyRobot>py_robot).c_robot)
            # Init with random positions
            ptr_robot.energy = 100
            ptr_robot.position = Vec2(rand_float(0,600), rand_float(0,400))
            ptr_robot.base_rotation = rand_float(0,1) * pi * 2
            ptr_robot.turret_rotation = rand_float(0,1) * pi * 2
            ptr_robot.radar_rotation = ptr_robot.turret_rotation

            # Call the init on the pyrobo
            py_robot.init()

    

    cdef void collide_bullets(self):
        for py_bullet in self.bullets.copy():
            p_bullet: BulletPtr = ((<PyBullet>py_bullet).c_bullet)

            if cirle_oob(p_bullet.position, 3, self.size):
                self.bullets.remove(py_bullet)
                del p_bullet
                continue

            for py_robot in self.robots:
                ptr_robot: &Robot = &((<PyRobot>py_robot).c_robot)
                if p_bullet.owner.uid != ptr_robot.uid:
                    if test_circle_to_circle(ptr_robot.position, ROBOT_RADIUS, p_bullet.position, 3):
                        # print(f"Bullet collided {py_robot}, {py_bullet}")
                        power: float = p_bullet.power
                        damage: float = 4 * power + ((power >= 1) * 2 * (power - 1))
                        ptr_robot.energy -= damage
                        self.bullets.remove(py_bullet)
                        del p_bullet
                        break
    
    cdef handle_wall_collision(self, p_robot: RobotPtr):
        p_robot.speed = 0.0
        p_robot.energy -= max(abs(p_robot.speed) * 0.5 - 1, 0)
        p_robot.position.clip(Vec2(28.0), self.size - 28)

    def step(self):
        self.collide_bullets()
        for py_bullet in self.bullets:
            p_bullet : BulletPtr = (<PyBullet>py_bullet).c_bullet
            p_bullet.step()

        for r1 in self.robots:
            p_robot1: &Robot = &(<PyRobot>r1).c_robot 
            for r2 in self.robots:
                p_robot2: &Robot = &(<PyRobot>r2).c_robot

                if p_robot1 == p_robot2:
                    continue
                elif test_circle_to_circle(p_robot1.position, ROBOT_RADIUS, p_robot2.position, ROBOT_RADIUS):
                    p_robot1.energy -= 0.6
                    p_robot2.energy -= 0.6
                    p_robot1.speed = 0.0
                    p_robot2.speed = 0.0

                    n: Vec2 = p_robot1.position - p_robot2.position
                    if n.sum() == 0:
                        n = Vec2(0.0,1.0)
                    n = n/n.len()
                    
                    p_robot1.position = p_robot1.position + n
                    p_robot2.position = p_robot2.position - n
                    r1.on_hit_robot(r2)
                    r2.on_hit_robot(r1)

        for py_robot in self.robots:
            p_robot: &Robot = &(<PyRobot>py_robot).c_robot
            if p_robot.energy > 0:
                p_robot.step()
                
                if cirle_oob(p_robot.position, 20, self.size):
                    self.handle_wall_collision(p_robot)

                py_robot.run()

                if p_robot.should_fire and (p_robot.heat <= 0.0):
                    p_bullet: BulletPtr = p_robot.fire()
                    self.bullets.add(PyBullet.from_c(p_bullet))

                p_robot.heat = max(0, p_robot.heat - 0.1)

