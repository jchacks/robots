#include <core.h>
#include <math.h>
#include <iostream>

const double PI_2f32 = 2.0f * M_PIf32;

void Bullet::step()
{
    position += velocity;
};

Bullet *Robot::fire()
{
    heat = 1.0f + fire_power / 5.0f;
    energy = std::max(0.0f, energy - fire_power);
    should_fire = false;
    Vec2 turret_direction = Vec2::from_rads(turret_rotation);
    std::cout << "Firing" << std::endl;
    return new Bullet(
        this,
        position + turret_direction * 30.0f,
        turret_direction * (20.0f - (3.0f * fire_power)),
        clip(fire_power, BULLET_MIN_POWER, BULLET_MAX_POWER));
};

void Robot::step()
{
    Vec2 direction = Vec2::from_rads(base_rotation);
    velocity = clip(velocity + acceleration(), -8.0f, 8.0f);
    position = position + (direction * velocity);
    float base_rotation_velocity =
        std::max(0.0f, (BASE_ROTATION_VELOCITY_RADS - BASE_ROTATION_VELOCITY_DEC_RADS * std::abs(velocity))) * (float)base_turning;
    // std::cout << "Rotation " << base_rotation << "Turning " << base_turning << "Rot Vel " << (BASE_ROTATION_VELOCITY_RADS - BASE_ROTATION_VELOCITY_DEC_RADS * std::abs(velocity)) << std::endl;
    base_rotation = std::remainderf(base_rotation + base_rotation_velocity, PI_2f32);
    float turret_rotation_velocity = TURRET_ROTATION_VELOCITY_RADS * turret_turning + base_rotation_velocity;
    turret_rotation = std::remainderf(turret_rotation + turret_rotation_velocity, PI_2f32);
    float radar_rotation_velocity = RADAR_ROTATION_VELOCITY_RADS * radar_turning + turret_rotation_velocity;
    radar_rotation = std::remainderf(radar_rotation + radar_rotation_velocity, PI_2f32);
};

float Robot::acceleration()
{
    if (velocity > 0.0f)
    {
        if (moving > 0)
            return 1.0f;
        else
            return -2.0f;
    }
    else if (velocity < 0.0f)
    {
        if (moving < 0)
            return -1.0f;
        else
            return 2.0f;
    }
    else if (std::abs(moving) > 0)
        return 1.0f;
    else
        return 0.0f;
};
