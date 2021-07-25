# distutils: language = c++

cimport cython
cimport robots.engine_c.core
from robots.engine_c.core cimport Vec2, Bullet

from libc.math cimport sin, cos, abs, pi, pow
from libcpp.set cimport set
from libc.stdlib cimport malloc, free
from uuid import uuid4

cdef float BASE_ROTATION_VELOCITY_RADS = 5/180 * pi
cdef float BASE_ROTATION_VELOCITY_DEC_RADS = 0.75/180 * pi
cdef float TURRET_ROTATION_VELOCITY_RADS = 5/180 * pi
cdef float RADAR_ROTATION_VELOCITY_RADS = 5/180 * pi

cdef float BULLET_MAX_POWER = 3.0
cdef float BULLET_MIN_POWER = 0.1
cdef float ROBOT_RADIUS = 24

cdef long ROBOT_COUNT = 0


cdef float clip(float val, float low, float high):
    return min(max(val, low), high)


cdef void clip_Vec2(Vec2 point, float x_low, float y_low, float x_high, float y_high):
    point.x = clip(point.x, x_low, x_high)
    point.y = clip(point.y, y_low, y_high)


cdef Vec2 rads_to_Vec2(float rads):
    return Vec2(cos(rads), sin(rads))


cdef bint test_circle_to_circle(const Vec2 c1, float r1, const Vec2 c2, float r2) :
    return (c1 - c2).pow(2).sum() <= pow((r1 + r2),2)


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

        self.c_robot.
    
    @property
    def uid(self):
        return self.c_robot.uid
    

cdef class Robot:
    cdef:
        readonly long uid
        float energy
        float velocity
        Vec2 position
        float base_rotation
        float turret_rotation
        float radar_rotation
        float heat

        public int moving
        public int base_turning
        public int turret_turning
        public int radar_turning
        public bint should_fire
        public int fire_power

    def __cinit__(self):
        global ROBOT_COUNT
        self.uid = ROBOT_COUNT
        ROBOT_COUNT += 1
        self.energy = 100.0
        self.velocity = 0.0
        self.heat = 0.0
        self.position = Vec2(0.0,0.0)
        self.base_rotation = 0.0
        self.turret_rotation = 0.0
        self.radar_rotation = 0.0

        self.moving = 1
        self.base_turning = 1
        self.fire_power = 1
        self.should_fire = True

    cdef void step(self):
        direction = rads_to_Vec2(self.base_rotation)
        self.position.x = self.position.x + direction.x
        self.position.y = self.position.y + direction.y
        
        self.velocity = clip(self.velocity + self.acceleration(), -8.0, 8.0)
        
        # Rotations
        base_rotation_velocity:float = max(0, (BASE_ROTATION_VELOCITY_RADS - BASE_ROTATION_VELOCITY_DEC_RADS * abs(self.velocity))) * self.base_turning
        self.base_rotation += base_rotation_velocity
        turret_rotation_velocity:float  = TURRET_ROTATION_VELOCITY_RADS * self.turret_turning + base_rotation_velocity
        self.turret_rotation += turret_rotation_velocity
        radar_rotation_velocity:float  = RADAR_ROTATION_VELOCITY_RADS * self.radar_turning + turret_rotation_velocity
        self.radar_rotation += radar_rotation_velocity

    cdef Bullet* fire(self):
        self.heat = 1.0 + self.fire_power/5.0
        self.energy = max(<float>0.0, self.energy - self.fire_power)
        self.should_fire = False
        turret_direction: Vec2 = rads_to_Vec2(self.turret_rotation)
        ptr_bullet: &Bullet = <Bullet*> malloc(sizeof(Bullet))
        ptr_bullet[0] = Bullet(
            self.uid,
            self.position +  turret_direction * 30.0, 
            turret_direction * (20.0 - (3.0 * self.fire_power)),
            max(min(BULLET_MAX_POWER, self.fire_power), BULLET_MIN_POWER)
        )
        return ptr_bullet 


    cdef float acceleration(self):
        if self.velocity > 0.0:
            if self.moving > 0:
                return 1.0
            else:
                return -2.0
        elif self.velocity < 0.0:
            if self.moving < 0:
                return -1.0
            else:
                return 2.0
        elif abs(self.moving) > 0:
            return 1.0
        else:
            return 0.0

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
            robot: Robot = <Robot>self.robots[i]
            for bullet in self.c_bullets:
                # if bullet.ptr_owner[0] != robot:
                #     if test_circle_to_circle(robot.position, ROBOT_RADIUS, bullet.position, 3):
                #         power = ptr_bullet[0].power
                #         damage: float = 4 * power + ((power >= 1) * 2 * (power - 1))
                #         robot.energy -= damage

                #         self.bullets.erase(ptr_bullet)
                #         free(ptr_bullet)
                pass
            #print(f"{<unsigned long>ptr_bullet[0].position.x}")
        

    def step(self):
        self.collide_bullets()
        for i in range(len(self.robots)):
            robot = <Robot>self.robots[i]
            # Need to do robot update here for the bullet to be added to bullets
            robot.step()
            if robot.should_fire and (robot.heat <= 0.0):
                bullet:&Bullet = robot.fire()
                # print(f"{<unsigned long>ptr_bullet}")
                self.c_bullets.insert(bullet)

            clip_Vec2(robot.position, 0.0, 0.0, self.size.x, self.size.y)
            
            robot.heat = max(robot.heat - 0.1, 0.0)

    def get_bullets(self):
        return None
        for b in self.bullets:
            print(b) 

    @property
    def bullets(self):
        return [PyBullet.from_c(bullet) for bullet in self.c_bullets]
