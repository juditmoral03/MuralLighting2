import drjit as dr
import mitsuba as mi
import gc
import torch

# Enable Dr.Jit's debug mode before initializing Mitsuba
dr.set_flag(dr.JitFlag.Debug, True)

# Function to print current GPU memory usage
def print_gpu_memory_usage():
    if torch.cuda.is_available():
        print(f"Allocated: {torch.cuda.memory_allocated() / 1024 ** 2:.2f} MB")
        print(f"Reserved: {torch.cuda.memory_reserved() / 1024 ** 2:.2f} MB")
    else:
        print("CUDA is not available.")

# Set the variant to use the GPU
mi.set_variant('cuda_spectral')

print("After setting variant:")
print_gpu_memory_usage()

# Load the scene from the XML file
scene = mi.load_file("code/xml/project.xml")

print("After loading scene:")
print_gpu_memory_usage()

# Run garbage collection to free up any unused memory
gc.collect()
torch.cuda.empty_cache()

print("After garbage collection:")
print_gpu_memory_usage()

# Render the scene
image = mi.render(scene, spp=256)  # Start with a lower value and gradually increase

print("After rendering scene:")
print_gpu_memory_usage()

# Save the rendered image to a file
mi.util.write_bitmap("renderPedret/XII/renders/myrender_1.png", image)

print("Rendering completed and image saved.")
print_gpu_memory_usage()
