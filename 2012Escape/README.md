# 2012Escape

A C++17 / EasyX 2D side-scrolling escape game inspired by the disaster-movie premise of reaching the Tibet ark base.

## Current milestone

Step 1 is complete: the Visual Studio project structure and object-oriented class skeletons are in place. The program opens an EasyX window, shows a start prompt, and can enter the first placeholder scene with Enter.

Both levels now include moving hazards in addition to static obstacles: rocks repeatedly fall from above in the earthquake city, while bouncing magma balls travel toward the player in Hawaii. Both dynamic hazards use collision damage, knockback, hit audio, and the existing invulnerability window.

The moving-hazard spawn calculation intentionally avoids `std::min` in code that includes Windows headers, preventing the Win32 `min` macro from causing MSVC syntax errors.

The Hawaii fallen tree now uses bright orange, yellow, and charred-brown pixels so it remains visible against the green forest. After `GAME OVER`, press `Enter` in either level to restart from level one. Background music uses a looping channel while jump, hit, and clear effects use separate MCI effect channels, so effects no longer stop the music.

The executable uses the Windows subsystem, so running from Visual Studio opens only the EasyX game window rather than an extra console input window. Controls are processed only while the game window has focus.

## Requirements

- Windows
- Visual Studio 2022
- C++17
- EasyX installed and configured for MSVC

## Build

Open `2012Escape.sln` in Visual Studio 2022 and build the `2012Escape` project. The project adds `include` as an additional include directory.

## Image assets

The current image milestone provides local BMP placeholders under `images/`:

- `images/player/`: idle, four-frame run, jump, hurt, and victory player sprites.
- `images/level1/`: city earthquake background layers, ground, crack, rock, and collapsed-building obstacles.
- `images/level2/`: volcanic sky, volcano, forest, lava ground, fire animation frames, fallen tree, and plane.
- `images/ui/`: heart and menu panel UI placeholders.
- `images/ending/`: Tibet ark base ending background.

The generated art uses a magenta background color for sprite-style assets so a later rendering step can treat it as a transparency key if needed. Regenerate the placeholder image set with:

```bash
python3 tools/generate_pixel_assets.py
```

## Sound assets

The current sound milestone provides generated placeholder WAV files under `sounds/`:

- `sounds/bgm.wav`: short looping-style background music placeholder.
- `sounds/jump.wav`: rising jump effect.
- `sounds/hit.wav`: low hit/damage effect.
- `sounds/clear.wav`: mission-clear success jingle.
- `sounds/ending.wav`: calm looping ending theme for the Tibet ark-base scene.

These sounds are generated locally from simple waveforms, so they are safe placeholders for development and can be replaced later with polished audio. Regenerate them with:

```bash
python3 tools/generate_sound_assets.py
```

## Controls planned

- `A` / `D` or arrow keys: move
- `Space`: jump
- `Enter`: start / confirm
- `Esc`: quit

## Development order

1. Window and compileable skeleton
2. Resource and Game systems
3. Player movement, jumping, and gravity
4. Scene system and level 1
5. Level 2
6. UI, audio, animation, and ending polish

## Windows 一键生成完整项目

如果 GitHub 克隆后没有看到项目文件，可单独下载仓库根目录中的
`Create2012Escape.ps1`，然后在该脚本所在目录打开 PowerShell，运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\Create2012Escape.ps1
```

脚本会在当前目录创建 `2012Escape` 文件夹，完整释放解决方案、C++ 源码、
图片、声音和资源生成工具。若要在生成后直接打开 Visual Studio，可运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\Create2012Escape.ps1 -OpenInVisualStudio
```

如果目标文件夹已存在且不为空，脚本会停止，避免覆盖已有文件。可使用
`-Destination` 指定其他位置，例如：

```powershell
powershell -ExecutionPolicy Bypass -File .\Create2012Escape.ps1 -Destination "D:\2012\2012Escape"
```
