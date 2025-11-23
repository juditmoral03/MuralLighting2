import mitsuba as mi

mi.set_variant('scalar_spectral')

from mitsuba import ScalarTransform4f as T
import pandas as pd
import os

#FUNCTIONS-----------------------------------------------------------------------------------

def create_obj_shape(filename, normal_texture, color_texture):
    return {
        'type': 'obj',
        'filename': filename,
        'bsdf': {
            'type': 'twosided',
            'bsdf': {
                'type': 'normalmap',
                'normalmap': {
                    'type': 'bitmap',
                    'raw': True,
                    'filename': normal_texture
                },
                'bsdf': {
                    'type': 'diffuse',
                    'reflectance': {
                        'type': 'bitmap',
                        'filename': color_texture,
                    },
                },
            },
        }
    }
    
def create_sphere_light(center, radius, radiance_scale):
    return {
        'type': 'sphere',
        'center': center,
        'radius': radius,
        'emitter': {
            'type': 'area',
            'radiance': {
                'type': 'd65',
                'scale': radiance_scale  # Adjustable intensity scale
            }
        }
    }

def load_sensor(r, phi, theta):
    # Convert from spherical to Cartesian coordinates and define the sensor's position and orientation
    origin = T.rotate([0, 0, 1], phi).rotate([0, 1, 0], theta) @ mi.ScalarPoint3f([0, 0, r])
    return mi.load_dict({
        'type': 'perspective',
        'fov': 20,
        'to_world': T.look_at(
            origin= origin,
            target=[0, 0, 0],
            up=[0, 1, 0]
        ),
        'sampler': {
            'type': 'independent',
            'sample_count': 128
        },
        'film': {
            'type': 'hdrfilm',
            'width': 1920,
            'height': 1080,
            'rfilter': {
                'type': 'tent',
            },
            'pixel_format': 'rgb',
        },
    })










#-------------------------------------------------------------------------------------------------------------------

sphere_light = create_sphere_light([10, 15, 25], 2, 30.0)

obj_shape1 = create_obj_shape('model/XII/1_Pedret_XII.obj', 'textures/pedret_XII/Pedret_X_normals_1.png', 'textures/pedret_XII/Pedret_X_color_1.png')
obj_shape2 = create_obj_shape('model/XII/2_Pedret_XII.obj', 'textures/pedret_XII/Pedret_X_normals_2.png', 'textures/pedret_XII/Pedret_X_color_2.png')
obj_shape3 = create_obj_shape('model/XII/3_Pedret_XII.obj', 'textures/pedret_XII/Pedret_XII_normals_absC.png', 'textures/pedret_XII/Pedret_XII_color_absC.png')
obj_shape4 = create_obj_shape('model/XII/4_Pedret_XII.obj', 'textures/pedret_XII/Pedret_XII_normals_absN.png', 'textures/pedret_XII/Pedret_XII_color_absN.png')
obj_shape5 = create_obj_shape('model/XII/5_Pedret_XII.obj', 'textures/pedret_XII/Pedret_XII_normals_absS.png', 'textures/pedret_XII/Pedret_XII_color_absS.png')
obj_shape6 = create_obj_shape('model/XII/6_Pedret_XII.obj', 'textures/pedret_XII/Pedret_XII_normals_nau.png', 'textures/pedret_XII/Pedret_XII_color_nau.png')



# Redefining the scene
scene_definition = {
    'type': 'scene',
    'integrator': {
        'type': 'path',
        'max_depth': 2
    },
    'shape1': obj_shape1,
    'shape2': obj_shape2,
    'shape3': obj_shape3,
    'shape4': obj_shape4,
    'shape5': obj_shape5,
    'shape6': obj_shape6,
    'sphere_def': sphere_light
}

scene = mi.load_dict(scene_definition)

sensor_count = 2  # Adjust this as needed
radius = 200
phis = [20.0 * i for i in range(sensor_count)]*0
theta = 0

# Create sensors based on the above parameters
sensors = [load_sensor(radius, phi, theta) for phi in phis]

# Render the scene from the perspectives of all sensors
images = [mi.render(scene, spp=16, sensor=sensor) for sensor in sensors]

# Save each image to a separate file
for i, img in enumerate(images):
    filename = f'renderXII/mytry{i}.png'
    mi.util.write_bitmap(filename, img)
    print(f'Saved: {filename}')