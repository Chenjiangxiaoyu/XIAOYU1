#include "Game.h"

#include "Resource.h"

#include <graphics.h>
#include <windows.h>

namespace {
constexpr int kScreenWidth = 960;
constexpr int kScreenHeight = 540;
}

Game::Game()
    : state_(State::Opening),
      running_(false),
      enterKeyDown_(false),
      escapeKeyDown_(false),
      currentScene_(nullptr) {}

Game::~Game() {
    shutdown();
}

bool Game::init() {
    initgraph(kScreenWidth, kScreenHeight);
    BeginBatchDraw();
    Resource::instance().loadDefaultImages();
    Resource::instance().playSound(L"sounds/bgm.wav", true);
    running_ = true;
    return true;
}

void Game::run() {
    while (running_) {
        processInput();
        update(1.0f / 60.0f);
        draw();
        FlushBatchDraw();
        Sleep(16);
    }
}

void Game::shutdown() {
    if (currentScene_) {
        currentScene_->release();
        currentScene_.reset();
    }
    Resource::instance().release();
    EndBatchDraw();
    closegraph();
    running_ = false;
}

void Game::processInput() {
    if (GetForegroundWindow() != GetHWnd()) {
        return;
    }

    const bool escapePressed = (GetAsyncKeyState(VK_ESCAPE) & 0x8000) != 0;
    if (escapePressed && !escapeKeyDown_) {
        running_ = false;
    }
    escapeKeyDown_ = escapePressed;

    const bool enterPressed = (GetAsyncKeyState(VK_RETURN) & 0x8000) != 0;
    if (state_ == State::Opening && enterPressed && !enterKeyDown_) {
        changeScene(State::Level1);
    }
    enterKeyDown_ = enterPressed;
}

void Game::update(float deltaTime) {
    if (currentScene_) {
        currentScene_->update(deltaTime);
        if (currentScene_->shouldRestart()) {
            Resource::instance().playSound(L"sounds/bgm.wav", true);
            changeScene(State::Level1);
        } else if (state_ == State::Level1 && currentScene_->isComplete()) {
            changeScene(State::Level2);
        } else if (state_ == State::Level2 && currentScene_->isComplete()) {
            changeScene(State::Ending);
        }
    }
}

void Game::draw() {
    cleardevice();
    if (currentScene_) {
        currentScene_->draw();
        return;
    }

    settextstyle(28, 0, L"Consolas");
    outtextxy(360, 180, L"2012 Escape");
    outtextxy(300, 240, L"Press Enter to Start");
}

void Game::changeScene(State nextState) {
    if (currentScene_) {
        currentScene_->release();
        currentScene_.reset();
    }

    state_ = nextState;
    if (state_ == State::Level1) {
        currentScene_ = std::make_unique<EarthquakeScene>();
    } else if (state_ == State::Level2) {
        currentScene_ = std::make_unique<HawaiiScene>();
    } else if (state_ == State::Ending) {
        currentScene_ = std::make_unique<EndingScene>();
    }

    if (currentScene_) {
        currentScene_->init();
    }
}
