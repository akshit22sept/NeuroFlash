# NeuroFlash Frontend

React-based frontend for brain stroke visualization.

## Features

- File upload interface
- Demo sample selection
- Real-time processing status
- Interactive 3D brain visualization
- 2D slice gallery
- Clinical metrics display

## Setup

```bash
npm install
```

## Run Development

```bash
npm start
```

App runs on: http://localhost:3000

## Build Production

```bash
npm run build
```

Output in: `build/`

## Configuration

Backend API URL: `http://localhost:8002/api`

Update in `src/App.tsx` line 8:
```typescript
const API_BASE = 'http://localhost:8002/api';
```

## Components

- `App.tsx` - Main application
- `BrainVisualization.tsx` - 3D brain viewer
- `SliceGallery.tsx` - 2D slice montage

## Technology

- React 18
- TypeScript
- Plotly.js - 3D visualization
- Axios - HTTP client

## Development

```bash
npm start        # Start dev server
npm test         # Run tests
npm run build    # Production build
npm run eject    # Eject from CRA (one-way!)
```

## Deployment

### Static Hosting (Vercel/Netlify)
```bash
npm run build
# Deploy build/ directory
```

### Docker
```bash
docker build -t neuroflash-frontend .
docker run -p 3000:3000 neuroflash-frontend
```

## Environment Variables

Create `.env`:
```
REACT_APP_API_URL=http://localhost:8002/api
```

## File Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── App.tsx          # Main app
│   ├── components/      # React components
│   ├── index.tsx        # Entry point
│   └── index.css        # Global styles
├── package.json         # Dependencies
└── tsconfig.json        # TypeScript config
```
