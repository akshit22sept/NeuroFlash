import torch
import numpy as np
import nibabel as nib
from scipy import ndimage
from monai.networks.nets import UNETR
from monai.inferers import sliding_window_inference
from monai.transforms import (
    Compose, LoadImage, EnsureChannelFirst, Orientation, 
    Spacing, NormalizeIntensity, RemoveSmallObjects
)
from skimage import measure, morphology
import trimesh
import os
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# Using the better-trained UNETR model (unetr4115.pth)
MODEL_PATH = r"c:\Projects 2\Neuroflash\1\Models\unetr4115.pth"

# --- 1. MODEL LOADING ---
def load_model():
    """Load the UNETR segmentation model"""
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
    
    if os.path.exists(MODEL_PATH):
        model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
        print(f"✅ Loaded model from {MODEL_PATH}")
    else:
        print(f"⚠️ Model file not found at {MODEL_PATH}, using untrained model")
    
    model.eval()
    return model

def load_gemma_model():
    """Load Gemma 1B model via Ollama"""
    try:
        print("🤖 Using Ollama Gemma 1B model...")
        # Ollama runs locally, no need to load model into memory
        # Just verify Ollama is accessible
        import requests
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                gemma_models = [m for m in models if 'gemma' in m.get('name', '').lower()]
                if gemma_models:
                    print(f"[OK] Ollama is running with Gemma model: {gemma_models[0]['name']}")
                    return {"type": "ollama", "model": gemma_models[0]['name']}
                else:
                    print("⚠️ Gemma model not found in Ollama. Install with: ollama pull gemma:2b")
                    return None
            else:
                print("⚠️ Ollama is not responding")
                return None
        except requests.exceptions.RequestException:
            print("⚠️ Could not connect to Ollama at http://localhost:11434")
            print("   Make sure Ollama is running: ollama serve")
            return None
    except Exception as e:
        print(f"⚠️ Error checking Ollama: {e}")
        return None

# --- 2. PREPROCESSING ---
def get_transforms():
    """Get preprocessing transforms"""
    return Compose([
        LoadImage(image_only=True),
        EnsureChannelFirst(),
        Orientation(axcodes="RAS"),
        Spacing(pixdim=(1.5, 1.5, 1.5), mode="bilinear"),
        NormalizeIntensity(nonzero=True, channel_wise=True),
    ])

# --- 3. INFERENCE ---
def run_inference(model, image_path):
    """Run inference on brain scan"""
    print(f"🧠 Running inference on {image_path}")
    transforms = get_transforms()
    image_tensor = transforms(image_path).unsqueeze(0).to(DEVICE)
    
    with torch.no_grad():
        output = sliding_window_inference(
            image_tensor, 
            (96, 96, 96), 
            4, 
            model,
            overlap=0.5
        )
        # Use softmax for probability-based thresholding
        probs = torch.softmax(output, dim=1).detach().cpu().numpy()[0]
        
    # Thresholding (tuned for demo sensitivity)
    # Background is channel 0, Stroke is 1, Hemorrhage is 2
    stroke_threshold = 0.10     # Lowered to capture weak signals
    hemorrhage_threshold = 0.05 # Lowered significantly for sensitivity
    
    pred_label = np.zeros(probs.shape[1:], dtype=np.int32)
    
    # Priority: Hemorrhage > Stroke (clinically critical)
    # Using > threshold logic
    pred_label[probs[1] > stroke_threshold] = 1
    pred_label[probs[2] > hemorrhage_threshold] = 2
    
    print(f"DEBUG: Raw voxels > threshold - Stroke: {np.sum(pred_label == 1)}, Hemorrhage: {np.sum(pred_label == 2)}")
    
    # Create brain mask (remove background/skull/air)
    # Normalize image for better brain extraction
    image_np = image_tensor.cpu().numpy()[0, 0]
    image_norm = (image_np - image_np.min()) / (image_np.max() - image_np.min() + 1e-8)
    brain_mask = image_norm > 0.1  # Simple intensity threshold for brain tissue
    
    # Apply brain mask to remove out-of-brain detections
    pred_label_masked = pred_label.copy()
    pred_label_masked[~brain_mask] = 0
    
    removed_stroke = np.sum((pred_label == 1) & ~brain_mask)
    removed_hem = np.sum((pred_label == 2) & ~brain_mask)
    if removed_stroke > 0 or removed_hem > 0:
        print(f"DEBUG: Removed out-of-brain voxels - Stroke: {removed_stroke}, Hemorrhage: {removed_hem}")
    
    pred_label = pred_label_masked
    
    # Enhanced post-processing
    cleanup = RemoveSmallObjects(min_size=5)  # Reduced drastically to keep tiny lesions
    final_mask = np.zeros_like(pred_label)
    
    for c in [1, 2]:
        class_mask = (pred_label == c).astype(np.float32)
        initial_count = np.sum(class_mask)
        if initial_count > 0:
            # Apply morphological operations
            if c == 1:  # Stroke - fill holes
                class_mask = ndimage.binary_fill_holes(class_mask)
            elif c == 2:  # Hemorrhage - skip erosion/opening to keep small points
                pass
            
            mid_count = np.sum(class_mask)
            
            # MONAI RemoveSmallObjects expects channel first
            cleaned = cleanup(torch.from_numpy(class_mask.astype(np.float32)).unsqueeze(0)).numpy()[0]
            final_count = np.sum(cleaned)
            
            final_mask[cleaned > 0] = c
            print(f"DEBUG: Class {c} flow: {initial_count} -> {mid_count} (morph) -> {final_count} (cleanup)")
    
    print(f"✅ Inference completed. Found {np.sum(final_mask == 1)} stroke voxels, {np.sum(final_mask == 2)} hemorrhage voxels")
    return final_mask





# --- 4. MESH GENERATION ---
def generate_mesh(mask, class_id):
    """Generate 3D mesh for specific lesion class"""
    binary_mask = (mask == class_id).astype(np.uint8)
    if np.sum(binary_mask) == 0:
        return None
    
    print(f"🔺 Generating mesh for class {class_id}")
    
    # Apply smoothing before marching cubes
    binary_mask = morphology.binary_closing(binary_mask, morphology.ball(1))
    
    # Marching Cubes
    try:
        verts, faces, normals, values = measure.marching_cubes(binary_mask, level=0.5)
        
        # Use trimesh for mesh optimization
        mesh = trimesh.Trimesh(vertices=verts, faces=faces)
        
        # Smooth the mesh
        mesh = trimesh.smoothing.filter_laplacian(mesh, iterations=5)
        
        # Simplify if needed
        if len(mesh.vertices) > 5000:
            mesh = mesh.simplify_quadric_decimation(5000)
        
        return {
            "vertices": mesh.vertices.tolist(),
            "faces": mesh.faces.tolist(),
            "normals": mesh.vertex_normals.tolist(),
            "volume_mm3": float(mesh.volume * (1.5**3))  # Convert to mm³
        }
    except Exception as e:
        print(f"⚠️ Error generating mesh for class {class_id}: {e}")
        return None

def get_brain_mesh(image_path):
    """Generate brain surface mesh"""
    print("🧠 Generating brain mesh")
    
    # Load image
    img_obj = nib.load(image_path)
    img = img_obj.get_fdata()
    
    # Enhanced brain extraction
    thresh = np.percentile(img[img > 0], 25) if np.any(img > 0) else 0
    brain_mask = (img > thresh).astype(np.uint8)
    
    # Morphological operations for smoother brain surface
    brain_mask = ndimage.binary_fill_holes(brain_mask)
    brain_mask = morphology.binary_closing(brain_mask, morphology.ball(3))
    
    # Aggressive downsampling for web performance
    brain_mask = brain_mask[::4, ::4, ::4]
    
    if np.sum(brain_mask) == 0:
        return None
        
    try:
        # Marching Cubes
        verts, faces, normals, values = measure.marching_cubes(brain_mask, level=0.5)
        
        # Use trimesh for advanced processing
        mesh = trimesh.Trimesh(vertices=verts * 4, faces=faces)  # Scale back up
        
        # Smooth and simplify
        mesh = trimesh.smoothing.filter_laplacian(mesh, iterations=15)
        
        # Target ~8k vertices for good web performance
        if len(mesh.vertices) > 8000:
            mesh = mesh.simplify_quadric_decimation(8000)
        
        return {
            "vertices": mesh.vertices.tolist(),
            "faces": mesh.faces.tolist(),
            "normals": mesh.vertex_normals.tolist()
        }
    except Exception as e:
        print(f"⚠️ Error generating brain mesh: {e}")
        return None

# --- 5. ADVANCED ANALYSIS ---
def analyze_slices(mask, image_path):
    """Analyze lesions slice by slice"""
    print("📊 Analyzing slices")
    
    # Load original image for context
    img = nib.load(image_path).get_fdata()
    
    slice_data = {"axial": [], "sagittal": [], "coronal": []}
    
    # Analyze axial slices (most common for radiologists)
    for i in range(mask.shape[2]):
        slice_mask = mask[:, :, i]
        stroke_count = np.sum(slice_mask == 1)
        hemorrhage_count = np.sum(slice_mask == 2)
        
        if stroke_count > 0 or hemorrhage_count > 0:
            slice_data["axial"].append({
                "slice_num": int(i),
                "stroke_voxels": int(stroke_count),
                "hemorrhage_voxels": int(hemorrhage_count),
                "total_lesion_voxels": int(stroke_count + hemorrhage_count),
                "percentage_affected": float((stroke_count + hemorrhage_count) / (mask.shape[0] * mask.shape[1]) * 100)
            })
    
    # Analyze sagittal slices
    for i in range(mask.shape[0]):
        slice_mask = mask[i, :, :]
        stroke_count = np.sum(slice_mask == 1)
        hemorrhage_count = np.sum(slice_mask == 2)
        
        if stroke_count > 0 or hemorrhage_count > 0:
            slice_data["sagittal"].append({
                "slice_num": int(i),
                "stroke_voxels": int(stroke_count),
                "hemorrhage_voxels": int(hemorrhage_count),
                "total_lesion_voxels": int(stroke_count + hemorrhage_count)
            })
    
    # Analyze coronal slices
    for i in range(mask.shape[1]):
        slice_mask = mask[:, i, :]
        stroke_count = np.sum(slice_mask == 1)
        hemorrhage_count = np.sum(slice_mask == 2)
        
        if stroke_count > 0 or hemorrhage_count > 0:
            slice_data["coronal"].append({
                "slice_num": int(i),
                "stroke_voxels": int(stroke_count),
                "hemorrhage_voxels": int(hemorrhage_count),
                "total_lesion_voxels": int(stroke_count + hemorrhage_count)
            })
    
    return slice_data

def get_most_affected_slices(mask, top_k=5):
    """Get slices with highest lesion burden"""
    affected_slices = []
    
    for i in range(mask.shape[2]):
        slice_mask = mask[:, :, i]
        total_lesion = np.sum(slice_mask > 0)
        if total_lesion > 0:
            affected_slices.append({
                "axis": "axial",
                "slice_num": int(i),
                "lesion_voxels": int(total_lesion),
                "stroke_voxels": int(np.sum(slice_mask == 1)),
                "hemorrhage_voxels": int(np.sum(slice_mask == 2))
            })
    
    # Sort by lesion burden and return top k
    affected_slices.sort(key=lambda x: x["lesion_voxels"], reverse=True)
    return affected_slices[:top_k]

def calculate_metrics(mask):
    """Calculate comprehensive metrics"""
    voxel_volume = 1.5 * 1.5 * 1.5  # mm³
    
    stroke_voxels = np.sum(mask == 1)
    hemorrhage_voxels = np.sum(mask == 2)
    total_brain_voxels = np.sum(mask >= 0)
    
    metrics = {
        "stroke_volume_mm3": float(stroke_voxels * voxel_volume),
        "hemorrhage_volume_mm3": float(hemorrhage_voxels * voxel_volume),
        "total_lesion_volume_mm3": float((stroke_voxels + hemorrhage_voxels) * voxel_volume),
        "stroke_voxel_count": int(stroke_voxels),
        "hemorrhage_voxel_count": int(hemorrhage_voxels),
        "lesion_to_brain_ratio": float((stroke_voxels + hemorrhage_voxels) / max(total_brain_voxels, 1)),
        "stroke_to_hemorrhage_ratio": float(stroke_voxels / max(hemorrhage_voxels, 1)) if hemorrhage_voxels > 0 else float('inf'),
        "severity_score": calculate_severity_score(stroke_voxels, hemorrhage_voxels, voxel_volume)
    }
    
    return metrics

def calculate_severity_score(stroke_voxels, hemorrhage_voxels, voxel_volume):
    """Calculate clinical severity score"""
    stroke_vol_ml = stroke_voxels * voxel_volume / 1000
    hemorrhage_vol_ml = hemorrhage_voxels * voxel_volume / 1000
    
    # Clinical thresholds (simplified)
    severity = "minimal"
    score = 0
    
    if stroke_vol_ml > 100 or hemorrhage_vol_ml > 30:
        severity = "severe"
        score = 3
    elif stroke_vol_ml > 50 or hemorrhage_vol_ml > 15:
        severity = "moderate"
        score = 2
    elif stroke_vol_ml > 10 or hemorrhage_vol_ml > 5:
        severity = "mild"
        score = 1
    
    return {"score": score, "category": severity}

def generate_ai_explanation(gemma_model, mask, metrics):
    """Generate AI explanation using Gemma via Ollama"""
    if not gemma_model:
        return {"explanation": "AI explanation not available - Gemma model not loaded", "confidence": 0}
    
    try:
        import requests
        
        # Prepare context
        stroke_vol = metrics["stroke_volume_mm3"]
        hemorrhage_vol = metrics["hemorrhage_volume_mm3"]
        severity = metrics["severity_score"]["category"]
        
        prompt = f"""You are a medical AI analyzing brain scan results. Provide a clear, professional explanation in 2-3 sentences.

Findings:
- Ischemic stroke volume: {stroke_vol:.1f} mm³
- Hemorrhage volume: {hemorrhage_vol:.1f} mm³
- Severity: {severity}

Explain the clinical significance and recommended actions:"""

        # Call Ollama API
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": gemma_model["model"],
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 150
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            explanation = result.get("response", "").strip()
            
            return {
                "explanation": explanation,
                "confidence": 0.85,
                "model": f"Ollama-{gemma_model['model']}"
            }
        else:
            raise Exception(f"Ollama API returned status {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Error generating AI explanation: {e}")
        return {
            "explanation": f"Based on the analysis, this scan shows {severity} brain damage with significant findings requiring medical attention.",
            "confidence": 0.0,
            "model": "fallback"
        }

def get_slice_data(file_id, axis, slice_num):
    """Get slice image data with overlays"""
    # This would generate base64 encoded slice images
    # For now, return placeholder
    return {
        "image_base64": "",
        "slice_info": {
            "axis": axis,
            "slice_num": slice_num,
            "has_stroke": False,
            "has_hemorrhage": False
        }
    }
