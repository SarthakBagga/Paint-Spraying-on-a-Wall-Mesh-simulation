# Robotic Spray Painting Simulation using Warp and OpenUSD

## Overview

This project implements a **simulated robotic spray-painting system** that models how paint droplets are emitted from a moving spray nozzle and accumulate on a wall surface over time. The simulation combines **particle-based spray modeling using NVIDIA Warp** with a **Gaussian droplet deposition model** to produce realistic paint coverage textures.

The resulting textures are applied to a **3D wall model in OpenUSD**, allowing the painting process to be visualized in tools such as `usdview`.

The simulation mimics real industrial spray-coating systems by moving the spray nozzle in a **serpentine pattern across the wall**, gradually building up paint layers until the surface is uniformly coated.

---

## Key Features

* **Particle-based spray simulation**

  * Implemented using the Warp simulation framework
  * Generates thousands of spray particles per step
  * Particles propagate toward the wall and compute hit positions

* **Gaussian spray falloff**

  * Spray intensity decreases with angular distance from the center of the nozzle
  * Produces realistic center-heavy spray patterns

* **Droplet-based paint deposition**

  * Thousands of droplets are deposited onto the wall surface
  * Each droplet contributes a small Gaussian splat to the paint map
  * Accumulation across time produces paint thickness

* **Serpentine robotic spray path**

  * The nozzle moves across the wall using a raster sweep pattern
  * Multiple passes ensure full coverage of the surface

* **Paint accumulation model**

  * Paint coverage is stored in a 2D grid representing the wall surface
  * Each simulation step adds paint to the surface

* **Texture generation**

  * A paint coverage map is exported as image textures
  * Frames are generated for each step of the simulation

* **OpenUSD visualization**

  * The generated textures can be applied to a wall mesh
  * The result can be inspected in `usdview`

---




---

## Simulation Workflow

The simulation follows several steps:

### 1. Create Wall Geometry

A wall surface is generated using OpenUSD.

```
python wall_model.py
```

This creates:

```
wall.usda
```

The wall is represented as a mesh that acts as the paint target.

---

### 2. Run the Spray Simulation

```
python spray_sim.py
```

The simulation performs:

1. Compute nozzle path across the wall
2. Emit spray particles using Warp
3. Generate droplet deposition on the wall surface
4. Accumulate paint thickness
5. Save texture frames

Outputs include:

```
paint_step_000.png
paint_step_001.png
...
paint_step_239.png
paint_final.png
```

---

### 3. Apply the Paint Texture

```
python apply_texture.py
```

This attaches the generated paint texture to the wall mesh in the USD scene.

Output:

```
wall_painted.usda
```

---

### 4. Visualize in usdview

Navigate to the OpenUSD tools directory:

```
cd usd_root
source python-usd-venv/bin/activate
./scripts/usdview_gui.sh ../wall_painted.usda
```

You will see the painted wall with the applied texture.

---



Multiple sweeps ensure uniform coverage.

---

## Simulation Parameters

Key parameters controlling the simulation that i made:

| Parameter           | Description                           |
| ------------------- | ------------------------------------- |
| `N_PARTICLES`       | Number of spray particles emitted     |
| `N_DROPLETS`        | Number of droplets deposited per step |
| `N_SWEEPS`          | Number of complete wall passes        |
| `SPRAY_SPREAD`      | Width of the spray cone               |
| `GAUSSIAN_SIGMA`    | Controls spray falloff                |
| `SPRAY_WORLD_SIGMA` | Spread of droplets on wall            |
| `RES`               | Texture resolution                    |

---


Install dependencies:

```
pip install warp-lang numpy pillow
pip install usd-core
```

---

