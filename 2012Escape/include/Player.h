#pragma once

#include "Animation.h"
#include "Collision.h"

class Player {
public:
    Player();

    void update(float deltaTime, float worldWidth);
    void draw(float cameraX) const;
    void moveLeft();
    void moveRight();
    void stop();
    bool jump();
    bool takeDamage(float sourceX);
    void celebrate();
    void fall(float deltaTime);
    bool collision(const Rect& obstacle) const;
    void loadAnimation();

    Rect getBounds() const;
    float getX() const;
    int getHp() const;
    bool isDead() const;

private:
    enum class Direction {
        Left,
        Right
    };

    enum class JumpState {
        Grounded,
        Jumping,
        Falling
    };

    float x_;
    float y_;
    float vx_;
    float vy_;
    float speed_;
    int hp_;
    Direction direction_;
    JumpState jumpState_;
    Animation idleAnimation_;
    Animation runAnimation_;
    Animation jumpAnimation_;
    Animation hurtAnimation_;
    Animation victoryAnimation_;
    Animation* activeAnimation_;
    float hurtTimer_;
    float invulnerableTimer_;
    bool victorious_;
};
