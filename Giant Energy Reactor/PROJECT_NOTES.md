# GIANT ENERGY REACTOR — THE CORE OF INFINITE POWER

## Status

Delivered: procedural scene, hero render, detail render, editable `.blend`, re-runnable build script.
Built end-to-end inside the user's live Blender session through the Blender MCP bridge (`execute_blender_code`) — no external asset downloads, no image planes.

## Scene specifications

| Item | Value |
|---|---|
| Blender version | 5.2.3 LTS (Steam build, `D:\Steam\steamapps\common\Blender\blender.exe`) |
| Render engine | `BLENDER_EEVEE` |
| Final resolution | 1920 × 1920, PNG, RGB |
| Preview render | 960 × 960, 32 samples |
| Final samples | 64 TAA |
| Color management | AgX, look `AgX - Medium High Contrast`, exposure 0.0 |
| Compositor | Glare node (Type `Bloom`, threshold 0.95, strength 0.75) inside the Blender 5.2 `CompositingNodeTree` group |
| Scene scale | Reactor height ≈ 16.8 units, footprint ≈ 13.8 units, base at Z = 0, core at Z = 7.6 |
| Objects | 695 `RE_` objects (10 collections) |
| Triangles | 57,698 |
| Polygons style | flat-shaded hard surface, bevel modifiers on structural parts |

## Scene hierarchy

```
GIANT_ENERGY_REACTOR
├── 01_REACTOR_CORE        luminous nucleus, energy shell, halo, containment shell, shards, stabilisers
├── 02_CONTAINMENT_RINGS   3 rings (4.55 / 4.05 / 3.55 u) at different heights and tilts, segmented armour, joints
├── 03_STRUCTURAL_FRAME    8 pillars, upper cone, 4 stacks, spires, antenna, chamber drum, cross-bracing
├── 04_GEAR_ASSEMBLIES     8 pillar-mounted gear assemblies + 1 meshing pair (30T / 20T) with spokes
├── 05_HYDRAULIC_SYSTEMS   16 piston assemblies with rods, joints and feet
├── 06_ENERGY_NETWORK      ring conduit, 4 curved feeds, 8 pillar energy lines, branches, nodes, amber secondaries
├── 07_INDUSTRIAL_BASE     stacked foundation, catwalk, vents, valves, control panels, ladders, warning plate
├── 08_ENVIRONMENT         floor, floor rings, 4 distant silhouette blocks, 2 suspended background gears
├── 09_LIGHTING            7 lights (key, cyan rim, blue fill, amber accent, amber kick, core, ground bounce) + world
└── 10_CAMERAS             CAMERA_REACTOR_HERO (34 mm), CAMERA_REACTOR_DETAIL (50 mm)
```

## Material library

| Material | Hex | Metallic | Roughness | Use |
|---|---|---|---|---|
| `MAT_DARK_GUNMETAL` | `#1E252D` | 1.0 | 0.55 | main structure |
| `MAT_INDUSTRIAL_STEEL` | `#3A444E` | 0.95 | 0.38 | structural components |
| `MAT_TITANIUM` | `#7C8A96` | 1.0 | 0.26 | mechanical highlights |
| `MAT_BRONZE` | `#8A5A38` | 1.0 | 0.46 | secondary detail |
| `MAT_COPPER` | `#B0673F` | 1.0 | 0.34 | pipes and connectors |
| `MAT_REACTOR_CYAN` | `#28DFFF` | 0.0 | 0.30 | energy strips (emission 3.0) |
| `MAT_ELECTRIC_BLUE` | `#087DFF` | 0.0 | 0.25 | core volume (emission 2.2, alpha 0.30) |
| `MAT_WARNING_AMBER` | `#FF9C32` | 0.0 | 0.35 | indicators (emission 7.0) |
| `MAT_CORE_NUCLEUS` | gradient | 0.0 | 0.25 | Layer-Weight driven emission gradient, strength 6.5 |
| `MAT_DARK_GLASS` | `#101B28` | 0.0 | 0.06 | containment shell (alpha 0.08) |
| `MAT_FLOOR_ALLOY` | `#0C1116` | 0.8 | 0.42 | floor |
| `MAT_BG_STRUCTURE` | `#05080C` | 0.0 | 0.95 | distant silhouettes |

## Build script

`build_reactor.py` is fully re-runnable and deterministic (seeded RNG). It purges every `RE_` object and rebuilds all 18 stages in ~24 s. Run inside Blender:

```python
exec(compile(open(r"D:\Tes Animasi-Motion-Blender\Giant Energy Reactor\build_reactor.py").read(), "build_reactor.py", "exec"))
```

## Blender 5.2 API notes (the script encodes these deliberately)

- The compositor no longer uses `scene.node_tree`. Blender 5.x uses a `CompositorNodeTree` node group assigned to `scene.compositing_node_group`, and the output node is `NodeGroupOutput` — `CompositorNodeComposite` no longer exists.
- Glare parameters are **input sockets** now (`inputs["Type"]`, `inputs["Threshold"]`, `inputs["Strength"]`), not RNA properties.
- EEVEE bloom was removed as a render setting; glow comes from the compositor.
- Alpha blending uses `material.surface_render_method = 'BLENDED'`.

## Known limitations

- The energy core reads as a soft luminous orb with a white-hot centre; the containment rings crossing in front of it are physically consistent but do reduce the visible core area from the hero angle.
- Flat, untextured materials: no UV work, no normal/bump maps, no weathering textures. Metal variation comes from roughness values and lighting only.
- Surface detail is geometric only (bevels, ribs, plates, bolts). No decals, no grunge.
- Close inspection reveals low-poly faceting on the gear teeth and cylinders — intentional at diorama scale, but not "AAA texture-level" detail.
- Background is deliberately minimal: 4 silhouette blocks and 2 distant gears. No volumetric fog (compositor bloom only) to stay inside the time budget.
- No animation in this project (still deliverable). A turntable or gear-rotation animation would require a separate pass: the gear hierarchy exists, but no keyframes were authored.

## Outputs (verified on disk)

| File | Size |
|---|---|
| `GIANT_ENERGY_REACTOR.blend` | 742,484 bytes (verified re-opened in Blender 5.2.3: 697 objects, 57,698 tris, 2 cameras, hero camera active) |
| `GIANT_ENERGY_REACTOR_FINAL.png` | 3,823,668 bytes (1920 × 1920) |
| `renders/reactor_detail.png` | 4,277,454 bytes (1920 × 1920) |
| `renders/preview_960.png` | 1,071,750 bytes (960 × 960) |
| `build_reactor.py` | 35,199 bytes |
