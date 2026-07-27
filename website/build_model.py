import numpy as np, trimesh, json, copy
from smooth import angle_normals
import detail as DET
from trimesh.creation import icosphere, cylinder

def rbox(lo, hi, r=1.5):
    """Caixa com arestas arredondadas de raio r (hull de esferas nos cantos erodidos)."""
    lo=np.array(lo,float); hi=np.array(hi,float)
    r=min(r, float((hi-lo).min())/2.5)
    corners=np.array([[x,y,z] for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])])
    c=(lo+hi)/2
    pts=[]
    sph=icosphere(subdivisions=1, radius=r).vertices
    for v in corners:
        vv=v.copy()
        for i in range(3): vv[i] += -r if v[i]>c[i] else r
        pts.append(sph+vv)
    return trimesh.Trimesh(vertices=np.vstack(pts)).convex_hull

def hull_rounded(verts, r=3.0):
    verts=np.array(verts,float); c=verts.mean(0)
    sph=icosphere(subdivisions=1, radius=r).vertices
    pts=[]
    for v in verts:
        vv=v.copy()
        for i in range(3):
            if abs(v[i]-c[i])>r*1.2: vv[i] += -r if v[i]>c[i] else r
        pts.append(sph+vv)
    return trimesh.Trimesh(vertices=np.vstack(pts)).convex_hull

def cyl(x0,x1,y,z,r,sections=64):
    m=cylinder(radius=r, height=abs(x1-x0), sections=sections)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]))
    m.apply_translation([(x0+x1)/2, y, z]); return m

def box(lo,hi):
    lo=np.array(lo,float); hi=np.array(hi,float)
    m=trimesh.creation.box(extents=hi-lo); m.apply_translation((lo+hi)/2); return m

# ---------------- CASCO ----------------
def casco(sign):
    s=sign
    # envelope convexo: prisma X200-800 + cunha X0-200 (cotas exatas do STEP)
    V=[]
    for x in (200.,800.):
        for y in (59.,175.):
            for z in (0.,146.): V.append([x,s*y,z])
    for y in (114.5,119.5):
        for z in (22.,116.): V.append([0.,s*y,z])
    h=hull_rounded(V, r=4.0)                      # r=4: aresta com fita de fibra + epoxi
    cuts=[]
    cuts.append(box([258.5,s*90.5 if s>0 else s*155.5, 45],[423.5, s*155.5 if s>0 else s*90.5, 150]))   # alojamento bateria
    cuts.append(box([200,  s*107 if s>0 else s*127, 136],[245, s*127 if s>0 else s*107, 150]))          # rasgo longarina proa
    cuts.append(box([430,  s*107 if s>0 else s*127, 136],[800, s*127 if s>0 else s*107, 150]))          # rasgo longarina re
    cuts.append(box([690,  s*92  if s>0 else s*142, 100],[780, s*142 if s>0 else s*92, 150]))           # alojamento ESC
    cuts.append(cyl(618, 802, s*117, 40, 20))                                                            # tunel de propulsao
    cuts.append(box([791, s*62 if s>0 else s*172, 3],[801, s*172 if s>0 else s*62, 143]))               # transom insert
    return trimesh.boolean.difference([h]+cuts, engine='manifold')

PARTS={}
def add(name, mesh, sub, color, metal=0.0, rough=0.75, dims=None, note=None):
    PARTS[name]=dict(mesh=mesh, sub=sub, color=color, metal=metal, rough=rough, dims=dims, note=note)

add('casco_direito', casco(+1), 'structure', '#e8e6e1', 0.0, 0.42, [800,116,146])
add('casco_esquerdo', casco(-1), 'structure', '#e8e6e1', 0.0, 0.42, [800,116,146])

WOOD='#c99a5b'; WOOD2='#d8b483'
for n,(x0,x1) in [('travessa_T1',(200,245)),('travessa_T2',(462.5,507.5)),('travessa_T3',(640.5,685.5))]:
    add(n, rbox([x0,-175,146],[x1,175,186],2.0),'structure',WOOD,0,0.7,[x1-x0,350,40])

MIR=[]
def addm(name, lo, hi, sub, color, metal=0, rough=0.7, r=1.5, note=None):
    lo=list(map(float,lo)); hi=list(map(float,hi))
    add(name, rbox(lo,hi,r), sub, color, metal, rough, [hi[0]-lo[0],hi[1]-lo[1],hi[2]-lo[2]], note)
    if name.endswith('_dir') or name.endswith('_1') or name.endswith('_3'):
        alt=name.replace('_dir','_esq').replace('_1','_2').replace('_3','_4')
        lo2=[lo[0],-hi[1],lo[2]]; hi2=[hi[0],-lo[1],hi[2]]
        add(alt, rbox(lo2,hi2,r), sub, color, metal, rough, [hi[0]-lo[0],hi[1]-lo[1],hi[2]-lo[2]], note)

addm('longarina_proa_dir',[200,107,136],[245,127,146],'structure',WOOD,0,0.7,1.5)
addm('longarina_re_dir',[430,107,136],[800,127,146],'structure',WOOD,0,0.7,1.5)
addm('escotilha_dir',[248.5,80.5,146],[433.5,165.5,150],'structure',WOOD2,0,0.6,2.0)
addm('transom_insert_dir',[791,62,3],[800,172,143],'structure','#b98b52',0,0.75,1.5)
addm('cobertura_ESC_dir',[690,92,146],[785,142,175],'structure',WOOD2,0,0.6,3.0)
addm('calco_IP66_1',[250,58,146],[274,78,152],'structure',WOOD,0,0.7,1.0)
addm('calco_IP66_3',[434,58,146],[458,78,152],'structure',WOOD,0,0.7,1.0)

add('caixa_IP66', rbox([252,-77.5,152],[456,77.5,252],4.0),'compute','#9aa3ac',0.0,0.45,[204,155,100])

addm('bateria_5000_dir',[263.5,99,45],[418.5,147,80],'power','#2f3338',0,0.55,3.0)
add('bateria_pi_2200', rbox([257.5,-52.5,155],[292.5,52.5,180],3.0),'power','#2f3338',0,0.55,[35,105,25])
add('conversor_DCDC_5V', rbox([300,38,155],[365,73,175],1.0),'power','#1f6f8c',0.3,0.5,[65,35,20])
add('distribuidor_fusiveis', rbox([388,30,155],[448,70,185],1.5),'power','#b02b2b',0,0.6,[60,40,30])
add('sensor_corrente', rbox([390,10,155],[421,23,170],1.0),'power','#8c1a1a',0,0.6,[31,13,15])

# ---------- componentes detalhados (detail.py) ----------
def place(parts, origin, rot=None, name='peca', sub='compute', dims=None):
    """junta as sub-pecas de um componente detalhado, agrupadas por material"""
    import collections
    g = collections.defaultdict(list)
    for mat, m in parts:
        mm = m.copy()
        if rot is not None: mm.apply_transform(rot)
        mm.apply_translation(origin)
        g[mat].append(mm)
    first = True
    for mat, ms in g.items():
        col, met, rou = DET.MATERIALS[mat]
        mesh = trimesh.util.concatenate(ms)
        add('%s__%s' % (name, mat), mesh, sub, col, met, rou,
            dims if first else None)
        first = False

RZ = lambda a: trimesh.transformations.rotation_matrix(np.radians(a), [0,0,1])

# Raspberry Pi 4 — deitado, conectores virados para bombordo
place(DET.raspberry_pi_4(), [300, -72, 163], None, 'raspberry_pi_4', 'compute', [85,56,20])
# ESP32 DevKit
place(DET.esp32_devkit(),   [300,   5, 163], None, 'esp32_devkit',   'compute', [55,28,13])
# GPS NEO-8M no topo do mastro
place(DET.gps_neo8m(),      [260,  47, 240], None, 'gps_modulo',     'sensing', [25,25,8])
# BNO055 elevado e centrado
place(DET.bno055(),         [400,-13.5,215], None, 'bno055_imu',     'sensing', [20,27,5])

add('ads1015', rbox([423,10,155],[448,28,159],1.0),'compute','#17a8b0',0,0.55,[25,18,4])


add('suporte_BNO055', rbox([403,-7,155],[417,7,215],1.5),'sensing','#8f949b',0.6,0.4,[14,14,60])

add('suporte_GPS', rbox([262,55,155],[277,69,240],1.5),'sensing','#8f949b',0.6,0.4,[15,14,85])

addm('esc_dir',[695,97,104],[775,137,134],'propulsion','#26282c',0,0.5,2.0)
for s in (+1,-1):
    t='dir' if s>0 else 'esq'
    place(DET.motor_bl(), [630, s*117, 40], None, 'motor_%s'%t, 'propulsion', [70,36,36])
    add('veio_motor_%s'%t, cyl(700,720,s*117,40,2.5,24),'propulsion','#6f757d',0.9,0.25,[20,5,5])
    mirror = None if s>0 else trimesh.transformations.scale_matrix(1,direction=[0,1,0])
    place(DET.waterjet(), [720, s*117, 40], None, 'waterjet_%s'%t, 'propulsion', [95,24,24])
    place(DET.servo(),    [700, s*117-6, 56], None, 'servo_bocal_%s'%t, 'propulsion', [23,12,22])

# ------------- montagem, orientacao Y-up, metros -------------
CX=407.5
M=np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]],float)   # Z-up -> Y-up
scene=trimesh.Scene(); meta={}
for name,p in PARTS.items():
    m=p['mesh'].copy()
    m.apply_translation([-CX,0,0]); m.apply_transform(M); m.apply_scale(0.001)
    V,F,N,UV = angle_normals(m, deg=38.0)
    m2 = trimesh.Trimesh(vertices=V, faces=F, vertex_normals=N, process=False)
    c=trimesh.visual.color.hex_to_rgba(p['color'])
    m2.visual=trimesh.visual.TextureVisuals(uv=UV, material=trimesh.visual.material.PBRMaterial(
        name=name, baseColorFactor=c, metallicFactor=p['metal'],
        roughnessFactor=p['rough'], doubleSided=False))
    scene.add_geometry(m2, geom_name=name, node_name=name)
    b=p['mesh'].bounds
    meta[name]=dict(sub=p['sub'], color=p['color'],
                    dims=[round(float(x),1) for x in (p['dims'] or (b[1]-b[0]))],
                    bbox=[[round(float(v),1) for v in b[0]],[round(float(v),1) for v in b[1]]])
out='assets/sailsafe.glb'
scene.export(out)
json.dump(meta, open('assets/part_meta.json','w'), indent=1)
import os
print('pecas:',len(PARTS),' triangulos:',sum(len(p['mesh'].faces) for p in PARTS.values()))
print('GLB:', round(os.path.getsize(out)/1024,1),'kB  (com normais suavizadas por angulo)')
