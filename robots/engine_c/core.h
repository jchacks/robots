#ifndef BULLET_H
#define BULLET_H

#include <Python.h>
#include <ostream>
#include <vec2.h>
#include <math.h>
#include <list>
#include <set>

unsigned long NUMBER_ROBOTS = 0;

const float PI_2f32 = 2.0f * M_PIf32;

const float BASE_ROTATION_VELOCITY_RADS = 5 * M_PI / 180;
const float BASE_ROTATION_VELOCITY_DEC_RADS = 0.75 * M_PI / 180;
const float TURRET_ROTATION_VELOCITY_RADS = 5 * M_PI / 180;
const float RADAR_ROTATION_VELOCITY_RADS = 5 * M_PI / 180;

const float BULLET_MAX_POWER = 3.0;
const float BULLET_MIN_POWER = 0.1;
const float ROBOT_RADIUS = 24;

const bool DEBUG=0;

void log_message(const char * msg) {
    if(DEBUG == 1)
        std::cout <<  msg << std::endl;
};

class Bullet
{
public:
    class Robot *owner;
    Vec2 position;
    Vec2 velocity;
    float power;

    Bullet()
        : owner(NULL),
          position(Vec2(0.0, 0.0)),
          velocity(Vec2(0.0, 0.0)),
          power(0)
    {
        log("default constructor");
    };
    Bullet(Robot *owner, Vec2 position, Vec2 velocity, float power)
        : owner(owner),
          position(position),
          velocity(velocity),
          power(power)
    {
        log("constructor");
    };

    ~Bullet()
    {
        log("destructor");
    };
    void step();

    bool operator>(const Bullet &other) const;
    bool operator<(const Bullet &other) const;

private:
    void log(const char *msg)
    {
        if(DEBUG == 1)
            std::cout << "Bullet[" << this << "] " << msg << std::endl;
    }
};

class Robot
{
public:
    PyObject * scripted_robot = NULL;

    static const float RADIUS;

    unsigned long uid;
    float energy;
    float speed;
    Vec2 position;
    float base_rotation;
    float turret_rotation;
    float radar_rotation;
    float heat;

    int moving;
    int base_turning;
    int turret_turning;
    int radar_turning;
    bool should_fire;
    float fire_power;

    Robot()
        : uid(NUMBER_ROBOTS += 1),
          energy(100.0),
          speed(0.0),
          position(Vec2(0.0, 0.0)),
          base_rotation(0.0),
          turret_rotation(0.0),
          radar_rotation(0.0),
          heat(0.0),

          moving(0),
          base_turning(0),
          turret_turning(0),
          radar_turning(0),
          should_fire(false),
          fire_power(0.0)
    {
        log("constructor");
    };

    ~Robot()
    {
        log("destructor");
    };

    void step();
    float get_acceleration();
    Vec2 get_velocity();
    Bullet *fire();

private:
    void log(const char *msg)
    {
        if(DEBUG == 1)
            std::cout << "Robot[" << this << "] " << msg << std::endl;
    }
};

class Engine
{
    Vec2 size;
    std::list<Robot *> robots;
    std::set<Bullet *> bullets;
    void collide_bullets();

public:
    Engine(){};
    Engine(Vec2 size) : size(size){};

    void add_robot(Robot *robot);
    void add_bullet(Bullet *bullet);
    void step();
    void run(); // Is this needed?

private:
    void log(const char *msg)
    {
        if(DEBUG == 1)
            std::cout << "Engine[" << this << "] " << msg << std::endl;
    }
};
#endif
