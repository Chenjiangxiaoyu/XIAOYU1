#include "UI.h"

#include <graphics.h>

void UI::drawHud(int hp, int level, int timeLeft) const {
    settextstyle(20, 0, L"Consolas");
    std::wstring text = L"HP: " + std::to_wstring(hp) + L"  Level: " + std::to_wstring(level) + L"  Time: " + std::to_wstring(timeLeft);
    outtextxy(20, 20, text.c_str());
}

void UI::drawOpening() const {
    settextstyle(24, 0, L"Consolas");
    outtextxy(300, 180, L"2012 Escape");
    outtextxy(260, 240, L"Press Enter to Start");
}

void UI::drawPauseMenu() const {
    drawMessage(L"Paused");
}

void UI::drawGameOver() const {
    drawMessage(L"Game Over");
}

void UI::drawMessage(const std::wstring& message) const {
    settextstyle(28, 0, L"Consolas");
    outtextxy(360, 240, message.c_str());
}
