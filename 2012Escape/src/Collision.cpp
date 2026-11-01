#include "Collision.h"

bool Collision::checkRect(const Rect& a, const Rect& b) {
    return a.x < b.x + b.width &&
           a.x + a.width > b.x &&
           a.y < b.y + b.height &&
           a.y + a.height > b.y;
}

bool Collision::checkGround(float y, float groundY) {
    return y >= groundY;
}
