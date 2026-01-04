from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import shutil
import uuid
import numpy as np
import asyncio
from typing import Dict, Optional, List
import json
from pathlib import Path
from datetime import datetime

def sanitize_for_json(obj):
    """Recursively convert numpy types and problematic floats to JSON-safe types."""
    import math
    # numpy is available in this module
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    if isinstance(obj, tuple):
        return [sanitize_for_json(v) for v in obj]
    try:
        import numpy as _np
        if isinstance(obj, _np.generic):
            py = obj.item()
            if isinstance(py, float):
                if math.isinf(py) or math.isnan(py):
                    return None
            return py
        if isinstance(obj, _np.ndarray):
            return sanitize_for_json(obj.tolist())
    except Exception:
        pass
    if isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return None
        return obj
    return obj
from utils import (
    load_model, load_gemma_model, run_inference, generate_mesh, get_brain_mesh,
    analyze_slices, generate_ai_explanation, get_slice_data, calculate_metrics,
    get_most_affected_slices
)

# Create API router
from fastapi import APIRouter
api_router = APIRouter()

app = FastAPI(title="NeuroFlash API", description="Advanced Brain Damage Segmentation API", version="2.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load samples configuration
def load_samples_config():
    """Load samples configuration from JSON file"""
    config_path = Path(__file__).parent / "samples_config.json"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {"data_directory": "./Data", "samples": []}

SAMPLES_CONFIG = load_samples_config()
DATA_DIR = os.path.join(os.path.dirname(__file__), SAMPLES_CONFIG.get("data_directory", "./Data"))

# Global model instances
segmentation_model = None
gemma_model = None
processing_status = {}

# Storage
UPLOAD_DIR = "temp_uploads"
RESULTS_DIR = "results"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    global segmentation_model, gemma_model
    print("[STARTUP] Scheduling model load in background...")

    async def _load_models_background():
        loop = asyncio.get_running_loop()
        try:
            # Load segmentation model in a thread to avoid blocking the event loop
            segmentation = await loop.run_in_executor(None, load_model)
            print("[OK] UNETR segmentation model loaded successfully")
            # Try loading gemma but don't fail startup if it can't load
            gemma = None
            try:
                gemma = await loop.run_in_executor(None, load_gemma_model)
                print("[OK] Gemma 1B explanation model loaded successfully")
            except Exception as gm_err:
                print(f"[WARNING] Could not load Gemma model: {gm_err}")
                import traceback
                traceback.print_exc()

            # Publish loaded models to globals
            globals()['segmentation_model'] = segmentation
            globals()['gemma_model'] = gemma
        except Exception as e:
            print(f"[ERROR] Error loading models in background: {e}")
            import traceback
            traceback.print_exc()

    # Start background task and do not block server startup
    asyncio.create_task(_load_models_background())

@api_router.post("/process-scan")
async def process_scan(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Process brain scan with comprehensive analysis"""
    if not file.filename.endswith(('.nii', '.nii.gz')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a .nii or .nii.gz file.")
    
    if segmentation_model is None:
        raise HTTPException(status_code=503, detail="Segmentation model not loaded")
    
    file_id = str(uuid.uuid4())
    processing_status[file_id] = {"status": "processing", "progress": 0, "stage": "uploading"}
    
    # Start background processing
    background_tasks.add_task(process_scan_background, file, file_id)
    
    return {"file_id": file_id, "status": "processing", "message": "Scan processing started"}

async def process_scan_background(file: UploadFile, file_id: str):
    """Background processing of brain scan"""
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    result_path = os.path.join(RESULTS_DIR, f"{file_id}.json")
    
    try:
        # Stage 1: File upload
        processing_status[file_id] = {"status": "processing", "progress": 10, "stage": "uploading"}
        
        # Read file content immediately before it gets closed
        file_content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Stage 2: Inference
        processing_status[file_id] = {"status": "processing", "progress": 30, "stage": "running_inference"}
        mask = run_inference(segmentation_model, file_path)
        
        # Save mask immediately for later mesh generation
        mask_path = os.path.join(RESULTS_DIR, f"{file_id}_mask.npy")
        np.save(mask_path, mask)
        
        # Ensure file is completely written and flushed
        import time
        time.sleep(0.1)  # Small delay to ensure file writes complete
        
        # Generate 3D HTML visualization (optional - don't let this block processing)
        viz_html_path = None
        try:
            processing_status[file_id] = {"status": "processing", "progress": 40, "stage": "generating_visualization"}
            from visualization_generator import generate_visualization_for_scan
            viz_html_path = generate_visualization_for_scan(file_path, mask_path, RESULTS_DIR, file_id)
            print(f"✓ Generated visualization: {viz_html_path}")
        except Exception as viz_error:
            print(f"⚠ Visualization generation failed (non-critical): {viz_error}")
            import traceback
            traceback.print_exc()
            # Continue processing even if visualization fails
        
        # Stage 3: Mesh generation
        processing_status[file_id] = {"status": "processing", "progress": 50, "stage": "generating_meshes"}
        stroke_mesh = generate_mesh(mask, 1)
        hemorrhage_mesh = generate_mesh(mask, 2)
        brain_mesh = get_brain_mesh(file_path)
        
        # Stage 4: Slice analysis
        processing_status[file_id] = {"status": "processing", "progress": 70, "stage": "analyzing_slices"}
        slice_analysis = analyze_slices(mask, file_path)
        most_affected = get_most_affected_slices(mask, top_k=5)
        
        # Stage 5: Metrics calculation
        processing_status[file_id] = {"status": "processing", "progress": 80, "stage": "calculating_metrics"}
        metrics = calculate_metrics(mask)
        
        # Stage 6: AI explanation
        processing_status[file_id] = {"status": "processing", "progress": 90, "stage": "generating_explanation"}
        ai_explanation = None
        if gemma_model:
            ai_explanation = generate_ai_explanation(gemma_model, mask, metrics)
        
        # Prepare final result
        result = {
            "file_id": file_id,
            "filename": file.filename,
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,  # Store for mesh generation
            "mask_path": mask_path,  # Store for mesh generation
            "visualization_html": viz_html_path,  # Store path to 3D HTML
            "analysis": {
                "metrics": metrics,
                "slice_analysis": slice_analysis,
                "most_affected_slices": most_affected,
                "ai_explanation": ai_explanation
            },
            "meshes": {
                "brain": brain_mesh,
                "stroke": stroke_mesh,
                "hemorrhage": hemorrhage_mesh
            }
        }
        
        # Save result (sanitize before writing)
        with open(result_path, 'w') as f:
            json.dump(sanitize_for_json(result), f)
        
        processing_status[file_id] = {
            "status": "completed", 
            "progress": 100, 
            "stage": "completed",
            "result_path": result_path
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Processing error for {file_id}: {error_msg}")
        import traceback
        traceback.print_exc()
        processing_status[file_id] = {
            "status": "error", 
            "progress": 0, 
            "stage": "error",
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }
    finally:
        # Clean up temp file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as cleanup_error:
                print(f"[WARNING] Failed to cleanup {file_path}: {cleanup_error}")

@api_router.get("/status/{file_id}")
async def get_processing_status(file_id: str):
    """Get processing status for a scan"""
    if file_id not in processing_status:
        raise HTTPException(status_code=404, detail="File ID not found")
    
    try:
        status_info = processing_status[file_id]
        
        # If error, return error info
        if status_info.get("status") == "error":
            return JSONResponse(content={
                "status": "error",
                "stage": "error",
                "progress": 0,
                "error": str(status_info.get("error", "Unknown error")),
                "timestamp": str(status_info.get("timestamp", ""))
            })
        
        # If completed, return the result
        if status_info.get("status") == "completed":
            result_path = status_info.get("result_path")
            if result_path and os.path.exists(result_path):
                with open(result_path, 'r') as f:
                    result = json.load(f)
                return JSONResponse(content=sanitize_for_json(result))
        
        # Still processing
        return JSONResponse(content={
            "status": "processing",
            "stage": str(status_info.get("stage", "processing")),
            "progress": int(status_info.get("progress", 0)),
            "timestamp": str(status_info.get("timestamp", ""))
        })
    except Exception as e:
        print(f"[ERROR] Error in get_processing_status: {e}")
        import traceback
        traceback.print_exc()
        print(f"Status info dict: {processing_status.get(file_id, {})}")
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")

@api_router.get("/slice/{file_id}/{axis}/{slice_num}")
async def get_slice_image(file_id: str, axis: str, slice_num: int):
    """Get specific slice image with overlays"""
    result_path = os.path.join(RESULTS_DIR, f"{file_id}.json")
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Scan results not found")
    
    # This would return base64 encoded slice image with lesion overlays
    slice_data = get_slice_data(file_id, axis, slice_num)
    return slice_data

@api_router.get("/available-scans")
async def list_available_scans():
    """List available demo scans from configuration"""
    available_scans = []
    
    for sample in SAMPLES_CONFIG.get("samples", []):
        if not sample.get("enabled", True):
            continue
            
        file_path = os.path.join(DATA_DIR, sample["filename"])
        
        # Check if file exists
        if os.path.exists(file_path):
            available_scans.append({
                "id": sample.get("id"),
                "filename": sample["filename"],
                "name": sample.get("name", sample["filename"]),
                "description": sample.get("description", ""),
                "type": sample.get("type", "unknown"),
                "severity": sample.get("severity", "unknown"),
                "exists": True
            })
        else:
            available_scans.append({
                "id": sample.get("id"),
                "filename": sample["filename"],
                "name": sample.get("name", sample["filename"]),
                "description": sample.get("description", ""),
                "type": sample.get("type", "unknown"),
                "severity": sample.get("severity", "unknown"),
                "exists": False
            })
    
    return {"scans": available_scans, "data_directory": DATA_DIR}

@api_router.post("/process-demo-scan")
async def process_demo_scan(background_tasks: BackgroundTasks, filename: str):
    """Process a demo scan from the Data directory"""
    file_path = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Demo scan '{filename}' not found in {DATA_DIR}")
    
    if segmentation_model is None:
        raise HTTPException(status_code=503, detail="Segmentation model not loaded")
    
    file_id = str(uuid.uuid4())
    processing_status[file_id] = {"status": "processing", "progress": 0, "stage": "starting"}
    
    # Create a mock file object for demo processing
    class DemoFile:
        def __init__(self, filename, filepath):
            self.filename = filename
            self.filepath = filepath
    
    demo_file = DemoFile(filename, file_path)
    background_tasks.add_task(process_demo_scan_background, demo_file, file_id)
    
    return {"file_id": file_id, "status": "processing", "message": f"Demo scan '{filename}' processing started"}

async def process_demo_scan_background(demo_file, file_id: str):
    """Background processing of demo scan"""
    result_path = os.path.join(RESULTS_DIR, f"{file_id}.json")
    
    try:
        # Stage 1: Start
        processing_status[file_id] = {"status": "processing", "progress": 20, "stage": "running_inference"}
        mask = run_inference(segmentation_model, demo_file.filepath)
        
        # Stage 2: Mesh generation
        processing_status[file_id] = {"status": "processing", "progress": 50, "stage": "generating_meshes"}
        stroke_mesh = generate_mesh(mask, 1)
        hemorrhage_mesh = generate_mesh(mask, 2)
        brain_mesh = get_brain_mesh(demo_file.filepath)
        
        # Stage 3: Analysis
        processing_status[file_id] = {"status": "processing", "progress": 70, "stage": "analyzing_slices"}
        slice_analysis = analyze_slices(mask, demo_file.filepath)
        most_affected = get_most_affected_slices(mask, top_k=5)
        metrics = calculate_metrics(mask)
        
        # Stage 4: AI explanation
        processing_status[file_id] = {"status": "processing", "progress": 90, "stage": "generating_explanation"}
        ai_explanation = None
        if gemma_model:
            ai_explanation = generate_ai_explanation(gemma_model, mask, metrics)
        
        # Final result
        result = {
            "file_id": file_id,
            "filename": demo_file.filename,
            "timestamp": datetime.now().isoformat(),
            "analysis": {
                "metrics": metrics,
                "slice_analysis": slice_analysis,
                "most_affected_slices": most_affected,
                "ai_explanation": ai_explanation
            },
            "meshes": {
                "brain": brain_mesh,
                "stroke": stroke_mesh,
                "hemorrhage": hemorrhage_mesh
            }
        }
        
        with open(result_path, 'w') as f:
            json.dump(result, f)
        
        processing_status[file_id] = {
            "status": "completed", 
            "progress": 100, 
            "stage": "completed",
            "result_path": result_path
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Demo processing error for {file_id}: {error_msg}")
        import traceback
        traceback.print_exc()
        processing_status[file_id] = {
            "status": "error", 
            "progress": 0, 
            "stage": "error",
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "segmentation_model_loaded": segmentation_model is not None,
        "gemma_model_loaded": gemma_model is not None,
        "version": "2.0.0"
    }

@api_router.delete("/cleanup/{file_id}")
async def cleanup_result(file_id: str):
    """Clean up processing results"""
    result_path = os.path.join(RESULTS_DIR, f"{file_id}.json")
    if os.path.exists(result_path):
        os.remove(result_path)
    
    if file_id in processing_status:
        del processing_status[file_id]
    
    return {"message": f"Cleaned up results for {file_id}"}

@api_router.get("/viz/{file_id}")
async def serve_visualization(file_id: str):
    """
    Serve the 3D HTML visualization file for a processed scan
    """
    from fastapi.responses import FileResponse
    
    html_path = os.path.join(RESULTS_DIR, f"{file_id}_3d.html")
    
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="Visualization not found")
    
    return FileResponse(html_path, media_type="text/html")

@api_router.get("/mesh-data/{file_id}")

async def get_mesh_data(file_id: str):
    """
    Generate Plotly-ready mesh data for 3D visualization
    Returns vertices and faces for brain, stroke, and hemorrhage surfaces
    """
    from mesh_utils import generate_mesh_data_for_plotly
    import nibabel as nib
    
    # Check if results exist
    result_path = os.path.join(RESULTS_DIR, f"{file_id}.json")
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Results not found for this file_id")
    
    # Load results to get file path and mask
    with open(result_path, 'r') as f:
        results = json.load(f)
    
    # Get original scan path
    file_path = results.get('file_path')
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Original scan file not found")
    
    # Load scan
    img = nib.load(file_path)
    volume = img.get_fdata()
    affine = img.affine
    
    # Load mask if it exists
    mask_path = results.get('mask_path')
    mask = None
    if mask_path and os.path.exists(mask_path):
        mask = np.load(mask_path)
    
    # Generate mesh data
    mesh_data = generate_mesh_data_for_plotly(volume, affine, mask)
    
    return JSONResponse(content=sanitize_for_json(mesh_data))

@api_router.get("/health")

async def health_check():
    """Health endpoint reporting model readiness"""
    return {
        "ready": segmentation_model is not None,
        "segmentation_loaded": segmentation_model is not None,
        "gemma_loaded": gemma_model is not None
    }

# Include API routes
app.include_router(api_router, prefix="/api")

# Mount static files for frontend
if os.path.exists("../frontend/build"):
    app.mount("/static", StaticFiles(directory="../frontend/build/static"), name="static")
    app.mount("/", StaticFiles(directory="../frontend/build", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
