import React from 'react';
import Plot from 'react-plotly.js';

interface BrainVisualizationProps {
    meshData: {
        vertices: number[][];
        faces: number[][];
        normals: number[][];
    } | null;
}

const BrainVisualization: React.FC<BrainVisualizationProps> = ({ meshData }) => {
    if (!meshData || !meshData.vertices || meshData.vertices.length === 0) {
        return (
            <div style={{
                background: '#1f2937',
                borderRadius: '8px',
                padding: '3rem',
                textAlign: 'center',
                color: '#9ca3af',
                minHeight: '600px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
            }}>
                <div>
                    <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🧠</div>
                    <div>No stroke detected - 3D visualization not available</div>
                </div>
            </div>
        );
    }

    const vertices = meshData.vertices;
    const faces = meshData.faces;

    const x = vertices.map(v => v[0]);
    const y = vertices.map(v => v[1]);
    const z = vertices.map(v => v[2]);
    const i = faces.map(f => f[0]);
    const j = faces.map(f => f[1]);
    const k = faces.map(f => f[2]);

    return (
        <div style={{
            background: '#1f2937',
            borderRadius: '8px',
            overflow: 'hidden'
        }}>
            <Plot
                data={[
                    {
                        type: 'mesh3d',
                        x,
                        y,
                        z,
                        i,
                        j,
                        k,
                        color: 'yellow',
                        opacity: 0.8,
                        flatshading: true,
                        lighting: {
                            ambient: 0.6,
                            diffuse: 0.8,
                            specular: 0.3,
                            roughness: 0.5
                        },
                        name: 'Stroke'
                    }
                ]}
                layout={{
                    scene: {
                        xaxis: { visible: false, showgrid: false, showticklabels: false },
                        yaxis: { visible: false, showgrid: false, showticklabels: false },
                        zaxis: { visible: false, showgrid: false, showticklabels: false },
                        bgcolor: '#1f2937',
                        camera: {
                            eye: { x: 1.5, y: 1.5, z: 1.5 }
                        }
                    },
                    paper_bgcolor: '#1f2937',
                    plot_bgcolor: '#1f2937',
                    margin: { l: 0, r: 0, t: 0, b: 0 },
                    showlegend: false,
                    height: 600,
                    autosize: true
                }}
                config={{
                    displayModeBar: false,
                    responsive: true
                }}
                style={{ width: '100%', height: '600px' }}
            />
        </div>
    );
};

export default BrainVisualization;
