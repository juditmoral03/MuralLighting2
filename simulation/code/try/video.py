import mitsuba as mi

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


def create_spd_file_and_emitter(sheet_name, number, filepath='/home/manvir/Escriptori/pedretgit/pedret/data/IT1073.xlsx'):
    # Adjust to use the actual column names for wavelength and intensity
    df = pd.read_excel(filepath, sheet_name=sheet_name, skiprows=1)
    df = df.drop([0, 1])
    df = df.drop(df.columns[0], axis=1)
    df = df.rename(columns={'ID medida': 'Longitud de onda'})
    output_filename = f"spdvid/{sheet_name}_{number}.spd"

    with open(output_filename, 'w') as file:
        for index, row in df.iterrows():
            # Ensure the correct intensity column is referenced in the f-string
            file.write(f"{row['Longitud de onda']} {row[number]*100000}\n")
    
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



def create_scene(emitter, sheet, number):
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
            'max_depth': 2 #posar mes
        },
        'shape1': obj_shape1,
        'shape2': obj_shape2,
        'shape3': obj_shape3,
        'shape4': obj_shape4,
        'shape5': obj_shape5,
        'shape6': obj_shape6,
        #'sphere_def': sphere_light,
        #'sphere_def':sphere_light_parafina_diam8,
        'emitter': emitter,
        'sensor': create_perspective_camera()
    }

    scene = mi.load_dict(scene_definition)

    # Render the scene
    image = mi.render(scene, spp=16)  # Sensor is already included in the scene

    # Save the rendered image to a file
    filename = f'provaim/PedretXII_{sheet}_{number}.png'
    mi.util.write_bitmap(filename, image)
    print(f'Saved: {filename}')




#CODE--------------------------------------------------------------------------------------
#create_spd_file(sheet_name='Medida Continua. Parafina diam8', position=2)  

excel_file_path =  '/home/manvir/Escriptori/pedretgit/pedret/data/IT1073.xlsx'
xls = pd.ExcelFile(excel_file_path)

sheet_names = xls.sheet_names
#print(sheet_names)

# df = pd.read_excel(excel_file_path, sheet_name='Medida Continua. Parafina diam8')
    
# columns = df.columns.tolist()

# #print(columns)


sheet_name='Medida Continua. Parafina diam3'
# my_emitter = create_spd_file_and_emitter(sheet_name='Medida Continua. Parafina diam3', number=2)  
# create_scene(my_emitter, sheet_name, 2)


for i in range(1,137):
     my_emitter = create_spd_file_and_emitter(sheet_name=sheet_name, number=i)  
     create_scene(my_emitter, sheet_name, i)
    


#-------------------------------------------------------------------------------------------------------------
#video making

from moviepy.editor import ImageSequenceClip

# Directory containing images
image_folder = '/home/manvir/Escriptori/pedretgit/pedret/rendersvid2'

# Video name
video_name = 'Parafina diam3_124_.mp4'

# Get list of images
images = [img for img in os.listdir(image_folder) if img.endswith(".png")]

# Sort images if necessary
images.sort()

clip = ImageSequenceClip([os.path.join(image_folder, img) for img in images], fps=25)
clip.write_videofile(video_name)


# # Calculate and save differences
# from skimage import io
# from skimage.util import compare_images
# import matplotlib.pyplot as plt
# from skimage import io, img_as_float
# import numpy as np

# image_folder = '/home/manvir/Escriptori/pedretgit/pedret/provaim'

# # Get list of images
# images = [img for img in os.listdir(image_folder) if img.endswith(".png")]



# previous_image = None

# for i, img in enumerate(images):
#     current_image = img_as_float(io.imread(os.path.join(image_folder, img)))

#     if previous_image is not None:
#         diff_image = compare_images(previous_image, current_image, method='diff')
        
#         # Normalize the difference image
#         diff_image = np.abs(diff_image)
        
#         plt.imshow(diff_image, cmap='plasma')
#         diff_filename = f'diff/diff_{i:03d}.png'
#         plt.axis('off')
#         plt.savefig(diff_filename, bbox_inches='tight', pad_inches=0)
#         plt.close()
    
#     previous_image = current_image
