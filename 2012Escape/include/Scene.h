#pragma once

#include <graphics.h>

#include "Camera.h"
#include "Player.h"

class Scene {
public:
    virtual ~Scene() = default;

    virtual void init() = 0;
    virtual void update(float deltaTime) = 0;
    virtual void draw() = 0;
    virtual void release() = 0;
    virtual bool isComplete() const = 0;
    virtual bool shouldRestart() const = 0;
};

class EarthquakeScene final : public Scene {
public:
    void init() override;
    void update(float deltaTime) override;
    void draw() override;
    void release() override;
    bool isComplete() const override;
    bool shouldRestart() const override;

private:
    IMAGE* sky_ = nullptr;
    IMAGE* farBuildings_ = nullptr;
    IMAGE* nearBuildings_ = nullptr;
    IMAGE* ground_ = nullptr;
    IMAGE* crack_ = nullptr;
    IMAGE* rock_ = nullptr;
    IMAGE* collapsedBuilding_ = nullptr;
    IMAGE* heart_ = nullptr;
    Player player_;
    Camera camera_;
    bool jumpKeyDown_ = false;
    bool gameOver_ = false;
    bool missionComplete_ = false;
    float completeTimer_ = 0.0f;
    float fallingRockX_ = 0.0f;
    float fallingRockY_ = 0.0f;
    float fallingRockTimer_ = 1.5f;
    bool fallingRockActive_ = false;
    bool restartRequested_ = false;
};

class HawaiiScene final : public Scene {
public:
    void init() override;
    void update(float deltaTime) override;
    void draw() override;
    void release() override;
    bool isComplete() const override;
    bool shouldRestart() const override;

private:
    IMAGE* sky_ = nullptr;
    IMAGE* volcano_ = nullptr;
    IMAGE* forest_ = nullptr;
    IMAGE* lavaGround_ = nullptr;
    IMAGE* fallenTree_ = nullptr;
    IMAGE* plane_ = nullptr;
    IMAGE* fireFrames_[3]{};
    IMAGE* heart_ = nullptr;
    Player player_;
    Camera camera_;
    int fireFrame_ = 0;
    float fireTimer_ = 0.0f;
    bool jumpKeyDown_ = false;
    bool gameOver_ = false;
    bool missionComplete_ = false;
    float completeTimer_ = 0.0f;
    float magmaBallX_ = 0.0f;
    float magmaBallY_ = 0.0f;
    float magmaBallVx_ = 0.0f;
    float magmaBallVy_ = 0.0f;
    float magmaBallTimer_ = 1.5f;
    bool magmaBallActive_ = false;
    bool restartRequested_ = false;
};

class EndingScene final : public Scene {
public:
    void init() override;
    void update(float deltaTime) override;
    void draw() override;
    void release() override;
    bool isComplete() const override;
    bool shouldRestart() const override;

private:
    IMAGE* background_ = nullptr;
    float elapsed_ = 0.0f;
};
