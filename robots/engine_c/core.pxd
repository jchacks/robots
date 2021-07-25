# distutils: language = c++

cimport cython
from libc.math cimport sin, cos, abs, pi, pow
from libcpp.set cimport set
from libc.stdlib cimport malloc, free
from uuid import uuid4


cdef extern from "vec2.h" nogil:
    cdef cppclass Vec2:
        float x,y
        Vec2() except +
        Vec2(float, float) except +
        @staticmethod
        Vec2 random(float, float)
        Vec2 pow(float)
        float sum()
        void clip(Vec2, Vec2)
        void clip(float,float,float,float)
        Vec2 operator+(Vec2)
        Vec2 operator-(Vec2)
        Vec2 operator*(float)
        # Vec2 &operator+=(Vec2)
    

cdef extern from "vec2.cpp":
    pass


cdef extern from "core.h" nogil:
    cdef cppclass Bullet:
        long owner_uid
        unsigned long uid
        Vec2 position, velocity
        float power
        Bullet()
        Bullet(long, Vec2, Vec2, float)
        void step()
        bint operator>(Vec2)
    
    cdef cppclass Robot:
        unsigned long uid
        Vec2 position
        float power, velocity
        Robot()
        void step()
        Bullet* fire()


cdef extern from "core.cpp":
    pass

