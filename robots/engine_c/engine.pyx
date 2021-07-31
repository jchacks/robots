# distutils: language = c++

cimport cython
from cython.operator cimport dereference as deref, preincrement as inc

cimport robots.engine_c.core
from robots.engine_c.core cimport Vec2, Bullet, Robot, ROBOT_RADIUS, rand_float

from libc.math cimport sin, cos, abs, pi, pow
from libcpp.set cimport set
from libcpp.vector cimport vector
from libcpp.list cimport list as c_list
from libc.time cimport time,time_t


cdef bint test_circle_to_circle(const Vec2 c1, float r1, const Vec2 c2, float r2) :
    return (c1 - c2).pow(2).sum() <= pow((r1 + r2),2)


cdef class PyBullet:
    """
    Needed for rendering bullets.
    Maybe swap to a list of tuples...
    """
    cdef Bullet* c_bullet

    @property
    def position(self):
        return self.c_bullet.position.x, self.c_bullet.position.y

    @staticmethod
    cdef PyBullet from_c(Bullet* c_bullet):
        bullet:PyBullet = PyBullet()
        bullet.c_bullet = c_bullet
        return bullet

    def __repr__(self):
        return f"Bullet,{<long>self.c_bullet}>({self.position})"


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


cdef bint cirle_oob(Vec2 c, float r, Vec2 size):
    return not ((r < c.x) & (c.x < size.x - r) & (r < c.y) & (c.y < size.x - r))


cdef class Engine:
    cdef Vec2 size
    cdef readonly list robots
    cdef readonly list bullets
    # cdef c_list[Bullet] c_bullets
    cdef public float interval
    cdef public int next_sim


    def __init__(self,list robots,tuple size=(600,400), rate=-1 ):
        if robots is None:
            raise ValueError()
        self.size:Vec2 = Vec2(size[0], size[1])
        self.robots = robots
        self.interval : float = 1/rate
        self.next_sim : float = 0

    def is_finished(self):
        return False

    def set_rate(self,int rate):
        rate: float = rate
        print(f"Set rate to {rate} sims/s.")
        self.interval = 1 / rate

    cpdef void init_robots(self):
        for py_robot in self.robots:
            ptr_robot: &Robot = &((<PyRobot>py_robot).c_robot)
            ptr_robot.position = Vec2(rand_float(0,600), rand_float(0,400))

    cdef void collide_bullets(self):
        it: c_list[Bullet].iterator = self.c_bullets.begin()
        while it != self.c_bullets.end():
            bullet: Bullet = deref(it) # does this copy?
            print(PyBullet.from_c(&(deref(it))))

            if cirle_oob(bullet.position, 3, self.size):
                print(f"Bullet {PyBullet.from_c(&bullet)} collided with wall.")
                it = self.c_bullets.erase(it)
                break

            for py_robot in self.robots:
                ptr_robot: &Robot = &((<PyRobot>py_robot).c_robot)
                if bullet.owner.uid != ptr_robot.uid:
                    if test_circle_to_circle(ptr_robot.position, ROBOT_RADIUS, bullet.position, 3):
                        print(f"Bullet collided {py_robot}, {PyBullet.from_c(&bullet)}")
                        power: float = bullet.power
                        damage: float = 4 * power + ((power >= 1) * 2 * (power - 1))
                        ptr_robot.energy -= damage
                        it = self.c_bullets.erase(it)
                        break
            
            inc(it)
            
    def step(self):
        self.collide_bullets()
        it: c_list[Bullet].iterator = self.c_bullets.begin()
        while it != self.c_bullets.end():
            deref(it).step()
            inc(it)

        for py_robot in self.robots:
            robot: &Robot = &(<PyRobot>py_robot).c_robot
            robot.step()
            py_robot.run()
            # Need to do robot update here for the bullet to be added to bullets
            if robot.should_fire and (robot.heat <= 0.0):
                p_bullet: &Bullet = robot.fire()
                # self.c_bullets.push_back()
                # self.bullets.append(PyBullet.from_c(&bullet))
                pass