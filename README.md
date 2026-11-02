# 3D Model — Blender

Four complete procedural Blender productions, built end-to-end in **Blender 5.2.3 LTS**
with the Blender Python API / Blender MCP bridge. No external asset packs, no image
planes, no pre-rendered backgrounds — the geometry, materials, lighting, cameras and
animation are all built in Blender.

## Selected captures

| | |
|:--:|:--:|
| [![Abyssal Living City](covers/abyssal-living-city.png)](Abyssal%20Living%20City) | [![Giant Energy Reactor](covers/giant-energy-reactor.png)](Giant%20Energy%20Reactor) |
| [![Neon Ritual](covers/neon-ritual.png)](Neon%20Ritual) | [![Tropical Island Civilization](covers/tropical-island-civilization.png)](Tropical%20Island%20Civilization) |

The four covers are curated 1200 × 800 gallery cards in [`covers/`](covers). Full
render sets stay inside each project folder.

## Projects

### [Abyssal Living City](Abyssal%20Living%20City)

Static underwater civilization: a domed abyssal city on a procedural seabed, with a
high street, districts, coral, kelp, fauna, figures, submarines, signal towers and a
foreground shelf. EEVEE, AgX, 1920 × 1920 hero render.

- 789 objects · 3.05 M triangles · 13 cameras · 18 lights
- Deliverables: `.blend`, final PNG, build script, project notes
- Renders and checkpoints are included.

### [Giant Energy Reactor](Giant%20Energy%20Reactor)

A giant hard-surface energy reactor: luminous core, energy shell, containment rings,
structural frame, stacks and chamber. EEVEE, AgX, 1920 × 1920 hero render.

- 695 objects · 57.7 k triangles
- Deliverables: `.blend`, final PNG, `build_reactor.py`, project notes

### [Neon Ritual](Neon%20Ritual)

A 15-second vertical 3D event advertisement for an underground electronic experience.
A chrome ribbon sculpture, a three-ring orbital structure, a gothic-industrial
cathedral, custom blackletter typography, a rain-wet stage, volumetric light, original
synthesized audio and eight camera shots. The on-screen title is **NEON RITUAL**.

- 717 objects · 304.6 k triangles · 8 cameras · 80 lights
- 1080 × 1920 · 30 fps · 450 frames · 15.0 s
- H.264 High / AAC 192 kb/s MP4
- Deliverables: `.blend`, final MP4, build/animation/render scripts, audio WAVs,
  HD preview stills, production notes
- The 450 PNG intermediate frames (`Neon Ritual/frames/`) are intentionally not
  versioned; the final MP4 is included.

### [Tropical Island Civilization](Tropical%20Island%20Civilization)

A static miniature tropical island town: procedural terrain and ocean, palms and
vegetation, ten building archetypes, people, animals, vehicles, boats, harbour and
farm. Includes a final render plus fast and HQ orbit review videos.

- Deliverables: `.blend`, final PNG, orbit MP4s, modular build scripts, project notes

## Repository notes

- Each project folder is self-contained: `.blend`, source scripts, notes and renders.
- `*.blend1` Blender backups and `__pycache__`/`*.pyc` files are excluded.
- `Neon Ritual/frames/` is excluded because it is a regenerable 817 MB PNG sequence;
  `NEON_RITUAL_FINAL.mp4` is the delivered video.
- Event details in Neon Ritual are intentionally placeholders, not a real event.
- Selected covers are in `covers/`; full render sets are in each project folder.

## Requirements

- Blender 5.2.3 LTS (EEVEE)
- Python 3.13 (bundled with Blender)
- ffmpeg for re-encoding the Neon Ritual video, if needed

The project notes in each folder document the exact scene structure, materials,
lighting, camera setup, render settings and known limitations.
