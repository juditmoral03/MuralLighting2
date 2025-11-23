import mitsuba as mi
import numpy as np


path = "renderPedret/C4-natural-and-artificial-pv2-upscale:0.5,sampler:independent,max_depth:6,exposure:13,spp:2048,save_noisy:True,save_albedo:False,save_normals:True,use_gray_albedo:False"
save_albedo = True
save_normals = True
exposure=13


#load the data
noisy_multichannel = mi.Bitmap(path+"-multichannel.exr")
to_sensor_matrix = np.load(path+"-to_sensor.npy")
path = "renderPedret/testing"

# Denoise the rendered image
mi.set_variant("cuda_ad_spectral")
to_sensor = mi.cuda_ad_rgb.Transform4f(to_sensor_matrix)
denoiser = mi.OptixDenoiser(input_size=noisy_multichannel.size(), albedo=True, normals=False, temporal=False)
denoised = denoiser(noisy_multichannel, albedo_ch="albedo", normals_ch="normals", to_sensor=to_sensor)

# save denoised image
mi.util.write_bitmap(path+ "-denoised.exr", denoised)

if save_albedo:  # save also albedo and normal map
    #print(noisy_multichannel)
    #print(noisy_multichannel.split())
    mi.util.write_bitmap(path +  "-albedo.exr", noisy_multichannel.split()[1][1])
    mi.util.write_bitmap(path + "-albedo.jpg", noisy_multichannel.split()[1][1])

if save_normals:
    mi.util.write_bitmap(path + "-normal.exr", noisy_multichannel.split()[3][1])
    mi.util.write_bitmap(path + "-normal.jpg", noisy_multichannel.split()[3][1])

if exposure != 1:
    denoised = np.array(denoised)
    denoised *= pow(2, exposure)
    mi.util.write_bitmap(path + "-denoised-adjusted.exr", denoised)
    mi.util.write_bitmap(path + "-denoised-adjusted.jpg", denoised)