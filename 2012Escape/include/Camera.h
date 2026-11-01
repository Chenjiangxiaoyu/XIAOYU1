#pragma once

class Camera {
public:
    Camera();

    void follow(float targetX, float mapWidth, float screenWidth);
    float worldToScreenX(float worldX) const;
    float getX() const;
    void reset();

private:
    float x_;
};
