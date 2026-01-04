from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import uuid
import numpy as np
from .utils import load_model, run_inference, generate_mesh, get_brain_mesh

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance
model = load_model()

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/process-scan")
async def process_scan(file: UploadFile = File(...)):
    if not file.filename.endswith(('.nii', '.nii.gz')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a .nii or .nii.gz file.")
    
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 1. Run inference
        mask = run_inference(model, file_path)
        
        # 2. Generate meshes
        stroke_mesh = generate_mesh(mask, 1)
        hemorrhage_mesh = generate_mesh(mask, 2)
        
        # 3. Generate brain mesh (simplified)
        brain_mesh = get_brain_mesh(file_path)
        
        # 4. Calculate volumes (Voxel count * Voxel size)
        # Assuming 1.5mm^3 voxels from preprocessing
        voxel_vol = 1.5 * 1.5 * 1.5
        stroke_vol = float(np.sum(mask == 1) * voxel_vol)
        hemorrhage_vol = float(np.sum(mask == 2) * voxel_vol)
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "analysis": {
                "stroke_volume_mm3": stroke_vol,
                "hemorrhage_volume_mm3": hemorrhage_vol,
                "total_lesion_volume_mm3": stroke_vol + hemorrhage_vol
            },
            "meshes": {
                "brain": brain_mesh,
                "stroke": stroke_mesh,
                "hemorrhage": hemorrhage_mesh
            }
        }
        
    except Exception as e:
        print(f"Error processing scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": model is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
