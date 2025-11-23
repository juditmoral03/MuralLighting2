import mitsuba as mi

mi.set_variant('scalar_spectral')

from mitsuba import ScalarTransform4f as T
import os
import pandas as pd
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


def create_perspective_camera():
    return {
        'type': 'perspective',
        'fov_axis': 'x',
        'fov': 39.597755,
        'near_clip': 0.1,
        'far_clip': 100.0,
        'to_world': T.translate([2.196963, 1.653877, -18.103842]) @
                    T.rotate([0, 0, 1], -1.459980469290317) @
                    T.rotate([0, 1, 0], 77.74145218970608) @
                    T.rotate([1, 0, 0], -1.1946243991554817e-05),
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

def create_spd_file(sheet_name, position, filepath= '/home/manvir/Escriptori/pedretgit/pedret/data/IT1072.xlsx'):
    intensity_column = f'Unnamed: {position}'

    df = pd.read_excel(filepath, sheet_name=sheet_name, 
                       usecols=['Longitud de onda (nm)', intensity_column])

    df = df.drop(df.index[0])
    output_filename = f"spdfiles/{sheet_name}_position{position}.spd"
    with open(output_filename, 'w') as file:
        for index, row in df.iterrows():
            # Ensure the correct intensity column is referenced in the f-string
            file.write(f"{row['Longitud de onda (nm)']} {row[intensity_column]}\n")


def create_emitter_spdfile(position, spd_filename):
    return {
            'type': 'point',
            'position': position,
            'intensity': {
                'type': 'spectrum',
                'filename': spd_filename
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
            file.write(f"{row['wavelength']} {row[' intensity']*0.75}\n")
    #print(f"SPD file '{spd_filename}' has been created.")


#CODE--------------------------------------------------------------------------------------
create_spd_file(sheet_name='Parafina_diam8_Horizontal', position=6)  
create_spd_file(sheet_name='Parafina_diam3_Horizontal', position=6)
create_spd_file(sheet_name='Abeja_Horizontal', position = 6)
create_spd_file(sheet_name='Aceite_Horizontal', position = 6)
create_spd_file(sheet_name='Aceite_sal_Horizontal', position = 2)


#sphere light d65
sphere_light = create_sphere_light([6.42342 , 1.73976 , -17.6098 ], 0.5, 15)
#sphere_light = create_sphere_light([6.484031677246094, 0.601311206817627, -17.736759185791016], 0.5, 5)

#csv tp spd sun
csv_file_path = '2629-sun-sun-sun.csv'
spd_filename = 'spdfiles/sun_spectrum.spd'
ConvertCSVtoSPD_lig(csv_file_path, spd_filename)

#create emitter
emitter_light_parafina_diam8 = create_emitter_spdfile([6.5284 , 1.1359 , -16.852 ],'spdfiles/Parafina_diam8_Horizontal_position6.spd')
emitter_light_parafina_diam3 = create_emitter_spdfile([6.5284 , 1.1359 , -16.852 ],'spdfiles/Parafina_diam3_Horizontal_position6.spd')
emitter_light_Abeja = create_emitter_spdfile([6.5284 , 1.1359 , -16.852 ],'spdfiles/Abeja_Horizontal_position6.spd')
emitter_light_Aceite = create_emitter_spdfile([6.5284 , 1.1359 , -16.852 ],'spdfiles/Aceite_Horizontal_position6.spd')
emitter_light_Aceite_sal = create_emitter_spdfile([6.5284 , 1.1359 , -16.852 ],'spdfiles/Aceite_sal_Horizontal_position2.spd')



sphere_light_parafina_diam8 = create_sphere_light_file([6.5284 , 1.1359 , -16.852 ], 0.05, 'spdfiles/Parafina_diam8_Horizontal_position6.spd')
sphere_light_parafina_diam3 = create_sphere_light_file([6.5284 , 1.1359 , -16.852 ],0.05,'spdfiles/Parafina_diam3_Horizontal_position6.spd')
sphere_light_Abeja = create_sphere_light_file([6.5284 , 1.1359 , -16.852 ],0.05,'spdfiles/Abeja_Horizontal_position6.spd')
sphere_light_Aceite = create_sphere_light_file([6.5284 , 1.1359 , -16.852 ],0.05,'spdfiles/Aceite_Horizontal_position6.spd')
sphere_light_Aceite_sal = create_sphere_light_file([6.5284 , 1.1359 , -16.852 ],0.05,'spdfiles/Aceite_sal_Horizontal_position2.spd')



#emitter_light = create_emitter_spdfile([6.42342 , 1.73976 , -17.6098 ],'spdfiles/Parafina_diam8_Horizontal_position6.spd')
#emitter_light = create_emitter_spdfile([6.484031677246094, 0.601311206817627, -17.736759185791016],'spdfiles/Parafina_diam8_Horizontal_position6.spd')
#emitter_light = create_emitter_spdfile([6.484031677246094, 0.601311206817627, -17.736759185791016],'spdfiles/sun_spectrum.spd')

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
    #'sphere_def': sphere_light,
    #'sphere_def':sphere_light_parafina_diam8,
    'emitter': emitter_light_parafina_diam8,
    'sensor': create_perspective_camera()
}

scene = mi.load_dict(scene_definition)

#----------------------------------------------------------------------
scene = mi.load_dict(scene_definition)

# Render the scene
image = mi.render(scene, spp=16)  # Sensor is already included in the scene

# Save the rendered image to a file
filename = 'renderXII/TexturePedretXII_Parafina_diam8_Horizontal_position6.exr'
mi.util.write_bitmap(filename, image)
print(f'Saved: {filename}')

#area light darrere de camara --> done 
#provar amb point light -->done
#provar amb sun --> done
#horitzontal -->done
#use sphere light to know where the position of the light is--> when i decrease the radius the light intensity decreases

#denoiser --> doesn't support cuda
#video a partir de frames 
#fer video que cuadri amb el video de la flama, hi han poques dades a dataset, fer interpolació lineal segons timestamp