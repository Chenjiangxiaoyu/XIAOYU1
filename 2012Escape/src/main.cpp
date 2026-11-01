#include "Game.h"

#include <windows.h>

int WINAPI wWinMain(HINSTANCE, HINSTANCE, PWSTR, int) {
    Game game;
    if (!game.init()) {
        return 1;
    }

    game.run();
    game.shutdown();
    return 0;
}
