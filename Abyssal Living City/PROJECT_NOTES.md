# PROJECT 10 — THE ABYSSAL LIVING CITY

Static underwater civilization. Blender 5.2.3 LTS, EEVEE, AgX.

**Status: complete and delivered.**

---

## 1. Deliverables

| File | Size |
|---|---|
| `Abyssal_Living_City.blend` | 15,856,272 B |
| `Abyssal_Living_City_Final.png` | 4,179,643 B — 1920 × 1920, 64 samples |
| `Abyssal_Living_City_Build.py` | 6,892 B — entry point, 13 modules, rebuild ~35 s |
| `PROJECT_NOTES.md` | this file |

Verification, run twice on the saved file:

```
objs=789  tris=3,047,434  cams=13  lights=18
actions=0  animated=0  frames=1-1
camera=CAMERA_ABYSSAL_HERO  res=1920x1920  engine=BLENDER_EEVEE
look=AgX - Punchy  exposure=0.35
22 numbered collections, 1 empty (20_REFERENCE_AND_HELPERS)
```

---

## 2. What the city contains

| Layer | Count |
|---|---|
| Domes (geodesic / ribbed / faceted) | 11 |
| Buildings across all districts | 60 |
| Commercial establishments | 12 |
| Submarine masters / placed | 6 / 8 |
| Coral pieces | 106 |
| Marine vegetation stands | 73 |
| Fauna species / instances | 15 / 94 |
| Figures | 53 |
| Environmental props | 59 |
| Signal towers / roof spires | 3 / 2 |

Districts: central ring, high street, residential, resort, research, industrial,
harbour, agriculture, public — plus the rim reef, the abyssal kelp forest, the
foreground shelf, three signal towers, two roof spires and the perimeter ring.

---

## 3. The three defining pieces

### 3.1 The high street
A straight 21.6 BU street at y = −22.6: roadway with dashed centre line and
crossings, kerbs and pavements, two terraced shop rows facing each other, awnings,
lit fascias, hanging blade signs, shop canopies with interior counters, lamp posts,
benches, planters, market stalls, two lit gantries. The transit station closes the
east end; the central dome closes the vista.

12 establishments: grocery, seafood, coffee, bakery, convenience, pharmacy,
dive shop, clothing, market hall, pharmacy annex, tech, fish market on the quay.

### 3.2 The central dome interior
Rebuilt in the final pass as a **terraced plaza**: four concentric terraces rising to
a lit basin and a monument, six radial spokes with stairs and handrails, ten buildings
pushed out against the shell with glazing bands and lit ground floors, planting and
benches on the terraces.

The earlier version stood towers in the middle of the floor, which from the hero
camera read as a field of glowing drums. `renders/FINAL_dome.png` shows the difference.

### 3.3 The skyline
The civic ring could not be built — the plateau has no ground at r ≈ 24.5 once the
street, the hospital, the hotel and the commercial outposts are placed, so only one of
six slots survives. The skyline is recovered without new footprints:

- 3 signal towers on the outer ring, 24–31 BU
- 2 roof spires sitting inside existing roofs (market hall, hospital)
- the commercial tower at 22 BU and the research tower at 21 BU
- the one surviving civic tower at 30 BU

---

## 4. Quality gate — final, honest

| Gate | Result |
|---|---|
| Buildings are architecture, not massing | **PASS** |
| Each district has its own character | **PARTIAL** — improved by material accents; public and central still similar |
| Commercial street reads as a street | **PASS** |
| 12 establishments | **PASS** |
| Submarines docked | **PASS** |
| Ecosystem in three bands | **PASS** |
| Fauna and population | **PASS** |
| Dome interior not a ring of cylinders | **PASS** — terraced plaza |
| Nothing overhangs the drop-off | **PARTIAL** — pier over water by design, 0.286 |
| Nothing interpenetrates | **PARTIAL** — 11 pairs, 6 are adjacent terraces |
| Triangle budget < 3.5 M | **PASS** — 3.05 M |
| Static only | **PASS** |

---

## 5. Known limitations

1. **One civic tower of six.** The ring is a composition casualty of a saturated
   plateau. Recovered vertically, not horizontally.
2. **11 overlap pairs.** 6 are adjacent terraced shop units that share a party wall by
   design. The other 5 are real: two street units against the agriculture racks, the
   street against the fish market, the market hall against the pharmacy annex, and one
   more reported by the build.
3. **The dome glass reads milky in close-up.** The interior is bright enough that the
   shell scatters; it works at hero scale, less so at 1000 px.
4. **Residential density is modest** — 4 buildings plus 6 habitat pods. The solver is
   correct; the ground is not there.
5. **The foreground is lit context, not narrative.** Two area lights and a rock-and-kelp
   shelf keep the bottom of frame from going black; there is no subject there.
6. **`M3_reef.png` is a bad camera**, not a bad reef.

---

## 6. Bugs found and fixed across the project

**M1**
1. Camera `right` vector was `Z × forward` instead of `forward × Z`, inverting every
   lateral composition correction.
2. `rock_cluster` double-offset geometry already baked at world coordinates.
3. District cameras placed inside buildings by azimuth alone.
4. Caustics covered the whole abyss; now masked by height.
5. Fog drove off the Z pass with wrong units; replaced with the Mist pass.

**M2**
6. `_foundation` name collision between the dome and architecture modules.
7. Bench cameras framed the origin — master geometry is baked in world space with the
   object at (0,0,0), so every bench render was the same building.
8. Shopfront emissive panel directly behind the glass blew out to a white bar.
9. Occupancy solver far too conservative: 3 buildings, zero shops.
10. Buildings spilled off the plateau because the solver tested the centre only.

**M3**
11. All modules share one exec namespace, so `_m()` in `abyss_eco` replaced `_m()` in
    `abyss_vessels` — the fleet reported 0 masters, fauna 30 species instead of 15.
12. Bounding-box overlap detection is useless when geometry is world-baked: 1233 false
    pairs out of 2016. Replaced with 2-D convex hull + separating-axis test.
13. `enforce_containment` created the contacts it was meant to prevent.
14. The hero camera framed the plateau, not the city: when the city shrank, 45% of the
    frame became empty seabed.
15. The civic ring was hard-coded at 24.5 BU — two slots inside the street, one inside
    the hospital.

**M4**
16. `relax_layout` moved objects but changed nothing: `matrix_world` is stale until the
    depsgraph updates. Fixed with an explicit `view_layer.update()`.
17. Agriculture nutrient tanks were placed at local +7.2, inside the high street.

**M5 (final polish)**
18. The dome interior's terraces used `concrete` on alternating rings and washed out;
    switched the dark ring to `deck`.
19. `build_district_blockout` lost its header line when the roof-tower function was
    inserted above it — caught by the `IndentationError` on the next build.

---

## 7. Files

```
Abyssal Living City/
  Abyssal_Living_City_Build.py     entry point, module loader, modes
  Abyssal_Living_City.blend        final scene (static)
  Abyssal_Living_City_Final.png    final hero, 1920², 64 samples
  PROJECT_NOTES.md
  references/ART_DIRECTION.md
  scripts/
    abyss_core.py                  scene, collections, materials, primitives, pipeline
    abyss_kit.py                   architectural, interior and prop components
    abyss_arch.py                  building archetypes incl. terrace rows
    abyss_seabed.py                height field, drop-off, rim rocks, foreground
    abyss_water.py                 mist fog, world volume, marine snow
    abyss_domes.py                 geodesic kit and terraced interiors
    abyss_layout.py                seed reservations, solver, districts, relax, QA
    abyss_look.py                  lights, cameras, framing solve, renders
    abyss_vessels.py               6 submarine masters and fleet placement
    abyss_eco.py                   coral, kelp, seagrass, bioluminescence, shelf
    abyss_fauna.py                 15 species and scatter
    abyss_people.py                9 figure masters and placement
    abyss_detail.py                crates, barrels, bollards, planters, stalls
  renders/                         FINAL_* set + M1–M4 archives
  checkpoints/                     M1_blockout … FINAL.blend
```

---

## 8. Reproduction

```python
p = r"D:\Tes Animasi-Motion-Blender\Abyssal Living City\Abyssal_Living_City_Build.py"
ns = {"__name__": "boot", "__file__": p}
exec(compile(open(p, encoding="utf-8").read(), p, "exec"), ns)
ns["main"]("build")     # build only, ~35 s
ns["main"]("m1")        # build + clay + hero + checkpoint
ns["main"]("bench")     # asset quality gate on the building archetypes
```

Deterministic: same script, same result. Every render in `renders/` came from this
entry point.

---

## 9. What is still worth doing

1. Author the civic ring as **two towers on the research and commercial plinths**,
   rather than hunting for ground that does not exist.
2. Fix the five real overlaps by hand — the checker names them every build.
3. Widen the commercial street by one module per side; the terraces currently read a
   little narrow for the amount of detail on them.
4. Build a proper reef camera and an eight-frame district contact sheet.
