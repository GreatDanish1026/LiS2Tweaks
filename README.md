# LiS2Tweaks 0.1.0

Graphics add-on for **Life is Strange 2** (PC, Steam), for ReShade with add-on support. Raises the
game's lighting, shadow and detail settings beyond what its menu offers and adds HDR output that
keeps the game's colour grade, live, from an in-game overlay.

- **HDR**: the game's menu has no HDR option. The HDR tab turns the finished picture into HDR10,
  keeping Dontnod's colours and stretching only the brightest parts, with **Peak brightness** and
  **Paper white** sliders (and a button that uses the peak Windows reports for your display).
  Menus, prompts and subtitles stay at paper white: the add-on copies the picture just before the
  game draws its UI and doesn't brighten what the UI covers. Windows HDR must be on. Tested on
  DirectX 11 (the game's default) and with `-dx12`.
- **Lighting**: Cinematic screen-space reflections (also on rougher surfaces), finer volumetric
  fog, finer lighting on translucent effects.
- **Shadows**: 4096 / 8192 shadow maps, longer shadow distance, full-resolution character shadows.
- **Characters and detail**: full-resolution skin, the most detailed characters, models and plants
  detailed twice as far, Dontnod's own Cinematic draw distance (10x, not in the menu), more texture
  memory than the game's 2.4 GB, 16x filtering.
- **Post-processing**: film grain, lens flares, depth of field, motion blur, chromatic aberration,
  sharpening.
- **Quality presets**: *Ultra+* and *Cinematic*. On an RTX 5080 at 4K with 133% resolution
  (DirectX 11): Game 155 fps (held by a frame cap), Ultra+ 133, Cinematic 132. **Measure preset
  costs** and **Measure each option** check them on your PC.
- **F8** switches every tweak off and on, to compare.

Every option starts at the game's own value. No ray tracing: Unreal Engine 4.16 predates it.

## Install

1. Install ReShade 6.8 or later with full add-on support for `LIS2-Win64-Shipping.exe`, in
   `Life is Strange 2\lis2\Binaries\Win64`.
2. Copy `LiS2Tweaks.addon64` into that folder.
3. Open ReShade (Home key): the LiS2Tweaks window opens beside it, and you can move and resize it.
   If you close it, turn it back on from the add-on's entry in ReShade's Add-ons tab.

Settings are saved in `ReShade.ini` under `[LiS2Tweaks]`. Log: `LiS2Tweaks.log` next to the game's
exe (and `-probe.txt`, every setting's value). Tested with Steam build 7519534.

## Build

`.\build.ps1` (Visual Studio 2022 C++ tools and the Windows SDK); `.\build.ps1 -Install` copies the
add-on into the game folder (game closed).

## How it works

Ported from LiSRemasteredTweaks (UE 4.23). The game's exe is Denuvo-packed, so its code only exists
in memory: the console variable layout was read from a dump of the running game
(`tools/dumpimage.py`, read-only). Everything goes through the game's console variables, set on
the game thread at console priority; letting go puts the game's value and priority back. The add-on
never writes to game code. HDR is a full-screen pass drawn at each present (`src/hdr.hlsl`).
`docs/FINDINGS.md` has the UE 4.16 layout and the game's values.
