#pragma once

struct Rect {
    float x;
    float y;
    float width;
    float height;
};

class Collision {
public:
    static bool checkRect(const Rect& a, const Rect& b);
    static bool checkGround(float y, float groundY);
};
