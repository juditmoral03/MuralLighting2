import mitsuba as mi
import numpy as np
mi.set_variant('cuda_spectral')

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

def create_obj_file_light_file(obj_file, radiance_file):
    return {
        'type': 'obj',
        'filename': obj_file,
        'emitter': {
            'type': 'area',
            'radiance': {
                'type': 'spectrum',
                'filename': radiance_file
            }
        },
        'bsdf': {
            'type': 'twosided',
            'bsdf': {
                'type': 'diffuse',
                'reflectance': {
                'type': 'rgb',
                'value': [1,1,1],
                }
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
            #file.write(f"{row['Longitud de onda']} {row[number]*1000}\n")
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

def create_shape_rgb(filename, color):
    return {
        'type': 'obj',
        'filename': filename,
        'bsdf': {
            'type': 'twosided',
            'bsdf': {
                'type': 'diffuse',
                'reflectance': {
                'type': 'rgb',
                'value': color,
                }
            }
        }
    }



def create_shape_dielectric(filename):
    return {
        'type': 'obj',
        'filename': filename,
        'bsdf': {
            'type': 'dielectric',
            'int_ior': 'bk7',
            'ext_ior':'air', 
        }
    }

#camera without using cuda
# def create_perspective_camera():
#     return {
#         'type': 'perspective',
#         'fov_axis': 'x',
#         'fov': 39.597755,
#         'near_clip': 0.1,
#         'far_clip': 100.0,
#         'to_world': T.translate([1.400590 , -0.601761 , -15.005084]) @
#                     T.rotate([0, 0, 1], -171.86098766942905) @
#                     T.rotate([0, 1, 0], 60.259371273194176) @
#                     T.rotate([1, 0, 0], 179.99944493344438),
#         'sampler': {
#             'type': 'independent',
#             'sample_count': 4
#         },
#         'film': {
#             'type': 'hdrfilm',
#             'width': 1920,
#             'height': 1080
#         }
#     }

#camera when we use cuda
#from mitsuba import ScalarTransform4f as T, ScalarPoint3f, Vector3f
from mitsuba.cuda_spectral import ScalarTransform4f as T, ScalarPoint3f, Vector3f

def create_perspective_camera():
    # Create the translation vector
    translation_vector = ScalarPoint3f(1.400590, -0.601761, -15.005084)
    
    # Create the scale vector (example values)
    scale_vector = ScalarPoint3f(1.0, 1.0, 1.0)

    
    return {
        'type': 'perspective',
        'fov_axis': 'x',
        'fov': 39.597755,
        'near_clip': 0.1,
        'far_clip': 100.0,
        'to_world': T().translate(translation_vector) @
                    T().scale(scale_vector) @
                    T().rotate([0, 0, 1], -171.86098766942905) @
                    T().rotate([0, 1, 0], 60.259371273194176) @
                    T().rotate([1, 0, 0], 179.99944493344438),
        'sampler': {
            'type': 'independent',
            'sample_count': 4
        },
        'film': {
            'type': 'hdrfilm',
            'width': 1920,
            'height': 1080,
            'filter':{'type':'box'}
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
            'max_depth': 4 #posar mes
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
    image = mi.render(scene, spp=500)  # Sensor is already included in the scene

    #denoising
    denoiser = mi.OptixDenoiser(input_size = image.shape[:2][::-1] , albedo = False, temporal=False)
    denoised = denoiser(image)

    # Save the denoised rendered image to a file
    denoised_filename = f'renderPedret/XII/rendersProvesEmitters/denoised.exr'
    mi.util.write_bitmap(denoised_filename, denoised)
    print(f'Saved: {denoised_filename}')


#CODE--------------------------------------------------------------------------------------
direction = np.array([-0.2024, -0.4050, -0.8916])
#sun
file_sun = 'spdFiles/XII/sun_spectrum.spd'
#d65
file_d65_csv = 'emitters/2661-StandardIlluminant-D65-StandardIlluminant.csv'
file_d65_spd = 'spdFiles/XII/d65_spectrum.spd'
ConvertCSVtoSPD_lig(file_d65_csv, file_d65_spd)
file_d65 = 'spdFiles/XII/d65_spectrum.spd'

#global pedret
df = pd.read_csv('emitters/pedret-d3t3.ext.txt', delim_whitespace=True)

df_selected = df[['Wvlgth', 'Global_horizn_irradiance']]
file_global_pedret_csv = 'emitters/global_pedret.csv'
file_global_pedret_spd = 'spdFiles/XII/global_pedret.spd'
df_selected.to_csv(file_global_pedret_csv, index=False)

df_new = pd.read_csv(file_global_pedret_csv, delimiter=',')    
with open(file_global_pedret_spd, 'w') as file:
    for index, row in df_new.iterrows():
        file.write(f"{row['Wvlgth']} {row['Global_horizn_irradiance']/(2*np.pi)}\n")

file_global_pedret = 'spdFiles/XII/global_pedret.spd'

#diffuse pedret
df_selected = df[['Wvlgth', 'Difuse_horizn_irradiance']]
file_difuse_pedret_csv = 'emitters/difuse_pedret.csv'
file_difuse_pedret_spd = 'spdFiles/XII/difuse_pedret.spd'
df_selected.to_csv(file_difuse_pedret_csv, index=False)

df_new = pd.read_csv(file_difuse_pedret_csv, delimiter=',')    
with open(file_difuse_pedret_spd, 'w') as file:
    for index, row in df_new.iterrows():
        file.write(f"{row['Wvlgth']} {row['Difuse_horizn_irradiance']/(2*np.pi)}\n")

file_difuse_pedret = 'spdFiles/XII/difuse_pedret.spd'

#direct normal pedret
df_selected = df[['Wvlgth', 'Direct_normal_irradiance']]
file_direct_normal_pedret_csv = 'emitters/direct_normal_pedret.csv'
file_direct_normal_pedret_spd = 'spdFiles/XII/direct_normal_pedret.spd'
df_selected.to_csv(file_direct_normal_pedret_csv, index=False)

df_new = pd.read_csv(file_direct_normal_pedret_csv, delimiter=',')    
with open(file_direct_normal_pedret_spd, 'w') as file:
    for index, row in df_new.iterrows():
        file.write(f"{row['Wvlgth']} {row['Direct_normal_irradiance']}\n")

file_direct_normal_pedret = 'spdFiles/XII/direct_normal_pedret.spd'

#distance emitter
my_emitter1 =  create_distant_directional_emitter(direction, file_global_pedret)

#constant enviroment
my_emitter3 = create_constant_enviroment_emitter(file_d65)
sheet_name='Medida Continua. Parafina diam3'
my_emitter2 = create_spd_file_and_emitter(sheet_name='Medida Continua. Parafina diam3', number=2)  

#artificial
def create_spd_file(sheet_name, position, filepath= 'data/IT1072.xlsx'):
    flame_area = 0.0013378719
    intensity_column = f'Unnamed: {position}'

    df = pd.read_excel(filepath, sheet_name=sheet_name, usecols=['Longitud de onda (nm)', intensity_column])
    
    df = df.drop(df.index[0])
    output_filename = f"spdFiles/XII/{sheet_name}_position{position}_by_flamearea.spd"

    with open(output_filename, 'w') as file:
        for index, row in df.iterrows():
            # Ensure the correct intensity column is referenced in the f-string
            #file.write(f"{row['Longitud de onda (nm)']} {(row[intensity_column]*1000)/flame_area}\n")
            file.write(f"{row['Longitud de onda (nm)']} {(row[intensity_column])/flame_area}\n")

#parafina
create_spd_file(sheet_name='Parafina_diam3_Horizontal', position=2)  
#aceite y sal
create_spd_file(sheet_name='Aceite_sal_Horizontal', position=2)



#POV 
#---------------------------------------------------------------------------------------------------------------------------------------------------
def create_perspective_camera_pv1():
    # Create the translation vector
    translation_vector = ScalarPoint3f(4.218666, 4.850953, 3.158030)
    
    # Create the scale vector
    scale_vector = ScalarPoint3f(1.0, 1.0, 1.0)

    return {
        'type': 'perspective',
        'fov_axis': 'x',
        'fov': 61.927515,
        'near_clip': 0.1,
        'far_clip': 1000.0,
        'to_world': T().translate(translation_vector) @
                    T().scale(scale_vector) @
                    T().rotate([1, 0, 0], 176.09519952083838) @
                    T().rotate([0, 1, 0], -66.83628336840451) @
                    T().rotate([0, 0, 1], -179.9997181410112 - 5.0),
        'sampler': {
            'type': 'independent',
            'sample_count': 4  
        },
        'film': {
            'type': 'hdrfilm',
            'width': 1920,  
            'height': 1080,  
            'filter': {'type': 'box'}
        }
    }

def create_perspective_camera_pv2():
    # Create the translation vector
    translation_vector = ScalarPoint3f(-0.690537, 5.133308, 1.291918)
    
    # Create the scale vector
    scale_vector = ScalarPoint3f(1.0, 1.0, 1.0)

    return {
        'type': 'perspective',
        'fov_axis': 'x',
        'fov': 61.927515,
        'near_clip': 0.1,
        'far_clip': 1000.0,
        'to_world': T().translate(translation_vector) @
                    T().scale(scale_vector) @
                    T().rotate([1, 0, 0], 174.5938966205129) @
                    T().rotate([0, 1, 0], -66.83964382147616) @
                    T().rotate([0, 0, 1], -179.99870727301402 - 5.0),
        'sampler': {
            'type': 'independent',
            'sample_count': 4
        },
        'film': {
            'type': 'hdrfilm',
            'width': 1920,
            'height': 1080,
            'filter': {'type': 'box'}
        }
    }

def create_perspective_camera_pv7():
    # Create the translation vector
    translation_vector = ScalarPoint3f(3.042980, 3.679800, 5.074699)
    
    # Create the scale vector
    scale_vector = ScalarPoint3f(1.0, 1.0, 1.0)

    return {
        'type': 'perspective',
        'fov_axis': 'x',
        'fov': 73.739795,
        'near_clip': 0.1,
        'far_clip': 1000.0,
        'to_world': T().translate(translation_vector) @
                    T().scale(scale_vector) @
                    T().rotate([1, 0, 0], 170.69448698183928) @
                    T().rotate([0, 1, 0], -48.53439875147807) @
                    T().rotate([0, 0, 1], -179.9996908202545 -5.0),
        'sampler': {
            'type': 'independent',
            'sample_count': 4
        },
        'film': {
            'type': 'hdrfilm',
            'width': 1920,
            'height': 1080,
            'filter': {'type': 'box'}
        }
    }



#C1
#---------------------------------------------------------------------------------------------------------------------------------------------------

#CAM C1 --> same as C3
#SCENE C1

def create_sceneC1(emitters):
    obj_shape1 = create_obj_shape('model/XII_2/Pedret_XII.baked-1.obj', 'textures/pedret_XII/Pedret_X_normals_1.png', 'textures/pedret_XII/Pedret_X_color_1.png')
    obj_shape2 = create_obj_shape('model/XII_2/Pedret_XII.baked-2.obj', 'textures/pedret_XII/Pedret_X_normals_2.png', 'textures/pedret_XII/Pedret_X_color_2.png')
    obj_shape3 = create_obj_shape('model/XII_2/Pedret_XII.baked-absC.obj', 'textures/pedret_XII/Pedret_XII_normals_absC.png', 'textures/pedret_XII/Pedret_XII_color_absC.png')
    obj_shape4 = create_obj_shape('model/XII_2/Pedret_XII.baked-absN.obj', 'textures/pedret_XII/Pedret_XII_normals_absN.png', 'textures/pedret_XII/Pedret_XII_color_absN.png')
    obj_shape5 = create_obj_shape('model/XII_2/Pedret_XII.baked-absS.obj', 'textures/pedret_XII/Pedret_XII_normals_absS.png', 'textures/pedret_XII/Pedret_XII_color_absS.png')
    obj_shape6 = create_obj_shape('model/XII_2/Pedret_XII.baked-nau.obj', 'textures/pedret_XII/Pedret_XII_normals_nau.png', 'textures/pedret_XII/Pedret_XII_color_nau.png')

    #corona
    anella = create_shape_rgb('iluminació/c1/Corona/Anella.obj', [0.05, 0.05, 0.05])
    anella2 = create_shape_rgb('iluminació/c1/Corona/Anella2.obj', [0.05, 0.05, 0.05])
    baseCorona = create_shape_rgb('iluminació/c1/Corona/Base.obj', [0.05, 0.05, 0.05])
    cadena = create_shape_rgb('iluminació/c1/Corona/Cadena.obj', [0.05, 0.05, 0.05])
    cadena2 = create_shape_rgb('iluminació/c1/Corona/Cadena2.obj', [0.05, 0.05, 0.05])
    cadena3 = create_shape_rgb('iluminació/c1/Corona/Cadena3.obj', [0.05, 0.05, 0.05])
    ganxo = create_shape_rgb('iluminació/c1/Corona/Ganxo.obj', [0.05, 0.05, 0.05])
    ganxo2 = create_shape_rgb('iluminació/c1/Corona/Ganxo2.obj', [0.05, 0.05, 0.05])
    ganxo3 = create_shape_rgb('iluminació/c1/Corona/Ganxo3.obj', [0.05, 0.05, 0.05])
    ganxo4 = create_shape_rgb('iluminació/c1/Corona/Ganxo4.obj', [0.05, 0.05, 0.05])
    llums = create_shape_dielectric('iluminació/c1/Corona/Llums.obj') 
    flama1 = create_obj_file_light_file('iluminació/c1/Corona/flama1.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')
    flama2 = create_obj_file_light_file('iluminació/c1/Corona/flama2.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')
    flama3 = create_obj_file_light_file('iluminació/c1/Corona/flama3.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')
    flama4 = create_obj_file_light_file('iluminació/c1/Corona/flama4.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')
    flama5 = create_obj_file_light_file('iluminació/c1/Corona/flama5.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')
    flama6 = create_obj_file_light_file('iluminació/c1/Corona/flama6.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')

    #llantia1
    argolla_l1 = create_shape_rgb('iluminació/c1/Llantia1/Argolla.obj', [0.05, 0.05, 0.05])
    cordill1Mesh_l1 = create_shape_rgb('iluminació/c1/Llantia1/Cordill1Mesh.obj', [0.05, 0.05, 0.05])
    cordill2Mesh_l1 = create_shape_rgb('iluminació/c1/Llantia1/Cordill2Mesh.obj', [0.05, 0.05, 0.05])
    cordill3Mesh_l1 = create_shape_rgb('iluminació/c1/Llantia1/Cordill3Mesh.obj', [0.05, 0.05, 0.05])
    cordill4Mesh_l1 = create_shape_rgb('iluminació/c1/Llantia1/Cordill4Mesh.obj', [0.05, 0.05, 0.05])
    llum_l1 = create_shape_dielectric('iluminació/c1/Llantia1/Llum.obj')
    flama_l1 = create_obj_file_light_file('iluminació/c1/Llantia1/Flama.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')

    #llantia2
    argolla_l2 = create_shape_rgb('iluminació/c1/Llantia2/Argolla.obj', [0.05, 0.05, 0.05])
    cordill1Mesh_l2 = create_shape_rgb('iluminació/c1/Llantia2/Cordill1Mesh.obj', [0.05, 0.05, 0.05])
    cordill2Mesh_l2 = create_shape_rgb('iluminació/c1/Llantia2/Cordill2Mesh.obj', [0.05, 0.05, 0.05])
    cordill3Mesh_l2 = create_shape_rgb('iluminació/c1/Llantia2/Cordill3Mesh.obj', [0.05, 0.05, 0.05])
    cordill4Mesh_l2 = create_shape_rgb('iluminació/c1/Llantia2/Cordill4Mesh.obj', [0.05, 0.05, 0.05])
    llum_l2 = create_shape_dielectric('iluminació/c1/Llantia2/Llum.obj')
    flama_l2 = create_obj_file_light_file('iluminació/c1/Llantia2/Flama.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')


    #altar
    base = create_shape_rgb('iluminació/Base.obj', [0.8, 0.8, 0.8])
    llosa = create_shape_rgb('iluminació/Llosa.obj', [0.8, 0.8, 0.8])

    scene_definition = {
        'type': 'scene',
        'integrator': {
            # 'type': 'path',
            # 'samples_per_pass': 64,
            # 'max_depth': 4 #posar mes
            'type': 'ptracer',
            'samples_per_pass': 128,
            'max_depth': 4
        },
        'shape1': obj_shape1,
        'shape2': obj_shape2,
        'shape3': obj_shape3,
        'shape4': obj_shape4,
        'shape5': obj_shape5,
        'shape6': obj_shape6,
        'shape7': anella,
        'shape8': anella2, 
        'shape9': baseCorona,
        'shape10': cadena,
        'shape11': cadena2,
        'shape12': cadena3,
        'shape13': ganxo,
        'shape14': ganxo2,
        'shape15': ganxo3,
        'shape16': ganxo4,
        'shape17': llums,
        'shape18': flama1,
        'shape19': flama2,
        'shape20': flama3,
        'shape21': flama4,
        'shape22': flama5,
        'shape23': flama6,
        'shape24': argolla_l1,
        'shape25': cordill1Mesh_l1,
        'shape26': cordill2Mesh_l1, 
        'shape27': cordill3Mesh_l1,
        'shape28': cordill4Mesh_l1,
        'shape29': llum_l1,
        'shape30': flama_l1,
        'shape31': argolla_l2,
        'shape32': cordill1Mesh_l2,
        'shape33': cordill2Mesh_l2,
        'shape34': cordill3Mesh_l2,
        'shape35': cordill4Mesh_l2,
        'shape36': llum_l2,
        'shape37': flama_l2,
        'shape38': base,
        'shape39': llosa,
        'sensor': create_perspective_camera_pv2() #change point of view here
    }

    for i, emitter in enumerate(emitters):
        scene_definition[f'emitter{i+1}'] = emitter

    scene = mi.load_dict(scene_definition)

    # Render the scene
    image = mi.render(scene, spp=4096)  # Sensor is already included in the scene

    #denoising
    denoiser = mi.OptixDenoiser(input_size = image.shape[:2][::-1] , albedo = False, temporal=False)
    denoised = denoiser(image)

    # Save the denoised rendered image to a file
    denoised_filename = f'renderPedret/XII/Artificial/pv2_c1_ptracer.exr'  #path for artificial
    #denoised_filename = f'renderPedret/XII/Artificial+Natural/pv7_c1.exr'   #path for artificial+nat
    #denoised_filename = f'renderPedret/XII/Natural/pv7_c1.exr'   #path for nat

    mi.util.write_bitmap(denoised_filename, denoised)
    print(f'Saved: {denoised_filename}')

def C1_llum_artificial():
    #artificial are flames that are already included in scene
    return create_sceneC1([])


def C1_llum_artificial_mes_natural():
    direction_D3T3 = [-0.00124458, -0.9470212,  -0.32116863]
    direction_D2T3 = [-0.000743358019, -0.795807242, -0.605549569]
    directional_sun = create_distant_directional_emitter(direction_D2T3, file_sun)
    cons_diffuse = create_constant_enviroment_emitter(file_difuse_pedret)

    return create_sceneC1([directional_sun, cons_diffuse])

def C1_llum_natural():
    #comment all the flames in scene
    direction_D2T3 = [-0.000743358019, -0.795807242, -0.605549569]
    directional_sun = create_distant_directional_emitter(direction_D2T3, file_sun)
    cons_diffuse = create_constant_enviroment_emitter(file_difuse_pedret)

    return create_sceneC1([directional_sun, cons_diffuse])


#C1_llum_artificial()
#C1_llum_artificial_mes_natural()
#C1_llum_natural()

#C2
#---------------------------------------------------------------------------------------------------------------------------------------------------
#SCENE C2
def create_sceneC2(emitters):
    obj_shape1 = create_obj_shape('model/XII_2/Pedret_XII.baked-1.obj', 'textures/pedret_XII/Pedret_X_normals_1.png', 'textures/pedret_XII/Pedret_X_color_1.png')
    obj_shape2 = create_obj_shape('model/XII_2/Pedret_XII.baked-2.obj', 'textures/pedret_XII/Pedret_X_normals_2.png', 'textures/pedret_XII/Pedret_X_color_2.png')
    obj_shape3 = create_obj_shape('model/XII_2/Pedret_XII.baked-absC.obj', 'textures/pedret_XII/Pedret_XII_normals_absC.png', 'textures/pedret_XII/Pedret_XII_color_absC.png')
    obj_shape4 = create_obj_shape('model/XII_2/Pedret_XII.baked-absN.obj', 'textures/pedret_XII/Pedret_XII_normals_absN.png', 'textures/pedret_XII/Pedret_XII_color_absN.png')
    obj_shape5 = create_obj_shape('model/XII_2/Pedret_XII.baked-absS.obj', 'textures/pedret_XII/Pedret_XII_normals_absS.png', 'textures/pedret_XII/Pedret_XII_color_absS.png')
    obj_shape6 = create_obj_shape('model/XII_2/Pedret_XII.baked-nau.obj', 'textures/pedret_XII/Pedret_XII_normals_nau.png', 'textures/pedret_XII/Pedret_XII_color_nau.png')

    #candeler 1
    support_1 =create_shape_rgb('iluminació/c2/candeler1/holder_1.obj', [0.05, 0.05, 0.05])
    espelma_1 = create_shape_rgb('iluminació/c2/candeler1/candle_1.obj', [0.8, 0.58, 0.33])
    metxa_1 = create_shape_rgb('iluminació/c2/candeler1/candle_wick_1.obj', [0.80, 0.48, 0.28])
    flama_1 = create_obj_file_light_file('iluminació/c2/candeler1/flame_1.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')

    #candeler 2
    support_2 = create_shape_rgb('iluminació/c2/candeler2/holder_2.obj', [0.05, 0.05, 0.05])
    espelma_2 = create_shape_rgb('iluminació/c2/candeler2/candle_2.obj', [0.8, 0.58, 0.33])
    metxa_2 = create_shape_rgb('iluminació/c2/candeler2/candle_wick_2.obj', [0.80, 0.48, 0.28])
    flama_2 = create_obj_file_light_file('iluminació/c2/candeler2/flame_2.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')

    #altar
    base = create_shape_rgb('iluminació/Base.obj', [0.8, 0.8, 0.8])
    llosa = create_shape_rgb('iluminació/Llosa.obj', [0.8, 0.8, 0.8])

    scene_definition = {
        'type': 'scene',
        'integrator': {
            'type': 'path',
            'max_depth': 4 #posar mes
        },
        'shape1': obj_shape1,
        'shape2': obj_shape2,
        'shape3': obj_shape3,
        'shape4': obj_shape4,
        'shape5': obj_shape5,
        'shape6': obj_shape6,
        'shape7': support_1,
        'shape8': espelma_1,
        'shape9': metxa_1,
        # 'shape10': flama_1,
        'shape11': support_2,
        'shape12': espelma_2,
        'shape13': metxa_2,
        # 'shape14': flama_2,
        'shape15': base,
        'shape16': llosa,
        'sensor': create_perspective_camera_pv2() #change point of view here
    }

    for i, emitter in enumerate(emitters):
        scene_definition[f'emitter{i+1}'] = emitter

    scene = mi.load_dict(scene_definition)

    # Render the scene
    image = mi.render(scene, spp=2048)  # Sensor is already included in the scene

    #denoising
    denoiser = mi.OptixDenoiser(input_size = image.shape[:2][::-1] , albedo = False, temporal=False)
    denoised = denoiser(image)

    # Save the denoised rendered image to a file
    #denoised_filename = f'renderPedret/XII/Artificial/pv7_c2.exr'          #path for artificial
    #denoised_filename = f'renderPedret/XII/Artificial+Natural/pv7_c2.exr'   #path for artificial+nat
    denoised_filename = f'renderPedret/XII/Natural/pv2_c2.exr'
    mi.util.write_bitmap(denoised_filename, denoised)
    print(f'Saved: {denoised_filename}')

def C2_llum_artificial():
    return create_sceneC2([])

def C2_cons_global():
    const_global = create_constant_enviroment_emitter(file_global_pedret)
    return create_sceneC2([const_global])

def C2_directional_sun():
    direction_D3T3 = [-0.00124458, -0.9470212,  -0.32116863]
    directional_sun = create_distant_directional_emitter(direction_D3T3, file_sun)
    return create_sceneC2([directional_sun])

def C2_cons_diffuse_directional_sun():
    direction_D3T3 = [-0.00124458, -0.9470212,  -0.32116863]
    directional_sun = create_distant_directional_emitter(direction_D3T3, file_sun)
    cons_diffuse = create_constant_enviroment_emitter(file_difuse_pedret)
    return create_sceneC2([directional_sun, cons_diffuse])

#D2T3
def C2_llum_artificial_mes_natural():
    direction_D3T3 = [-0.00124458, -0.9470212,  -0.32116863]
    direction_D2T3 = [-0.000743358019, -0.795807242, -0.605549569]
    directional_sun = create_distant_directional_emitter(direction_D2T3, file_sun)
    cons_diffuse = create_constant_enviroment_emitter(file_difuse_pedret)

    return create_sceneC2([directional_sun, cons_diffuse])

def C2_llum_natural():
    direction_D2T3 = [-0.000743358019, -0.795807242, -0.605549569]
    directional_sun = create_distant_directional_emitter(direction_D2T3, file_sun)
    cons_diffuse = create_constant_enviroment_emitter(file_difuse_pedret)
    return create_sceneC2([directional_sun, cons_diffuse])

#C2_llum_artificial()
#C2_llum_artificial_mes_natural()
#C2_llum_natural()

#C3
#---------------------------------------------------------------------------------------------------------------------------------------------------

#SCENE C3-----------------------------------------------------------------------------------------------------------------------------------------------------

def create_sceneC3(emitters):
    obj_shape1 = create_obj_shape('model/XII_2/Pedret_XII.baked-1.obj', 'textures/pedret_XII/Pedret_X_normals_1.png', 'textures/pedret_XII/Pedret_X_color_1.png')
    obj_shape2 = create_obj_shape('model/XII_2/Pedret_XII.baked-2.obj', 'textures/pedret_XII/Pedret_X_normals_2.png', 'textures/pedret_XII/Pedret_X_color_2.png')
    obj_shape3 = create_obj_shape('model/XII_2/Pedret_XII.baked-absC.obj', 'textures/pedret_XII/Pedret_XII_normals_absC.png', 'textures/pedret_XII/Pedret_XII_color_absC.png')
    obj_shape4 = create_obj_shape('model/XII_2/Pedret_XII.baked-absN.obj', 'textures/pedret_XII/Pedret_XII_normals_absN.png', 'textures/pedret_XII/Pedret_XII_color_absN.png')
    obj_shape5 = create_obj_shape('model/XII_2/Pedret_XII.baked-absS.obj', 'textures/pedret_XII/Pedret_XII_normals_absS.png', 'textures/pedret_XII/Pedret_XII_color_absS.png')
    obj_shape6 = create_obj_shape('model/XII_2/Pedret_XII.baked-nau.obj', 'textures/pedret_XII/Pedret_XII_normals_nau.png', 'textures/pedret_XII/Pedret_XII_color_nau.png')

    #canelobre 1
    support_1 =create_shape_rgb('iluminació/c3/canelobre1/holder.obj', [0.05, 0.05, 0.05])
    espelma_1 = create_shape_rgb('iluminació/c3/canelobre1/candle_2.obj', [0.8, 0.58, 0.33])
    metxa_1 = create_shape_rgb('iluminació/c3/canelobre1/candle_wick_2.obj', [0.80, 0.48, 0.28])
    flama_1 = create_obj_file_light_file('iluminació/c3/canelobre1/flame.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')

    #canelobre 2
    support_2 = create_shape_rgb('iluminació/c3/canelobre2/holder.obj', [0.05, 0.05, 0.05])
    espelma_2 = create_shape_rgb('iluminació/c3/canelobre2/candle_2.obj', [0.8, 0.58, 0.33])
    metxa_2 = create_shape_rgb('iluminació/c3/canelobre2/candle_wick_2.obj', [0.80, 0.48, 0.28])
    flama_2 = create_obj_file_light_file('iluminació/c3/canelobre2/flame.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')

    #altar
    base = create_shape_rgb('iluminació/Base.obj', [0.8, 0.8, 0.8])
    llosa = create_shape_rgb('iluminació/Llosa.obj', [0.8, 0.8, 0.8])

    
    scene_definition = {
        'type': 'scene',
        'integrator': {
            'type': 'path',
            'max_depth': 4 #posar mes
        },
        'shape1': obj_shape1,
        'shape2': obj_shape2,
        'shape3': obj_shape3,
        'shape4': obj_shape4,
        'shape5': obj_shape5,
        'shape6': obj_shape6,
        'shape7': support_1,
        'shape8': espelma_1,
        'shape9': metxa_1,
        'shape10': flama_1,
        'shape11': support_2,
        'shape12': espelma_2,
        'shape13': metxa_2,
        'shape14': flama_2,
        'shape15': base,
        'shape16': llosa,
        'sensor': create_perspective_camera_pv2() #change point of view here for C3
    }

    for i, emitter in enumerate(emitters):
        scene_definition[f'emitter{i+1}'] = emitter

    scene = mi.load_dict(scene_definition)

    # Render the scene
    image = mi.render(scene, spp=2048)  # Sensor is already included in the scene

    #denoising
    denoiser = mi.OptixDenoiser(input_size = image.shape[:2][::-1] , albedo = False, temporal=False)
    denoised = denoiser(image)

    # Save the denoised rendered image to a file
    #denoised_filename = f'renderPedret/XII/Artificial/pv2_c3.exr'
    denoised_filename = f'renderPedret/XII/Artificial+Natural/pv1_c3.exr'   #path foro artificial+nat

    mi.util.write_bitmap(denoised_filename, denoised)
    print(f'Saved: {denoised_filename}')


def C3_llum_artificial():
    return create_sceneC3([])

#C3_llum_artificial()

#C4
#---------------------------------------------------------------------------------------------------------------------------------------------------
#SCENE C4
def create_sceneC4(emitters):
    obj_shape1 = create_obj_shape('model/XII_2/Pedret_XII.baked-1.obj', 'textures/pedret_XII/Pedret_X_normals_1.png', 'textures/pedret_XII/Pedret_X_color_1.png')
    obj_shape2 = create_obj_shape('model/XII_2/Pedret_XII.baked-2.obj', 'textures/pedret_XII/Pedret_X_normals_2.png', 'textures/pedret_XII/Pedret_X_color_2.png')
    obj_shape3 = create_obj_shape('model/XII_2/Pedret_XII.baked-absC.obj', 'textures/pedret_XII/Pedret_XII_normals_absC.png', 'textures/pedret_XII/Pedret_XII_color_absC.png')
    obj_shape4 = create_obj_shape('model/XII_2/Pedret_XII.baked-absN.obj', 'textures/pedret_XII/Pedret_XII_normals_absN.png', 'textures/pedret_XII/Pedret_XII_color_absN.png')
    obj_shape5 = create_obj_shape('model/XII_2/Pedret_XII.baked-absS.obj', 'textures/pedret_XII/Pedret_XII_normals_absS.png', 'textures/pedret_XII/Pedret_XII_color_absS.png')
    obj_shape6 = create_obj_shape('model/XII_2/Pedret_XII.baked-nau.obj', 'textures/pedret_XII/Pedret_XII_normals_nau.png', 'textures/pedret_XII/Pedret_XII_color_nau.png')

    #canelobre 1
    support_1 =create_shape_rgb('iluminació/c3/canelobre1/holder.obj', [0.05, 0.05, 0.05])
    espelma_1 = create_shape_rgb('iluminació/c3/canelobre1/candle_2.obj', [0.8, 0.58, 0.33])
    metxa_1 = create_shape_rgb('iluminació/c3/canelobre1/candle_wick_2.obj', [0.80, 0.48, 0.28])
    flama_1 = create_obj_file_light_file('iluminació/c3/canelobre1/flame.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')

    #canelobre 2
    support_2 = create_shape_rgb('iluminació/c3/canelobre2/holder.obj', [0.05, 0.05, 0.05])
    espelma_2 = create_shape_rgb('iluminació/c3/canelobre2/candle_2.obj', [0.8, 0.58, 0.33])
    metxa_2 = create_shape_rgb('iluminació/c3/canelobre2/candle_wick_2.obj', [0.80, 0.48, 0.28])
    flama_2 = create_obj_file_light_file('iluminació/c3/canelobre2/flame.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')

    #canelobre 3
    support_3 = create_shape_rgb('iluminació/c4/canelobre3/holder_3.obj', [0.05, 0.05, 0.05])
    espelma_3 = create_shape_rgb('iluminació/c4/canelobre3/candle_3.obj', [0.8, 0.58, 0.33])
    metxa_3 = create_shape_rgb('iluminació/c4/canelobre3/candle_wick_3.obj', [0.80, 0.48, 0.28])
    flama_3 = create_obj_file_light_file('iluminació/c4/canelobre3/flame_3.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')

    #canelobre 4
    support_4 = create_shape_rgb('iluminació/c4/canelobre4/holder_4.obj', [0.05, 0.05, 0.05])
    espelma_4 = create_shape_rgb('iluminació/c4/canelobre4/candle_4.obj', [0.8, 0.58, 0.33])
    metxa_4 = create_shape_rgb('iluminació/c4/canelobre4/candle_wick_4.obj', [0.80, 0.48, 0.28])
    flama_4 = create_obj_file_light_file('iluminació/c4/canelobre4/flame_4.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')
    
    #altar
    base = create_shape_rgb('iluminació/Base.obj', [0.8, 0.8, 0.8])
    llosa = create_shape_rgb('iluminació/Llosa.obj', [0.8, 0.8, 0.8])

    scene_definition = {
        'type': 'scene',
        'integrator': {
            'type': 'path',
            'max_depth': 4 #posar mes
        },
        'shape1': obj_shape1,
        'shape2': obj_shape2,
        'shape3': obj_shape3,
        'shape4': obj_shape4,
        'shape5': obj_shape5,
        'shape6': obj_shape6,
        'shape7': support_1,
        'shape8': espelma_1,
        'shape9': metxa_1,
        # 'shape10': flama_1,
        'shape11': support_2,
        'shape12': espelma_2,
        'shape13': metxa_2,
        # 'shape14': flama_2,
        'shape15': support_3,
        'shape16': espelma_3,
        'shape17': metxa_3,
        # 'shape18': flama_3,
        'shape19': support_4,
        'shape20': espelma_4,
        'shape21': metxa_4,
        # 'shape22': flama_4,
        'shape23': base,
        'shape24': llosa,
        'sensor': create_perspective_camera_pv2() #change point of view here 
    }

    for i, emitter in enumerate(emitters):
        scene_definition[f'emitter{i+1}'] = emitter

    scene = mi.load_dict(scene_definition)

    # Render the scene
    image = mi.render(scene, spp=2048)  # Sensor is already included in the scene

    #denoising
    denoiser = mi.OptixDenoiser(input_size = image.shape[:2][::-1] , albedo = False, temporal=False)
    denoised = denoiser(image)

    # Save the denoised rendered image to a file
    #denoised_filename = f'renderPedret/XII/Artificial/pv7_C4.exr'
    #denoised_filename = f'renderPedret/XII/Artificial+Natural/pv7_c4.exr'   #path foro artificial+nat
    denoised_filename = f'renderPedret/XII/Natural/pv2_c4.exr'   #path foro nat


    mi.util.write_bitmap(denoised_filename, denoised)
    print(f'Saved: {denoised_filename}')

def C4_llum_artificial():
    return create_sceneC4([])

def C4_llum_artificial_mes_natural():
    direction_D3T3 = [-0.00124458, -0.9470212,  -0.32116863]
    direction_D2T3 = [-0.000743358019, -0.795807242, -0.605549569]
    directional_sun = create_distant_directional_emitter(direction_D2T3, file_sun)
    cons_diffuse = create_constant_enviroment_emitter(file_difuse_pedret)

    return create_sceneC4([directional_sun, cons_diffuse])

def C4_llum_natural():
    direction_D2T3 = [-0.000743358019, -0.795807242, -0.605549569]
    directional_sun = create_distant_directional_emitter(direction_D2T3, file_sun)
    cons_diffuse = create_constant_enviroment_emitter(file_difuse_pedret)

    return create_sceneC4([directional_sun, cons_diffuse])

#C4_llum_artificial()
#C4_llum_artificial_mes_natural()
#C4_llum_natural()


#C5
#---------------------------------------------------------------------------------------------------------------------------------------------------
#SCENE C5

def create_sceneC5(emitters):
    obj_shape1 = create_obj_shape('model/XII_2/Pedret_XII.baked-1.obj', 'textures/pedret_XII/Pedret_X_normals_1.png', 'textures/pedret_XII/Pedret_X_color_1.png')
    obj_shape2 = create_obj_shape('model/XII_2/Pedret_XII.baked-2.obj', 'textures/pedret_XII/Pedret_X_normals_2.png', 'textures/pedret_XII/Pedret_X_color_2.png')
    obj_shape3 = create_obj_shape('model/XII_2/Pedret_XII.baked-absC.obj', 'textures/pedret_XII/Pedret_XII_normals_absC.png', 'textures/pedret_XII/Pedret_XII_color_absC.png')
    obj_shape4 = create_obj_shape('model/XII_2/Pedret_XII.baked-absN.obj', 'textures/pedret_XII/Pedret_XII_normals_absN.png', 'textures/pedret_XII/Pedret_XII_color_absN.png')
    obj_shape5 = create_obj_shape('model/XII_2/Pedret_XII.baked-absS.obj', 'textures/pedret_XII/Pedret_XII_normals_absS.png', 'textures/pedret_XII/Pedret_XII_color_absS.png')
    obj_shape6 = create_obj_shape('model/XII_2/Pedret_XII.baked-nau.obj', 'textures/pedret_XII/Pedret_XII_normals_nau.png', 'textures/pedret_XII/Pedret_XII_color_nau.png')

    #corona
    anella = create_shape_rgb('iluminació/c1/Corona/Anella.obj', [0.05, 0.05, 0.05])
    anella2 = create_shape_rgb('iluminació/c1/Corona/Anella2.obj', [0.05, 0.05, 0.05])
    baseCorona = create_shape_rgb('iluminació/c1/Corona/Base.obj', [0.05, 0.05, 0.05])
    cadena = create_shape_rgb('iluminació/c1/Corona/Cadena.obj', [0.05, 0.05, 0.05])
    cadena2 = create_shape_rgb('iluminació/c1/Corona/Cadena2.obj', [0.05, 0.05, 0.05])
    cadena3 = create_shape_rgb('iluminació/c1/Corona/Cadena3.obj', [0.05, 0.05, 0.05])
    ganxo = create_shape_rgb('iluminació/c1/Corona/Ganxo.obj', [0.05, 0.05, 0.05])
    ganxo2 = create_shape_rgb('iluminació/c1/Corona/Ganxo2.obj', [0.05, 0.05, 0.05])
    ganxo3 = create_shape_rgb('iluminació/c1/Corona/Ganxo3.obj', [0.05, 0.05, 0.05])
    ganxo4 = create_shape_rgb('iluminació/c1/Corona/Ganxo4.obj', [0.05, 0.05, 0.05])
    llums = create_shape_dielectric('iluminació/c1/Corona/Llums.obj') 
    flama1 = create_obj_file_light_file('iluminació/c1/Corona/flama1.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')
    flama2 = create_obj_file_light_file('iluminació/c1/Corona/flama2.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')
    flama3 = create_obj_file_light_file('iluminació/c1/Corona/flama3.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')
    flama4 = create_obj_file_light_file('iluminació/c1/Corona/flama4.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')
    flama5 = create_obj_file_light_file('iluminació/c1/Corona/flama5.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')
    flama6 = create_obj_file_light_file('iluminació/c1/Corona/flama6.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')

    #llantia1
    argolla_l1 = create_shape_rgb('iluminació/c1/Llantia1/Argolla.obj', [0.05, 0.05, 0.05])
    cordill1Mesh_l1 = create_shape_rgb('iluminació/c1/Llantia1/Cordill1Mesh.obj', [0.05, 0.05, 0.05])
    cordill2Mesh_l1 = create_shape_rgb('iluminació/c1/Llantia1/Cordill2Mesh.obj', [0.05, 0.05, 0.05])
    cordill3Mesh_l1 = create_shape_rgb('iluminació/c1/Llantia1/Cordill3Mesh.obj', [0.05, 0.05, 0.05])
    cordill4Mesh_l1 = create_shape_rgb('iluminació/c1/Llantia1/Cordill4Mesh.obj', [0.05, 0.05, 0.05])
    llum_l1 = create_shape_dielectric('iluminació/c1/Llantia1/Llum.obj')
    flama_l1 = create_obj_file_light_file('iluminació/c1/Llantia1/Flama.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')

    #llantia2
    argolla_l2 = create_shape_rgb('iluminació/c1/Llantia2/Argolla.obj', [0.05, 0.05, 0.05])
    cordill1Mesh_l2 = create_shape_rgb('iluminació/c1/Llantia2/Cordill1Mesh.obj', [0.05, 0.05, 0.05])
    cordill2Mesh_l2 = create_shape_rgb('iluminació/c1/Llantia2/Cordill2Mesh.obj', [0.05, 0.05, 0.05])
    cordill3Mesh_l2 = create_shape_rgb('iluminació/c1/Llantia2/Cordill3Mesh.obj', [0.05, 0.05, 0.05])
    cordill4Mesh_l2 = create_shape_rgb('iluminació/c1/Llantia2/Cordill4Mesh.obj', [0.05, 0.05, 0.05])
    llum_l2 = create_shape_dielectric('iluminació/c1/Llantia2/Llum.obj')
    flama_l2 = create_obj_file_light_file('iluminació/c1/Llantia2/Flama.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')

    #candeler 1
    support_1 =create_shape_rgb('iluminació/c2/candeler1/holder_1.obj', [0.05, 0.05, 0.05])
    espelma_1 = create_shape_rgb('iluminació/c2/candeler1/candle_1.obj', [0.8, 0.58, 0.33])
    metxa_1 = create_shape_rgb('iluminació/c2/candeler1/candle_wick_1.obj', [0.80, 0.48, 0.28])
    flama_1 = create_obj_file_light_file('iluminació/c2/candeler1/flame_1.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')


    #candeler 2
    support_2 = create_shape_rgb('iluminació/c2/candeler2/holder_2.obj', [0.05, 0.05, 0.05])
    espelma_2 = create_shape_rgb('iluminació/c2/candeler2/candle_2.obj', [0.8, 0.58, 0.33])
    metxa_2 = create_shape_rgb('iluminació/c2/candeler2/candle_wick_2.obj', [0.80, 0.48, 0.28])
    flama_2 = create_obj_file_light_file('iluminació/c2/candeler2/flame_2.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')

    #canelobre 1
    support_1_c =create_shape_rgb('iluminació/c3/canelobre1/holder.obj', [0.05, 0.05, 0.05])
    espelma_1_c = create_shape_rgb('iluminació/c3/canelobre1/candle_2.obj', [0.8, 0.58, 0.33])
    metxa_1_c = create_shape_rgb('iluminació/c3/canelobre1/candle_wick_2.obj', [0.80, 0.48, 0.28])
    flama_1_c = create_obj_file_light_file('iluminació/c3/canelobre1/flame.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')

    #canelobre 2
    support_2_c = create_shape_rgb('iluminació/c3/canelobre2/holder.obj', [0.05, 0.05, 0.05])
    espelma_2_c = create_shape_rgb('iluminació/c3/canelobre2/candle_2.obj', [0.8, 0.58, 0.33])
    metxa_2_c = create_shape_rgb('iluminació/c3/canelobre2/candle_wick_2.obj', [0.80, 0.48, 0.28])
    flama_2_c = create_obj_file_light_file('iluminació/c3/canelobre2/flame.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')

    #canelobre 3
    support_3_c = create_shape_rgb('iluminació/c4/canelobre3/holder_3.obj', [0.05, 0.05, 0.05])
    espelma_3_c = create_shape_rgb('iluminació/c4/canelobre3/candle_3.obj', [0.8, 0.58, 0.33])
    metxa_3_c = create_shape_rgb('iluminació/c4/canelobre3/candle_wick_3.obj', [0.80, 0.48, 0.28])
    flama_3_c = create_obj_file_light_file('iluminació/c4/canelobre3/flame_3.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')

    #canelobre 4
    support_4_c = create_shape_rgb('iluminació/c4/canelobre4/holder_4.obj', [0.05, 0.05, 0.05])
    espelma_4_c = create_shape_rgb('iluminació/c4/canelobre4/candle_4.obj', [0.8, 0.58, 0.33])
    metxa_4_c = create_shape_rgb('iluminació/c4/canelobre4/candle_wick_4.obj', [0.80, 0.48, 0.28])
    flama_4_c = create_obj_file_light_file('iluminació/c4/canelobre4/flame_4.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')

    #altar
    base = create_shape_rgb('iluminació/Base.obj', [0.8, 0.8, 0.8])
    llosa = create_shape_rgb('iluminació/Llosa.obj', [0.8, 0.8, 0.8])

    scene_definition = {
        'type': 'scene',
        'integrator': {
            'type': 'path',
            'samples_per_pass': 64,
            'max_depth': 4 #posar mes
        },
        'shape1': obj_shape1,
        'shape2': obj_shape2,
        'shape3': obj_shape3,
        'shape4': obj_shape4,
        'shape5': obj_shape5,
        'shape6': obj_shape6,
        'shape7': anella,
        'shape8': anella2, 
        'shape9': baseCorona,
        'shape10': cadena,
        'shape11': cadena2,
        'shape12': cadena3,
        'shape13': ganxo,
        'shape14': ganxo2,
        'shape15': ganxo3,
        'shape16': ganxo4,
        'shape17': llums,
        'shape18': flama1,
        'shape19': flama2,
        'shape20': flama3,
        'shape21': flama4,
        'shape22': flama5,
        'shape23': flama6,
        'shape24': argolla_l1,
        'shape25': cordill1Mesh_l1,
        'shape26': cordill2Mesh_l1, 
        'shape27': cordill3Mesh_l1,
        'shape28': cordill4Mesh_l1,
        'shape29': llum_l1,
        'shape30': flama_l1,
        'shape31': argolla_l2,
        'shape32': cordill1Mesh_l2,
        'shape33': cordill2Mesh_l2,
        'shape34': cordill3Mesh_l2,
        'shape35': cordill4Mesh_l2,
        'shape36': llum_l2,
        'shape37': flama_l2,
        'shape38': support_1,
        'shape39': espelma_1, 
        'shape40': metxa_1,
        'shape41': flama_1,
        'shape42': support_2,
        'shape43': espelma_2, 
        'shape44': metxa_2,
        'shape45': flama_2,
        'shape46': support_1_c, 
        'shape47': espelma_1_c,
        'shape48': metxa_1_c,
        'shape49': flama_1_c,
        'shape50': support_2_c,
        'shape51': espelma_2_c,
        'shape52': metxa_2_c,
        'shape53': flama_2_c,
        'shape54': support_3_c,
        'shape55': espelma_3_c,
        'shape56': metxa_3_c,
        'shape57': flama_3_c,
        'shape58': support_4_c,
        'shape59': espelma_4_c,
        'shape60': metxa_4_c,
        'shape61': flama_4_c,
        'shape62': base,
        'shape63': llosa,
        'sensor': create_perspective_camera_pv7() #change point of view here
    }

    for i, emitter in enumerate(emitters):
        scene_definition[f'emitter{i+1}'] = emitter

    scene = mi.load_dict(scene_definition)

    # Render the scene
    image = mi.render(scene, spp=2048)  # Sensor is already included in the scene

    #denoising
    denoiser = mi.OptixDenoiser(input_size = image.shape[:2][::-1] , albedo = False, temporal=False)
    denoised = denoiser(image)

    # Save the denoised rendered image to a file
    denoised_filename = f'renderPedret/XII/Artificial/pv7_c5_samples_per_pass_mes_mostres.exr'   #path render nat
    #denoised_filename = f'renderPedret/XII/Artificial+Natural/pv7_c5.exr'   #path render artificial+nat
    #denoised_filename = f'renderPedret/XII/Natural/pv7_c5.exr'   #path render nat

    mi.util.write_bitmap(denoised_filename, denoised)
    print(f'Saved: {denoised_filename}')


def C5_llum_artificial():
    return create_sceneC5([])

def C5_llum_artificial_mes_natural():
    direction_D3T3 = [-0.00124458, -0.9470212,  -0.32116863]
    direction_D2T3 = [-0.000743358019, -0.795807242, -0.605549569]
    directional_sun = create_distant_directional_emitter(direction_D2T3, file_sun)
    cons_diffuse = create_constant_enviroment_emitter(file_difuse_pedret)

    return create_sceneC5([directional_sun, cons_diffuse])

def C5_llum_natural():
    direction_D2T3 = [-0.000743358019, -0.795807242, -0.605549569]
    directional_sun = create_distant_directional_emitter(direction_D2T3, file_sun)
    cons_diffuse = create_constant_enviroment_emitter(file_difuse_pedret)

    return create_sceneC5([directional_sun, cons_diffuse])

#C5_llum_artificial()


#SEGLE XIII$
#---------------------------------------------------------------------------------------------------------------------
def create_sceneC5_XIII(emitters):

    obj_shape1 = create_obj_shape('model/XIII/Pedret_XIII_1.obj','textures/pedret_XIII/Pedret_XIII_normals_1.png', 'textures/pedret_XIII/Pedret_XIII_color_1.png')
    obj_shape2 = create_obj_shape('model/XIII/Pedret_XIII_2.obj', 'textures/pedret_XII/Pedret_X_normals_2.png', 'textures/pedret_XII/Pedret_X_color_2.png')
    obj_shape3 = create_obj_shape('model/XIII/Pedret_XIII_absC.obj', 'textures/pedret_XII/Pedret_XII_normals_absC.png', 'textures/pedret_XII/Pedret_XII_color_absC.png')
    obj_shape4 = create_obj_shape('model/XIII/Pedret_XIII_absN.obj', 'textures/pedret_XII/Pedret_XII_normals_absN.png', 'textures/pedret_XII/Pedret_XII_color_absN.png')
    obj_shape5 = create_obj_shape('model/XIII/Pedret_XIII_absS.obj', 'textures/pedret_XII/Pedret_XII_normals_absS.png', 'textures/pedret_XII/Pedret_XII_color_absS.png')
    obj_shape6 = create_obj_shape('model/XIII/Pedret_XIII_nau.obj', 'textures/pedret_XII/Pedret_XII_normals_nau.png', 'textures/pedret_XII/Pedret_XII_color_nau.png')


    #corona
    anella = create_shape_rgb('iluminació/c1/Corona/Anella.obj', [0.05, 0.05, 0.05])
    anella2 = create_shape_rgb('iluminació/c1/Corona/Anella2.obj', [0.05, 0.05, 0.05])
    baseCorona = create_shape_rgb('iluminació/c1/Corona/Base.obj', [0.05, 0.05, 0.05])
    cadena = create_shape_rgb('iluminació/c1/Corona/Cadena.obj', [0.05, 0.05, 0.05])
    cadena2 = create_shape_rgb('iluminació/c1/Corona/Cadena2.obj', [0.05, 0.05, 0.05])
    cadena3 = create_shape_rgb('iluminació/c1/Corona/Cadena3.obj', [0.05, 0.05, 0.05])
    ganxo = create_shape_rgb('iluminació/c1/Corona/Ganxo.obj', [0.05, 0.05, 0.05])
    ganxo2 = create_shape_rgb('iluminació/c1/Corona/Ganxo2.obj', [0.05, 0.05, 0.05])
    ganxo3 = create_shape_rgb('iluminació/c1/Corona/Ganxo3.obj', [0.05, 0.05, 0.05])
    ganxo4 = create_shape_rgb('iluminació/c1/Corona/Ganxo4.obj', [0.05, 0.05, 0.05])
    llums = create_shape_dielectric('iluminació/c1/Corona/Llums.obj') 
    flama1 = create_obj_file_light_file('iluminació/c1/Corona/flama1.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')
    flama2 = create_obj_file_light_file('iluminació/c1/Corona/flama2.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')
    flama3 = create_obj_file_light_file('iluminació/c1/Corona/flama3.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')
    flama4 = create_obj_file_light_file('iluminació/c1/Corona/flama4.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')
    flama5 = create_obj_file_light_file('iluminació/c1/Corona/flama5.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')
    flama6 = create_obj_file_light_file('iluminació/c1/Corona/flama6.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')

    #llantia1
    argolla_l1 = create_shape_rgb('iluminació/c1/Llantia1/Argolla.obj', [0.05, 0.05, 0.05])
    cordill1Mesh_l1 = create_shape_rgb('iluminació/c1/Llantia1/Cordill1Mesh.obj', [0.05, 0.05, 0.05])
    cordill2Mesh_l1 = create_shape_rgb('iluminació/c1/Llantia1/Cordill2Mesh.obj', [0.05, 0.05, 0.05])
    cordill3Mesh_l1 = create_shape_rgb('iluminació/c1/Llantia1/Cordill3Mesh.obj', [0.05, 0.05, 0.05])
    cordill4Mesh_l1 = create_shape_rgb('iluminació/c1/Llantia1/Cordill4Mesh.obj', [0.05, 0.05, 0.05])
    llum_l1 = create_shape_dielectric('iluminació/c1/Llantia1/Llum.obj')
    flama_l1 = create_obj_file_light_file('iluminació/c1/Llantia1/Flama.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')

    #llantia2
    argolla_l2 = create_shape_rgb('iluminació/c1/Llantia2/Argolla.obj', [0.05, 0.05, 0.05])
    cordill1Mesh_l2 = create_shape_rgb('iluminació/c1/Llantia2/Cordill1Mesh.obj', [0.05, 0.05, 0.05])
    cordill2Mesh_l2 = create_shape_rgb('iluminació/c1/Llantia2/Cordill2Mesh.obj', [0.05, 0.05, 0.05])
    cordill3Mesh_l2 = create_shape_rgb('iluminació/c1/Llantia2/Cordill3Mesh.obj', [0.05, 0.05, 0.05])
    cordill4Mesh_l2 = create_shape_rgb('iluminació/c1/Llantia2/Cordill4Mesh.obj', [0.05, 0.05, 0.05])
    llum_l2 = create_shape_dielectric('iluminació/c1/Llantia2/Llum.obj')
    flama_l2 = create_obj_file_light_file('iluminació/c1/Llantia2/Flama.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd')

    #candeler 1
    support_1 =create_shape_rgb('iluminació/c2/candeler1/holder_1.obj', [0.05, 0.05, 0.05])
    espelma_1 = create_shape_rgb('iluminació/c2/candeler1/candle_1.obj', [0.8, 0.58, 0.33])
    metxa_1 = create_shape_rgb('iluminació/c2/candeler1/candle_wick_1.obj', [0.80, 0.48, 0.28])
    flama_1 = create_obj_file_light_file('iluminació/c2/candeler1/flame_1.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')


    #candeler 2
    support_2 = create_shape_rgb('iluminació/c2/candeler2/holder_2.obj', [0.05, 0.05, 0.05])
    espelma_2 = create_shape_rgb('iluminació/c2/candeler2/candle_2.obj', [0.8, 0.58, 0.33])
    metxa_2 = create_shape_rgb('iluminació/c2/candeler2/candle_wick_2.obj', [0.80, 0.48, 0.28])
    flama_2 = create_obj_file_light_file('iluminació/c2/candeler2/flame_2.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')

    #canelobre 1
    support_1_c =create_shape_rgb('iluminació/c3/canelobre1/holder.obj', [0.05, 0.05, 0.05])
    espelma_1_c = create_shape_rgb('iluminació/c3/canelobre1/candle_2.obj', [0.8, 0.58, 0.33])
    metxa_1_c = create_shape_rgb('iluminació/c3/canelobre1/candle_wick_2.obj', [0.80, 0.48, 0.28])
    flama_1_c = create_obj_file_light_file('iluminació/c3/canelobre1/flame.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')

    #canelobre 2
    support_2_c = create_shape_rgb('iluminació/c3/canelobre2/holder.obj', [0.05, 0.05, 0.05])
    espelma_2_c = create_shape_rgb('iluminació/c3/canelobre2/candle_2.obj', [0.8, 0.58, 0.33])
    metxa_2_c = create_shape_rgb('iluminació/c3/canelobre2/candle_wick_2.obj', [0.80, 0.48, 0.28])
    flama_2_c = create_obj_file_light_file('iluminació/c3/canelobre2/flame.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')

    #canelobre 3
    support_3_c = create_shape_rgb('iluminació/c4/canelobre3/holder_3.obj', [0.05, 0.05, 0.05])
    espelma_3_c = create_shape_rgb('iluminació/c4/canelobre3/candle_3.obj', [0.8, 0.58, 0.33])
    metxa_3_c = create_shape_rgb('iluminació/c4/canelobre3/candle_wick_3.obj', [0.80, 0.48, 0.28])
    flama_3_c = create_obj_file_light_file('iluminació/c4/canelobre3/flame_3.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')

    #canelobre 4
    support_4_c = create_shape_rgb('iluminació/c4/canelobre4/holder_4.obj', [0.05, 0.05, 0.05])
    espelma_4_c = create_shape_rgb('iluminació/c4/canelobre4/candle_4.obj', [0.8, 0.58, 0.33])
    metxa_4_c = create_shape_rgb('iluminació/c4/canelobre4/candle_wick_4.obj', [0.80, 0.48, 0.28])
    flama_4_c = create_obj_file_light_file('iluminació/c4/canelobre4/flame_4.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd')

    #altar
    base = create_shape_rgb('iluminació/Base.obj', [0.8, 0.8, 0.8])
    llosa = create_shape_rgb('iluminació/Llosa.obj', [0.8, 0.8, 0.8])

    scene_definition = {
        'type': 'scene',
        'integrator': {
            'type': 'path',
            'max_depth': 4 #posar mes
        },
        'shape1': obj_shape1,
        'shape2': obj_shape2,
        'shape3': obj_shape3,
        'shape4': obj_shape4,
        'shape5': obj_shape5,
        'shape6': obj_shape6,
        'shape7': anella,
        'shape8': anella2, 
        'shape9': baseCorona,
        'shape10': cadena,
        'shape11': cadena2,
        'shape12': cadena3,
        'shape13': ganxo,
        'shape14': ganxo2,
        'shape15': ganxo3,
        'shape16': ganxo4,
        'shape17': llums,
        'shape18': flama1,
        'shape19': flama2,
        'shape20': flama3,
        'shape21': flama4,
        'shape22': flama5,
        'shape23': flama6,
        'shape24': argolla_l1,
        'shape25': cordill1Mesh_l1,
        'shape26': cordill2Mesh_l1, 
        'shape27': cordill3Mesh_l1,
        'shape28': cordill4Mesh_l1,
        'shape29': llum_l1,
        'shape30': flama_l1,
        'shape31': argolla_l2,
        'shape32': cordill1Mesh_l2,
        'shape33': cordill2Mesh_l2,
        'shape34': cordill3Mesh_l2,
        'shape35': cordill4Mesh_l2,
        'shape36': llum_l2,
        'shape37': flama_l2,
        'shape38': support_1,
        'shape39': espelma_1, 
        'shape40': metxa_1,
        'shape41': flama_1,
        'shape42': support_2,
        'shape43': espelma_2, 
        'shape44': metxa_2,
        'shape45': flama_2,
        'shape46': support_1_c, 
        'shape47': espelma_1_c,
        'shape48': metxa_1_c,
        'shape49': flama_1_c,
        'shape50': support_2_c,
        'shape51': espelma_2_c,
        'shape52': metxa_2_c,
        'shape53': flama_2_c,
        'shape54': support_3_c,
        'shape55': espelma_3_c,
        'shape56': metxa_3_c,
        'shape57': flama_3_c,
        'shape58': support_4_c,
        'shape59': espelma_4_c,
        'shape60': metxa_4_c,
        'shape61': flama_4_c,
        'shape62': base,
        'shape63': llosa,
        'sensor': create_perspective_camera_pv1() #change point of view here
    }

    for i, emitter in enumerate(emitters):
        scene_definition[f'emitter{i+1}'] = emitter

    scene = mi.load_dict(scene_definition)

    # Render the scene
    image = mi.render(scene, spp=2048)  # Sensor is already included in the scene

    #denoising
    denoiser = mi.OptixDenoiser(input_size = image.shape[:2][::-1] , albedo = False, temporal=False)
    denoised = denoiser(image)

    # Save the denoised rendered image to a file
    denoised_filename = f'renderPedret/XIII/Artificial/pv1_c5.exr'
    # denoised_filename = f'renderPedret/XIII/Artificial+Natural/pv7_c5.exr'   #path for artificial+nat
    # denoised_filename = f'renderPedret/XIII/Natural/pv7_c5.exr'   #path foro artificial+nat

    mi.util.write_bitmap(denoised_filename, denoised)
    print(f'Saved: {denoised_filename}')


def C5_llum_artificial():
    return create_sceneC5_XIII([])

def C5_llum_artificial_mes_natural():
    direction_D3T3 = [-0.00124458, -0.9470212,  -0.32116863]
    direction_D2T3 = [-0.000743358019, -0.795807242, -0.605549569]
    directional_sun = create_distant_directional_emitter(direction_D2T3, file_sun)
    cons_diffuse = create_constant_enviroment_emitter(file_difuse_pedret)

    return create_sceneC5_XIII([directional_sun, cons_diffuse])

def C5_llum_natural():
    direction_D2T3 = [-0.000743358019, -0.795807242, -0.605549569]
    directional_sun = create_distant_directional_emitter(direction_D2T3, file_sun)
    cons_diffuse = create_constant_enviroment_emitter(file_difuse_pedret)

    return create_sceneC5_XIII([directional_sun, cons_diffuse])



C5_llum_artificial()
#C5_llum_artificial_mes_natural()
#C5_llum_natural()
