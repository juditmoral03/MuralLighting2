import drjit as dr
import mitsuba as mi
import drjit as dr

import datetime
import numpy as np

#print(mi.__file__)
mi.set_log_level(mi.LogLevel.Info)

mi.set_variant('llvm_ad_spectral')

#from MyNormalMap import MyNormalMap
#mi.register_bsdf("mynormalmap", lambda props: MyNormalMap(props))

from mitsuba import ScalarTransform4f as T
import pandas as pd

from sunsky_configurations import SUNSKY_CONFIGURATIONS

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
            'type': 'normalmap',
            'normalmap': {
                'type': 'bitmap',
                'raw': True,
                'filename': 'textures/normalmap.jpg'
            },
            'bsdf': {
                'type': 'diffuse',
                'reflectance': {
                'type': 'rgb',
                'value': [1,1,1],
                }
            }
        }
    }

def create_distant_directional_emitter(dirBlender, file):
    dirMitsuba = [dirBlender[0], dirBlender[2], -dirBlender[1]]
    return {
        'type' : 'directional',
        'direction': dirMitsuba,
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
        'face_normals': False,
        #'bsdf': {
        #    'type': 'twosided',
            'bsdf': {
                'type': 'normalmap',#mynormalmap
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
        #}
    }

def create_shape_rgb(filename, color):
    return {
        'type': 'obj',
        'filename': filename,
        'bsdf': {
            'type': 'normalmap',
            'normalmap': {
                'type': 'bitmap',
                'raw': True,
                'filename': 'textures/normalmap.jpg'
            },
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
            'type': 'normalmap',
            'normalmap': {
                'type': 'bitmap',
                'raw': True,
                'filename': 'textures/normalmap.jpg'
            },
            'bsdf': {
                'type': 'dielectric',
                'int_ior': 'bk7',
                'ext_ior':'air', 
            }
        }
    }


#camera when we use cuda
from mitsuba import ScalarTransform4f as T, ScalarPoint3f, Vector3f


def ConvertCSVtoSPD_lig(csv_file_path, spd_filename):
    # Read the CSV file, skipping the first 13 rows
    df = pd.read_csv(csv_file_path, delimiter=',', skiprows=13)
   
    # Write the spectral data to an SPD file
    with open(spd_filename, 'w') as file:
        for index, row in df.iterrows():
            file.write(f"{row['wavelength']} {row[' intensity']}\n")
    #print(f"SPD file '{spd_filename}' has been created.")

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


def add_SXII_shapes(shapes, use_gray_albedo = False):
    t1 = 'textures/pedret_XII/Pedret_X_color_1.png'
    t2 = 'textures/pedret_XII/Pedret_X_color_2.png'
    t3 = 'textures/pedret_XII/Pedret_XII_color_absC.png'
    t4 = 'textures/pedret_XII/Pedret_XII_color_absN.png'
    t5 = 'textures/pedret_XII/Pedret_XII_color_absS.png'
    t6 = 'textures/pedret_XII/Pedret_XII_color_nau.png'
    if use_gray_albedo:
        t1 = t2 = t3 = t4 = t5 = t6 = 'textures/midgray.png'

    shapes.append(create_obj_shape('model/XII_2/Pedret_XII.baked-1.obj', 'textures/pedret_XII/Pedret_X_normals_1.png', t1))
    shapes.append(create_obj_shape('model/XII_2/Pedret_XII.baked-2.obj', 'textures/pedret_XII/Pedret_X_normals_2.png', t2))
    shapes.append(create_obj_shape('model/XII_2/Pedret_XII.baked-absC.obj', 'textures/pedret_XII/Pedret_XII_normals_absC.png', t3))
    shapes.append(create_obj_shape('model/XII_2/Pedret_XII.baked-absN.obj', 'textures/pedret_XII/Pedret_XII_normals_absN.png', t4))
    shapes.append(create_obj_shape('model/XII_2/Pedret_XII.baked-absS.obj', 'textures/pedret_XII/Pedret_XII_normals_absS.png', t5))
    shapes.append(create_obj_shape('model/XII_2/Pedret_XII.baked-nau.obj', 'textures/pedret_XII/Pedret_XII_normals_nau.png', t6))

def add_SXIII_shapes(shapes, use_gray_albedo = False):
    t1 = 'textures/pedret_XII/Pedret_XIII_color_1.png'
    t2 = 'textures/pedret_XII/Pedret_XIII_color_2.png'
    t3 = 'textures/pedret_XII/Pedret_XII_color_absC.png'
    t4 = 'textures/pedret_XII/Pedret_XII_color_absN.png'
    t5 = 'textures/pedret_XII/Pedret_XII_color_absS.png'
    t6 = 'textures/pedret_XII/Pedret_XII_color_nau.png'
    if use_gray_albedo:
        t1 = t2 = t3 = t4 = t5 = t6 = 'textures/midgray.png'

    shapes.append(create_obj_shape('model/XIII/Pedret_XIII_1.obj', 'textures/pedret_XII/Pedret_XIII_normals_1.png', t1))
    shapes.append(create_obj_shape('model/XIII/Pedret_XIII_2.obj', 'textures/pedret_XII/Pedret_XIII_normals_2.png', t2))
    shapes.append(create_obj_shape('model/XIII/Pedret_XIII_absC.obj', 'textures/pedret_XII/Pedret_XII_normals_absC.png', t3))
    shapes.append(create_obj_shape('model/XIII/Pedret_XIII_absN.obj', 'textures/pedret_XII/Pedret_XII_normals_absN.png', t4))
    shapes.append(create_obj_shape('model/XIII/Pedret_XIII_absS.obj', 'textures/pedret_XII/Pedret_XII_normals_absS.png', t5))
    shapes.append(create_obj_shape('model/XIII/Pedret_XIII_nau.obj', 'textures/pedret_XII/Pedret_XII_normals_nau.png', t6))
    
def add_corona_shapes(shapes):
    color = [0.05, 0.05, 0.05]
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Anella.obj', color))
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Anella2.obj', color))
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Base.obj', color))
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Cadena.obj', color))
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Cadena2.obj', color))
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Cadena3.obj', color))
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Ganxo.obj', color))
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Ganxo2.obj', color))
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Ganxo3.obj', color))
    shapes.append(create_shape_rgb('iluminació/c1/Corona/Ganxo4.obj', color))
    shapes.append(create_shape_dielectric('iluminació/c1/Corona/Llums.obj'))
    shapes.append(create_obj_file_light_file('iluminació/c1/Corona/flama1.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd'))
    shapes.append(create_obj_file_light_file('iluminació/c1/Corona/flama2.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd'))
    shapes.append(create_obj_file_light_file('iluminació/c1/Corona/flama3.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd'))
    shapes.append(create_obj_file_light_file('iluminació/c1/Corona/flama4.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd'))
    shapes.append(create_obj_file_light_file('iluminació/c1/Corona/flama5.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd'))
    shapes.append(create_obj_file_light_file('iluminació/c1/Corona/flama6.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd'))

def add_llantia_shapes(shapes):
    #llantia1
    shapes.append(create_shape_rgb('iluminació/c1/Llantia1/Argolla.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c1/Llantia1/Cordill1Mesh.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c1/Llantia1/Cordill2Mesh.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c1/Llantia1/Cordill3Mesh.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c1/Llantia1/Cordill4Mesh.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_dielectric('iluminació/c1/Llantia1/Llum.obj'))
    shapes.append(create_obj_file_light_file('iluminació/c1/Llantia1/Flama.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd'))

    #llantia2
    shapes.append(create_shape_rgb('iluminació/c1/Llantia2/Argolla.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c1/Llantia2/Cordill1Mesh.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c1/Llantia2/Cordill2Mesh.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c1/Llantia2/Cordill3Mesh.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c1/Llantia2/Cordill4Mesh.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_dielectric('iluminació/c1/Llantia2/Llum.obj'))
    shapes.append(create_obj_file_light_file('iluminació/c1/Llantia2/Flama.obj', 'spdFiles/XII/Aceite_sal_Horizontal_position2_by_flamearea.spd'))

def add_candelers(shapes):
    #candeler 1
    shapes.append(create_shape_rgb('iluminació/c2/candeler1/holder_1.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c2/candeler1/candle_1.obj', [0.8, 0.58, 0.33]))
    shapes.append(create_shape_rgb('iluminació/c2/candeler1/candle_wick_1.obj', [0.80, 0.48, 0.28]))
    shapes.append(create_obj_file_light_file('iluminació/c2/candeler1/flame_1.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd'))

    #candeler 2
    shapes.append(create_shape_rgb('iluminació/c2/candeler2/holder_2.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c2/candeler2/candle_2.obj', [0.8, 0.58, 0.33]))
    shapes.append(create_shape_rgb('iluminació/c2/candeler2/candle_wick_2.obj', [0.80, 0.48, 0.28]))
    shapes.append(create_obj_file_light_file('iluminació/c2/candeler2/flame_2.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd'))

def add_candelers2(shapes):
    #canelobre 1
    shapes.append(create_shape_rgb('iluminació/c3/canelobre1/holder.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c3/canelobre1/candle_2.obj', [0.8, 0.58, 0.33]))
    shapes.append(create_shape_rgb('iluminació/c3/canelobre1/candle_wick_2.obj', [0.80, 0.48, 0.28]))
    shapes.append(create_obj_file_light_file('iluminació/c3/canelobre1/flame.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd'))

    #canelobre 2
    shapes.append(create_shape_rgb('iluminació/c3/canelobre2/holder.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c3/canelobre2/candle_2.obj', [0.8, 0.58, 0.33]))
    shapes.append(create_shape_rgb('iluminació/c3/canelobre2/candle_wick_2.obj', [0.80, 0.48, 0.28]))
    shapes.append(create_obj_file_light_file('iluminació/c3/canelobre2/flame.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd'))


def add_candelers4(shapes):
    #canelobre 1
    shapes.append(create_shape_rgb('iluminació/c3/canelobre1/holder.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c3/canelobre1/candle_2.obj', [0.8, 0.58, 0.33]))
    shapes.append(create_shape_rgb('iluminació/c3/canelobre1/candle_wick_2.obj', [0.80, 0.48, 0.28]))
    shapes.append(create_obj_file_light_file('iluminació/c3/canelobre1/flame.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd'))

    #canelobre 2
    shapes.append(create_shape_rgb('iluminació/c3/canelobre2/holder.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c3/canelobre2/candle_2.obj', [0.8, 0.58, 0.33]))
    shapes.append(create_shape_rgb('iluminació/c3/canelobre2/candle_wick_2.obj', [0.80, 0.48, 0.28]))
    shapes.append(create_obj_file_light_file('iluminació/c3/canelobre2/flame.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd'))

    #canelobre 3
    shapes.append(create_shape_rgb('iluminació/c4/canelobre3/holder_3.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c4/canelobre3/candle_3.obj', [0.8, 0.58, 0.33]))
    shapes.append(create_shape_rgb('iluminació/c4/canelobre3/candle_wick_3.obj', [0.80, 0.48, 0.28]))
    shapes.append(create_obj_file_light_file('iluminació/c4/canelobre3/flame_3.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd'))

    #canelobre 4
    shapes.append(create_shape_rgb('iluminació/c4/canelobre4/holder_4.obj', [0.05, 0.05, 0.05]))
    shapes.append(create_shape_rgb('iluminació/c4/canelobre4/candle_4.obj', [0.8, 0.58, 0.33]))
    shapes.append(create_shape_rgb('iluminació/c4/canelobre4/candle_wick_4.obj', [0.80, 0.48, 0.28]))
    shapes.append(create_obj_file_light_file('iluminació/c4/canelobre4/flame_4.obj', 'spdFiles/XII/Parafina_diam3_Horizontal_position2_by_flamearea.spd'))


def add_altar(shapes):
    shapes.append(create_obj_shape('iluminació/Base.obj', "textures/altar/plastersubstance001_Plaster_normal.png", "textures/altar/plastersubstance001_Plaster_basecolor.png"))
    shapes.append(create_obj_shape('iluminació/Llosa.obj', "textures/altar/granite_001_Granite_001_normal.png", "textures/altar/granite_001_Granite_001_basecolor.png"))


def create_scene_from_shapes(building_shapes, lighting_shapes):
    scene_definition = { 'type': 'scene' }
    for i, shape in enumerate(building_shapes):
        scene_definition[f'b_shape{i+1}'] = shape
    for i, shape in enumerate(lighting_shapes):
        scene_definition[f'l_shape{i+1}'] = shape
    return scene_definition

def create_aov_integrator(max_depth):
    return mi.load_dict({
    'type': 'aov',
    'aovs': 'albedo:albedo,normals:sh_normal',#tex_normal
    'integrator': {
        'type': 'path',
        'max_depth': max_depth
    }
    })

def add_camera(scene, translation, rotX, rotY, rotZ, fov, sampler, upscale = 1):
    scene['sensor'] = {
        'type': 'perspective',
        'fov_axis': 'x',
        'fov': fov,
        'near_clip': 0.1,
        'far_clip': 1000.0,
        'to_world': T().translate(mi.ScalarPoint3f(translation.x, translation.z, -translation.y)) @
                    T().rotate([0, 1, 0], rotZ) @
                    T().rotate([0, 0, 1], -rotY+180) @
                    T().rotate([-1, 0, 0], (rotX+90)),
#        'to_world': T().translate(mi.Point3f(translation[0], translation[1], translation[2])) @
#                    T().rotate([1, 0, 0], rotX) @
#                    T().rotate([0, 1, 0], rotZ) @
#                    T().rotate([0, 0, 1], rotY),
        'sampler': {
            'type': sampler,
            'sample_count': 4
        },
        'film': {
            'type': 'hdrfilm',
            'width': int(1024*upscale),  
            'height': int(1024*upscale),  
            'filter': {'type': 'box'}
        }
    }

def pvExt():
    translation = mi.Point3f(-19.7637, -3.08869, 12.4302)
    rotX  = 61.8091
    rotY  = 0.001683
    rotZ  = -76.2696
    fov = 61.9
    return (translation, rotX, rotY, rotZ, fov)

def pv1():
    translation = mi.Point3f(-4.21867, 3.15803, 4.85095)
    rotX  = 93.9045
    rotY  = -0.000112
    rotZ  = -113.164
    fov = 61.9
    return (translation, rotX, rotY, rotZ, fov)

def pv2():
    translation = mi.ScalarPoint3f(0.690537, 1.29192, 5.13331)
    rotX  = 95.4049
    rotY  = -0.000511
    rotZ  = 246.84
    fov = 61.9
    return (translation, rotX, rotY, rotZ, fov)

def pv7():
    translation = mi.Point3f(-3.04298, 5.0747, 3.6798)
    rotX  = 99.3053
    rotY  = -0.000209
    rotZ  = -131.466
    fov = 61.9
    return (translation, rotX, rotY, rotZ, fov)

def my_render(scene, spp, integrator, exposure, basename, save_albedo = False, save_normals = False, save_noisy = True, exposure_noisy = 1):
    sensor = scene.sensors()[0]
    to_sensor = sensor.world_transform().inverse()
    print("Rendering the scene")
    print(datetime.datetime.now())
    image = mi.render(scene, spp=spp, integrator=integrator)  
    print(datetime.datetime.now())

    # save multichannel image
    noisy_multichannel = sensor.film().bitmap()
    mi.util.write_bitmap("renderPedret/"+basename+"-multichannel.exr", noisy_multichannel)
    # Extract and convert the transform to a numpy array:
    to_sensor_matrix = np.array(dr.detach(to_sensor.matrix), dtype=np.float32, order='C')
    np.save("renderPedret/"+basename+"-to_sensor.npy", to_sensor_matrix)

    # Denoise the rendered image
    mi.set_variant("cuda_ad_spectral")
    to_sensor = mi.cuda_ad_rgb.Transform4f(to_sensor_matrix)
#    to_sensor = mi.cuda_ad_rgb.Transform4f(to_sensor)
    denoiser = mi.OptixDenoiser(input_size=noisy_multichannel.size(), albedo=True, normals=False, temporal=False) # TODO!!!
    denoised = denoiser(noisy_multichannel, albedo_ch="albedo", normals_ch="normals", to_sensor=to_sensor)
    # save denoised image
    mi.util.write_bitmap("renderPedret/" + basename + "-denoised.exr", denoised)

    if save_albedo:  # save also albedo and normal map
        #print(noisy_multichannel)
        #print(noisy_multichannel.split())
        mi.util.write_bitmap("renderPedret/" + basename + "-albedo.exr", noisy_multichannel.split()[1][1])
        mi.util.write_bitmap("renderPedret/" + basename + "-albedo.jpg", noisy_multichannel.split()[1][1])
    
    if save_normals:
        mi.util.write_bitmap("renderPedret/" + basename + "-normal.exr", noisy_multichannel.split()[3][1])
        mi.util.write_bitmap("renderPedret/" + basename + "-normal.jpg", noisy_multichannel.split()[3][1])


    if False:
        denoiser = mi.OptixDenoiser(input_size=noisy_multichannel.size(), albedo=False, normals=False, temporal=False)
        denoised2 = denoiser(noisy_multichannel)
        mi.util.write_bitmap("renderPedret/carlos2-denoised-no-albedo.exr", denoised2)
        denoised2 = None

    if exposure != 1:
        print("Adjusting exposure...")
        denoised = np.array(denoised)
        denoised *= pow(2, exposure)
        mi.util.write_bitmap("renderPedret/" + basename + "-denoised-adjusted.exr", denoised)

    if save_noisy:
        noisy = dict(noisy_multichannel.split())['<root>']        
        if exposure_noisy != 1:
            print("Adjusting exposure...")
            noisy = np.array(noisy)
            noisy *= pow(2, exposure_noisy)
            mi.util.write_bitmap("renderPedret/" + basename + "-noisy.exr", noisy)

    mi.set_variant("llvm_ad_spectral")

def generate_shapes(load_church_model, use_gray_albedo):
    shapes = []
    load_church_model(shapes, use_gray_albedo)
    add_altar(shapes)

    return shapes

def generate_C1_shapes():
    shapes = []
    add_corona_shapes(shapes)
    add_llantia_shapes(shapes)
    return shapes

def generate_C2_shapes():
    shapes = []
    add_candelers(shapes)
    return shapes

def generate_C3_shapes():
    shapes = []
    add_candelers2(shapes)
    return shapes

def generate_C4_shapes():
    shapes = []
    add_candelers4(shapes)
    return shapes

def generate_C5_shapes():
    shapes = []
    add_corona_shapes(shapes)
    add_llantia_shapes(shapes)
    add_candelers(shapes)
    add_candelers4(shapes)
    return shapes


def generate_natural_light(moment):
    direction = SUNSKY_CONFIGURATIONS.get(moment).get("sundir")
    sun_file = SUNSKY_CONFIGURATIONS.get(moment).get("sun_file")
    sky_file = SUNSKY_CONFIGURATIONS.get(moment).get("sky_file")
    directional_sun = create_distant_directional_emitter(direction, 'emitters/spd/'+sun_file)#file_sun
    cons_diffuse = create_constant_enviroment_emitter('emitters/spd/'+sky_file)#file_difuse_pedret
    return [directional_sun, cons_diffuse]


def make_filename_compatible(s):
    invalid = """#%&{}\<>*?/$!'"@+`|= """
    for c in invalid: 
        s = s.replace(c, "")
    return s

def render(basename, upscale, model, artificial_lighting_shape_generator, natural_lighting_generator, sampler, max_depth, exposure, spp, point_of_view, save_noisy, save_albedo = False, save_normals = True, use_gray_albedo = False):
    local_vars = locals()
    del local_vars['artificial_lighting_shape_generator']
    del local_vars['point_of_view']
    del local_vars['basename']
    del local_vars['natural_lighting_generator']
    del local_vars['model']
    local_vars = make_filename_compatible(str(local_vars))
    print(local_vars)
    building_shapes = generate_shapes(model, use_gray_albedo)
    lighting_shapes = []
    if artificial_lighting_shape_generator:
        lighting_shapes = artificial_lighting_shape_generator()
    scene_definition = create_scene_from_shapes(building_shapes, lighting_shapes)
    
    if natural_lighting_generator:
        emitters = generate_natural_light(natural_lighting_generator)
        for i, emitter in enumerate(emitters):
            scene_definition[f'emitter{i+1}'] = emitter

    (translation, rotX, rotY, rotZ, fov) = point_of_view
    add_camera(scene_definition, translation=translation, rotX=rotX, rotY=rotY, rotZ=rotZ, fov=fov, sampler = sampler, upscale=upscale)
    print(scene_definition)
    scene = mi.load_dict(scene_definition)
    integrator = create_aov_integrator(max_depth)
    my_render(scene=scene, spp=spp, integrator=integrator, exposure=exposure, basename=basename+"-"+local_vars,
              save_noisy=save_noisy, exposure_noisy=exposure, save_albedo=save_albedo, save_normals=save_normals)


sampler = 'independent' # sampler = 'stratified'  sampler = 'multijitter' sampler = 'orthogonal'
exposure = 13 # 18 
#spp = 256
#pov = pv1()
#for spp in [513]: #[256, 512, 1024, 2048, 4096, 8192]:
    #render("C5-natural-and-artificial-pv1", upscale=0.25, shape_generator = generate_C5_shapes, emitter_generator = generate_natural_light, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = pv1(), save_noisy=False, save_albedo = False, use_gray_albedo=True)
    #pass

# high-quality C% natural
spp = 8096 # 2048
#render("C5-natural-and-artificial-pv1", upscale=2.5, shape_generator = generate_C5_shapes, emitter_generator = generate_natural_light, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = pv1(), save_noisy=False, save_albedo = False, use_gray_albedo=False)
#render("C1-natural-and-artificial-pv2", upscale=0.25, shape_generator = generate_C1_shapes, emitter_generator = generate_natural_light, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = pv2(), save_noisy=True, save_albedo = False, use_gray_albedo=False)
#render("C1-natural-and-artificial-pv2", upscale=2, shape_generator = generate_C1_shapes, emitter_generator = generate_natural_light, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = pv2(), save_noisy=True, save_albedo = False, use_gray_albedo=False)
#render("C4-natural-and-artificial-pv2", upscale=0.5, building_shape_generator = generate_sXII_shapes, artificial_lighting_shape_generator = generate_C4_shapes, natural_lighting_generator = "D1T1", sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = pv2(), save_noisy=False, save_albedo = False, use_gray_albedo=False)
#render("C4-artificial-pv2", upscale=0.5, building_shape_generator = generate_sXII_shapes, artificial_lighting_shape_generator = generate_C4_shapes, natural_lighting_generator = False, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = pv2(), save_noisy=False, save_albedo = False, use_gray_albedo=False)

#NATURAL
#moment = "D1T1"
#render(moment+"-natural-pv2", upscale=2, building_shape_generator = generate_sXII_shapes, artificial_lighting_shape_generator = False, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = pv2(), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
#moment = "D1T2"
#render(moment+"-natural-pv2", upscale=2, building_shape_generator = generate_sXII_shapes, artificial_lighting_shape_generator = False, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = pv2(), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
#moment = "D1T3"
#render(moment+"-natural-pv2", upscale=2, building_shape_generator = generate_sXII_shapes, artificial_lighting_shape_generator = False, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = pv2(), save_noisy=True, save_albedo = False, use_gray_albedo=False, save_normals=True)
#moment = "D2T1"
#render(moment+"-natural-pv2", upscale=2, building_shape_generator = generate_sXII_shapes, artificial_lighting_shape_generator = False, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = pv2(), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
#moment = "D2T2"
#render(moment+"-natural-pv2", upscale=2, building_shape_generator = generate_sXII_shapes, artificial_lighting_shape_generator = False, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = pv2(), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
#moment = "D2T3"
#render(moment+"-natural-pv2", upscale=2, building_shape_generator = generate_sXII_shapes, artificial_lighting_shape_generator = False, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = pv2(), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
#moment = "D3T1"
#render(moment+"-natural-pv2", upscale=2, building_shape_generator = generate_sXII_shapes, artificial_lighting_shape_generator = False, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = pv2(), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
#moment = "D3T2"
#render(moment+"-natural-pv2", upscale=2, building_shape_generator = generate_sXII_shapes, artificial_lighting_shape_generator = False, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = pv2(), save_noisy=False, save_albedo = False, use_gray_albedo=False, save_normals=False)
#moment = "D3T3"
#render(moment+"-natural-pv2", upscale=2, building_shape_generator = generate_sXII_shapes, artificial_lighting_shape_generator = False, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = pv2(), save_noisy=True, save_albedo = False, use_gray_albedo=False, save_normals=False)


#Artificial
#moment = False
#spp=8096
#for artLightConfig in [generate_C2_shapes, generate_C3_shapes, generate_C5_shapes]:#, generate_C4_shapes, generate_C1_shapes]:
#    print(str(artLightConfig).split('_')[1])
#    render(str(moment)+"-artificial"+str(artLightConfig).split('_')[1]+"-pv2", upscale=2, building_shape_generator = generate_sXII_shapes, artificial_lighting_shape_generator = artLightConfig, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = pv2(), save_noisy=True, save_albedo = False, use_gray_albedo=False, save_normals=False)

#Natural+Articficial
spp=8096
for moment in ["D1T3", "D2T3"]:
    for artLightConfig in [generate_C2_shapes, generate_C5_shapes]:#generate_C4_shapes
        print(str(moment)+" "+str(artLightConfig).split('_')[1])
        render(str(moment)+"-atificial"+str(artLightConfig).split('_')[1]+"-pv2", upscale=2, building_shape_generator = generate_sXII_shapes, artificial_lighting_shape_generator = artLightConfig, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = pv2(), save_noisy=True, save_albedo = False, use_gray_albedo=False, save_normals=False)

print("Finished")

"""moment = "D1T3"
exposure=12
for spp in [512, 1024, 2048, 4096, 8192]:
    render(moment+"-natural-pv2", upscale=0.5, building_shape_generator = generate_sXII_shapes, artificial_lighting_shape_generator = False, natural_lighting_generator = moment, sampler=sampler, max_depth=6, exposure = exposure, spp = spp, point_of_view = pv2(), save_noisy=False, save_albedo = False, use_gray_albedo=False)
"""


# Force cleanup of DrJit resources to avoid hanging
#dr.flush_malloc_cache()  # Clear memory cache
import gc
gc.collect()
#mi.shutdown()  # Shutdown DrJit explicitly (if applicable)
