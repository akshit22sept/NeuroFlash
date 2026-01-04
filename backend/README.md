# NeuroFlash Backend

FastAPI backend for brain stroke detection and visualization.

## Features

- Brain scan processing (NIfTI format)
- UNet3D/UNETR model inference
- 3D mesh generation
- Slice analysis
- Real-time processing status

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

Server runs on: http://localhost:8000

API docs: http://localhost:8000/docs

## API Endpoints

### Core
- `POST /api/process-scan` - Upload and process scan
- `GET /api/status/{file_id}` - Check processing status
- `POST /api/process-demo-scan?filename=X` - Process demo sample

### Data
- `GET /api/available-scans` - List demo samples
- `GET /api/slice/{file_id}/{axis}/{slice_num}` - Get slice image
- `GET /api/viz/{file_id}` - Get 3D visualization HTML
- `GET /api/mesh-data/{file_id}` - Get Plotly mesh data

### Utility
- `GET /api/health` - Health check
- `DELETE /api/cleanup/{file_id}` - Clean up results

## Configuration

Edit `samples_config.json` to add demo samples:

```json
{
  "data_directory": "../Data",
  "samples": [
    {
      "id": "sample_1",
      "filename": "scan.nii",
      "name": "Demo Case",
      "type": "stroke",
      "enabled": true
    }
  ]
}
```

## Models

Place model files in `../Models/`:
- `unetr50.pth` - UNETR-50 model (484M params)
- `model_epoch_55.pt` - UNet3D model (1.4M params)

## Dependencies

- FastAPI - Web framework
- PyTorch - Model inference
- MONAI - Medical imaging tools
- nibabel - NIfTI file handling
- NumPy, SciPy - Data processing
- scikit-image - Mesh generation

## Development

```bash
uvicorn main:app --reload --port 8000
```

## Production

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Environment

- Python 3.8+
- CUDA GPU recommended (CPU fallback available)
- 8GB+ RAM

## File Structure

```
backend/
├── main.py              # FastAPI application
├── utils.py             # Model and processing utilities
├── mesh_utils.py        # 3D mesh generation
├── visualization_generator.py  # HTML viz generation
├── samples_config.json  # Demo samples configuration
├── requirements.txt     # Python dependencies
├── temp_uploads/        # Temporary upload storage
└── results/             # Processing results
```
