from pxr import Usd, UsdGeom, Sdf

def create_wall_usd(filename="wall.usda"):

    stage = Usd.Stage.CreateNew(filename)

    mesh = UsdGeom.Mesh.Define(stage, "/Wall")

    width = 2.0
    height = 2.0
    thickness = 0.1

    w = width / 2
    h = height / 2
    t = thickness / 2

    # 8 cube vertices
    points = [
        (-w, -h, -t),  
        ( w, -h, -t),  
        ( w,  h, -t),  
        (-w,  h, -t),  
        (-w, -h,  t),  
        ( w, -h,  t),  
        ( w,  h,  t), 
        (-w,  h,  t), 
    ]

    faceVertexCounts = [4,4,4,4,4,4]

    faceVertexIndices = [
        0,1,2,3,   
        4,5,6,7,   
        0,4,7,3,
        1,5,6,2,
        3,2,6,7,
        0,1,5,4
    ]

    mesh.CreatePointsAttr(points)
    mesh.CreateFaceVertexCountsAttr(faceVertexCounts)
    mesh.CreateFaceVertexIndicesAttr(faceVertexIndices)

    uv = [
        (0,0),(1,0),(1,1),(0,1),  
        (0,0),(1,0),(1,1),(0,1)   
    ]

    primvars = UsdGeom.PrimvarsAPI(mesh)
    st = primvars.CreatePrimvar(
        "st",
        Sdf.ValueTypeNames.TexCoord2fArray,
        UsdGeom.Tokens.vertex
    )
    st.Set(uv)

    stage.GetRootLayer().Save()
    print("wall.usda created successfully.")


if __name__ == "__main__":
    create_wall_usd()