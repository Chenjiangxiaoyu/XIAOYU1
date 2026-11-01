#pragma once

#include <string>

class UI {
public:
    void drawHud(int hp, int level, int timeLeft) const;
    void drawOpening() const;
    void drawPauseMenu() const;
    void drawGameOver() const;
    void drawMessage(const std::wstring& message) const;
};
