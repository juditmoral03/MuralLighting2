import mitsuba as mi


#mi.set_variant('scalar_spectral')
mi.set_variant('cuda_ad_rgb')


from mitsuba import ScalarTransform4f as T
import pandas as pd
import os

#FUNCTIONS------------------------------------------------------------------------------------------
#Use SCI if you want to capture both the color and sheen (like shiny plastics or metals).
#Use SCE if you are focusing solely on the color properties of a matte or non-glossy surface.
def ConvertCSVtoSPD_mat(fileName):
    # Extract the base name without the extension to use in creating unique spd file names
    base_name = os.path.splitext(os.path.basename(fileName))[0]

    df = pd.read_csv(fileName)

    # Define the spectral channels you're interested in
    channels = ['sci', 'sce']
    spd_files = {}  # Store the filenames here

    # Create SPD files for each channel
    for channel in channels:
        # Create a unique file name for each channel
        spd_filename = f'{base_name}_{channel}.spd'
        with open(spd_filename, 'w') as spd_file:
            for _, row in df.iterrows():
                # Write each wavelength and value pair to the SPD file
                spd_file.write(f"{row['wl']} {row[channel]}\n")
        spd_files[channel] = spd_filename
    #print(f"SPD file '{spd_filename}' has been created.")



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


# def load_sensor(r, phi, theta):
#     origin = T.rotate([0, 0, 1], phi).rotate([0, 1, 0], theta) @ mi.ScalarPoint3f([0, 0, r])
#     return mi.load_dict({
#         'type': 'perspective',
#         'fov': 20,
#         'to_world': T.look_at(
#             origin=origin,
#             target=[0, 0, 0],
#             up=[0, 1, 0]
#         ),
#         'sampler': {
#             'type': 'independent',
#             'sample_count': 256
#         },
#         'film': {
#             'type': 'specfilm',
#             'width': 1920,
#             'height': 1080,
#             'filter': { 'type': 'gaussian' },  # Ensure only one filter key is present
#             'band1': {
#                 'type': 'spectrum',
#                 'filename': 'spectralS1_sce.spd'
#             },
#             'band2': {
#                 'type': 'spectrum',
#                 'filename': 'spectralS2_sce.spd'
#             },
#             'band3': {
#                 'type': 'spectrum',
#                 'filename': 'spectralS3_sce.spd'
#             }
#         },
#     })

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
            'sample_count': 256
        },
        'film': {
            'type': 'hdrfilm',
            'width': 1920,
            'height': 1080,
            # 'rfilter': {
            #     'type': 'tent',
            # },
            # 'pixel_format': 'rgb',
        },
    })
    
    
def create_sphere(center, radius, spd_filename):
    sphere_def = {
        'type': 'sphere',
        'center': center,
        'radius': radius,
        'bsdf': {
            'type': 'plastic',
            'diffuse_reflectance': {
                'type': 'spectrum',
                'filename': spd_filename
            }
        }
    }
    return sphere_def
    
#CODE------------------------------------------------------------------------------------------

#spectral light 
csv_file_path = '2629-sun-sun-sun.csv'

spd_filename = 'sun_spectrum.spd'
ConvertCSVtoSPD_lig(csv_file_path, spd_filename)

ConvertCSVtoSPD_mat('spectralMaterials/spectralS1.csv')
ConvertCSVtoSPD_mat('spectralMaterials/spectralS2.csv')
ConvertCSVtoSPD_mat('spectralMaterials/spectralS3.csv')

# Scene setup
scene_definition = {
    'type': 'scene',
    'integrator': {
        'type': 'path',  # Adding the path tracer integrator
        'max_depth': 2
    },
        
    # 'point_light':{
    #     'type': 'point',
    #     'position': [10.0, 0.0, 10.0],
    #     'intensity': {
    #         'type': 'spectrum',
    #         'value': 10.0,
    #     }    
    # }
    
    # 'emitter_id': {
    #     'type': 'point',
    #     'position': [10.0, 0.0, 10.0],
    #     'intensity': {
    #         'type': 'spectrum',
    #         'filename': spd_filename
    #     }
    # },
     'sphere_def' : {
        'type': 'sphere',
        'center': [10.0, 10, 0],
        'radius': 2,
        'emitter': {
            'type': 'area',
            'radiance': {
                'type':'d65',
            }
        }
     },
}
#include spheres
scene_definition['sphere_1'] = create_sphere([0, 0, 0], 2, 'spectralS1_sce.spd')
scene_definition['sphere_2'] = create_sphere([15, 0, 0], 2, 'spectralS2_sce.spd')
scene_definition['sphere_3'] = create_sphere([-15, 0, 0], 2, 'spectralS3_sce.spd')

# Load the scene
scene = mi.load_dict(scene_definition)

sensor_count = 1
radius = 100
phis = [20.0 * i for i in range(sensor_count)]
theta = 50.0

# Create sensors based on the above parameters
sensors = [load_sensor(radius, phi, theta) for phi in phis]

# Render the scene from the perspectives of all sensors
images = [mi.render(scene, spp=11, sensor=sensor) for sensor in sensors]

# Save each image to a separate file
for i, img in enumerate(images):
    filename = f'renders/zholipecoutput{i}.png'
    mi.util.write_bitmap(filename, img)
    print(f'Saved: {filename}')




 