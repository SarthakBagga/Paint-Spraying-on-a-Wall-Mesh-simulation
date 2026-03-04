#!/usr/bin/env python3

# Creates an animated USD scene for task 5

from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf
import numpy as np
import math
import os

from spray_sim import (
    run_simulation, compute_nozzle_path,
    N_STEPS, N_SWEEPS, N_ROWS_PER_SWEEP, N_STEPS_PER_ROW,
    WALL_WIDTH, WALL_HEIGHT, WALL_Z,
    SPRAY_SPREAD, NOZZLE_Z, RES,
)


def create_animated_scene(nozzle_positions, output_path="wall_animated.usda",
                          texture_file="paint_final.png"):
    
    n_frames = len(nozzle_positions)

    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)

    
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(n_frames - 1)
    stage.SetFramesPerSecond(24)
    stage.SetTimeCodesPerSecond(24)

    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

    
    wall = UsdGeom.Mesh.Define(stage, "/World/Wall")

    w = WALL_WIDTH  / 2.0
    h = WALL_HEIGHT / 2.0
    t = 0.05                         

    points = [
        (-w, -h, -t), ( w, -h, -t), ( w,  h, -t), (-w,  h, -t),   
        (-w, -h,  t), ( w, -h,  t), ( w,  h,  t), (-w,  h,  t),   
    ]
    fvc = [4, 4, 4, 4, 4, 4]
    fvi = [
        0, 1, 2, 3,         
        4, 5, 6, 7,         
        0, 4, 7, 3,         
        1, 5, 6, 2,         
        3, 2, 6, 7,         
        0, 1, 5, 4,         
    ]
    uv = [(0, 0), (1, 0), (1, 1), (0, 1)] * 2   

    wall.CreatePointsAttr(points)
    wall.CreateFaceVertexCountsAttr(fvc)
    wall.CreateFaceVertexIndicesAttr(fvi)

    pv = UsdGeom.PrimvarsAPI(wall)
    st = pv.CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray,
                          UsdGeom.Tokens.vertex)
    st.Set(uv)

   
    mat = UsdShade.Material.Define(stage, "/World/WallMaterial")

    surf = UsdShade.Shader.Define(stage, "/World/WallMaterial/PreviewSurface")
    surf.CreateIdAttr("UsdPreviewSurface")

    tex = UsdShade.Shader.Define(stage, "/World/WallMaterial/DiffuseTexture")
    tex.CreateIdAttr("UsdUVTexture")
    tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(texture_file)
    tex.CreateInput("st", Sdf.ValueTypeNames.Float2)
    tex_rgb = tex.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)

    surf.CreateInput("diffuseColor",
                     Sdf.ValueTypeNames.Color3f).ConnectToSource(tex_rgb)
    surf_out = surf.CreateOutput("surface", Sdf.ValueTypeNames.Token)
    mat.CreateSurfaceOutput().ConnectToSource(surf_out)

    UsdShade.MaterialBindingAPI(wall).Bind(mat)

  
    noz_mat = UsdShade.Material.Define(stage, "/World/NozzleMaterial")
    noz_sh  = UsdShade.Shader.Define(stage, "/World/NozzleMaterial/Surface")
    noz_sh.CreateIdAttr("UsdPreviewSurface")
    noz_sh.CreateInput("diffuseColor",
                       Sdf.ValueTypeNames.Color3f).Set((0.15, 0.15, 0.15))
    noz_sh.CreateInput("metallic",
                       Sdf.ValueTypeNames.Float).Set(0.9)
    noz_sh.CreateInput("roughness",
                       Sdf.ValueTypeNames.Float).Set(0.3)
    noz_out = noz_sh.CreateOutput("surface", Sdf.ValueTypeNames.Token)
    noz_mat.CreateSurfaceOutput().ConnectToSource(noz_out)

   
    spr_mat = UsdShade.Material.Define(stage, "/World/SprayMaterial")
    spr_sh  = UsdShade.Shader.Define(stage, "/World/SprayMaterial/Surface")
    spr_sh.CreateIdAttr("UsdPreviewSurface")
    spr_sh.CreateInput("diffuseColor",
                       Sdf.ValueTypeNames.Color3f).Set((1.0, 0.15, 0.05))
    spr_sh.CreateInput("opacity",
                       Sdf.ValueTypeNames.Float).Set(0.25)
    spr_sh.CreateInput("roughness",
                       Sdf.ValueTypeNames.Float).Set(1.0)
    spr_out = spr_sh.CreateOutput("surface", Sdf.ValueTypeNames.Token)
    spr_mat.CreateSurfaceOutput().ConnectToSource(spr_out)

    nozzle_xf = UsdGeom.Xform.Define(stage, "/World/SprayNozzle")
    noz_tr    = nozzle_xf.AddTranslateOp()

    for frame, (nx, ny, nz) in enumerate(nozzle_positions):
        noz_tr.Set(Gf.Vec3d(nx, ny, nz), frame)

    body = UsdGeom.Cube.Define(stage, "/World/SprayNozzle/Body")
    body.CreateSizeAttr(1.0)
    body_xf = UsdGeom.Xformable(body)
    body_xf.AddScaleOp().Set(Gf.Vec3f(0.06, 0.06, 0.10))

    UsdShade.MaterialBindingAPI(body).Bind(noz_mat)

   
    distance      = abs(WALL_Z - NOZZLE_Z)          
    spread_radius = distance * math.tan(SPRAY_SPREAD / 2.0)

    spray_xf = UsdGeom.Xform.Define(stage, "/World/SprayCone")
    spr_tr   = spray_xf.AddTranslateOp()

    for frame, (nx, ny, nz) in enumerate(nozzle_positions):
        mid_z = (nz + WALL_Z) / 2.0
        spr_tr.Set(Gf.Vec3d(nx, ny, mid_z), frame)

    spray_xf.AddRotateXOp().Set(180.0)

    cone = UsdGeom.Cone.Define(stage, "/World/SprayCone/Cone")
    cone.CreateHeightAttr(distance)
    cone.CreateRadiusAttr(spread_radius)
    cone.CreateAxisAttr("Z")

    UsdShade.MaterialBindingAPI(cone).Bind(spr_mat)

    
    stage.GetRootLayer().Save()

    print(f"Animated scene saved → {output_path}")
    print(f"  Frames : 0 – {n_frames - 1}")
    print(f"  FPS    : 24")
    print(f"  Texture: {texture_file}")
    print(f"  View with:  usdview {output_path}")



if __name__ == "__main__":

    
    print("=" * 60)
    print("– Creating wall surface (wall.usda)")
    print("=" * 60)
    from wall_model import create_wall_usd
    create_wall_usd("wall.usda")

    print("\n" + "=" * 60)
    print("– Running spray simulation (serpentine path)")
    print("=" * 60)
    paint_map, nozzle_positions = run_simulation()

    
    print("\n" + "=" * 60)
    print("– Applying paint texture to wall_painted.usda")
    print("=" * 60)
    from apply_texture import apply_texture
    final_texture = "paint_final.png"
    apply_texture("wall.usda", final_texture, "wall_painted.usda")

    
    print("\n" + "=" * 60)
    print("– Building animated scene (wall_animated.usda)")
    print("=" * 60)
    create_animated_scene(nozzle_positions, texture_file=final_texture)

    print("\n" + "=" * 60)
    print("All tasks complete!")
    print("=" * 60)
