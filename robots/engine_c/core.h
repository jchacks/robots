#ifndef BULLET_H
#define BULLET_H

#include <ostream>
#include <vec2.h>
#include <math.h>

unsigned long NUMBER_BULLETS = 0;
unsigned long NUMBER_ROBOTS = 0;

const float BASE_ROTATION_VELOCITY_RADS = 5/180 * M_PI;
const float BASE_ROTATION_VELOCITY_DEC_RADS = 0.75/180 * M_PI;
const float TURRET_ROTATION_VELOCITY_RADS = 5/180 * M_PI;
const float RADAR_ROTATION_VELOCITY_RADS = 5/180 * M_PI;

const float BULLET_MAX_POWER = 3.0;
const float BULLET_MIN_POWER = 0.1;
const float ROBOT_RADIUS = 24;


struct Bullet
{
    unsigned long uid;
    long owner_uid;
    Vec2 position;
    Vec2 velocity;
    float power;

    Bullet()
        : uid(NUMBER_BULLETS += 1),
          owner_uid(-1),
          position(Vec2(0.0, 0.0)),
          velocity(Vec2(0.0, 0.0)),
          power(0){};
    Bullet(long owner_uid, Vec2 position, Vec2 velocity, float power)
        : uid(NUMBER_BULLETS += 1),
          owner_uid(owner_uid),
          position(position),
          velocity(velocity),
          power(power){};
    void step();

    bool operator>(const Bullet &other) const;
    bool operator<(const Bullet &other) const;
};

struct Robot
{
    unsigned long uid;
    float energy;
    float velocity;
    Vec2 position;
    float base_rotation;
    float turret_rotation;
    float radar_rotation;
    float heat;

public:
    int moving;
    int base_turning;
    int turret_turning;
    int radar_turning;
    bool should_fire;
    int fire_power;

    Robot()
        : uid(NUMBER_ROBOTS += 1),
          energy(100.0),
          velocity(0.0),
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
          fire_power(0)
          {};

    void step();
    float acceleration();
    Bullet *fire();
};

#endif
