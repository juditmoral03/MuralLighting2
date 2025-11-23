import mitsuba as mi
print(mi.__file__)
import drjit as dr

import time


mi.set_variant("llvm_ad_rgb")

from MyNormalMap import MyNormalMap

mi.register_bsdf("mynormalmap", lambda props: MyNormalMap(props))
from mitsuba import ScalarTransform4f as T

"""my_normalmap = mi.load_dict({
    'type' : 'mynormalmap',
    'tint' : [0.2, 0.9, 0.2],
    'eta' : 1.33
})"""

def create_scene(p, plugin):
    scene_def = {
        'type': 'scene',
        'integrator': {
            'type': 'path'
        },
        'light': {
            'type': 'constant',
            'radiance': 0.99,
        },
        'rectangle': {
            'type': 'obj',
            'filename': 'model/XII_2/Pedret_XII.baked-1.obj', 
            'face_normals': False, 
            'bsdf': {
                'type': plugin,
                'normalmap': {
                    'type': 'bitmap',
                    'raw': True,
                    'filename': 'textures/pedret_XII/Pedret_X_normals_1.png'
                },
                'bsdf': {
                    'type': 'diffuse',
                    'reflectance': {
                        'type': 'bitmap',
                        'filename': 'textures/pedret_XII/Pedret_X_color_1.png'
                    }
                }
            }
        },
        'sensor': {
            'type': 'perspective', 
            'fov_axis': 'x', 
            'fov': 61.9, 
            'near_clip': 0.1,
            'far_clip': 1000.0, 
            'to_world': T().translate(mi.ScalarPoint3f(0,0,0)) @
                    T().rotate([0, 1, 0], 0) @
                    T().rotate([0, 0, 1], 0) @
                    T().rotate([-1, 0, 0], (0)),
            'sampler': {
                'type': 'independent', 
                'sample_count': 4
            }, 
            'film': {
                'type': 'hdrfilm',
                'width': 540, 
                'height': 540, 
                'filter': {
                    'type': 'box'
                }
            }
        }
    }
    print(scene_def)
    return mi.load_dict(scene_def)

print("Start rendering...")

points = [[0,0,5], [5,0,5], [-5,0,5], [0,5,5], [0,-5,5]]
plugins = ['mynormalmap', 'normalmap']
i = 0
for point in points[:1]:
    for plugin in plugins[:1]:
        start_time = time.perf_counter()
        scene = create_scene(point, plugin)
        print(scene)
        image = mi.render(scene)
        end_time = time.perf_counter()
        elapsed_time = end_time-start_time
        print(f"Done in {elapsed_time} seconds.")
        mi.util.write_bitmap('renderPedret/normalmap/rectangle_scene'+str(i)+'_'+plugin+'.png', image)
    i = i+1

point, plugin = [0,0,5], 'mynormalmap'