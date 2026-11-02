# Paradise After Dark — Tropical Futuristic Festival Courtyard

Procedural Blender environment built from the eight visual references in
`visual reference/`. The environment pass, hero stills and the 15 second
animation are included.

## Deliverables

| File | What it is |
| --- | --- |
| `render_preview.png` | 1920x1080 hero still, Cycles, 96 samples + denoise |
| `render_preview_eevee.png` | Same frame, EEVEE, 64 samples (authored engine) |
| `PARADISE_AFTER_DARK_15s.mp4` | 15 s / 450 frame / 30 fps / 1080p EEVEE animation |
| `PARADISE_AFTER_DARK_15s_poster.png` | 1920x1080 poster frame decoded from the MP4 |
| `tropical_festival_courtyard.blend` | Complete still scene, collections, camera, lights |
| `tropical_festival_courtyard_15s.blend` | Animated scene with the 15 s camera orbit |
| `build_environment.py` | Rebuilds the scene from an empty file |
| `animate_scene.py` | Adds the camera orbit and all motion, saves the 15 s blend |
| `render_final.py` | Renders the two 1920x1080 still previews |
| `render_animation.py` | Renders the H.264 animation (with `--test` for 10 frames) |
| `scripts/tf_core.py` | Scene settings, materials, primitives |
| `scripts/tf_arch.py` | Pavilion, stage, pool, deck, canopy lights, decor |
| `scripts/tf_nature.py` | Palms, fan palms, monstera, banana, flowers, crowd |
| `scripts/tf_look.py` | Sky, sun, fill, camera, compositor, reflection probe |
| `renders/` | Inspection renders, camera tests, animation log |
| `assets/` | Asset notes (all geometry is procedural) |

## Scene specification

- Site: compact courtyard, roughly 24 x 18 m of usable floor; the wider
  ground and backdrop extend beyond it.
- Pavilion: central lotus shell ~16 m across the lower wings, dome apex
  ~10.4 m. White ceramic shell, white ribs, pastel iridescent glass inlays.
- Stage: 7.0 x 3.5 x 0.6 m, DJ booth, LED wall, speaker stacks, arch with
  neon line and brand sign.
- Pool: 13.4 x 4.7 m organic lagoon in the foreground, with caustic floor,
  turquoise water, white stepping stones, lily pads and a rock waterfall.
- Camera: 19 mm, 16:9, at (-1.8, -10.5, 1.35) aiming at (0.4, 2.6, 2.6).
  The pool occupies the lower third, the shell and palms frame the top.
- Render: 1920x1080, AgX, Medium High Contrast, exposure -0.45.
  EEVEE 64 samples; the hero still uses Cycles 96 samples + OpenImageDenoise.
- Scene size: around 690 objects in the saved .blend.
- Collections: architecture, petals, dome, stage, LED, pool/waterfall,
  tropical trees, plants, crowd, landscape, festival decor, lighting,
  cameras, masters. All geometry is generated with bmesh/curves; there are
  no image planes or external textures. The only external file is the
  League Spartan font used for the 3D signage.

## Look and intent

The target is not photoreal CGI. It is a clean, art-directed tropical
futurism: white organic architecture, pastel iridescent glass, dense green
foliage, coral/orange flowers and a clear turquoise lagoon. The reference
images drove the composition, the white shell/rib language, the glass
inlays, the pool foreground and the layered palm skyline.

The scene is authored for EEVEE so it can be animated later. The EEVEE
preview is included for comparison. The Cycles preview is the quality
target for stills; its GI, soft shadows and water reflection read much
closer to the references.

## Rebuild / render

```powershell
# rebuild geometry, materials, camera and save the .blend
& "D:\Steam\steamapps\common\Blender\blender.exe" -b --python build_environment.py

# render the two 1920x1080 previews from the saved .blend
& "D:\Steam\steamapps\common\Blender\blender.exe" -b tropical_festival_courtyard.blend --python render_final.py

# add the 15 s camera orbit / motion and save the animated .blend
& "D:\Steam\steamapps\common\Blender\blender.exe" -b tropical_festival_courtyard.blend --python animate_scene.py

# render the animation (add -- --test for a 10-frame encode check)
& "D:\Steam\steamapps\common\Blender\blender.exe" -b tropical_festival_courtyard_15s.blend --python render_animation.py
```

`build_environment.py` currently calls `build(with_plants=True, render=True,
quick=True)`, so it also writes a 960x540 `renders/blockout.png` for quick
inspection.

## The 15 second animation

- 450 frames at 30 fps, 1920x1080, H.264, silent.
- One continuous lateral orbit / slider move: the camera travels from a
  left 3/4 at (-5.2, -10.6, 1.50) to a right 3/4 at (3.2, -9.9, 1.62),
  keeping the pool in the lower third and the shell centered. 19 mm lens,
  f/8 DOF, target moves from (0.3, 2.8, 2.9) to (0.1, 2.9, 3.0).
- Motion: 4D noise drift on the water and pool-floor caustics, scrolling
  LED phase, a slow neon pulse, bobbing floating lanterns, palm sway and a
  subtle DJ bob.
- Render recipe: EEVEE, 16 samples, compositor on, DOF on, screen-space
  raytracing at half resolution, only the sun casts shadows. The planar
  reflection probe is hidden for animation because re-baking it every
  frame costs about 10x; screen-space reflections still carry the water.
- Measured cost with that recipe: **1.76 s per 1080p frame** on this CPU.
  450 frames rendered in **13m 12s**; the H.264 file is 14.4 MB.

## 30 second feasibility (answered)

30 seconds at 30 fps is 900 frames. At 1080p:

- Cycles, 96 samples: roughly 6-10 minutes per frame, so 900 frames is not
  practical (90+ hours).
- EEVEE at the animation recipe above: 1.76 s per frame, so 900 frames is
  roughly 27-35 minutes plus iteration. Technically safe.
- The creative risk is repetition, not render time. A single compact
  courtyard padded to 30 seconds will feel long. A 30 second cut made of
  6-8 distinct 4-5 second shots (wide, pool reflection, shell detail, stage,
  palms, sign, plants) is the stronger choice.

## Validation performed

- Headless Blender 5.2.3 LTS, EEVEE and Cycles.
- Multiple camera angles tested: front, left 3/4, right 3/4, elevated 3/4,
  low 19 mm pool foreground, plus orbit start/end frames.
- Sign text verified close-up after fixing the dome base ring that crossed
  the plaque.
- Pool caustics, stepping stones and reflections checked in both engines.
- 10-frame H.264 test decoded at 1920x1080 / 30 fps before the full render.
- No image textures; no external asset packs.

## Known limitations / next pass

- Geometry is stylized and low-to-mid density; it does not attempt scanned
  foliage or photoreal displacement.
- The crowd was removed from the hero shot because the simple stand-in
  figures read as mannequins at this scale. Only a single dark DJ
  silhouette remains behind the booth. A better crowd is a separate
  modelling task.
- The waterfall is a stylized rock stack with three white streams at the
  right edge; it is intentionally secondary.
- Water is shader-driven, not simulated. The animation drifts animated 4D
  noise through the water and caustic shaders; a true fluid bake or moving
  normal map is a later upgrade.
- The 15 s cut is silent. Music/SFX and a final grade are the next audio /
  post step.
- The canopy in the references is represented by festoon lights and hanging
  vines rather than a full glass roof, to keep the sky and the shell
  silhouette readable from the hero angle.
