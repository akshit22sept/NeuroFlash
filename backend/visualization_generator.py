"""
Generate HTML visualization files for 3D brain rendering
Extracted from test_visualizations.py for production use
"""
import numpy as np
from skimage import measure
import plotly.graph_objects as go
import nibabel as nib
import os


def generate_3d_html_visualization(volume, affine, mask, output_path):
    """
    Generate interactive 3D Plotly visualization HTML file
    
    Args:
        volume: 3D numpy array of scan data
        affine: NIfTI affine matrix
        mask: 3D segmentation mask (optional)
        output_path: Path to save HTML file
    
    Returns:
        str: Path to generated HTML file
    """
    print(f"Generating 3D visualization HTML...")
    
    # Extract voxel spacing from affine matrix
    voxel_spacing = np.abs(np.diag(affine)[:3])
    
    # Ensure proper aspect ratio
    min_spacing = voxel_spacing.min()
    aspect_ratio = voxel_spacing / min_spacing
    spacing_corrected = (1.0, aspect_ratio[1], aspect_ratio[2])
    
    # Normalize volume
    volume_norm = (volume - volume.min()) / (volume.max() - volume.min())
    
    fig = go.Figure()
    
    # Create brain surface (semi-transparent)
    brain_threshold = 0.1
    try:
        verts_brain, faces_brain, _, _ = measure.marching_cubes(
            volume_norm, level=brain_threshold, step_size=2, spacing=spacing_corrected
        )
        
        fig.add_trace(go.Mesh3d(
            x=verts_brain[:, 0],
            y=verts_brain[:, 1],
            z=verts_brain[:, 2],
            i=faces_brain[:, 0],
            j=faces_brain[:, 1],
            k=faces_brain[:, 2],
            opacity=0.15,
            color='lightpink',
            name='Brain Surface',
            hoverinfo='name'
        ))
        print(f"  ✓ Brain surface: {len(verts_brain)} vertices")
    except Exception as e:
        print(f"  ⚠ Could not create brain surface: {e}")
    
    # Create lesion surfaces if mask available
    if mask is not None:
        # Create brain mask to filter out-of-brain detections
        brain_mask = volume_norm > 0.05
        
        # Stroke lesions (class 1)
        stroke_mask = (mask == 1).astype(np.float32) * brain_mask
        if stroke_mask.sum() > 0:
            try:
                verts_stroke, faces_stroke, _, _ = measure.marching_cubes(
                    stroke_mask, level=0.5, step_size=1, spacing=spacing_corrected
                )
                
                fig.add_trace(go.Mesh3d(
                    x=verts_stroke[:, 0],
                    y=verts_stroke[:, 1],
                    z=verts_stroke[:, 2],
                    i=faces_stroke[:, 0],
                    j=faces_stroke[:, 1],
                    k=faces_stroke[:, 2],
                    opacity=0.4,
                    color='cyan',
                    name='Ischemic Stroke',
                    hoverinfo='name',
                    lighting=dict(ambient=0.5, diffuse=0.8, specular=0.2)
                ))
                print(f"  ✓ Stroke surface: {len(verts_stroke)} vertices")
            except Exception as e:
                print(f"  ⚠ Could not create stroke surface: {e}")
        
        # Hemorrhage lesions (class 2)
        hem_mask = (mask == 2).astype(np.float32) * brain_mask
        if hem_mask.sum() > 0:
            try:
                verts_hem, faces_hem, _, _ = measure.marching_cubes(
                    hem_mask, level=0.5, step_size=1, spacing=spacing_corrected
                )
                
                fig.add_trace(go.Mesh3d(
                    x=verts_hem[:, 0],
                    y=verts_hem[:, 1],
                    z=verts_hem[:, 2],
                    i=faces_hem[:, 0],
                    j=faces_hem[:, 1],
                    k=faces_hem[:, 2],
                    opacity=0.5,
                    color='red',
                    name='Hemorrhage',
                    hoverinfo='name',
                    lighting=dict(ambient=0.6, diffuse=0.9, specular=0.5)
                ))
                print(f"  ✓ Hemorrhage surface: {len(verts_hem)} vertices")
            except Exception as e:
                print(f"  ⚠ Could not create hemorrhage surface: {e}")
    
    # Update layout for better viewing
    fig.update_layout(
        title=dict(
            text='3D Brain Visualization',
            font=dict(size=20, color='white')
        ),
        scene=dict(
            xaxis=dict(title='X', backgroundcolor='rgb(20, 20, 30)', gridcolor='gray', showgrid=True),
            yaxis=dict(title='Y', backgroundcolor='rgb(20, 20, 30)', gridcolor='gray', showgrid=True),
            zaxis=dict(title='Z', backgroundcolor='rgb(20, 20, 30)', gridcolor='gray', showgrid=True),
            bgcolor='rgb(10, 10, 20)',
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        paper_bgcolor='rgb(10, 10, 20)',
        plot_bgcolor='rgb(10, 10, 20)',
        font=dict(color='white'),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(20, 20, 30, 0.8)',
            bordercolor='gray',
            borderwidth=1
        )
    )
    
    # Save HTML
    fig.write_html(output_path)
    print(f"  ✓ Saved visualization: {output_path}")
    
    return output_path


def generate_visualization_for_scan(file_path, mask_path, output_dir, file_id):
    """
    Generate visualization HTML for a processed scan
    
    Args:
        file_path: Path to NIfTI scan file
        mask_path: Path to .npy mask file
        output_dir: Directory to save HTML
        file_id: Unique file identifier
    
    Returns:
        str: Path to generated HTML file
    """
    try:
        # Load scan with explicit file path (not file handle)
        print(f"Loading scan from: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Scan file not found: {file_path}")
        
        # Load with nibabel - ensure file is completely written and closed
        img = nib.load(file_path)
        volume = np.asarray(img.get_fdata())  # Explicitly convert to numpy array
        affine = np.array(img.affine)  # Copy affine to avoid file handle issues
        
        # Clear the nibabel object to close file handles
        del img
        
        # Load mask
        mask = None
        if mask_path and os.path.exists(mask_path):
            print(f"Loading mask from: {mask_path}")
            mask = np.load(mask_path)
        
        # Generate HTML
        output_path = os.path.join(output_dir, f"{file_id}_3d.html")
        print(f"Generating HTML to: {output_path}")
        result = generate_3d_html_visualization(volume, affine, mask, output_path)
        
        # Clean up memory
        del volume
        if mask is not None:
            del mask
        
        return result
    except Exception as e:
        print(f"Error generating visualization: {e}")
        import traceback
        traceback.print_exc()
        raise
