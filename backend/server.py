"""
NeuroFlash Minimal Backend - UNet3D Stroke Detection
Simple, clean FastAPI server for brain stroke analysis
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import uuid
import json
from pathlib import Path
from datetime import datetime
import uvicorn

# Import our UNet model and utilities
from unet_model import load_unet_model, run_inference, calculate_metrics
from ollama_ai import generate_ai_insight
from visualization import get_most_affected_slices, generate_3d_mesh, create_plotly_visualization
from slice_generator import generate_all_slice_images

app = FastAPI(title="NeuroFlash API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving HTML visualizations
app.mount("/results", StaticFiles(directory="results"), name="results")

# Directories
DATA_DIR = Path("../Data2")
UPLOAD_DIR = Path("uploads")
RESULTS_DIR = Path("results")
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Global state
model = None
processing_status = {}

# Load samples config
SAMPLES = [
    {
        "id": "stroke_5",
        "filename": "(5).nii",
        "name": "Stroke Case 5",
        "description": "Small ischemic stroke (0.17%)",
        "type": "stroke",
        "severity": "low"
    },
    {
        "id": "stroke_9",
        "filename": "(9).nii",
        "name": "Stroke Case 9",
        "description": "Small ischemic stroke (0.08%)",
        "type": "stroke",
        "severity": "low"
    },
    {
        "id": "stroke_3",
        "filename": "(3).nii",
        "name": "Stroke Case 3 (Negative)",
        "description": "Clean scan",
        "type": "negative",
        "severity": "none"
    }
]

@app.on_event("startup")
async def startup():
    """Load model on startup"""
    global model
    print("🚀 Starting NeuroFlash Backend...")
    model = load_unet_model()
    print("✅ Backend ready!")

@app.get("/api/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "version": "1.0.0"
    }

@app.get("/api/available-scans")
async def get_scans():
    """Get available demo scans"""
    scans = []
    for sample in SAMPLES:
        file_path = DATA_DIR / sample["filename"]
        scans.append({
            **sample,
            "exists": file_path.exists()
        })
    return {"scans": scans}

@app.post("/api/process-demo-scan")
async def process_demo(background_tasks: BackgroundTasks, filename: str):
    """Process a demo scan"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    file_path = DATA_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    file_id = str(uuid.uuid4())
    processing_status[file_id] = {
        "status": "processing",
        "progress": 0,
        "stage": "starting"
    }
    
    # Start background processing
    background_tasks.add_task(process_scan_task, file_id, str(file_path), filename)
    
    return {
        "file_id": file_id,
        "status": "processing",
        "message": f"Processing {filename}"
    }

@app.post("/api/process-scan")
async def process_upload(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Process uploaded scan"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if not file.filename.endswith(('.nii', '.nii.gz')):
        raise HTTPException(status_code=400, detail="Invalid file format")
    
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    
    # Save uploaded file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    processing_status[file_id] = {
        "status": "processing",
        "progress": 0,
        "stage": "starting"
    }
    
    # Start background processing
    background_tasks.add_task(process_scan_task, file_id, str(file_path), file.filename)
    
    return {
        "file_id": file_id,
        "status": "processing",
        "message": f"Processing {file.filename}"
    }

@app.get("/api/status/{file_id}")
async def get_status(file_id: str):
    """Get processing status"""
    if file_id not in processing_status:
        raise HTTPException(status_code=404, detail="File ID not found")
    
    status_info = processing_status[file_id]
    
    # If completed, return full results
    if status_info["status"] == "completed":
        result_path = RESULTS_DIR / f"{file_id}.json"
        if result_path.exists():
            with open(result_path, 'r') as f:
                return JSONResponse(content=json.load(f))
    
    # If error
    if status_info["status"] == "error":
        return JSONResponse(content={
            "status": "error",
            "error": status_info.get("error", "Unknown error"),
            "progress": 0
        })
    
    # Still processing
    return JSONResponse(content=status_info)

async def process_scan_task(file_id: str, scan_path: str, filename: str):
    """Background task to process scan"""
    try:
        # Update status
        processing_status[file_id] = {
            "status": "processing",
            "progress": 20,
            "stage": "running_inference"
        }
        
        # Run inference
        print(f"🔬 Processing {filename}...")
        pred_mask, scan_shape = run_inference(model, scan_path)
        
        processing_status[file_id]["progress"] = 60
        processing_status[file_id]["stage"] = "calculating_metrics"
        
        # Calculate metrics
        metrics = calculate_metrics(pred_mask)
        
        processing_status[file_id]["progress"] = 80
        processing_status[file_id]["stage"] = "generating_insights"
        
        # Generate AI insights
        ai_explanation = await generate_ai_insight(metrics)
        
        processing_status[file_id]["progress"] = 90
        processing_status[file_id]["stage"] = "generating_visualizations"
        
        # Get most affected slices
        most_affected_slices = get_most_affected_slices(pred_mask, scan_path)
        
        # Generate 3D mesh
        stroke_mesh = generate_3d_mesh(pred_mask, scan_path)
        
        # Generate 3D HTML visualization
        viz_html = create_plotly_visualization(pred_mask, scan_path)
        
        # Save visualization HTML to file for iframe access
        viz_url = None
        if viz_html:
            viz_filename = f"{file_id}_3d.html"
            viz_path = RESULTS_DIR / viz_filename
            with open(viz_path, 'w', encoding='utf-8') as f:
                f.write(viz_html)
            viz_url = f"/results/{viz_filename}"
        
        # Generate slice images for top slices
        slice_nums = [s["slice_num"] for s in most_affected_slices[:6]]
        slice_images = generate_all_slice_images(pred_mask, scan_path, slice_nums, axis='axial')
        
        # Add slice image data to most_affected_slices
        for slice_info in most_affected_slices:
            slice_num = slice_info["slice_num"]
            if slice_num in slice_images:
                slice_info["image_data"] = slice_images[slice_num]
        
        # Prepare final result
        result = {
            "file_id": file_id,
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "analysis": {
                "metrics": metrics,
                "ai_explanation": ai_explanation,
                "most_affected_slices": most_affected_slices
            },
            "stroke_mesh": stroke_mesh,
            "visualization_url": viz_url
        }
        
        # Save result
        result_path = RESULTS_DIR / f"{file_id}.json"
        with open(result_path, 'w') as f:
            json.dump(result, f)
        
        processing_status[file_id] = {
            "status": "completed",
            "progress": 100,
            "stage": "completed",
            "result_path": str(result_path)
        }
        
        print(f"✅ Completed processing {filename}")
        
    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")
        import traceback
        traceback.print_exc()
        processing_status[file_id] = {
            "status": "error",
            "progress": 0,
            "stage": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
