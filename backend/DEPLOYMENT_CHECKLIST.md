# Backend Deployment Checklist

## ✅ Pre-Deployment

### Files Ready
- [x] `main.py` - FastAPI application
- [x] `utils.py` - Model utilities
- [x] `requirements.txt` - Python dependencies
- [x] `samples_config.json` - Sample configuration
- [x] `Procfile` - For Heroku/Railway
- [x] `runtime.txt` - Python version
- [x] `.gitignore` - Git ignore rules
- [x] `start.sh` / `start.bat` - Startup scripts
- [x] `README.md` - Documentation

### Required Assets
- [ ] `../Models/unetr50.pth` - UNETR-50 model (484MB)
- [ ] `../Models/model_epoch_55.pt` - UNet3D model (17MB)
- [ ] `../Data/` - Sample CT scans (optional)
- [ ] `../Data2/` - Sample FLAIR scans (optional)

**Note**: Model files are large and should NOT be committed to Git!

### Environment Setup
- [ ] Python 3.8+ installed
- [ ] CUDA GPU available (recommended) or CPU fallback
- [ ] 8GB+ RAM
- [ ] 2GB+ disk space for models

## 🚀 Deployment Options

### Option 1: Local Development

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Access: `http://localhost:8000`  
Docs: `http://localhost:8000/docs`

### Option 2: Railway

1. Create account at [railway.app](https://railway.app)
2. Create new project
3. Connect GitHub repository
4. Select `backend/` as root directory
5. Add environment variables:
   ```
   PYTHON_VERSION=3.11
   PORT=8000
   ```
6. Deploy automatically from Git

**Model Upload**: Upload to Railway volumes or use external storage (S3/GCS)

### Option 3: Render

1. Create account at [render.com](https://render.com)
2. New Web Service
3. Connect repository
4. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `backend`
   - **Environment**: Python 3.11

### Option 4: Heroku

```bash
cd backend
heroku create your-app-name
git add .
git commit -m "Deploy backend"
git push heroku main
```

### Option 5: Docker

```bash
cd backend
docker build -t neuroflash-backend .
docker run -p 8000:8000 neuroflash-backend
```

## 📋 Post-Deployment Verification

### Health Check
```bash
curl http://your-backend-url/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "segmentation_model_loaded": true,
  "gemma_model_loaded": false,
  "version": "2.0.0"
}
```

### Test Endpoints

1. **List samples**:
   ```bash
   curl http://your-backend-url/api/available-scans
   ```

2. **Process demo scan**:
   ```bash
   curl -X POST "http://your-backend-url/api/process-demo-scan?filename=(5).nii"
   ```

3. **Check status**:
   ```bash
   curl http://your-backend-url/api/status/{file_id}
   ```

## ⚙️ Configuration

### Environment Variables

Create `.env` file (don't commit!):
```
MODEL_PATH=./Models
DATA_PATH=./Data
PORT=8000
LOG_LEVEL=info
```

### Model Loading

The backend automatically loads models on startup from:
- `../Models/unetr50.pth`
- `../Models/model_epoch_55.pt`

If models are not in this location, update paths in `samples_config.json`.

### CORS Configuration

For production, update `main.py` CORS settings:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## 🔒 Security

### Before Production

- [ ] Change CORS from `allow_origins=["*"]` to specific domain
- [ ] Add authentication/API keys
- [ ] Enable rate limiting
- [ ] Add input validation
- [ ] Set up HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Add monitoring/logging

### Secrets Management

**Never commit**:
- Model files (.pth, .pt)
- Patient data (.nii files)
- API keys
- Environment variables with sensitive data

Use `.gitignore` to prevent accidental commits.

## 🐛 Troubleshooting

### Model Not Loading
- Check file paths in `samples_config.json`
- Verify model files exist
- Check GPU/CUDA availability
- Review server logs

### Memory Issues
- Reduce batch size
- Use CPU instead of GPU
- Increase server RAM
- Implement disk-based caching

### Slow Inference
- Use GPU if available
- Reduce input resolution
- Enable model quantization
- Use faster model (UNet3D vs UNETR-50)

## 📊 Monitoring

### Logs
```bash
# View logs
tail -f logs/backend.log

# Or on cloud platform
railway logs
heroku logs --tail
```

### Metrics to Monitor
- Response time
- Memory usage
- CPU/GPU utilization
- Request rate
- Error rate
- Model loading time

## 🔄 Updates

### Code Updates
```bash
git pull
pip install -r requirements.txt
# Restart server
```

### Model Updates
1. Upload new model file
2. Update path in `samples_config.json`
3. Restart server

## 📚 Resources

- FastAPI Docs: https://fastapi.tiangolo.com/
- MONAI Docs: https://docs.monai.io/
- PyTorch Docs: https://pytorch.org/docs/

---

**Status**: ✅ READY FOR DEPLOYMENT

**Last Updated**: 2026-01-02
