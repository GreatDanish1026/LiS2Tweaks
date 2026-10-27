# Findings: Life is Strange 2

## The game

- Steam app 532210, build 7519534. Folder `Life is Strange 2`, project **lis2**, exe
  `lis2\Binaries\Win64\LIS2-Win64-Shipping.exe` (391 MB, PE timestamp 0x615ae124, no PDB).
  **Unreal Engine 4.16** (`++UE4+Release-4.16`), Dontnod's fork (`DNE` cvars and comments).
- Config: `%LOCALAPPDATA%\Dontnod\<SteamID>\LIS2\Saved\Config\WindowsNoEditor\`.
- DirectX 11 (feature level 11_0). The back buffer is **R10G10B10A2_UNORM** (ReShade.log), so
  the graded HDR pass from LiSRemasteredTweaks applies unchanged.
- Paks version 4: index not encrypted, zlib, and compression block offsets are **absolute** file
  offsets (relative from version 5 on): `tools/pak4.py <pak> list|extract <glob> [out]`.

## Denuvo

The exe carries Denuvo. Sections: `.xcode` (executable, near-empty), `.link` (read-only data:
the cvar names), `.sdata` (data: the console manager singleton), `.edata` (318 MB, writable +
executable, encrypted on disk). The code only exists unpacked in memory, so offline code scans
find nothing. `tools/dumpimage.py` copies the running game's image (read-only access) with file
offset = RVA; the scans below ran on that dump (2026-10-27, main menu). The add-on treats every
executable section as code (writable or not) and never writes to code.

## Console variables

- `IConsoleManager::Singleton` RVA **0x4290328** (4 of 4 references to `L"r.ScreenPercentage"`).
  The image loads at its preferred base 0x140000000.
- IConsoleManager: `+0x38` CallAllConsoleVariableSinks (its code tests the pending flag at
  `+0x8c` and loops over the sink array at `+0x70`/`+0x78`), `+0x40` RegisterConsoleVariableSink
  (appends to that array, handle out in rdx), `+0x90` FindConsoleVariable (1299 calls; calls
  FindConsoleObject `+0x98`, the object's GetFlags `+0x18` and AsVariable `+0x28`).
- IConsoleObject has no IsVariableInt/Float/String yet: three slots fewer than 4.23. The add-on
  reads every value through GetFloat.
- IConsoleVariable: Set `+0x58` (39 call sites right after `mov r8d, SetBy`), GetInt `+0x60`,
  GetFloat `+0x68`, GetString `+0x70` (interface order after Set; checked at run time).
- SetBy: 0x08000000 (code, 32 sites), 0x09000000 (console, 13 sites).

## What the project ships

DefaultEngine.ini: TargetedRHIs PCD3D_SM5 only; global shader cache PCD3D_SM5; TAA
(`r.DefaultFeature.AntiAliasing=2`); AO, auto exposure, motion blur on by default; lens flare
off; `r.TonemapperFilm=1`; `r.SSS.Checkerboard=1` with the comment "Non checkerboard SSS profile
doesn't seems to work properly (DNE AZA)": no skin option. No ray tracing (Unreal added it in
4.22). `r.Shadow.FilterMethod` (contact-hardening shadows) doesn't exist yet in 4.16.

The player's settings (2026-10-27): 4K, `sg.ResolutionQuality` 133.3 (supersampling), sg.* 3
(Epic) except textures 4 and foliage 2.

## First run (2026-10-27, DirectX 11, in a scene)

Layout check passed: singleton found (1 of 1 at run time), r.MaxAnisotropy 8 and
r.ScreenPercentage 100 read through GetFloat, priorities 0x01 (sensible), and the game-thread hook
went in (CallAllConsoleVariableSinks slot points at RVA 0x8b41a0, a jump to 0x979ec30). The 5 s
and 60 s probes are identical.

| Setting | Game | Option |
|---|---|---|
| r.SSR.Quality / MaxRoughness | 3 / -1 | Cinematic (4), and 0.8 roughness |
| r.VolumetricFog.GridPixelSize / GridSizeZ | 8 / 128 | Fine: 4 px |
| r.AmbientOcclusionLevels / MaxQuality | -1 / 100 | already at the top: no option |
| r.TranslucencyLightingVolumeDim | 64 | 128 |
| r.Shadow.MaxResolution / MaxCSMResolution | 2048 / 2048 | 4096 / 8192 |
| r.Shadow.DistanceScale, CSM.MaxCascades | 1, 10 | 1.5 / 2 |
| r.CapsuleShadowsFullResolution | 0 | 1 |
| r.SSS.Checkerboard / HalfRes / Quality | 1 (forced, set by 0x03) / 1 / 1 | HalfRes 0 only |
| r.SkeletalMeshLODBias | 0 | -1 |
| r.StaticMeshLODDistanceScale, foliage.LODDistanceScale | 10, 10 | 20 (see below) |
| r.ViewDistanceScale | 1 | 2, 10 |
| r.Streaming.PoolSize | 2400 | 4/6/8 GB |
| r.MaxAnisotropy | 8 | 16 |
| r.TemporalAASamples | 8 | already Unreal's default: no option |
| r.Tonemapper.Quality / Sharpen | 5 / 0 | |
| r.DepthOfFieldQuality, LensFlareQuality, MotionBlurQuality, SceneColorFringeQuality | 2, 2, 4, 1 | |
| foliage.DensityScale | 0.8 (menu foliage High) | the menu's Epic gives 1.0 |

Dontnod reversed the LOD scales: their BaseScalability.ini sets `foliage.LODDistanceScale` and
`r.StaticMeshLODDistanceScale` to 0.5 / 1 / 5 / 10 / 10 for Low..Cinematic with the comment "Lod
scale are less agressive" on the high ones, so higher keeps detail farther (Unreal's own scale is
the other way round). Their Cinematic view distance is `r.ViewDistanceScale=10`; the menu stops at
Epic (1).

## HDR

The graded pass runs on DirectX 11 too (2026-10-27 18:24): pipeline built on the 3840x2160
R10G10B10A2 back buffer, swap chain switched to HDR10 and back cleanly, the display reports 3700
nits. The user's verdict: looks good.

Screenshots (SDR 18:29 vs HDR 18:30, DirectX 11, peak 3700, paper white 250): colour balance per
unit luminance within 1% overall and in every ninth of the picture, saturation +7%, no pixel
outside Rec. 709; the darkest 2% about 22% darker (gamma 2.2 decode, as on an SDR monitor). But
white UI went to the peak: the tutorial box reached 3680 nits.

### UI at paper white

Draw logs (`LiS2Tweaks-draws.txt`, Advanced tab): the swap chain has three buffers drawn in turn;
each frame's first draw into a back buffer is the scene (one full-screen `draw_indexed 3`, the
tonemapper/upscale), and everything after it is Slate UI (6-index quads, text), sometimes after a
short detour to a smaller target. A frame without UI has only the scene draw. Same on DirectX 12.

So right before the second draw into a back buffer in a frame, the add-on copies it (the picture
without UI); at present the pass marks pixels that differ from that copy by more than half a
10-bit step as UI and doesn't stretch them. Timing on DirectX 12 checked: copy and present on the
same thread, copy of the buffer that's then presented. Debug views (Advanced): "Tint what counts
as UI" showed exactly the tutorial box, the Rock/Look/Mushroom prompts and the dotted line;
"Show the picture before UI" a clean frame. The tutorial box now peaks at 248 nits (paper white
250) instead of 3680.

The DirectX 12 shots of the same scene had dimmer SDR highlights than the DirectX 11 SDR shot
(brightest 0.1% at code 0.85 vs 0.95, medians equal), so the snow got less stretch there: the
stretch above the knee (0.6) is quadratic and only climbs steeply near SDR white. Not looked into
further.

### Highlights start at (slider, default 50%)

The stretch used to start at a fixed 0.6 of SDR white in linear light (79% as encoded). Both
games keep many highlights below that (Remastered's title-screen sun and sea glare at 80%,
LiS 2's snow at 85%), so they barely brightened. The HDR tab now has a "Highlights start at"
slider (40-90% of SDR white as encoded; the shader's knee is that share decoded with gamma 2.2),
ini key HdrHighlightStart. Below it the picture is exactly as graded; above it the same quadratic
rise lands SDR white on the peak.

At peak 3700 and paper white 250 (SDR level -> nits): 50% 54 (unchanged), 60% 90, 70% 212,
80% 595, 85% 980, 90% 1571, 95% 2445, 100% 3700. The old start gave 153 at 80% and 228 at 85%.
User test on the Remastered title screen (2026-10-27): 40% "much brighter": it also lifts the
bright mid-tones (a 70% sky 2.8x), drifting from the grade; 50% was chosen as the default. UI is
excluded before the stretch, so menus stay at paper white at any setting.

## Preset costs

Measure preset costs (2026-10-27 18:25, RTX 5080, 4K at 133% resolution, DirectX 11, one scene,
about 1050-1240 frames each): Game 6.46 ms (154.9 fps, at the user's 156 fps cap), Ultra+
7.52 ms (133.0 fps), Cinematic 7.56 ms (132.3 fps). Game was capped, so +16% / +17% are lower
bounds. Every preset value was taken (applied 15, failed 0).

## Not done yet

- Per-option costs; an uncapped measurement; a visual check of the 20x LOD scale and 10x draw
  distance (Cinematic was switched on briefly, no problems reported).
- Why the DirectX 12 picture's highlights are dimmer than DirectX 11's (an SDR shot on DX12 would
  tell).
