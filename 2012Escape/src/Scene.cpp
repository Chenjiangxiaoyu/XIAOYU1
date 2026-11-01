#include "Scene.h"

#include "Resource.h"

#include <array>
#include <cmath>
#include <cwchar>
#include <graphics.h>
#include <windows.h>

namespace {
constexpr COLORREF kTransparentColor = RGB(255, 0, 255);
constexpr float kScreenWidth = 960.0f;
constexpr float kMapWidth = 2880.0f;
constexpr float kFinishX = kMapWidth - 96.0f;
constexpr float kCompleteDelay = 2.0f;
constexpr float kHawaiiMapWidth = 2880.0f;
constexpr float kHawaiiFinishX = kHawaiiMapWidth - 170.0f;
constexpr float kFireFrameDuration = 0.12f;
constexpr float kFallingRockSpeed = 300.0f;
constexpr float kMagmaGravity = 700.0f;

enum class HazardImage {
    Crack,
    Rock,
    Building
};

struct Hazard {
    HazardImage image;
    Rect collision;
    int drawY;
    int drawWidth;
    int drawHeight;
};

constexpr std::array<Hazard, 9> kHazards{{
    {HazardImage::Crack, {342.0f, 432.0f, 40.0f, 12.0f}, 420, 64, 64},
    {HazardImage::Rock, {598.0f, 413.0f, 32.0f, 31.0f}, 405, 48, 48},
    {HazardImage::Building, {842.0f, 405.0f, 100.0f, 39.0f}, 390, 144, 96},
    {HazardImage::Crack, {1132.0f, 432.0f, 40.0f, 12.0f}, 420, 64, 64},
    {HazardImage::Rock, {1378.0f, 413.0f, 32.0f, 31.0f}, 405, 48, 48},
    {HazardImage::Building, {1602.0f, 405.0f, 100.0f, 39.0f}, 390, 144, 96},
    {HazardImage::Rock, {2048.0f, 413.0f, 32.0f, 31.0f}, 405, 48, 48},
    {HazardImage::Crack, {2302.0f, 432.0f, 40.0f, 12.0f}, 420, 64, 64},
    {HazardImage::Building, {2582.0f, 405.0f, 100.0f, 39.0f}, 390, 144, 96}
}};

enum class HawaiiHazardImage {
    Fire,
    Tree
};

struct HawaiiHazard {
    HawaiiHazardImage image;
    Rect collision;
    int drawY;
    int drawWidth;
    int drawHeight;
};

constexpr std::array<HawaiiHazard, 8> kHawaiiHazards{{
    {HawaiiHazardImage::Fire, {390.0f, 412.0f, 34.0f, 32.0f}, 396, 48, 48},
    {HawaiiHazardImage::Tree, {690.0f, 416.0f, 110.0f, 28.0f}, 396, 128, 48},
    {HawaiiHazardImage::Fire, {1030.0f, 412.0f, 34.0f, 32.0f}, 396, 48, 48},
    {HawaiiHazardImage::Fire, {1320.0f, 412.0f, 34.0f, 32.0f}, 396, 48, 48},
    {HawaiiHazardImage::Tree, {1530.0f, 416.0f, 110.0f, 28.0f}, 396, 128, 48},
    {HawaiiHazardImage::Fire, {1910.0f, 412.0f, 34.0f, 32.0f}, 396, 48, 48},
    {HawaiiHazardImage::Tree, {2180.0f, 416.0f, 110.0f, 28.0f}, 396, 128, 48},
    {HawaiiHazardImage::Fire, {2470.0f, 412.0f, 34.0f, 32.0f}, 396, 48, 48}
}};

void drawOpaque(IMAGE* image, int x, int y, int width, int height) {
    if (!image) {
        return;
    }
    StretchBlt(
        GetImageHDC(nullptr), x, y, width, height,
        GetImageHDC(image), 0, 0, image->getwidth(), image->getheight(),
        SRCCOPY);
}

void drawTransparent(IMAGE* image, int x, int y, int width, int height) {
    if (!image) {
        return;
    }
    TransparentBlt(
        GetImageHDC(nullptr), x, y, width, height,
        GetImageHDC(image), 0, 0, image->getwidth(), image->getheight(),
        kTransparentColor);
}

void drawAlpha(IMAGE* image, int x, int y, int width, int height, unsigned char alpha) {
    if (!image || alpha == 0) {
        return;
    }

    BLENDFUNCTION blend{};
    blend.BlendOp = AC_SRC_OVER;
    blend.SourceConstantAlpha = alpha;
    AlphaBlend(
        GetImageHDC(nullptr), x, y, width, height,
        GetImageHDC(image), 0, 0, image->getwidth(), image->getheight(),
        blend);
}

void drawTiledLayer(IMAGE* image, float offset, int y, int width, int height, bool transparent) {
    if (!image) {
        return;
    }

    const int firstX = static_cast<int>(std::floor(offset / width)) * width;
    for (int x = firstX; x < static_cast<int>(kScreenWidth); x += width) {
        if (transparent) {
            drawTransparent(image, x, y, width, height);
        } else {
            drawOpaque(image, x, y, width, height);
        }
    }
}
}

void EarthquakeScene::init() {
    Resource& resources = Resource::instance();
    sky_ = resources.getImage(L"level1.sky");
    farBuildings_ = resources.getImage(L"level1.far");
    nearBuildings_ = resources.getImage(L"level1.near");
    ground_ = resources.getImage(L"level1.ground");
    crack_ = resources.getImage(L"level1.crack");
    rock_ = resources.getImage(L"level1.rock");
    collapsedBuilding_ = resources.getImage(L"level1.building");
    heart_ = resources.getImage(L"ui.heart");
    camera_.reset();
    gameOver_ = false;
    missionComplete_ = false;
    completeTimer_ = 0.0f;
    fallingRockTimer_ = 1.5f;
    fallingRockActive_ = false;
    restartRequested_ = false;
}
void EarthquakeScene::update(float deltaTime) {
    if (GetForegroundWindow() != GetHWnd()) {
        player_.stop();
        return;
    }

    if (gameOver_) {
        player_.stop();
        if ((GetAsyncKeyState(VK_RETURN) & 0x8000) != 0) {
            restartRequested_ = true;
        }
        return;
    }

    if (missionComplete_) {
        completeTimer_ += deltaTime;
        player_.update(deltaTime, kMapWidth);
        return;
    }

    const bool left = (GetAsyncKeyState('A') & 0x8000) != 0 ||
                      (GetAsyncKeyState(VK_LEFT) & 0x8000) != 0;
    const bool right = (GetAsyncKeyState('D') & 0x8000) != 0 ||
                       (GetAsyncKeyState(VK_RIGHT) & 0x8000) != 0;

    if (left == right) {
        player_.stop();
    } else if (left) {
        player_.moveLeft();
    } else {
        player_.moveRight();
    }

    const bool jumpPressed = (GetAsyncKeyState(VK_SPACE) & 0x8000) != 0;
    if (jumpPressed && !jumpKeyDown_ && player_.jump()) {
        Resource::instance().playSound(L"sounds/jump.wav");
    }
    jumpKeyDown_ = jumpPressed;
    player_.update(deltaTime, kMapWidth);

    if (fallingRockActive_) {
        fallingRockY_ += kFallingRockSpeed * deltaTime;
        const Rect fallingRockBounds{fallingRockX_, fallingRockY_, 36.0f, 36.0f};
        if (player_.collision(fallingRockBounds) &&
            player_.takeDamage(fallingRockX_ + 18.0f)) {
            Resource::instance().playSound(L"sounds/hit.wav");
            gameOver_ = player_.isDead();
            fallingRockActive_ = false;
            fallingRockTimer_ = 1.2f;
        } else if (fallingRockY_ >= 444.0f) {
            fallingRockActive_ = false;
            fallingRockTimer_ = 1.2f;
        }
    } else {
        fallingRockTimer_ -= deltaTime;
        if (fallingRockTimer_ <= 0.0f) {
            const float targetX = player_.getX() + 260.0f;
            fallingRockX_ = targetX < kMapWidth - 48.0f
                ? targetX
                : kMapWidth - 48.0f;
            fallingRockY_ = 40.0f;
            fallingRockActive_ = true;
        }
    }

    for (const Hazard& hazard : kHazards) {
        if (player_.collision(hazard.collision) &&
            player_.takeDamage(hazard.collision.x + hazard.collision.width * 0.5f)) {
            Resource::instance().playSound(L"sounds/hit.wav");
            if (player_.isDead()) {
                gameOver_ = true;
            }
            break;
        }
    }

    camera_.follow(player_.getX() + 16.0f, kMapWidth, kScreenWidth);

    if (player_.getX() >= kFinishX) {
        missionComplete_ = true;
        completeTimer_ = 0.0f;
        player_.celebrate();
        Resource::instance().playSound(L"sounds/clear.wav");
    }
}
void EarthquakeScene::draw() {
    if (!sky_) {
        settextstyle(24, 0, L"Consolas");
        outtextxy(220, 230, L"Assets not found. Run from the project directory.");
        return;
    }

    drawOpaque(sky_, 0, 0, 960, 540);

    const float cameraX = camera_.getX();
    drawTiledLayer(farBuildings_, -std::fmod(cameraX * 0.25f, 960.0f), 155, 960, 264, true);
    drawTiledLayer(nearBuildings_, -std::fmod(cameraX * 0.55f, 960.0f), 190, 960, 312, true);
    drawTiledLayer(ground_, -std::fmod(cameraX, 960.0f), 444, 960, 96, false);

    for (const Hazard& hazard : kHazards) {
        IMAGE* image = crack_;
        if (hazard.image == HazardImage::Rock) {
            image = rock_;
        } else if (hazard.image == HazardImage::Building) {
            image = collapsedBuilding_;
        }

        const int screenX = static_cast<int>(camera_.worldToScreenX(hazard.collision.x));
        if (screenX + hazard.drawWidth >= 0 && screenX < static_cast<int>(kScreenWidth)) {
            drawTransparent(image, screenX, hazard.drawY, hazard.drawWidth, hazard.drawHeight);
        }
    }

    if (fallingRockActive_) {
        const int fallingRockScreenX = static_cast<int>(camera_.worldToScreenX(fallingRockX_));
        drawTransparent(rock_, fallingRockScreenX, static_cast<int>(fallingRockY_), 40, 40);
    }

    player_.draw(cameraX);

    for (int i = 0; i < player_.getHp(); ++i) {
        drawTransparent(heart_, 24 + i * 30, 20, 24, 24);
    }
    setbkmode(TRANSPARENT);
    settextcolor(WHITE);
    settextstyle(22, 0, L"Consolas");
    outtextxy(330, 20, L"LEVEL 1  CITY EARTHQUAKE ESCAPE");
    settextstyle(16, 0, L"Consolas");
    const int progress = static_cast<int>((player_.getX() / (kMapWidth - 32.0f)) * 100.0f);
    wchar_t progressText[64]{};
    std::swprintf(progressText, 64, L"Map progress: %d%%", progress);
    outtextxy(760, 20, progressText);
    outtextxy(24, 505, L"A/D or arrows: Move   SPACE: Jump   ESC: Exit");

    if (gameOver_) {
        setfillcolor(RGB(20, 20, 20));
        solidrectangle(300, 190, 660, 330);
        settextcolor(RGB(255, 90, 70));
        settextstyle(42, 0, L"Consolas");
        outtextxy(365, 220, L"GAME OVER");
        settextcolor(WHITE);
        settextstyle(18, 0, L"Consolas");
        outtextxy(330, 285, L"ENTER: Restart from Level 1");
    } else if (missionComplete_) {
        setfillcolor(RGB(15, 35, 55));
        solidrectangle(280, 185, 680, 335);
        settextcolor(RGB(255, 220, 70));
        settextstyle(38, 0, L"Consolas");
        outtextxy(315, 215, L"MISSION COMPLETE");
        settextcolor(WHITE);
        settextstyle(18, 0, L"Consolas");
        outtextxy(360, 285, L"Next: Hawaii");
    }
}
void EarthquakeScene::release() {
    sky_ = nullptr;
    farBuildings_ = nullptr;
    nearBuildings_ = nullptr;
    ground_ = nullptr;
    crack_ = nullptr;
    rock_ = nullptr;
    collapsedBuilding_ = nullptr;
    heart_ = nullptr;
    camera_.reset();
    jumpKeyDown_ = false;
    gameOver_ = false;
    missionComplete_ = false;
    completeTimer_ = 0.0f;
    fallingRockActive_ = false;
    fallingRockTimer_ = 1.5f;
    restartRequested_ = false;
}

bool EarthquakeScene::isComplete() const {
    return missionComplete_ && completeTimer_ >= kCompleteDelay;
}
bool EarthquakeScene::shouldRestart() const {
    return restartRequested_;
}

void HawaiiScene::init() {
    Resource& resources = Resource::instance();
    sky_ = resources.getImage(L"level2.sky");
    volcano_ = resources.getImage(L"level2.volcano");
    forest_ = resources.getImage(L"level2.forest");
    lavaGround_ = resources.getImage(L"level2.ground");
    fallenTree_ = resources.getImage(L"level2.tree");
    plane_ = resources.getImage(L"level2.plane");
    fireFrames_[0] = resources.getImage(L"level2.fire1");
    fireFrames_[1] = resources.getImage(L"level2.fire2");
    fireFrames_[2] = resources.getImage(L"level2.fire3");
    heart_ = resources.getImage(L"ui.heart");
    camera_.reset();
    fireFrame_ = 0;
    fireTimer_ = 0.0f;
    jumpKeyDown_ = false;
    gameOver_ = false;
    missionComplete_ = false;
    completeTimer_ = 0.0f;
    magmaBallTimer_ = 1.5f;
    magmaBallActive_ = false;
    restartRequested_ = false;
}
void HawaiiScene::update(float deltaTime) {
    fireTimer_ += deltaTime;
    if (fireTimer_ >= kFireFrameDuration) {
        fireTimer_ -= kFireFrameDuration;
        fireFrame_ = (fireFrame_ + 1) % 3;
    }

    if (GetForegroundWindow() != GetHWnd()) {
        player_.stop();
        return;
    }
    if (gameOver_) {
        player_.stop();
        if ((GetAsyncKeyState(VK_RETURN) & 0x8000) != 0) {
            restartRequested_ = true;
        }
        return;
    }
    if (missionComplete_) {
        completeTimer_ += deltaTime;
        player_.update(deltaTime, kHawaiiMapWidth);
        return;
    }

    const bool left = (GetAsyncKeyState('A') & 0x8000) != 0 ||
                      (GetAsyncKeyState(VK_LEFT) & 0x8000) != 0;
    const bool right = (GetAsyncKeyState('D') & 0x8000) != 0 ||
                       (GetAsyncKeyState(VK_RIGHT) & 0x8000) != 0;
    if (left == right) {
        player_.stop();
    } else if (left) {
        player_.moveLeft();
    } else {
        player_.moveRight();
    }

    const bool jumpPressed = (GetAsyncKeyState(VK_SPACE) & 0x8000) != 0;
    if (jumpPressed && !jumpKeyDown_ && player_.jump()) {
        Resource::instance().playSound(L"sounds/jump.wav");
    }
    jumpKeyDown_ = jumpPressed;
    player_.update(deltaTime, kHawaiiMapWidth);

    if (magmaBallActive_) {
        magmaBallVy_ += kMagmaGravity * deltaTime;
        magmaBallX_ += magmaBallVx_ * deltaTime;
        magmaBallY_ += magmaBallVy_ * deltaTime;
        if (magmaBallY_ >= 408.0f) {
            magmaBallY_ = 408.0f;
            magmaBallVy_ = -310.0f;
        }

        const Rect magmaBounds{magmaBallX_, magmaBallY_, 34.0f, 34.0f};
        if (player_.collision(magmaBounds) &&
            player_.takeDamage(magmaBallX_ + 17.0f)) {
            Resource::instance().playSound(L"sounds/hit.wav");
            gameOver_ = player_.isDead();
            magmaBallActive_ = false;
            magmaBallTimer_ = 1.0f;
        } else if (magmaBallX_ < player_.getX() - 600.0f || magmaBallX_ < 0.0f) {
            magmaBallActive_ = false;
            magmaBallTimer_ = 1.0f;
        }
    } else {
        magmaBallTimer_ -= deltaTime;
        if (magmaBallTimer_ <= 0.0f) {
            const float targetX = player_.getX() + 620.0f;
            magmaBallX_ = targetX < kHawaiiMapWidth - 60.0f
                ? targetX
                : kHawaiiMapWidth - 60.0f;
            magmaBallY_ = 240.0f;
            magmaBallVx_ = -190.0f;
            magmaBallVy_ = -80.0f;
            magmaBallActive_ = true;
        }
    }

    for (const HawaiiHazard& hazard : kHawaiiHazards) {
        if (player_.collision(hazard.collision) &&
            player_.takeDamage(hazard.collision.x + hazard.collision.width * 0.5f)) {
            Resource::instance().playSound(L"sounds/hit.wav");
            gameOver_ = player_.isDead();
            break;
        }
    }

    camera_.follow(player_.getX() + 16.0f, kHawaiiMapWidth, kScreenWidth);
    if (player_.getX() >= kHawaiiFinishX) {
        missionComplete_ = true;
        completeTimer_ = 0.0f;
        player_.celebrate();
        Resource::instance().playSound(L"sounds/clear.wav");
    }
}
void HawaiiScene::draw() {
    if (!sky_) {
        settextstyle(24, 0, L"Consolas");
        outtextxy(220, 230, L"Level 2 assets not found.");
        return;
    }

    drawOpaque(sky_, 0, 0, 960, 540);
    const float cameraX = camera_.getX();
    drawTiledLayer(volcano_, -std::fmod(cameraX * 0.2f, 960.0f), 70, 960, 360, true);
    drawTiledLayer(forest_, -std::fmod(cameraX * 0.55f, 960.0f), 180, 960, 264, true);
    drawTiledLayer(lavaGround_, -std::fmod(cameraX, 960.0f), 444, 960, 96, false);

    for (const HawaiiHazard& hazard : kHawaiiHazards) {
        IMAGE* image = hazard.image == HawaiiHazardImage::Fire
            ? fireFrames_[fireFrame_]
            : fallenTree_;
        const int screenX = static_cast<int>(camera_.worldToScreenX(hazard.collision.x));
        if (screenX + hazard.drawWidth >= 0 && screenX < static_cast<int>(kScreenWidth)) {
            drawTransparent(image, screenX, hazard.drawY, hazard.drawWidth, hazard.drawHeight);
        }
    }

    if (magmaBallActive_) {
        const int magmaScreenX = static_cast<int>(camera_.worldToScreenX(magmaBallX_));
        drawTransparent(
            fireFrames_[fireFrame_],
            magmaScreenX,
            static_cast<int>(magmaBallY_),
            40,
            40);
    }

    const int planeX = static_cast<int>(camera_.worldToScreenX(kHawaiiMapWidth - 190.0f));
    drawTransparent(plane_, planeX, 360, 160, 80);
    player_.draw(cameraX);

    for (int i = 0; i < player_.getHp(); ++i) {
        drawTransparent(heart_, 24 + i * 30, 20, 24, 24);
    }
    setbkmode(TRANSPARENT);
    settextcolor(WHITE);
    settextstyle(22, 0, L"Consolas");
    outtextxy(350, 20, L"LEVEL 2  HAWAII IN FLAMES");

    if (gameOver_) {
        setfillcolor(RGB(20, 20, 20));
        solidrectangle(300, 190, 660, 330);
        settextcolor(RGB(255, 90, 70));
        settextstyle(42, 0, L"Consolas");
        outtextxy(365, 220, L"GAME OVER");
        settextcolor(WHITE);
        settextstyle(18, 0, L"Consolas");
        outtextxy(330, 285, L"ENTER: Restart from Level 1");
    } else if (missionComplete_) {
        setfillcolor(RGB(45, 20, 10));
        solidrectangle(280, 185, 680, 335);
        settextcolor(RGB(255, 220, 70));
        settextstyle(38, 0, L"Consolas");
        outtextxy(315, 215, L"MISSION COMPLETE");
        settextcolor(WHITE);
        settextstyle(18, 0, L"Consolas");
        outtextxy(350, 285, L"Flying to Tibet...");
    }
}
void HawaiiScene::release() {
    sky_ = nullptr;
    volcano_ = nullptr;
    forest_ = nullptr;
    lavaGround_ = nullptr;
    fallenTree_ = nullptr;
    plane_ = nullptr;
    fireFrames_[0] = nullptr;
    fireFrames_[1] = nullptr;
    fireFrames_[2] = nullptr;
    heart_ = nullptr;
    camera_.reset();
    magmaBallActive_ = false;
    magmaBallTimer_ = 1.5f;
    restartRequested_ = false;
}
bool HawaiiScene::isComplete() const {
    return missionComplete_ && completeTimer_ >= kCompleteDelay;
}
bool HawaiiScene::shouldRestart() const {
    return restartRequested_;
}

void EndingScene::init() {
    background_ = Resource::instance().getImage(L"ending.background");
    elapsed_ = 0.0f;
    Resource::instance().playSound(L"sounds/ending.wav", true);
}
void EndingScene::update(float deltaTime) {
    elapsed_ += deltaTime;
}
void EndingScene::draw() {
    const float fade = elapsed_ < 3.0f ? elapsed_ / 3.0f : 1.0f;
    const unsigned char alpha = static_cast<unsigned char>(fade * 255.0f);
    drawAlpha(background_, 0, 0, 960, 540, alpha);

    if (elapsed_ < 2.0f) {
        return;
    }

    const int textBrightness = static_cast<int>(fade * 255.0f);
    setbkmode(TRANSPARENT);
    settextcolor(RGB(textBrightness, textBrightness, textBrightness));
    settextstyle(34, 0, L"Microsoft YaHei");
    outtextxy(330, 105, L"恭喜！");

    if (elapsed_ >= 3.2f) {
        settextstyle(28, 0, L"Microsoft YaHei");
        outtextxy(260, 165, L"成功抵达西藏方舟基地！");
    }
    if (elapsed_ >= 4.5f) {
        settextstyle(26, 0, L"Microsoft YaHei");
        outtextxy(300, 220, L"人类文明得以延续！");
    }
    if (elapsed_ >= 6.0f) {
        settextcolor(RGB(255, 225, 90));
        settextstyle(46, 0, L"Consolas");
        outtextxy(340, 305, L"THANK YOU");
    }
    if (elapsed_ >= 7.5f) {
        settextcolor(WHITE);
        settextstyle(17, 0, L"Consolas");
        outtextxy(365, 480, L"ESC: Exit Game");
    }
}
void EndingScene::release() {
    Resource::instance().stopSound();
    background_ = nullptr;
    elapsed_ = 0.0f;
}
bool EndingScene::isComplete() const { return false; }
bool EndingScene::shouldRestart() const { return false; }
