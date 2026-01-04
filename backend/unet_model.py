"""
UNet3D Model - Exact architecture matching the trained model
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import nibabel as nib
import numpy as np
from pathlib import Path
from collections import OrderedDict

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = Path("../Models/model_epoch_55.pt")

def crop_or_pad(enc_feat, dec_feat):
    _, _, D_enc, H_enc, W_enc = enc_feat.shape
    _, _, D_dec, H_dec, W_dec = dec_feat.shape

    dec_feat = F.pad(
        dec_feat,
        [max(0, W_enc - W_dec), 0,  
         max(0, H_enc - H_dec), 0,  
         max(0, D_enc - D_dec), 0]   
    )

    _, _, D_dec, H_dec, W_dec = dec_feat.shape

    d_start = (D_dec - D_enc) // 2
    h_start = (H_dec - H_enc) // 2
    w_start = (W_dec - W_enc) // 2

    dec_feat = dec_feat[:, :,
                        d_start:d_start + D_enc,
                        h_start:h_start + H_enc,
                        w_start:w_start + W_enc]

    return dec_feat


class ConvBlock3D(nn.Module):
    def __init__(self, in_channels, out_channels, dropout=0.2):
        super().__init__()
        self.conv1 = nn.Conv3d(in_channels, out_channels, 3, padding=1)
        self.bn1 = nn.BatchNorm3d(out_channels)
        self.conv2 = nn.Conv3d(out_channels, out_channels, 3, padding=1)
        self.bn2 = nn.BatchNorm3d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.dropout = nn.Dropout3d(dropout)

    def forward(self, x):
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.dropout(x)
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.dropout(x)
        return x


class UNet3D(nn.Module):
    def __init__(self, in_channels=1, out_channels=2, base_filters=8, dropout=0.2):
        super().__init__()

        self.enc1 = ConvBlock3D(in_channels, base_filters, dropout)
        self.pool1 = nn.MaxPool3d(2)

        self.enc2 = ConvBlock3D(base_filters, base_filters*2, dropout)
        self.pool2 = nn.MaxPool3d(2)

        self.enc3 = ConvBlock3D(base_filters*2, base_filters*4, dropout)
        self.pool3 = nn.MaxPool3d(2)

        self.enc4 = ConvBlock3D(base_filters*4, base_filters*8, dropout)
        self.pool4 = nn.MaxPool3d(2)

        self.bottleneck = ConvBlock3D(base_filters*8, base_filters*16, dropout)

        self.up4 = nn.ConvTranspose3d(base_filters*16, base_filters*8, kernel_size=2, stride=2)
        self.dec4 = ConvBlock3D(base_filters*16, base_filters*8, dropout)

        self.up3 = nn.ConvTranspose3d(base_filters*8, base_filters*4, kernel_size=2, stride=2)
        self.dec3 = ConvBlock3D(base_filters*8, base_filters*4, dropout)

        self.up2 = nn.ConvTranspose3d(base_filters*4, base_filters*2, kernel_size=2, stride=2)
        self.dec2 = ConvBlock3D(base_filters*4, base_filters*2, dropout)

        self.up1 = nn.ConvTranspose3d(base_filters*2, base_filters, kernel_size=2, stride=2)
        self.dec1 = ConvBlock3D(base_filters*2, base_filters, dropout)

        self.final = nn.Conv3d(base_filters, out_channels, kernel_size=1)

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool1(e1))
        e3 = self.enc3(self.pool2(e2))
        e4 = self.enc4(self.pool3(e3))

        b = self.bottleneck(self.pool4(e4))

        d4 = self.up4(b)
        d4 = crop_or_pad(e4, d4)
        d4 = torch.cat([d4, e4], dim=1)
        d4 = self.dec4(d4)

        d3 = self.up3(d4)
        d3 = crop_or_pad(e3, d3)
        d3 = torch.cat([d3, e3], dim=1)
        d3 = self.dec3(d3)

        d2 = self.up2(d3)
        d2 = crop_or_pad(e2, d2)
        d2 = torch.cat([d2, e2], dim=1)
        d2 = self.dec2(d2)

        d1 = self.up1(d2)
        d1 = crop_or_pad(e1, d1)
        d1 = torch.cat([d1, e1], dim=1)
        d1 = self.dec1(d1)

        return self.final(d1)


def load_unet_model():
    """Load trained UNet3D model"""
    print(f"📦 Loading UNet3D model from {MODEL_PATH}...")
    
    model = UNet3D(in_channels=1, out_channels=2, base_filters=8, dropout=0.2).to(DEVICE)
    
    if MODEL_PATH.exists():
        checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
        state_dict = checkpoint["model_state_dict"]
        
        # Remove 'module.' prefix from DataParallel
        new_state_dict = OrderedDict()
        for k, v in state_dict.items():
            new_state_dict[k.replace("module.", "")] = v
        
        model.load_state_dict(new_state_dict)
        print(f"✅ Loaded UNet3D model successfully")
        print(f"  Parameters: {sum(p.numel() for p in model.parameters()):,}")
    else:
        print(f"⚠️ Model not found at {MODEL_PATH}")
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    
    model.eval()
    return model


def run_inference(model, scan_path):
    """Run inference on a brain scan"""
    print(f"🔬 Running inference on {scan_path}...")
    
    # Load scan
    nii = nib.load(scan_path)
    image = nii.get_fdata()
    
    # Normalization (matching training)
    image_norm = (image - image.mean()) / (image.std() + 1e-8)
    input_tensor = torch.from_numpy(image_norm[None, None].astype(np.float32)).to(DEVICE)
    
    # Inference
    with torch.no_grad():
        output = model(input_tensor)
        pred = torch.argmax(output, dim=1).squeeze().cpu().numpy()
    
    stroke_voxels = np.sum(pred > 0)
    print(f"✅ Inference complete. Detected {stroke_voxels} stroke voxels")
    
    return pred, image.shape


def calculate_metrics(pred_mask):
    """Calculate clinical metrics"""
    stroke_voxels = int(np.sum(pred_mask > 0))
    total_voxels = int(np.prod(pred_mask.shape))
    
    # Volume (assuming 1mm³ voxels for simplicity)
    volume_mm3 = stroke_voxels
    volume_cm3 = volume_mm3 / 1000
    
    # Percentage
    percentage = (stroke_voxels / max(total_voxels, 1)) * 100
    
    # Severity
    if stroke_voxels == 0:
        severity = "None"
        score = 0
    elif percentage < 0.1:
        severity = "Minimal"
        score = 1
    elif percentage < 0.5:
        severity = "Low"
        score = 2
    elif percentage < 1.5:
        severity = "Moderate"
        score = 3
    else:
        severity = "High"
        score = 4
    
    return {
        "stroke_voxels": stroke_voxels,
        "stroke_volume_mm3": float(volume_mm3),
        "stroke_volume_cm3": float(volume_cm3),
        "brain_percentage": float(percentage),
        "severity": severity,
        "severity_score": score,
        "has_stroke": stroke_voxels > 0
    }
