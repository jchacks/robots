#include <core.h>
#include <math.h>
#include <iostream>
#include <list>
#include <set>


PyObject *stop_name = PyUnicode_InternFromString("stop");


bool test_cirle_oob(const Vec2 &c, const float r, const Vec2 &size)
{
    return !((r < c.x) & (c.x < size.x - r) & (r < c.y) & (c.y < size.y - r));
};

bool test_circle_to_circle(const Vec2 c1, float r1, const Vec2 c2, float r2)
{
    return (c1 - c2).pow(2).sum() <= pow((r1 + r2), 2);
};

void Engine::collide_bullets()
{
    std::set<Bullet *>::iterator it_bullet = bullets.begin();
    while (it_bullet != bullets.end())
    {
        // Test outofbounds
        if (test_cirle_oob((*it_bullet)->position, 3, size))
        {
            log("Bullet hit wall");
            delete *it_bullet;
            bullets.erase(it_bullet);
            it_bullet++;
            continue;
        }

        // Test robot collisions
        std::list<Robot *>::iterator it_robot = robots.begin();
        while (it_robot != robots.end())
        {
            if (test_circle_to_circle((*it_robot)->position, Robot::RADIUS, (*it_bullet)->position, 3))
            {
                log("Bullet hit tank");
                float power = (*it_bullet)->power;
                (*it_robot)->energy -= 4.0f * +((power >= 1) * 2.0f * (power - 1.0f));

                delete *it_bullet;
                bullets.erase(it_bullet);
                break;
            }
        }

        it_bullet++;
    }
};

void Engine::step()
{
    collide_bullets();
    for (auto it = bullets.begin(); it != bullets.end(); ++it)
        (*it)->step();

    for (auto it = robots.begin(); it != robots.end(); ++it)
    {
        Robot &robot = **it;
        robot.step();
        if (test_cirle_oob(robot.position, Robot::RADIUS, size))
        {
            log("Robot collided with wall.");
        }
    }
};

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
    log("Firing");
    return new Bullet(
        this,
        position + turret_direction * 30.0f,
        turret_direction * (20.0f - (3.0f * fire_power)),
        clip(fire_power, BULLET_MIN_POWER, BULLET_MAX_POWER));
};

const float Robot::RADIUS = 24;

void Robot::step()
{
    PyObject_CallMethodObjArgs(scripted_robot, stop_name, NULL);
    speed = clip(speed + get_acceleration(), -8.0f, 8.0f);
    position = position + get_velocity();
    float base_rotation_velocity =
        std::max(0.0f, (BASE_ROTATION_VELOCITY_RADS - BASE_ROTATION_VELOCITY_DEC_RADS * std::abs(speed))) * (float)base_turning;
    // std::cout << "Rotation " << base_rotation << "Turning " << base_turning << "Rot Vel " << (BASE_ROTATION_VELOCITY_RADS - BASE_ROTATION_VELOCITY_DEC_RADS * std::abs(velocity)) << std::endl;
    base_rotation = std::remainderf(base_rotation + base_rotation_velocity, PI_2f32);
    float turret_rotation_velocity = TURRET_ROTATION_VELOCITY_RADS * turret_turning + base_rotation_velocity;
    turret_rotation = std::remainderf(turret_rotation + turret_rotation_velocity, PI_2f32);
    float radar_rotation_velocity = RADAR_ROTATION_VELOCITY_RADS * radar_turning + turret_rotation_velocity;
    radar_rotation = std::remainderf(radar_rotation + radar_rotation_velocity, PI_2f32);
};

Vec2 Robot::get_velocity()
{
    return  Vec2::from_rads(base_rotation) * speed;
}

float Robot::get_acceleration()
{
    if (speed > 0.0f)
    {
        if (moving > 0)
            return 1.0f;
        else
            return -2.0f;
    }
    else if (speed < 0.0f)
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
