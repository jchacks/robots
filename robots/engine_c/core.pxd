# distutils: language = c++

cimport cython
from cpython.ref cimport PyObject


from libc.math cimport sin, cos, abs, pi, pow
from libcpp.set cimport set
from libc.stdlib cimport malloc, free
from uuid import uuid4

cdef extern from "vec2.h" nogil:
    cdef cppclass Vec2:
        float x,y
        Vec2() except +
        Vec2(float, float) except +
        Vec2(float) except +
        @staticmethod
        Vec2 random(float, float)
        Vec2 pow(float)
        float sum()
        float len()
        void clip(Vec2, Vec2)
        void clip(float,float,float,float)
        Vec2 operator+(Vec2)
        Vec2 operator-(Vec2)
        Vec2 operator-(float)
        Vec2 operator*(float)
        Vec2 operator/(float)
        # Vec2 &operator+=(Vec2)
    float rand_float(float, float)
    float rand_seed()
    float rand_seed(unsigned int)
    

cdef extern from "vec2.cpp":
    pass


cdef extern from "core.h" nogil:
    cdef cppclass Bullet:
        Robot* owner
        Vec2 position, velocity
        float power
        Bullet()
        Bullet(long, Vec2, Vec2, float)
        void step()
    
    cdef cppclass Robot:
        PyObject* scripted_robot
        unsigned long uid
        int moving, base_turning, turret_turning, radar_turning
        float energy, fire_power, speed, heat, base_rotation, turret_rotation, radar_rotation
        bint should_fire
        Vec2 position
        Robot()
        void step()
        Vec2 get_velocity()
        float get_acceleration()
        Bullet* fire()
    
    cdef float ROBOT_RADIUS
    cdef float PI_2f32



cdef extern from "core.cpp":
    pass

