# Robotic Spray Painting Simulation using Warp and OpenUSD

## Overview

This project implements a **simulated robotic spray-painting system** that models how paint droplets are emitted from a moving spray nozzle and accumulate on a wall surface over time. The simulation combines **particle-based spray modeling using NVIDIA Warp** with a **Gaussian droplet deposition model** to produce realistic paint coverage textures.

The resulting textures are applied to a **3D wall model in OpenUSD**, allowing the painting process to be visualized in tools such as `usdview`.

The simulation mimics real industrial spray-coating systems by moving the spray nozzle in a **serpentine pattern across the wall**, gradually building up paint layers until the surface is uniformly coated.

This project has been made with respect to the assignment guidelines provided.

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




