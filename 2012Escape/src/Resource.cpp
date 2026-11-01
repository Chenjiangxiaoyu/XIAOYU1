#include "Resource.h"

#include <array>
#include <io.h>
#include <mmsystem.h>

namespace {
const wchar_t* effectAlias(const std::wstring& path) {
    if (path.find(L"jump") != std::wstring::npos) {
        return L"jumpEffect";
    }
    if (path.find(L"hit") != std::wstring::npos) {
        return L"hitEffect";
    }
    return L"clearEffect";
}
}

Resource& Resource::instance() {
    static Resource resource;
    return resource;
}

bool Resource::loadImage(const std::wstring& key, const std::wstring& path) {
    if (_waccess(path.c_str(), 0) != 0) {
        return false;
    }

    auto image = std::make_unique<IMAGE>();
    loadimage(image.get(), path.c_str());
    images_[key] = std::move(image);
    return true;
}

bool Resource::loadDefaultImages() {
    const std::array<std::pair<const wchar_t*, const wchar_t*>, 26> assets{{
        {L"level1.sky", L"images/level1/sky.bmp"},
        {L"level1.far", L"images/level1/far_buildings.bmp"},
        {L"level1.near", L"images/level1/near_buildings.bmp"},
        {L"level1.ground", L"images/level1/ground.bmp"},
        {L"level1.crack", L"images/level1/crack.bmp"},
        {L"level1.rock", L"images/level1/rock.bmp"},
        {L"level1.building", L"images/level1/collapsed_building.bmp"},
        {L"player.idle", L"images/player/player_idle.bmp"},
        {L"player.run1", L"images/player/player_run_1.bmp"},
        {L"player.run2", L"images/player/player_run_2.bmp"},
        {L"player.run3", L"images/player/player_run_3.bmp"},
        {L"player.run4", L"images/player/player_run_4.bmp"},
        {L"player.jump", L"images/player/player_jump.bmp"},
        {L"player.hurt", L"images/player/player_hurt.bmp"},
        {L"player.victory", L"images/player/player_victory.bmp"},
        {L"ui.heart", L"images/ui/heart.bmp"},
        {L"level2.sky", L"images/level2/sky.bmp"},
        {L"level2.volcano", L"images/level2/volcano.bmp"},
        {L"level2.forest", L"images/level2/forest.bmp"},
        {L"level2.ground", L"images/level2/lava_ground.bmp"},
        {L"level2.fire1", L"images/level2/fire_1.bmp"},
        {L"level2.fire2", L"images/level2/fire_2.bmp"},
        {L"level2.fire3", L"images/level2/fire_3.bmp"},
        {L"level2.tree", L"images/level2/fallen_tree.bmp"},
        {L"level2.plane", L"images/level2/plane.bmp"},
        {L"ending.background", L"images/ending/tibet_ark_base.bmp"},
    }};

    bool allLoaded = true;
    for (const auto& asset : assets) {
        allLoaded = loadImage(asset.first, asset.second) && allLoaded;
    }
    return allLoaded;
}

IMAGE* Resource::getImage(const std::wstring& key) {
    auto it = images_.find(key);
    if (it == images_.end()) {
        return nullptr;
    }
    return it->second.get();
}

bool Resource::playSound(const std::wstring& path, bool loop) const {
    if (_waccess(path.c_str(), 0) != 0) {
        return false;
    }
    if (loop) {
        const DWORD flags = SND_FILENAME | SND_ASYNC | SND_NODEFAULT | SND_LOOP;
        return PlaySound(path.c_str(), nullptr, flags) != FALSE;
    }

    const wchar_t* alias = effectAlias(path);
    std::wstring command = L"close ";
    command += alias;
    mciSendString(command.c_str(), nullptr, 0, nullptr);

    command = L"open \"" + path + L"\" type waveaudio alias " + alias;
    if (mciSendString(command.c_str(), nullptr, 0, nullptr) != 0) {
        return false;
    }

    command = L"play ";
    command += alias;
    command += L" from 0";
    return mciSendString(command.c_str(), nullptr, 0, nullptr) == 0;
}

void Resource::stopSound() const {
    PlaySound(nullptr, nullptr, 0);
    mciSendString(L"close jumpEffect", nullptr, 0, nullptr);
    mciSendString(L"close hitEffect", nullptr, 0, nullptr);
    mciSendString(L"close clearEffect", nullptr, 0, nullptr);
}

void Resource::release() {
    stopSound();
    images_.clear();
}
