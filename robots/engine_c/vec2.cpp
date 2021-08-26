#include <vec2.h>
#include <math.h>
#include <stdlib.h>
#include <chrono>
#include <random>
#include <ostream>

unsigned seed = std::chrono::system_clock::now().time_since_epoch().count();
std::default_random_engine generator(seed);

float rand_float(float low, float high)
{
    std::uniform_real_distribution<float> distribution(low, high);
    return distribution(generator);
}

Vec2 Vec2::from_rads(float rads)
{
    return Vec2(std::cos(rads), std::sin(rads));
};

Vec2 Vec2::random(float low, float high)
{
    return Vec2(rand_float(low, high), rand_float(low, high));
};

Vec2 Vec2::pow(float exponent)
{
    return Vec2(std::pow(x, exponent), std::pow(y, exponent));
};

float Vec2::sum()
{
    return x + y;
};

float Vec2::len()
{
    return sqrt(this->pow(2.0f).sum());
};

void Vec2::clip(Vec2 min, Vec2 max)
{
    // Inplace clip the Vec2
    x = std::min(std::max(x, min.x), max.x);
    y = std::min(std::max(y, min.y), max.y);
};

void Vec2::clip(float top, float left, float bottom, float right)
{
    // Inplace clip the Vec2
    x = std::min(std::max(x, left), right);
    y = std::min(std::max(y, bottom), top);
};

Vec2 Vec2::operator+(const Vec2 &other) const
{
    return Vec2(x + other.x, y + other.y);
};

Vec2 Vec2::operator-(const Vec2 &other) const
{
    return Vec2(x - other.x, y - other.y);
};

Vec2 Vec2::operator-(const float &val) const
{
    return Vec2(x - val, y - val);
};

Vec2 Vec2::operator*(const float &scalar) const
{
    return Vec2(x * scalar, y * scalar);
};

Vec2 Vec2::operator/(const float &scalar) const
{
    return Vec2(x / scalar, y / scalar);
};

Vec2 &Vec2::operator+=(const Vec2 &other)
{
    x = x + other.x;
    y = y + other.y;
    return *this;
};

std::ostream &operator<<(std::ostream &strm, const Vec2 &v)
{
    return strm << "(" << v.x << "," << v.y << ")";
}

float clip(float clip, float min, float max)
{
    return std::max(min, std::min(max, clip));
}