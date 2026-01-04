"""
Generate slice images from NIfTI data
"""

import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from pathlib import Path

def generate_slice_image(pred_mask, scan_path, axis, slice_num):
    """Generate a 2D slice image with overlay"""
    # Load original scan
    scan = nib.load(scan_path).get_fdata()
    
    # Get the slice based on axis
    if axis == 'axial':
        scan_slice = scan[:, :, slice_num]
        mask_slice = pred_mask[:, :, slice_num]
    elif axis == 'sagittal':
        scan_slice = scan[slice_num, :, :]
        mask_slice = pred_mask[slice_num, :, :]
    elif axis == 'coronal':
        scan_slice = scan[:, slice_num, :]
        mask_slice = pred_mask[:, slice_num, :]
    else:
        raise ValueError(f"Invalid axis: {axis}")
    
    # Create figure with square aspect
    fig, ax = plt.subplots(1, 1, figsize=(5, 5), facecolor='#1f2937')
    ax.set_facecolor('#1f2937')
    ax.set_aspect('equal')
    
    # Display scan
    ax.imshow(scan_slice.T, cmap='gray', origin='lower', aspect='auto')
    
    # Overlay stroke mask
    if np.any(mask_slice > 0):
        masked = np.ma.masked_where(mask_slice == 0, mask_slice)
        ax.imshow(masked.T, cmap='hot', alpha=0.6, origin='lower', aspect='auto')
    
    # Remove axes and padding
    ax.axis('off')
    plt.tight_layout(pad=0)
    
    # Convert to base64
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', 
                facecolor='#1f2937', edgecolor='none', dpi=100)
    plt.close(fig)
    
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    
    return f"data:image/png;base64,{img_base64}"


def generate_all_slice_images(pred_mask, scan_path, slice_nums, axis='axial'):
    """Generate images for multiple slices"""
    images = {}
    
    for slice_num in slice_nums:
        try:
            img_data = generate_slice_image(pred_mask, scan_path, axis, slice_num)
            images[slice_num] = img_data
        except Exception as e:
            print(f"Error generating slice {slice_num}: {e}")
            images[slice_num] = None
    
    return images
