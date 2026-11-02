# THE ABYSSAL LIVING CITY — Art Direction Brief

Project 10. Written before modelling, so shape/material/lighting decisions have a
reference to be judged against instead of "looks nice".

## 1. One-line concept

A compact arcology on a raised abyssal plateau, lit from far above by a sun that
never quite reaches it — engineered geometry in a natural void.

## 2. Visual tension (the whole design rests on this)

| Engineered | Natural |
|---|---|
| Hard, precise, orthogonal, machined | Soft, irregular, organic, eroded |
| Cyan / amber / white emissive | Teal / violet bioluminescence |
| Cool desaturated metal and ceramic | Warm coral, cold rock |
| Grids, rings, radial symmetry | Frames, arches, asymmetry |

The city must never look sprayed onto the seabed. Every structure sits on a
foundation collar that meets the sediment.

## 3. Shape language

- **Domes**: geodesic, visible ribs. Glass is not a soap bubble — the frame carries it.
- **Towers**: tapered, chamfered, banded. Vertical ribs, horizontal light bands.
- **Industrial**: cylinders, spheres, pipe runs. Tank farms read as clusters, not singles.
- **Transport**: tubes with ribbing every few metres, never a plain glass cylinder.
- **Silhouette test**: each district must be identifiable as a black shape at 200 px.

## 4. Palette

Anchors (all in sRGB, converted to linear in `abyss_core.PAL`):

- Structure navy `#16233A`, titanium `#9BA8B4`, ceramic `#E8EDEC`, steel `#2B3540`
- City light cyan `#48E9FF`, teal `#2FD9C4`, amber `#FFAE43`, warm interior `#FFD2A0`
- Seabed `#8C8271` sediment, `#3C444D` rock
- Coral pink `#F2738F`, orange `#F0975A`, purple `#9C79C8`, lime `#93D95C`
- Bioluminescence `#63F0E0`, `#9A7BFF` — used sparingly, never as a light source for
  the whole scene

Rule: **no material gets 100% of anything.** Every metal has a roughness range, every
glass has a dirt/edge tint, every coral cluster has 2–3 hues.

## 5. Composition (hero shot)

- Camera: 40° elevation, three-quarter from the south-southeast, mild telephoto.
- Read order, deliberately staged: **central dome → harbor foreground → resort rim
  against open water → research and industrial flanks**.
- The city fills ~80% of frame width; the remaining 20% is water and coral, not empty.
- Foreground: a dark rock/coral silhouette anchors the bottom edge.
- Background: the plateau drops away into unlit water. No horizon line.

## 6. Lighting intent

- Key: a single broad, cool source from high above — the "sun through 400 m of water".
- Fill: cyan bounce from the city itself, not a lamp.
- Practicals: warm interiors inside domes, amber industrial, cyan research.
- Contrast: the abyss is near-black. The city is the only bright thing. Do not lift
  the shadows to make the seabed "readable" — let it fall off.

## 7. Detail budget by distance

At hero framing 1 BU ≈ 15 px.

| Scale | What must exist | What can be omitted |
|---|---|---|
| 10–30 BU (domes, towers) | ribs, rings, airlocks, window bands, foundations | interior furniture beyond silhouette |
| 3–10 BU (pods, tanks, subs) | hatch, fins, pipes, signage blocks | bolt-level detail |
| 0.5–3 BU (people, props, fish) | silhouette, pose, colour block | faces, fingers, text |

## 8. Quality gates (M1)

- PG-1 Every district reads as a distinct silhouette from the hero camera.
- PG-2 No structure floats; foundations meet terrain.
- PG-3 Domes read as glass with a frame, not as plastic spheres.
- PG-4 The frame has depth: near, mid, far separated by value, not just by size.
- PG-5 Nothing important is clipped by the frame edge.

## 9. Known deliberate compromises

- 1 BU = 1 m, but the city is compressed: a 100 m wide arcology hosting a
  "thousands of people" story. Density is staged for readability, not realism.
- No animation, no simulation. Water motion is implied by coral posture, sediment
  drifts and light, all static.
