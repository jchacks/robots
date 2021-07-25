#include <bullet.h>

void Bullet::update()
{
    position += velocity;
};

bool Bullet::operator>(const Bullet &other) const
{
    return uid > other.uid;
};

bool Bullet::operator<(const Bullet &other) const
{
    return uid < other.uid;
};