# NEON_RITUAL — PRODUCTION NOTES

**Underground Electronic Experience — 15 s 3D event advertisement**
Blender 5.2.3 LTS · EEVEE · 1080 × 1920 · 30 fps · 450 frames · H.264/AAC

Status: **complete and delivered.**

---

## 1. Deliverables

| File | Size |
|---|---|
| `NEON_RITUAL.blend` | 2,995,042 B |
| `NEON_RITUAL_FINAL.mp4` | 11,341,630 B |
| `NEON_RITUAL_BUILD.py` | 485 B — entry point, loads `scripts/` |
| `NEON_RITUAL_ANIMATION.py` | animation entry point |
| `NEON_RITUAL_RENDER.py` | render + ffmpeg encode entry point |
| `NEON_RITUAL_ASSET_LIBRARY.blend` | full-scene asset library copy |
| `audio/NEON_RITUAL_AUDIO.wav` | 2,880,044 B — final track |
| `audio/NEON_RITUAL_AUDIO_CINEMATIC.wav` | 2,880,044 B — alternate |
| `frames/0001.png … 0450.png` | 450 frames, 1080 × 1920 |
| `PREVIEW/` | HD stills, font specimens, marker tests, contact sheet |
| `PRODUCTION_NOTES.md` | this file |

Final MP4 verification (ffmpeg 6.1.1 + Blender movie clip):

```
Duration 00:00:15.00
Video    H.264 High, yuv420p, 1080 × 1920, 30 fps
Audio    AAC LC, 48 kHz, stereo, 192 kb/s
Frames   450
```

Blender verification, reopened from disk:

```
scene       NEON_RITUAL
objects     717
triangles   304,590
cameras     8
lights      80
actions     52
markers     8
collections 47
materials   28
frames      1–450
resolution  1080 × 1920
fps         30
samples     24 (EEVEE)
camera      CAM_01_CORRIDOR
```

---

## 2. What was built

A single interconnected industrial-cathedral venue, not a collage of props.

### Main hall
38 × 60 × 34 m. Nave 18 m wide, two side aisles, eight 26 m pillars per side,
seven pointed nave arches, transverse aisle arches, catwalks at 12 m, steel
trusses at 28–30 m, side chapels, a 4.5 × 6 × 18 m approach corridor, and a
three-arch apse.

### Central stage
16 m circular base, two upper tiers, a real five-step front stair, steel
understructure, cable trays, DJ booth with turntables and LED screens, two
speaker stacks, a 13 m lighting truss, and a red-lit ritual pedestal.

### Hero assets
- **Chrome sculpture**: nine Bezier ribbons/tendrils, mixed round tubes and
  wide flat profiles, 23,722 verts / 47,328 tris, a red crystal core, six
  floating chrome shards, and a thin red support beam.
- **Orbital ring**: three concentric segmented rings at z = 22 m, machined
  brackets, red inner strips, four ceiling struts. The rings counter-rotate.
- **NEON RITUAL typography**: Canterbury blackletter, thickened outline,
  extruded and beveled, custom blade terminals and an eight-point sigil.
  The top line uses a slightly brighter brushed-chrome material (see
  limitations); the bottom line is full chrome. The sign hangs from four
  rods behind the letters.
- **Ritual halo**: dark metal frame plus a red inner ring behind the sculpture,
  switched on with the title reveal.

### Environment / atmosphere
Wet floor with puddle-varied roughness, red floor strips, hundreds of
procedural architecture and prop objects, hanging chains, red banners with modeled
folds, industrial crates/barrels/pipes/fans/tanks/generators/fences/cameras/
panels/cables/barriers, dust motes, ground fog, smoke volumes, and a large
white light shaft through the ring.

---

## 3. Cameras and edit

Eight cameras, eight timeline markers, hard cuts.

| Shot | Frames | Camera | Lens | Move |
|---|---|---|---|---|
| 01 Approach | 1–90 | `CAM_01_CORRIDOR` | 24 mm | forward dolly, tilt up |
| 02 Reveal | 91–180 | `CAM_02_REVEAL` | 35 mm | push into the nave, tilt up |
| 03 Title intro | 181–240 | `CAM_03_TITLE` | 32 mm | push, slight orbit |
| 04 Title hero | 241–300 | `CAM_04_HERO` | 28 mm | low-angle push |
| 05 Event info | 301–360 | `CAM_05_INFO` | 32 mm | slow push on the info |
| 06 Wide | 361–390 | `CAM_06_WIDE` | 18 mm | pull back / crane |
| 07 Impact | 391–420 | `CAM_07_IMPACT` | 35 mm | low-angle push |
| 08 End | 421–450 | `CAM_08_END` | 28 mm | hold, tagline |

The title is dark in shots 1–2, then the halo, vertical light bars, title
backlight and white key are keyed on between frames 180–210. The sign is
revealed by light, not by a scale-in. The rings counter-rotate; the sculpture
turns slowly; banners sway 1–2°; the sculpture has an extra turn at the
impact; the fragments drift; the fog noise is keyed over the full 15 s.

Info is visible only in frames 301–360. The end frame carries the title,
secondary line and tagline only.

---

## 4. Materials and lighting

28 materials, all procedural:

- `CHROME_MIRROR` — metallic 1.0, roughness 0.10–0.20, anisotropic, micro-bump.
- `CHROME_TITLE_TOP` — metallic 0.95, roughness 0.18, slight warm emission
  (0.12) so the top title line survives the dark vault.
- `AGED_CONCRETE`, `CONCRETE_DARK` — noise color variation and bump.
- `WET_FLOOR` — dark base, coat 1.0, puddle roughness 0.035–0.30.
- `RED_EMISSIVE`, `RED_HOT` — neon strips, stage edges, halo, rods.
- `RED_FABRIC`, `BLACK_GLASS`, `LED_RED`, `DUST`, `SIGIL`, `DARK_GUNMETAL`.
- Dedicated emitters for info, tagline, secondary, halo and the stage light bar,
  so each can be gated and pulsed independently.

Lighting: 80 lights total, dominated by practicals — one overhead key spot,
two white rims, a chrome softbox, a stage wash, a ring uplight, ten red
architecture washes, neutral wall/arch reveals, a front pillar fill, a
corridor fill, the title key/rim/soft/low/on-axis set, the large white beam,
and 16 small red pillar-rod practicals. World volume plus ground fog and
three smoke volumes; the vertical white/red ritual bars and the red halo are
physical emissive set pieces and are what the chrome actually reflects.

Compositor: AgX Punchy, exposure +0.70, exposure fade-in at frames 1–12,
restrained Bloom, slight lens distortion/dispersion, and a soft vignette.
Motion blur is off to keep chrome and neon crisp.

---

## 5. Audio

Original synthesized soundtrack, no licensed or ripped audio.

- 120 BPM · D Phrygian · 15.0 s · 48 kHz / 16-bit stereo.
- Sub drone, four-on-the-floor kick (3–10 s, break 10–12 s, re-entry 12 s),
  sidechained bass, metallic percussion, chain rattles, bell, red-alert synth,
  risers, and impacts at the cut points 3, 6, 8, 10, 12, 13 and 14 s.
- Peak −1.9 dBFS, RMS −9.2 dBFS. Fade-in 2.5 s, fade-out 0.35 s.
- Final MP4 uses `NEON_RITUAL_AUDIO.wav`; a no-four-on-floor cinematic variant
  is included for comparison.
- Audio is intentionally **not** from the TikTok references.

---

## 6. Render pipeline

- 450 frames at 1080 × 1920, EEVEE, 24 TAA samples, 30 fps.
- Rendered in 50-frame batches through the live Blender MCP session;
  ~3.4 s/frame, ~26 minutes total.
- PNG sequence `frames/0001.png … 0450.png` (450/450 present, 0 missing).
- Encoded with ffmpeg 6.1.1 (libx264, CRF 18, High profile, yuv420p,
  AAC 192 kb/s, 48 kHz, `-movflags +faststart`).
- ffmpeg command used:

```
ffmpeg -y -framerate 30 -start_number 1 -i frames/%04d.png \
  -i audio/NEON_RITUAL_AUDIO.wav \
  -c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium \
  -profile:v high -level 4.1 \
  -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart \
  NEON_RITUAL_FINAL.mp4
```

- Blender 5.2's VSE image-strip encode crashed on the 450-element strip in
  this environment; the delivered MP4 is the ffmpeg encode above. The VSE
  path remains in `scripts/nr_render.py` as a fallback/experiment.

---

## 7. Bugs found and fixed

1. **Stale `matrix_world` in joins.** The first build collapsed pillars,
   arches, trusses, catwalk stairs and the dust field because `matrix_world`
   had not been evaluated when objects were joined. This produced a white
   column in the centre of the stage (a 12 m staircase stacked at the origin),
   short pillars, flat arches and missing ceiling trusses. Fixed by calling
   `bpy.context.view_layer.update()` before reading transforms in
   `join_objects`, `origin_to_world` and `text_to_mesh`.
2. **Title top line disappeared.** Pure mirror chrome on the upper line
   reflected the dark vault and read as black. The top line now uses a
   slightly brighter brushed chrome with a small warm emission; the lower
   line stays full chrome.
3. **Info ghosting.** White info text was visible in shots 3–4 even with
   emission 0 because the white base color caught the key lights. Fixed with
   black base colors and hard `hide_render` gates.
4. **Info persisted into the wide shot.** Moved the info cut to frame 361,
   matching the shot boundary.
5. **White floor strip looked like a column.** Removed; the final floor
   reflections come from the stage and red strips.
6. **Title suspension rods crossed the letters.** Moved behind the sign.
7. **Horizontal white light bar crossed the title.** Removed; the title
   lights and vertical bars now do the reflection work.
8. **VSE encode crash** on the 450-element image strip; switched to ffmpeg.
9. **Marker/camera switching** verified at frames 90/91, 180/181, 360/361,
   420/421 and 450; `scene.camera` resolves to the correct shot camera.

---

## 8. Known limitations / honest compromises

1. **Top title line is a lighter metal**, not full mirror chrome. It reads
   clearly but is slightly different from the lower line. A pure chrome top
   line vanished against the dark upper vault at every tested light position.
2. **Stage and LED detail are simpler than the reference.** The stage has the
   main tiers, stairs, DJ booth, two speaker stacks, back screen and truss,
   but not the dense speaker wall / crowd-scale detail of the poster.
3. **Concrete is procedural, not texture-baked.** At 1080 × 1920 the large
   forms read; close-up grunge is smoother than the reference.
4. **Banners are modeled folds plus object sway**, not cloth simulation.
   Chosen for determinism and render speed.
5. **Fog/smoke are volume shaders**, not fluid simulations.
6. **No motion blur.** It would smear the neon and chrome; the camera moves
   are slow and eased.
7. **80 lights** is a lot, mostly small practicals. EEVEE handles the scene
   at 3.4 s/frame on the RTX 3050 laptop.
8. **Event details are placeholders**, filled at the user's request:
   `SAT, 24 MAY 2025 · THE VOID`, `JAKARTA`, `TICKETS AT NEONRITUAL.COM`.
   They are not claims about a real event.
9. **Audio is synthesized**, not a commercial track. It is timed to the cuts
   but has not been evaluated by ear by the agent; the cinematic alternate is
   included for comparison.
10. **Asset library is a full-scene copy.** It contains every master and placed
    asset, but is not stripped to a masters-only file.
11. **The central beam crosses the info text** in the event-info shot. It is
    part of the ritual lighting language; the text remains readable.
12. **The opening corridor is deliberately very dark.** It is a motion shot:
    the dolly, the fade-in and the audio build carry it. The frame-60 still
    reads darker than the hero frames; that is intentional.

---

## 9. Reproduction

```python
# Build
p = r"D:\Tes Animasi-Motion-Blender\NEON_RITUAL\NEON_RITUAL_BUILD.py"
ns = {"__name__": "boot", "__file__": p}
exec(compile(open(p, encoding="utf-8").read(), p, "exec"), ns)
ns["build"]()          # builds and saves NEON_RITUAL.blend (~2 s)

# Animation is included by build(); to apply separately on a fresh build:
exec(open(r"...\NEON_RITUAL_ANIMATION.py", encoding="utf-8").read())
apply()

# Render 450 PNGs
exec(open(r"...\NEON_RITUAL_RENDER.py", encoding="utf-8").read())
render_all(1, 450)

# Encode
encode_final()
```

Deterministic: the procedural build uses fixed seeds; the same scripts produce
the same scene and the same frame sequence. The build entry point expects a
Blender GUI/MCP session or a working headless Blender with EEVEE; the delivered
frames were rendered through the live MCP session.

---

## 10. Preview set

```
PREVIEW/HD_S1_corridor.png
PREVIEW/HD_S2_reveal.png
PREVIEW/HD_S3_title.png
PREVIEW/HD_S4_hero.png
PREVIEW/HD_S5_info.png
PREVIEW/HD_S6_wide.png
PREVIEW/HD_S7_impact.png
PREVIEW/HD_S8_end.png
PREVIEW/00_font_specimen.png
PREVIEW/00_font_specimen2.png
PREVIEW/00_contact_sheet.png
PREVIEW/MK_*.png (marker/cut tests)
```

The final hero frame is `HD_S8_end.png`; the title hero is `HD_S4_hero.png`;
the environment reveal is `HD_S6_wide.png`.
