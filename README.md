# NeuroFlash - Complete Setup Guide

AI-powered 3D brain stroke detection with React frontend and FastAPI backend.

## Quick Start

### Prerequisites
- **Python 3.8+** - [Download](https://python.org)
- **Node.js 16+** - [Download](https://nodejs.org)
- **Git** - [Download](https://git-scm.com)

### One-Command Start

```bash
run.bat
```

This will:
1. Check Python and Node.js
2. Install all dependencies
3. Start backend on http://localhost:8000
4. Start frontend on http://localhost:3000
5. Open both in your browser

## Manual Setup

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Backend runs on: **http://localhost:8000**  
API docs: **http://localhost:8000/docs**

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

Frontend runs on: **http://localhost:3000**

## Project Structure

```
neuroflash/
├── start.bat              # Master startup script
├── backend/               # FastAPI backend
│   ├── main.py           # API server
│   ├── utils.py          # Model utilities
│   ├── requirements.txt  # Python deps
│   └── README.md
├── frontend/              # React frontend
│   ├── src/              # React source
│   ├── package.json      # Node deps
│   └── README.md
├── pages/                 # Static demo (deployed)
├── Models/                # AI model weights
└── Data2/                 # Sample scans
```

## Configuration

### Backend Port
Default: **8000**  
Change in: `backend/main.py` (line 523)

### Frontend API URL
Default: **http://localhost:8000/api**  
Change in: `frontend/src/App.tsx` (line 8)

### Models
Place in `Models/` directory:
- `unetr50.pth` (484MB) - Hemorrhage detection
- `model_epoch_55.pt` (17MB) - Stroke detection

## Features

- 📤 File upload for brain scans (.nii, .nii.gz)
- 🧪 Demo samples with pre-loaded cases
- 🧠 Real-time AI inference
- 📊 3D brain visualization
- 🎯 Slice-by-slice analysis
- 📈 Clinical metrics
- 🤖 AI-generated explanations

## Development

### Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm start
```

### Build for Production

**Backend**:
```bash
cd backend
```

**Frontend**:
```bash
cd frontend
npm run build
```

## API Endpoints

### Core
- `POST /api/process-scan` - Upload and process
- `GET /api/status/{file_id}` - Check status
- `GET /api/available-scans` - List demo samples

### Visualization
- `GET /api/viz/{file_id}` - 3D HTML
- `GET /api/mesh-data/{file_id}` - Plotly mesh

### Health
- `GET /api/health` - Backend status

## Troubleshooting

### Backend won't start
- Check Python version: `python --version`
- Install dependencies: `pip install -r backend/requirements.txt`
- Check port 8000 is free

### Frontend won't start
- Check Node.js version: `node --version`
- Install dependencies: `npm install` in frontend/
- Check port 3000 is free

### CORS errors
- Backend must be running on port 8000
- Frontend configured for http://localhost:8000/api
- Check `main.py` CORS settings

### Model errors
- Verify model files in `Models/` directory
- Check file paths in `backend/samples_config.json`
- Review backend logs

## Production Deployment

See `PRODUCTION_DEPLOYMENT.md` for:
- Railway deployment
- Render deployment
- Docker containerization
- Environment configuration

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend | FastAPI | Latest |
| Frontend | React 18 | 18.x |
| AI | PyTorch + MONAI | 2.1+ |
| 3D Viz | Plotly.js | Latest |
| Database | None (stateless) | - |

## Support

- **Issues**: Check logs in terminal windows
- **API Docs**: http://localhost:8000/docs (when backend running)
- **Model Info**: See `backend/README.md`
