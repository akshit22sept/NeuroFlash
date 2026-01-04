import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import axios from 'axios';

interface PlotlyBrainViewerProps {
    fileId: string;
}

export default function PlotlyBrainViewer({ fileId }: PlotlyBrainViewerProps) {
    const [meshData, setMeshData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchMeshData = async () => {
            try {
                setLoading(true);
                const response = await axios.get(`http://localhost:8002/api/mesh-data/${fileId}`);
                setMeshData(response.data);
                setLoading(false);
            } catch (err: any) {
                console.error('Failed to load mesh data:', err);
                setError(err.response?.data?.detail || 'Failed to load 3D visualization');
                setLoading(false);
            }
        };

        if (fileId) {
            fetchMeshData();
        }
    }, [fileId]);

    if (loading) {
        return (
            <div className="w-full h-full flex items-center justify-center bg-slate-900/50 rounded-lg">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-slate-400">Generating 3D visualization...</p>
                </div>
            </div>
        );
    }

    if (error || !meshData) {
        return (
            <div className="w-full h-full flex items-center justify-center bg-slate-900/50 rounded-lg">
                <p className="text-red-400">⚠️ {error || '3D visualization unavailable'}</p>
            </div>
        );
    }

    const traces: any[] = [];

    // Add brain surface (semi-transparent)
    if (meshData.brain_mesh) {
        const brain = meshData.brain_mesh;
        traces.push({
            type: 'mesh3d',
            x: brain.vertices.map((v: number[]) => v[0]),
            y: brain.vertices.map((v: number[]) => v[1]),
            z: brain.vertices.map((v: number[]) => v[2]),
            i: brain.faces.map((f: number[]) => f[0]),
            j: brain.faces.map((f: number[]) => f[1]),
            k: brain.faces.map((f: number[]) => f[2]),
            opacity: 0.15,
            color: 'lightpink',
            name: 'Brain Surface',
            hoverinfo: 'name',
        });
    }

    // Add stroke lesion (transparent cyan)
    if (meshData.stroke_mesh) {
        const stroke = meshData.stroke_mesh;
        traces.push({
            type: 'mesh3d',
            x: stroke.vertices.map((v: number[]) => v[0]),
            y: stroke.vertices.map((v: number[]) => v[1]),
            z: stroke.vertices.map((v: number[]) => v[2]),
            i: stroke.faces.map((f: number[]) => f[0]),
            j: stroke.faces.map((f: number[]) => f[1]),
            k: stroke.faces.map((f: number[]) => f[2]),
            opacity: 0.4,  // Transparent
            color: 'cyan',
            name: 'Ischemic Stroke',
            hoverinfo: 'name',
            lighting: {
                ambient: 0.5,
                diffuse: 0.8,
                specular: 0.2,
            },
        });
    }

    // Add hemorrhage lesion (transparent red)
    if (meshData.hemorrhage_mesh) {
        const hem = meshData.hemorrhage_mesh;
        traces.push({
            type: 'mesh3d',
            x: hem.vertices.map((v: number[]) => v[0]),
            y: hem.vertices.map((v: number[]) => v[1]),
            z: hem.vertices.map((v: number[]) => v[2]),
            i: hem.faces.map((f: number[]) => f[0]),
            j: hem.faces.map((f: number[]) => f[1]),
            k: hem.faces.map((f: number[]) => f[2]),
            opacity: 0.5,  // Transparent
            color: 'red',
            name: 'Hemorrhage',
            hoverinfo: 'name',
            lighting: {
                ambient: 0.6,
                diffuse: 0.9,
                specular: 0.5,
            },
        });
    }

    const layout = {
        title: {
            text: '3D Brain Visualization',
            font: { size: 20, color: 'white' },
        },
        scene: {
            xaxis: { title: 'X', backgroundcolor: 'rgb(20, 20, 30)', gridcolor: 'gray', showgrid: true },
            yaxis: { title: 'Y', backgroundcolor: 'rgb(20, 20, 30)', gridcolor: 'gray', showgrid: true },
            zaxis: { title: 'Z', backgroundcolor: 'rgb(20, 20, 30)', gridcolor: 'gray', showgrid: true },
            bgcolor: 'rgb(10, 10, 20)',
            aspectmode: 'data',  // Maintain correct proportions
            camera: {
                eye: { x: 1.5, y: 1.5, z: 1.5 },
            },
        },
        paper_bgcolor: 'rgb(10, 10, 20)',
        plot_bgcolor: 'rgb(10, 10, 20)',
        font: { color: 'white' },
        showlegend: true,
        legend: {
            bgcolor: 'rgba(20, 20, 30, 0.8)',
            bordercolor: 'gray',
            borderwidth: 1,
        },
        autosize: true,
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
    };

    return (
        <div className="w-full h-full min-h-[500px]">
            <Plot
                data={traces}
                layout={layout}
                config={config}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
            />
        </div>
    );
}
