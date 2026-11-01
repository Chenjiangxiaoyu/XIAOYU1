#include "Obstacle.h"

#include <graphics.h>

namespace {
void drawRectObstacle(const Rect& bounds, float cameraX, COLORREF color) {
    setfillcolor(color);
    solidrectangle(
        static_cast<int>(bounds.x - cameraX),
        static_cast<int>(bounds.y),
        static_cast<int>(bounds.x - cameraX + bounds.width),
        static_cast<int>(bounds.y + bounds.height));
}
}

Crack::Crack(float x, float y, float width, float height) : bounds_{x, y, width, height} {}
void Crack::update(float) {}
void Crack::draw(float cameraX) { drawRectObstacle(bounds_, cameraX, RGB(40, 40, 40)); }
Rect Crack::getBounds() const { return bounds_; }

Building::Building(float x, float y, float width, float height) : bounds_{x, y, width, height} {}
void Building::update(float) {}
void Building::draw(float cameraX) { drawRectObstacle(bounds_, cameraX, RGB(120, 120, 120)); }
Rect Building::getBounds() const { return bounds_; }

Fire::Fire(float x, float y, float width, float height) : bounds_{x, y, width, height} {}
void Fire::update(float) {}
void Fire::draw(float cameraX) { drawRectObstacle(bounds_, cameraX, RGB(240, 80, 20)); }
Rect Fire::getBounds() const { return bounds_; }

Tree::Tree(float x, float y, float width, float height) : bounds_{x, y, width, height} {}
void Tree::update(float) {}
void Tree::draw(float cameraX) { drawRectObstacle(bounds_, cameraX, RGB(80, 120, 40)); }
Rect Tree::getBounds() const { return bounds_; }

Rock::Rock(float x, float y, float width, float height) : bounds_{x, y, width, height} {}
void Rock::update(float) {}
void Rock::draw(float cameraX) { drawRectObstacle(bounds_, cameraX, RGB(100, 80, 70)); }
Rect Rock::getBounds() const { return bounds_; }
