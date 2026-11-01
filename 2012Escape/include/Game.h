#pragma once

#include <memory>

#include "Scene.h"

class Game {
public:
    Game();
    ~Game();

    bool init();
    void run();
    void shutdown();

private:
    enum class State {
        Opening,
        Level1,
        Level2,
        Ending,
        GameOver,
        Exit
    };

    void processInput();
    void update(float deltaTime);
    void draw();
    void changeScene(State nextState);

    State state_;
    bool running_;
    bool enterKeyDown_;
    bool escapeKeyDown_;
    std::unique_ptr<Scene> currentScene_;
};
