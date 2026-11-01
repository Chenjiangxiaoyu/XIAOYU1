#pragma once

#include "Collision.h"

class Obstacle {
public:
    virtual ~Obstacle() = default;

    virtual void update(float deltaTime) = 0;
    virtual void draw(float cameraX) = 0;
    virtual Rect getBounds() const = 0;
};

class Crack final : public Obstacle {
public:
    Crack(float x, float y, float width, float height);
    void update(float deltaTime) override;
    void draw(float cameraX) override;
    Rect getBounds() const override;

private:
    Rect bounds_;
};

class Building final : public Obstacle {
public:
    Building(float x, float y, float width, float height);
    void update(float deltaTime) override;
    void draw(float cameraX) override;
    Rect getBounds() const override;

private:
    Rect bounds_;
};

class Fire final : public Obstacle {
public:
    Fire(float x, float y, float width, float height);
    void update(float deltaTime) override;
    void draw(float cameraX) override;
    Rect getBounds() const override;

private:
    Rect bounds_;
};

class Tree final : public Obstacle {
public:
    Tree(float x, float y, float width, float height);
    void update(float deltaTime) override;
    void draw(float cameraX) override;
    Rect getBounds() const override;

private:
    Rect bounds_;
};

class Rock final : public Obstacle {
public:
    Rock(float x, float y, float width, float height);
    void update(float deltaTime) override;
    void draw(float cameraX) override;
    Rect getBounds() const override;

private:
    Rect bounds_;
};
