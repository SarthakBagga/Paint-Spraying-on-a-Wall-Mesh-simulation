import warp as wp
import numpy as np
from PIL import Image, ImageFilter
import math

wp.init()


N_PARTICLES      = 10000       
N_DROPLETS       = 12000 

N_SWEEPS         = 3 
N_ROWS_PER_SWEEP = 10
N_STEPS_PER_ROW  = 8
N_STEPS          = N_SWEEPS * N_ROWS_PER_SWEEP * N_STEPS_PER_ROW  # 240 number of steps

WALL_WIDTH  = 2.0
WALL_HEIGHT = 2.0
WALL_Z      = 0.05

SPRAY_SPREAD   = 0.7         
SPRAY_RANGE    = 2.5
GAUSSIAN_SIGMA = 0.30     

NOZZLE_Z       = -1.0        

SPRAY_WORLD_SIGMA = 0.40      
DROPLET_JITTER    = 0.015     

SPLAT_RADIUS = 1               
SPLAT_SIGMA  = 0.6             

RES = 512



@wp.kernel
def spray_kernel(
    origin: wp.vec3,
    wall_z: float,
    width: float,
    height: float,
    spread: float,
    max_range: float,
    sigma: float,
    seed: int,
    hits: wp.array(dtype=wp.vec2),
    weights: wp.array(dtype=float),
):
    tid = wp.tid()

    state = wp.rand_init(seed, tid)
    u = wp.randf(state)
    v = wp.randf(state)

    angle_x = (u - 0.5) * spread
    angle_y = (v - 0.5) * spread

    direction = wp.normalize(wp.vec3(angle_x, angle_y, 1.0))

    if direction[2] <= 0.0:
        weights[tid] = 0.0
        return

    t = (wall_z - origin[2]) / direction[2]

    if t <= 0.0 or t > max_range:
        weights[tid] = 0.0
        return

    hit = origin + t * direction

    if wp.abs(hit[0]) <= width * 0.5 and wp.abs(hit[1]) <= height * 0.5:
        hits[tid] = wp.vec2(hit[0], hit[1])
        theta_sq = angle_x * angle_x + angle_y * angle_y
        intensity = wp.exp(-theta_sq / (2.0 * sigma * sigma))
        weights[tid] = intensity
    else:
        weights[tid] = 0.0



def _build_splat_kernel():
    """Pre-compute a normalised 2-D Gaussian splat kernel."""
    R = SPLAT_RADIUS
    dxs, dys, ws = [], [], []
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            w = math.exp(-(dx * dx + dy * dy) / (2.0 * SPLAT_SIGMA ** 2))
            dxs.append(dx); dys.append(dy); ws.append(w)
    total = sum(ws)
    ws = [w / total for w in ws]
    return (np.array(dxs, dtype=np.int32),
            np.array(dys, dtype=np.int32),
            np.array(ws,  dtype=np.float64))

SPLAT_DX, SPLAT_DY, SPLAT_W = _build_splat_kernel()



def _deposit_gaussian_droplets(paint_map, nozzle_x, nozzle_y, rng):
    dx = rng.normal(0.0, SPRAY_WORLD_SIGMA, N_DROPLETS)
    dy = rng.normal(0.0, SPRAY_WORLD_SIGMA, N_DROPLETS)

    dx += rng.normal(0.0, DROPLET_JITTER, N_DROPLETS)
    dy += rng.normal(0.0, DROPLET_JITTER, N_DROPLETS)

    world_x = nozzle_x + dx
    world_y = nozzle_y + dy

    u = (world_x + WALL_WIDTH  / 2.0) / WALL_WIDTH
    v = (world_y + WALL_HEIGHT / 2.0) / WALL_HEIGHT

    valid = (u >= 0.0) & (u <= 1.0) & (v >= 0.0) & (v <= 1.0)
    u = u[valid]
    v = v[valid]

    px = np.clip((u * (RES - 1)).astype(np.int32), 0, RES - 1)
    py = np.clip((v * (RES - 1)).astype(np.int32), 0, RES - 1)

    
    weight = 1.0                           
    for sdx, sdy, sw in zip(SPLAT_DX, SPLAT_DY, SPLAT_W):
        py_s = np.clip(py + int(sdy), 0, RES - 1)
        px_s = np.clip(px + int(sdx), 0, RES - 1)
        np.add.at(paint_map, (py_s, px_s), weight * sw)



def _launch_spray(step, position):
    """Fire the Warp kernel for one nozzle position (Task 2 requirement)."""
    x_pos, y_pos, z_pos = position
    spray_origin = wp.vec3(x_pos, y_pos, z_pos)

    hits    = wp.zeros(N_PARTICLES, dtype=wp.vec2)
    weights = wp.zeros(N_PARTICLES, dtype=float)

    wp.launch(
        kernel=spray_kernel,
        dim=N_PARTICLES,
        inputs=[
            spray_origin, WALL_Z, WALL_WIDTH, WALL_HEIGHT,
            SPRAY_SPREAD, SPRAY_RANGE, GAUSSIAN_SIGMA,
            step, hits, weights,
        ],
    )




def _save_texture(paint_map, step, ref_max):
    normalized = np.clip(paint_map / ref_max, 0.0, 1.0)
    normalized = np.sqrt(normalized)          # gamma 0.5

    img = np.zeros((RES, RES, 3), dtype=np.uint8)
    img[:, :, 0] = (normalized * 255).astype(np.uint8)

    Image.fromarray(img).save(f"paint_step_{step:03d}.png")


def _save_uniform_texture(paint_map, ref_max, filename="paint_final.png"):
    nonzero = paint_map > 0.01 * ref_max
    if np.any(nonzero):
        p5 = np.percentile(paint_map[nonzero], 5)
    else:
        p5 = ref_max

    normalized = np.clip(paint_map / p5, 0.0, 1.0)
    normalized[~nonzero] = 0.0

    img = np.zeros((RES, RES, 3), dtype=np.uint8)
    img[:, :, 0] = (normalized * 255).astype(np.uint8)

    image = Image.fromarray(img)
    image = image.filter(ImageFilter.GaussianBlur(radius=4))
    image = image.filter(ImageFilter.GaussianBlur(radius=2))
    image.save(filename)
    print(f"Saved uniform final texture → {filename}")


# Nozzle path - uses a serpentine path for spraying paint

def compute_nozzle_path(n_sweeps=N_SWEEPS,
                        rows_per_sweep=N_ROWS_PER_SWEEP,
                        steps_per_row=N_STEPS_PER_ROW,
                        x_range=1.05, y_range=1.05,
                        z_pos=NOZZLE_Z):
    """Build a serpentine nozzle path that covers the wall *n_sweeps* times.

    The range deliberately exceeds the wall boundaries (±1.0) so that
    the spray fully covers the edges and corners.
    """
    positions = []
    total_rows = n_sweeps * rows_per_sweep

    for row_idx in range(total_rows):
        sweep   = row_idx // rows_per_sweep
        local_r = row_idx %  rows_per_sweep

        if sweep % 2 == 0:
            y = -y_range + (2.0 * y_range) * local_r / max(rows_per_sweep - 1, 1)
        else:
            y = y_range - (2.0 * y_range) * local_r / max(rows_per_sweep - 1, 1)

        for s in range(steps_per_row):
            t = s / max(steps_per_row - 1, 1)
            if row_idx % 2 == 0:
                x = -x_range + 2.0 * x_range * t
            else:
                x = x_range - 2.0 * x_range * t
            positions.append((float(x), float(y), z_pos))

    return positions




def run_simulation():
    nozzle_positions = compute_nozzle_path()
    total_steps = len(nozzle_positions)
    rng = np.random.default_rng(42)        

    print("Phase 1 — Computing reference maximum …")
    paint_ref = np.zeros((RES, RES), dtype=np.float64)
    rng_ph1   = np.random.default_rng(42)  

    for step in range(total_steps):
        x_pos, y_pos, _ = nozzle_positions[step]
        _deposit_gaussian_droplets(paint_ref, x_pos, y_pos, rng_ph1)
        if (step + 1) % 60 == 0 or step == total_steps - 1:
            print(f"  … {step + 1}/{total_steps}")

    ref_max = np.max(paint_ref)
    print(f"  ref_max = {ref_max:.2f}")

    
    print("Phase 2 — Generating frame textures …")
    paint_map = np.zeros((RES, RES), dtype=np.float64)
    rng_ph2   = np.random.default_rng(42)  

    for step in range(total_steps):
        x_pos, y_pos, z_pos = nozzle_positions[step]

        
        _launch_spray(step, nozzle_positions[step])
        _deposit_gaussian_droplets(paint_map, x_pos, y_pos, rng_ph2)

        _save_texture(paint_map, step, ref_max)

        sweep_num = step // (N_ROWS_PER_SWEEP * N_STEPS_PER_ROW) + 1
        print(f"Step {step + 1}/{total_steps}  sweep {sweep_num}/{N_SWEEPS}"
              f"  nozzle ({x_pos:+.2f}, {y_pos:+.2f})")

    _save_uniform_texture(paint_map, ref_max)

    print("Simulation complete.")
    return paint_map, nozzle_positions


if __name__ == "__main__":
    print("Running on device:", wp.get_device())
    run_simulation()