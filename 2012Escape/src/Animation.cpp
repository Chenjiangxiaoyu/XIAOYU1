#include "Animation.h"

#include <windows.h>

Animation::Animation()
    : frameDuration_(0.1f), elapsed_(0.0f), currentFrame_(0), loop_(true) {}

void Animation::setFrames(const std::vector<IMAGE*>& frames, float frameDuration, bool loop) {
    frames_.clear();
    for (IMAGE* frame : frames) {
        if (frame) {
            frames_.push_back(frame);
        }
    }
    frameDuration_ = frameDuration;
    loop_ = loop;
    reset();
}

void Animation::update(float deltaTime) {
    if (frames_.empty()) {
        return;
    }

    elapsed_ += deltaTime;
    if (elapsed_ >= frameDuration_) {
        elapsed_ = 0.0f;
        ++currentFrame_;
        if (currentFrame_ >= static_cast<int>(frames_.size())) {
            currentFrame_ = loop_ ? 0 : static_cast<int>(frames_.size()) - 1;
        }
    }
}

void Animation::draw(int x, int y) const {
    if (!frames_.empty()) {
        IMAGE* frame = frames_[currentFrame_];
        TransparentBlt(
            GetImageHDC(nullptr), x, y, frame->getwidth(), frame->getheight(),
            GetImageHDC(frame), 0, 0, frame->getwidth(), frame->getheight(),
            RGB(255, 0, 255));
    }
}

void Animation::reset() {
    elapsed_ = 0.0f;
    currentFrame_ = 0;
}
