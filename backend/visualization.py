"""
Generate 3D visualization and slices for frontend
"""

import numpy as np
import nibabel as nib
from skimage import measure
import plotly.graph_objects as go
from pathlib import Path

def get_most_affected_slices(pred_mask, scan_path, top_k=6):
    """Get slices with most lesions"""
    affected_slices = []
    
    # Analyze axial slices (Z-axis)
    for i in range(pred_mask.shape[2]):
        slice_mask = pred_mask[:, :, i]
        lesion_voxels = int(np.sum(slice_mask > 0))
        
        if lesion_voxels > 0:
            affected_slices.append({
                "slice_num": int(i),
                "lesion_voxels": lesion_voxels,
                "stroke_voxels": lesion_voxels,
                "hemorrhage_voxels": 0,
                "axis": "axial"
            })
    
    # Sort by lesion burden
    affected_slices.sort(key=lambda x: x["lesion_voxels"], reverse=True)
    
    return affected_slices[:top_k]


def generate_3d_mesh(pred_mask, scan_path):
    """Generate simple 3D mesh data for Plotly"""
    stroke_mask = (pred_mask > 0).astype(np.uint8)
    
    if np.sum(stroke_mask) == 0:
        return None
    
    try:
        # Downsample for performance
        stroke_small = stroke_mask[::2, ::2, ::2]
        
        # Generate mesh
        verts, faces, normals, values = measure.marching_cubes(
            stroke_small, 
            level=0.5,
            step_size=1
        )
        
        # Scale back up
        verts = verts * 2
        
        return {
            "vertices": verts.tolist(),
            "faces": faces.tolist(),
            "normals": normals.tolist()
        }
    except Exception as e:
        print(f"⚠️ Could not generate 3D mesh: {e}")
        return None


def create_plotly_visualization(pred_mask, scan_path):
    """Create Plotly 3D visualization HTML with brain + stroke"""
    # Load the original brain scan
    scan_nii = nib.load(scan_path)
    scan_data = scan_nii.get_fdata()
    
    # Downsample for performance
    scan_small = scan_data[::2, ::2, ::2]
    stroke_mask_small = (pred_mask[::2, ::2, ::2] > 0).astype(np.uint8)
    
    data_traces = []
    
    try:
        # Create brain isosurface
        brain_threshold = scan_small.mean() + 0.5 * scan_small.std()
        print(f"  Generating brain mesh (threshold={brain_threshold:.3f})...")
        
        brain_verts, brain_faces, _, _ = measure.marching_cubes(
            scan_small,
            level=brain_threshold,
            step_size=2
        )
        
        brain_mesh = go.Mesh3d(
            x=brain_verts[:, 0],
            y=brain_verts[:, 1],
            z=brain_verts[:, 2],
            i=brain_faces[:, 0],
            j=brain_faces[:, 1],
            k=brain_faces[:, 2],
            color='lightgray',
            opacity=0.15,
            name='Brain',
            flatshading=False,
            lighting=dict(
                ambient=0.5,
                diffuse=0.6,
                specular=0.2,
                roughness=0.8
            ),
            hoverinfo='skip'
        )
        data_traces.append(brain_mesh)
        print(f"    Brain: {len(brain_verts):,} vertices")
        
    except Exception as e:
        print(f"  ⚠️ Could not create brain mesh: {e}")
    
    # Create stroke isosurface if there's stroke
    if np.sum(stroke_mask_small) > 0:
        try:
            print(f"  Generating stroke mesh...")
            stroke_verts, stroke_faces, _, _ = measure.marching_cubes(
                stroke_mask_small,
                level=0.5,
                step_size=1
            )
            
            stroke_mesh = go.Mesh3d(
                x=stroke_verts[:, 0],
                y=stroke_verts[:, 1],
                z=stroke_verts[:, 2],
                i=stroke_faces[:, 0],
                j=stroke_faces[:, 1],
                k=stroke_faces[:, 2],
                color='yellow',
                opacity=0.9,
                name='Stroke Region',
                flatshading=True,
                lighting=dict(
                    ambient=0.6,
                    diffuse=0.8,
                    specular=0.4,
                    roughness=0.5
                )
            )
            data_traces.append(stroke_mesh)
            print(f"    Stroke: {len(stroke_verts):,} vertices")
            
        except Exception as e:
            print(f"  ⚠️ Could not create stroke mesh: {e}")
    
    if not data_traces:
        return None
    
    # Create figure
    fig = go.Figure(data=data_traces)
    
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False, showgrid=False, showticklabels=False),
            yaxis=dict(visible=False, showgrid=False, showticklabels=False),
            zaxis=dict(visible=False, showgrid=False, showticklabels=False),
            bgcolor='#0f172a',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        paper_bgcolor='#0f172a',
        plot_bgcolor='#0f172a',
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(31, 41, 55, 0.8)',
            bordercolor='#374151',
            borderwidth=1,
            font=dict(color='white', size=12)
        ),
        height=600
    )
    
    return fig.to_html(
        include_plotlyjs='cdn',
        div_id='brain-viz',
        config={'displayModeBar': True, 'responsive': True}
    )
