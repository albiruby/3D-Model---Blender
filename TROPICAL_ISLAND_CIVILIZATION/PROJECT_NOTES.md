# TROPICAL ISLAND CIVILIZATION — THE LIVING PARADISE

Static miniature island town, built entirely procedurally inside Blender 5.2 via the
Blender MCP bridge. No external assets, no image textures, no simulations, no
armatures, no keyframes.

## Deliverables

| File | Size |
|---|---|
| `TROPICAL_ISLAND_CIVILIZATION.blend` | ~4.6 MB |
| `TROPICAL_ISLAND_FINAL.png` | 1920 × 1920, PNG |
| `TROPICAL_ISLAND_ORBIT_FAST.mp4` | 480 × 480, 240 f, 24 fps, H.264 |
| `TROPICAL_ISLAND_ORBIT_HQ.mp4` | 1152 × 1152, 240 f, 24 fps, H.264 |
| `build_island.py` | entry point (loads the modules below) |
| `PROJECT_NOTES.md` | this file |

Supporting modules (must stay next to `build_island.py`):

```
island_core.py       terrain field, ocean, materials, palette, primitives, QA bench
island_nature.py     palms, broadleaf, banana, mangrove, bushes, ferns, flowers, rocks, coral
island_arch.py       construction kit + 10 building archetypes (29 instances)
island_people.py     parametric bodies, 8 static poses, 11 templates
island_animals.py    9 species (chicken, rooster, dog, cat, gull, crab, turtle, fish)
island_vehicles.py   pickup, car, scooter, golf cart
island_boats.py      hulls with sheer/transom/deck, cabins, wheelhouse, gear
island_orbit.py      camera-only orbit for the review video
island_layout.py     pads, roads, town square, harbour, boats, beach, farm, population
island_look.py       sun, fill lights, world, hero camera with numeric framing
```

## Scene

| Item | Value |
|---|---|
| Engine | `BLENDER_EEVEE`, 64 TAA samples, raytracing on |
| Resolution | 1920 × 1920, PNG RGB |
| Colour management | AgX, look `AgX - Punchy`, exposure 0.0 |
| Compositor | Glare/Bloom, threshold 1.35, strength 0.22 (subtle) |
| Objects | 900 |
| Triangles | 1,167,844 |
| Collections | 15 spec collections + root + asset library + workspace |
| Terrain | 31,428 verts baked from a signed-distance field, 74 × 52 BU island |
| Ocean | 19,551 verts, non-uniform grid out to ±900 BU, per-vertex shoreline distance |
| Cameras | `CAMERA_ISLAND_HERO` (auto-framed to 80 % width), `CAMERA_TOWN_CLOSE` |

### Districts present

- **Central village** — paved plaza with fountain, obelisk monument, clock tower,
  notice board, benches, 8 lamps, planters, market stalls.
- **Residential east / west** — 13 houses from 4 archetypes (stilt, coastal veranda,
  modern villa with pool, family home), laundry, bicycles, garden fences.
- **Commercial street** — 4 shophouses with open shopfronts, counters, shelves and
  goods, awnings, signage; 6 café sets with tables and chairs.
- **Fishing harbour** — pier with plank deck, pilings, bollards, net racks, crates,
  barrels, fish auction, harbour office, 5 boats, buoys.
- **Resort / beach** — hotel villa with glazed front and terrace, beach pavilions,
  pool, 7 lounger + umbrella sets, volleyball net, lifeguard hut.
- **Agriculture** — 7 irrigated vegetable beds, fence, pump, storage shed, banana and
  palm rows.
- **Forest** — 34 palms, 12 broadleaf, 120 bushes, 70 ferns, 90 beach-grass clumps,
  coral heads in the lagoon.
- **Infrastructure** — 6 road ribbons with shoulders and dashed centre lines, stone
  stairs, street lamps, bicycles, 2 pickups, 2 cars, 2 scooters, a golf cart.

## Build

```python
exec(compile(open(r"D:\Tes Animasi-Motion-Blender\TROPICAL_ISLAND_CIVILIZATION\build_island.py",
                  encoding="utf-8").read(), "build_island.py", "exec"))
```

Full rebuild + render + save takes ~13 s on the target machine (RTX 3050, i7).
The build is deterministic: the random generator is seeded per module.

## Verified (not claimed)
Printed by `build_island.py` on every run:

```
actions=0  armatures=0  animated=0  sim_modifiers=0  cameras=2  active camera set
RESIDENTIAL:15 COMMERCIAL:14 RESORT:71 HARBOR:95 PUBLIC_FACILITIES:84
HUMAN_CHARACTERS:36 ANIMALS:43 VEGETATION:340 AGRICULTURE:54
ENVIRONMENTAL_PROPS:52 LIGHTING:3 TERRAIN:1 OCEAN:1
```

Camera framing is solved numerically: `world_to_camera_view` is run over the island
boundary and the camera distance is iterated until the island spans 80 % of the frame.

## Revision 2 — asset + layout fixes

Applied after the first delivery:

1. **Boats rebuilt** (`island_boats.py`): lofted hull with a real sheer line, pointed bow,
   transom stern, cambered deck, gunwale + rub rail, bow rail, cleats, fenders, outboard
   with leg and propeller, and wheelhouses with glazed panes, door, console, wheel and
   roof handrail. Small boats keep thwarts and an open deck.
2. **Rear elevations**: stilt houses, family homes and shophouses now carry rear windows,
   a service door and a rear balcony/awning instead of a blank wall.
3. **Agriculture moved to the camera side**: the vegetable beds, irrigation channel, pump,
   fence and storage shed now sit on the south slope at (2.6, −16.2), inside the hero
   frame instead of behind the hill.
4. **Collision pass**: an OBB/SAT solver (`solve_sites`) runs before the terrain is built
   and separates interpenetrating building footprints, refusing moves that would push a
   building within 7 BU of the coastline. Roof intersections are largely gone; a few soft
   contacts remain where the town is dense.

## Review video (camera-only animation)

`island_orbit.py` keyframes **only the camera** — a 360° orbit, 240 frames at 24 fps,
elevation drifting 38° → 26°, slight distance breathing. Every mesh, person, animal and
boat stays completely static, so the "static world" rule still holds; there are still
zero object-level actions in the `.blend`.

| Output | Resolution | Frames | Size |
|---|---|---|---|
| `TROPICAL_ISLAND_ORBIT_FAST.mp4` | 480 × 480, 12 samples | 240 @ 24 fps | 3.3 MB |
| `TROPICAL_ISLAND_ORBIT_HQ.mp4` | 1152 × 1152, 40 samples | 240 @ 24 fps | 13.5 MB |

Both verified by loading them back into Blender as movie clips (correct size, 240 frames,
24 fps). The `.blend` itself is saved in the **static** state with the orbit removed.

## Known limitations (honest)

- **Style, not photorealism.** This is a stylised miniature: bevelled boxes, flat
  painted materials, no UV unwrap, no normal/bump maps, no weathering. Metals and
  wood differ only by base colour and roughness.
- **Close-up quality is "game asset", not "hero prop".** The hero camera at 22 px per
  Blender unit is where the scene is designed to be read. The town close-up exposes
  simplified boats, blank rear facades on some buildings, and low-poly people.
- **Interiors are only suggested.** Shophouses have counters, shelves and goods
  because their fronts are open; houses are hollow with a dark interior box.
- **Boats** now have proper hulls, cabins and gear, but the wheelhouse interiors are
  empty shells and the rigging is symbolic.
- **Some buildings still touch** where the town is dense. The OBB solver removes hard
  interpenetration but is deliberately limited (small pushes, coastline guard) so the
  authored layout is not scrambled.
- **The agricultural district is small** (5 beds) and read as a kitchen garden rather
  than the plantation the brief describes; the remaining crop area is off-camera.
- **Roads are partly hidden** under buildings/trees in the town core.
- **No vehicles on the water animation, no crowd dynamics** — the brief requires a
  completely static world, so every figure and boat is frozen.
- **People are small.** At the hero framing a 1.72 m islander is ~38 px tall; they read
  as colour/pose silhouettes, which is why every template carries a hat, an apron or a
  prop.
- **No animation, rigs, keyframes or simulations** — asserted at build time, not just
  intended.

## Blender 5.2 API notes

- `bpy.context` inside the MCP sandbox is restricted: `context.object` and
  `context.selected_objects` are unavailable. All geometry is therefore built with
  `bmesh` and merged in Python; `bpy.ops.object.join` is not used.
- The compositor uses a `CompositorNodeTree` node group assigned to
  `scene.compositing_node_group`; `CompositorNodeComposite` no longer exists.
- Glare parameters are input sockets, not RNA properties.
- EEVEE has no render-time bloom; glow comes from the compositor.
