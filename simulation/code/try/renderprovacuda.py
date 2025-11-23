import mitsuba as mi

mi.set_variant('cuda_spectral')
scene = mi.load_file("/home/manu/Desktop/project/Pedret_Project/code/xml/project.xml")
image = mi.render(scene, spp=1024)

mi.util.write_bitmap("my_first_render2.png", image)




# import matplotlib.pyplot as plt


# #DENOISER 
# # Set a `cuda` variant
# mi.set_variant('cuda_ad_rgb')

# # Use the `box` reconstruction filter
# scene_description = mi.cornell_box()
# scene_description['sensor']['film']['rfilter']['type'] = 'box'
# scene = mi.load_dict(scene_description)

# noisy = mi.render(scene, spp=1)

# # Denoise the rendered image
# denoiser = mi.OptixDenoiser(input_size=noisy.shape[:2], albedo=False, normals=False, temporal=False)
# denoised = denoiser(noisy)

# fig, axs = plt.subplots(1, 2, figsize=(12, 4))
# axs[0].imshow(mi.util.convert_to_bitmap(noisy));     axs[0].axis('off'); axs[0].set_title('noisy (1 spp)')
# axs[1].imshow(mi.util.convert_to_bitmap(denoised));  axs[1].axis('off'); axs[1].set_title('denoised')