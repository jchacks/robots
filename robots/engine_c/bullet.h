#ifndef BULLET_H
#define BULLET_H

#include <ostream>
#include <vec2.h>

unsigned long long NUMBER_BULLETS = 0;

struct Bullet
{
    unsigned long long uid;
    long owner_uid;
    Vec2 position;
    Vec2 velocity;
    float power;

    Bullet()
        : uid(NUMBER_BULLETS += 1),
          owner_uid(NULL),
          position(Vec2(0.0, 0.0)),
          velocity(Vec2(0.0, 0.0)),
          power(0){};
    Bullet(long owner_uid, Vec2 position, Vec2 velocity, float power)
        : uid(NUMBER_BULLETS += 1),
          owner_uid(owner_uid),
          position(position),
          velocity(velocity),
          power(power){};
    void update();

    bool operator>(const Bullet &other) const;
    bool operator<(const Bullet &other) const;
};

#endif
