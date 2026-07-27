import numpy as np
from collections import defaultdict

def angle_normals(mesh, deg=38.0, uv_scale=0.30):
    """Normais por canto com limite de angulo (suave nas concordancias, nitido
       nas arestas duras) + UV por projeccao de caixa. Reindexa por (pos,normal,uv)."""
    V=mesh.vertices.view(np.ndarray); F=mesh.faces.view(np.ndarray)
    FN=mesh.face_normals.view(np.ndarray); A=mesh.area_faces.view(np.ndarray)
    inc=defaultdict(list)
    for fi,f in enumerate(F):
        for vi in f: inc[vi].append(fi)
    cos=np.cos(np.radians(deg))
    cornerN=np.zeros((len(F),3,3))
    for fi,f in enumerate(F):
        n0=FN[fi]
        for k,vi in enumerate(f):
            acc=np.zeros(3)
            for fj in inc[vi]:
                if FN[fj]@n0>=cos: acc+=FN[fj]*A[fj]
            ln=np.linalg.norm(acc)
            cornerN[fi,k]=acc/ln if ln>1e-12 else n0
    P=V[F].reshape(-1,3); N=cornerN.reshape(-1,3)
    # box mapping: eixo dominante da normal da FACE (nao do canto)
    ax=np.abs(FN).argmax(1)
    UV=np.zeros((len(F),3,2))
    pair={0:(2,1),1:(0,2),2:(0,1)}
    for fi,f in enumerate(F):
        a,b=pair[ax[fi]]
        UV[fi,:,0]=V[f][:,a]/uv_scale
        UV[fi,:,1]=V[f][:,b]/uv_scale
    UV=UV.reshape(-1,2)
    key=np.round(np.hstack([P*1e5, N*1e3, UV*1e3])).astype(np.int64)
    _,first,inv=np.unique(key,axis=0,return_index=True,return_inverse=True)
    return P[first], inv.reshape(-1,3).astype(np.int64), N[first], UV[first]
