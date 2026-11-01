#include "Player.h"

#include "Resource.h"

#include <graphics.h>
#include <vector>

namespace {
constexpr float kGravity = 980.0f;
constexpr float kGroundY = 412.0f;
constexpr float kJumpVelocity = -460.0f;
constexpr float kPlayerWidth = 32.0f;
constexpr float kPlayerHeight = 32.0f;
constexpr float kHurtDuration = 0.35f;
constexpr float kInvulnerableDuration = 1.25f;
}

Player::Player()
    : x_(80.0f),
      y_(kGroundY),
      vx_(0.0f),
      vy_(0.0f),
      speed_(220.0f),
      hp_(3),
      direction_(Direction::Right),
      jumpState_(JumpState::Grounded),
      activeAnimation_(&idleAnimation_),
      hurtTimer_(0.0f),
      invulnerableTimer_(0.0f),
      victorious_(false) {
    loadAnimation();
}

void Player::update(float deltaTime, float worldWidth) {
    if (hurtTimer_ > 0.0f) {
        hurtTimer_ -= deltaTime;
    }
    if (invulnerableTimer_ > 0.0f) {
        invulnerableTimer_ -= deltaTime;
    }

    x_ += vx_ * deltaTime;
    if (x_ < 0.0f) {
        x_ = 0.0f;
    } else if (x_ > worldWidth - kPlayerWidth) {
        x_ = worldWidth - kPlayerWidth;
    }
    fall(deltaTime);

    if (victorious_) {
        activeAnimation_ = &victoryAnimation_;
    } else if (hurtTimer_ > 0.0f) {
        activeAnimation_ = &hurtAnimation_;
    } else if (jumpState_ != JumpState::Grounded) {
        activeAnimation_ = &jumpAnimation_;
    } else if (vx_ != 0.0f) {
        activeAnimation_ = &runAnimation_;
    } else {
        activeAnimation_ = &idleAnimation_;
    }
    activeAnimation_->update(deltaTime);
}

void Player::draw(float cameraX) const {
    activeAnimation_->draw(
        static_cast<int>(x_ - cameraX),
        static_cast<int>(y_));
}

void Player::moveLeft() {
    if (hurtTimer_ > 0.0f) {
        return;
    }
    vx_ = -speed_;
    direction_ = Direction::Left;
}

void Player::moveRight() {
    if (hurtTimer_ > 0.0f) {
        return;
    }
    vx_ = speed_;
    direction_ = Direction::Right;
}

void Player::stop() {
    if (hurtTimer_ > 0.0f) {
        return;
    }
    vx_ = 0.0f;
}

bool Player::jump() {
    if (jumpState_ == JumpState::Grounded) {
        vy_ = kJumpVelocity;
        jumpState_ = JumpState::Jumping;
        return true;
    }
    return false;
}

bool Player::takeDamage(float sourceX) {
    if (victorious_ || hp_ <= 0 || invulnerableTimer_ > 0.0f) {
        return false;
    }

    --hp_;
    hurtTimer_ = kHurtDuration;
    invulnerableTimer_ = kInvulnerableDuration;
    vx_ = x_ < sourceX ? -speed_ : speed_;
    vy_ = -240.0f;
    jumpState_ = JumpState::Jumping;
    activeAnimation_ = &hurtAnimation_;
    return true;
}

void Player::celebrate() {
    victorious_ = true;
    vx_ = 0.0f;
    activeAnimation_ = &victoryAnimation_;
}

void Player::fall(float deltaTime) {
    vy_ += kGravity * deltaTime;
    y_ += vy_ * deltaTime;

    if (Collision::checkGround(y_, kGroundY)) {
        y_ = kGroundY;
        vy_ = 0.0f;
        jumpState_ = JumpState::Grounded;
    } else if (vy_ > 0.0f) {
        jumpState_ = JumpState::Falling;
    }
}

bool Player::collision(const Rect& obstacle) const {
    return Collision::checkRect(getBounds(), obstacle);
}

void Player::loadAnimation() {
    Resource& resources = Resource::instance();
    idleAnimation_.setFrames({resources.getImage(L"player.idle")}, 0.2f, true);
    runAnimation_.setFrames({
        resources.getImage(L"player.run1"),
        resources.getImage(L"player.run2"),
        resources.getImage(L"player.run3"),
        resources.getImage(L"player.run4")}, 0.09f, true);
    jumpAnimation_.setFrames({resources.getImage(L"player.jump")}, 0.2f, false);
    hurtAnimation_.setFrames({resources.getImage(L"player.hurt")}, 0.2f, false);
    victoryAnimation_.setFrames({resources.getImage(L"player.victory")}, 0.2f, false);
}

Rect Player::getBounds() const {
    return Rect{x_, y_, kPlayerWidth, kPlayerHeight};
}

float Player::getX() const {
    return x_;
}

int Player::getHp() const {
    return hp_;
}

bool Player::isDead() const {
    return hp_ <= 0;
}
