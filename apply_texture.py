from pxr import Usd, UsdShade, Sdf

def apply_texture(stage_path, texture_path, output_path):

    stage = Usd.Stage.Open(stage_path)
    material = UsdShade.Material.Define(stage, "/WallMaterial")
    shader = UsdShade.Shader.Define(stage, "/WallMaterial/PreviewSurface")
    shader.CreateIdAttr("UsdPreviewSurface")
    texture = UsdShade.Shader.Define(stage, "/WallMaterial/DiffuseTexture")
    texture.CreateIdAttr("UsdUVTexture")

    texture.CreateInput(
        "file", Sdf.ValueTypeNames.Asset
    ).Set(texture_path)

    texture.CreateInput(
        "st", Sdf.ValueTypeNames.Float2
    )

    tex_output = texture.CreateOutput(
        "rgb", Sdf.ValueTypeNames.Float3
    )

    diffuse_input = shader.CreateInput(
        "diffuseColor",
        Sdf.ValueTypeNames.Color3f
    )
    diffuse_input.ConnectToSource(tex_output)

    surface_output = shader.CreateOutput(
        "surface",
        Sdf.ValueTypeNames.Token
    )

    material_surface = material.CreateSurfaceOutput()
    material_surface.ConnectToSource(surface_output)

    wall_prim = stage.GetPrimAtPath("/Wall")
    UsdShade.MaterialBindingAPI(wall_prim).Bind(material)

    stage.GetRootLayer().Export(output_path)

    print(f"{output_path} saved successfully.")


if __name__ == "__main__":
    apply_texture(
        "wall.usda",
        "paint_step_059.png",   
        "wall_painted.usda"
    )