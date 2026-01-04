import torch
import numpy as np
import nibabel as nib
from monai.networks.nets import UNETR
from monai.inferers import sliding_window_inference
from monai.transforms import (
    Compose, LoadImage, EnsureChannelFirst, Orientation, 
    Spacing, NormalizeIntensity, RemoveSmallObjects
)
from skimage import measure
import trimesh
import os

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = r"c:\Projects 2\Neuroflash\1\Models\unetr_best_stroke_model.pth"

# --- 1. MODEL LOADING ---
def load_model():
    model = UNETR(
        in_channels=1,
        out_channels=3,
        img_size=(96, 96, 96),
        feature_size=16,
        hidden_size=768,
        mlp_dim=3072,
        num_heads=12,
        proj_type="perceptron",
        norm_name="instance",
        res_block=True,
    ).to(DEVICE)
    
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()
    return model

# --- 2. PREPROCESSING ---
def get_transforms():
    return Compose([
        LoadImage(image_only=True),
        EnsureChannelFirst(),
        Orientation(axcodes="RAS"),
        Spacing(pixdim=(1.5, 1.5, 1.5), mode="bilinear"),
        NormalizeIntensity(nonzero=True, channel_wise=True),
    ])

# --- 3. INFERENCE ---
def run_inference(model, image_path):
    transforms = get_transforms()
    image_tensor = transforms(image_path).unsqueeze(0).to(DEVICE)
    
    with torch.no_grad():
        output = sliding_window_inference(image_tensor, (96, 96, 96), 4, model)
        pred_label = torch.argmax(output, dim=1).detach().cpu().numpy()[0]
    
    # Post-processing
    cleanup = RemoveSmallObjects(min_size=10)
    final_mask = np.zeros_like(pred_label)
    
    for c in [1, 2]:
        class_mask = (pred_label == c).astype(np.float32)
        if np.sum(class_mask) > 0:
            # MONAI RemoveSmallObjects expects channel first
            cleaned = cleanup(torch.from_numpy(class_mask).unsqueeze(0)).numpy()[0]
            final_mask[cleaned > 0] = c
            
    return final_mask

# --- 4. MESH GENERATION ---
def generate_mesh(mask, class_id):
    binary_mask = (mask == class_id).astype(np.uint8)
    if np.sum(binary_mask) == 0:
        return None
    
    # Marching Cubes
    verts, faces, normals, values = measure.marching_cubes(binary_mask, level=0.5)
    
    # Convert to list for JSON serialization
    return {
        "vertices": verts.tolist(),
        "faces": faces.tolist(),
        "normals": normals.tolist()
    }

def get_brain_mesh(image_path):
    # Load image
    img_obj = nib.load(image_path)
    img = img_obj.get_fdata()
    
    # Simple brain extraction: thresholding + morphological closing
    # We use a percentile to get a better threshold than just the mean
    thresh = np.percentile(img[img > 0], 15) if np.any(img > 0) else 0
    brain_mask = (img > thresh).astype(np.uint8)
    
    # Downsample for performance (every 2nd voxel)
    # This significantly reduces vertex count for the frontend
    brain_mask = brain_mask[::2, ::2, ::2]
    
    if np.sum(brain_mask) == 0:
        return None
        
    # Marching Cubes
    verts, faces, normals, values = measure.marching_cubes(brain_mask, level=0.5)
    
    # Use trimesh for smoothing and simplification
    mesh = trimesh.Trimesh(vertices=verts, faces=faces)
    
    # Smooth the mesh
    mesh = trimesh.smoothing.filter_laplacian(mesh, iterations=10)
    
    # Simplify if too many vertices (target ~10k vertices for smooth web perf)
    if len(mesh.vertices) > 15000:
        mesh = mesh.simplify_quadratic_decimation(15000)
    
    return {
        "vertices": mesh.vertices.tolist(),
        "faces": mesh.faces.tolist(),
        "normals": mesh.vertex_normals.tolist()
    }
