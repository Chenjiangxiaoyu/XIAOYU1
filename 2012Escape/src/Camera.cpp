#include "Camera.h"

#include <algorithm>

Camera::Camera() : x_(0.0f) {}

void Camera::follow(float targetX, float mapWidth, float screenWidth) {
    x_ = std::clamp(targetX - screenWidth * 0.5f, 0.0f, std::max(0.0f, mapWidth - screenWidth));
}

float Camera::worldToScreenX(float worldX) const {
    return worldX - x_;
}

float Camera::getX() const {
    return x_;
}

void Camera::reset() {
    x_ = 0.0f;
}
