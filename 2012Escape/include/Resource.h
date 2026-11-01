#pragma once

#include <graphics.h>
#include <memory>
#include <string>
#include <unordered_map>

class Resource {
public:
    static Resource& instance();

    bool loadImage(const std::wstring& key, const std::wstring& path);
    bool loadDefaultImages();
    IMAGE* getImage(const std::wstring& key);
    bool playSound(const std::wstring& path, bool loop = false) const;
    void stopSound() const;
    void release();

private:
    Resource() = default;
    Resource(const Resource&) = delete;
    Resource& operator=(const Resource&) = delete;

    std::unordered_map<std::wstring, std::unique_ptr<IMAGE>> images_;
};
