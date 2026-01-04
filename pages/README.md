# NeuroFlash Demo - GitHub Pages

Static demo of 3D brain stroke visualization.

## Files

- `index.html` - Main demo page
- `stroke_case_*_full.html` - Comprehensive analysis pages (3 cases)
- `stroke_case_*.html` - 3D visualizations only
- `stroke_case_*_slices.png` - 2D slice montages

## Local Testing

```bash
python -m http.server 8080
```

Open: http://localhost:8080

## GitHub Pages Deployment

1. Push this directory to GitHub
2. Go to repository Settings → Pages
3. Select branch and `/pages` folder
4. Access at: https://github.com/akshit22sept/NeuroFlashDep

## Cases Included

| Case | Volume | % Brain | Type |
|------|--------|---------|------|
| Case 5 | 15,383 voxels | 0.17% | Small stroke |
| Case 9 | 7,191 voxels | 0.08% | Small stroke |
| Case 3 | 0 voxels | 0.00% | Negative |

## Features

- Interactive 3D brain visualization
- Most affected slice montages
- Clinical metrics and severity scoring
- Fully static - no backend required

## Size

Total: ~21 MB (3D visualizations are large HTML files with embedded data)
