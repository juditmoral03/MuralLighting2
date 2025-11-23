import mitsuba as mi
import numpy as np

mi.set_variant('scalar_spectral')

from mitsuba import ScalarTransform4f as T
import os
import pandas as pd

def create_emitter_spdfile(position, spd_filename):
    return {
            'type': 'point',
            'position': position,
            'intensity': {
                'type': 'spectrum',
                'filename': spd_filename
            }
        }


def create_sphere_light_file(center, radius, file):
    return {
        'type': 'sphere',
        'center': center,
        'radius': radius,
        'emitter': {
            'type': 'area',
            'radiance': {
                'type': 'spectrum',
                'filename': file
            }
        }
    }

def create_distant_directional_emitter(direction, file):
    return {
        'type' : 'directional',
        'direction': direction,
        'irradiance':{
            'type':'spectrum',
            'filename': file,
        }
    }

def create_constant_enviroment_emitter(file):
    return{
        'type': 'constant',
        'radiance': {
            'type': 'spectrum',
            'filename': file,
        }
    }

def create_spd_file_and_emitter(sheet_name, number, filepath='data/IT1073.xlsx'):
    # Adjust to use the actual column names for wavelength and intensity
    df = pd.read_excel(filepath, sheet_name=sheet_name, skiprows=1)
    df = df.drop([0, 1])
    df = df.drop(df.columns[0], axis=1)
    df = df.rename(columns={'ID medida': 'Longitud de onda'})
    output_filename = f"spdvid/{sheet_name}_{number}.spd"

    with open(output_filename, 'w') as file:
        for index, row in df.iterrows():
            # Ensure the correct intensity column is referenced in the f-string
            file.write(f"{row['Longitud de onda']} {row[number]}\n")
    
    return create_emitter_spdfile([6.5284 , 1.1359 , -16.852 ], output_filename)
    #return create_sphere_light_file([6.5284 , 1.1359 , -16.852 ],  0.05, output_filename)
    


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

def create_perspective_camera():
    return {
        'type': 'perspective',
        'fov_axis': 'x',
        'fov': 39.597755,
        'near_clip': 0.1,
        'far_clip': 100.0,
        'to_world': T.translate([1.400590 , -0.601761 , -15.005084]) @
                    T.rotate([0, 0, 1], -171.86098766942905) @
                    T.rotate([0, 1, 0], 60.259371273194176) @
                    T.rotate([1, 0, 0], 179.99944493344438),
        'sampler': {
            'type': 'independent',
            'sample_count': 4096
        },
        'film': {
            'type': 'hdrfilm',
            'width': 1920,
            'height': 1080
        }
    }


def ConvertCSVtoSPD_lig(csv_file_path, spd_filename):
    # Read the CSV file, skipping the first 13 rows
    df = pd.read_csv(csv_file_path, delimiter=',', skiprows=13)
    
    # Display the first few rows 
    #print(df.head())
    #print("DataFrame Columns:", df.columns)
    
    # Write the spectral data to an SPD file
    with open(spd_filename, 'w') as file:
        for index, row in df.iterrows():
            file.write(f"{row['wavelength']} {row[' intensity']}\n")
    #print(f"SPD file '{spd_filename}' has been created.")



def create_scene(emitters):
    obj_shape1 = create_obj_shape('model/XII/1_Pedret_XII.obj', 'textures/pedret_XII/Pedret_X_normals_1.png', 'textures/pedret_XII/Pedret_X_color_1.png')
    obj_shape2 = create_obj_shape('model/XII/2_Pedret_XII.obj', 'textures/pedret_XII/Pedret_X_normals_2.png', 'textures/pedret_XII/Pedret_X_color_2.png')
    obj_shape3 = create_obj_shape('model/XII/3_Pedret_XII.obj', 'textures/pedret_XII/Pedret_XII_normals_absC.png', 'textures/pedret_XII/Pedret_XII_color_absC.png')
    obj_shape4 = create_obj_shape('model/XII/4_Pedret_XII.obj', 'textures/pedret_XII/Pedret_XII_normals_absN.png', 'textures/pedret_XII/Pedret_XII_color_absN.png')
    obj_shape5 = create_obj_shape('model/XII/5_Pedret_XII.obj', 'textures/pedret_XII/Pedret_XII_normals_absS.png', 'textures/pedret_XII/Pedret_XII_color_absS.png')
    obj_shape6 = create_obj_shape('model/XII/6_Pedret_XII.obj', 'textures/pedret_XII/Pedret_XII_normals_nau.png', 'textures/pedret_XII/Pedret_XII_color_nau.png')


    scene_definition = {
        'type': 'scene',
        'integrator': {
            'type': 'path',
            'max_depth': 7 #posar mes
        },
        'shape1': obj_shape1,
        'shape2': obj_shape2,
        'shape3': obj_shape3,
        'shape4': obj_shape4,
        'shape5': obj_shape5,
        'shape6': obj_shape6,
        'sensor': create_perspective_camera()
    }

    for i, emitter in enumerate(emitters):
        scene_definition[f'emitter{i+1}'] = emitter

    scene = mi.load_dict(scene_definition)

    # Render the scene
    image = mi.render(scene, spp=16)  # Sensor is already included in the scene

    # Save the rendered image to a file
    filename = f'rendersProvesemitters/constantEnv_distant.exr'
    mi.util.write_bitmap(filename, image)
    print(f'Saved: {filename}')

#CODE--------------------------------------------------------------------------------------
direction = np.array([-0.2024, 0.8916, -0.4050])
#sun
file_sun = 'spdFiles/XII/sun_spectrum.spd'
#d65
file_d65_csv = 'emitters/2661-StandardIlluminant-D65-StandardIlluminant.csv'
file_d65_spd = 'spdFiles/XII/d65_spectrum.spd'
ConvertCSVtoSPD_lig(file_d65_csv, file_d65_spd)
file_d65 = 'spdFiles/XII/d65_spectrum.spd'

#global pedret
df = pd.read_csv('emitters/pedret.ext.txt', delim_whitespace=True)

df_selected = df[['Wvlgth', 'Global_horizn_irradiance']]
file_global_pedret_csv = 'emitters/global_pedret.csv'
file_global_pedret_spd = 'spdFiles/XII/global_pedret.spd'
df_selected.to_csv(file_global_pedret_csv, index=False)

df_new = pd.read_csv(file_global_pedret_csv, delimiter=',')    
with open(file_global_pedret_spd, 'w') as file:
    for index, row in df_new.iterrows():
        file.write(f"{row['Wvlgth']} {row['Global_horizn_irradiance']}\n")

file_global_pedret = 'spdFiles/XII/global_pedret.spd'

#diffuse pedret
df_selected = df[['Wvlgth', 'Difuse_horizn_irradiance']]
file_difuse_pedret_csv = 'emitters/difuse_pedret.csv'
file_difuse_pedret_spd = 'spdFiles/XII/difuse_pedret.spd'
df_selected.to_csv(file_difuse_pedret_csv, index=False)

df_new = pd.read_csv(file_difuse_pedret_csv, delimiter=',')    
with open(file_difuse_pedret_spd, 'w') as file:
    for index, row in df_new.iterrows():
        file.write(f"{row['Wvlgth']} {row['Difuse_horizn_irradiance']}\n")

file_difuse_pedret = 'spdFiles/XII/difuse_pedret.spd'


#distance emitter
my_emitter1 =  create_distant_directional_emitter(direction, file_sun)

#constant enviroment
my_emitter3 = create_constant_enviroment_emitter(file_difuse_pedret)
sheet_name='Medida Continua. Parafina diam3'
my_emitter2 = create_spd_file_and_emitter(sheet_name='Medida Continua. Parafina diam3', number=2)  

create_scene([my_emitter1, my_emitter2, my_emitter3])


