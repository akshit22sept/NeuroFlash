"""
Helper function to generate mesh data using marching cubes
Extracted from test_visualizations.py for use in backend API
"""
import numpy as np
from skimage import measure
import nibabel as nib


def generate_mesh_data_for_plotly(volume, affine, mask=None):
    """
    Generate mesh data for Plotly 3D visualization using marching cubes
    
    Args:
        volume: 3D numpy array of scan data
        affine: NIfTI affine matrix
        mask: Optional 3D segmentation mask
    
    Returns:
        dict with brain_mesh, stroke_mesh, hemorrhage_mesh
    """
    # Extract voxel spacing from affine matrix
    voxel_spacing = np.abs(np.diag(affine)[:3])
    
    # Ensure proper aspect ratio
    min_spacing = voxel_spacing.min()
    aspect_ratio = voxel_spacing / min_spacing
    spacing_corrected = (1.0, aspect_ratio[1], aspect_ratio[2])
    
    # Normalize volume
    volume_norm = (volume - volume.min()) / (volume.max() - volume.min())
    
    result = {}
    
    # Generate brain surface
    brain_threshold = 0.1
    try:
        verts_brain, faces_brain, _, _ = measure.marching_cubes(
            volume_norm, level=brain_threshold, step_size=2, spacing=spacing_corrected
        )
        result['brain_mesh'] = {
            'vertices': verts_brain.tolist(),
            'faces': faces_brain.tolist()
        }
    except Exception as e:
        print(f"Could not create brain surface: {e}")
        result['brain_mesh'] = None
    
    # Generate lesion surfaces if mask available
    if mask is not None:
        # Create brain mask to filter out-of-brain detections
        brain_mask = volume_norm > 0.05
        
        # Stroke mesh (class 1)
        stroke_mask = (mask == 1).astype(np.float32) * brain_mask
        if stroke_mask.sum() > 0:
            try:
                verts_stroke, faces_stroke, _, _ = measure.marching_cubes(
                    stroke_mask, level=0.5, step_size=1, spacing=spacing_corrected
                )
                result['stroke_mesh'] = {
                    'vertices': verts_stroke.tolist(),
                    'faces': faces_stroke.tolist()
                }
            except Exception as e:
                print(f"Could not create stroke surface: {e}")
                result['stroke_mesh'] = None
        else:
            result['stroke_mesh'] = None
        
        # Hemorrhage mesh (class 2)
        hem_mask = (mask == 2).astype(np.float32) * brain_mask
        if hem_mask.sum() > 0:
            try:
                verts_hem, faces_hem, _, _ = measure.marching_cubes(
                    hem_mask, level=0.5, step_size=1, spacing=spacing_corrected
                )
                result['hemorrhage_mesh'] = {
                    'vertices': verts_hem.tolist(),
                    'faces': faces_hem.tolist()
                }
            except Exception as e:
                print(f"Could not create hemorrhage surface: {e}")
                result['hemorrhage_mesh'] = None
        else:
            result['hemorrhage_mesh'] = None
    else:
        result['stroke_mesh'] = None
        result['hemorrhage_mesh'] = None
    
    result['spacing'] = voxel_spacing.tolist()
    
    return result
