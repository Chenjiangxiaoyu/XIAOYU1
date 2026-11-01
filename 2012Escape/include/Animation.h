#pragma once

#include <graphics.h>
#include <vector>

class Animation {
public:
    Animation();

    void setFrames(const std::vector<IMAGE*>& frames, float frameDuration, bool loop);
    void update(float deltaTime);
    void draw(int x, int y) const;
    void reset();

private:
    std::vector<IMAGE*> frames_;
    float frameDuration_;
    float elapsed_;
    int currentFrame_;
    bool loop_;
};
