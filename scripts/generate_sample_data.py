"""
Sample Data Generator for Lunar Ice Detection System.

Creates synthetic DEM, radar, and OHRC data for testing and demonstration
purposes when real Chandrayaan-2 data is not available.
"""

import numpy as np
import rasterio
from rasterio.transform import from_origin
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def create_sample_dem(output_path: str, width: int = 1000, height: int = 1000,
                     resolution: float = 5.0, lat0: float = -89.9, lon0: float = 0.0):
    """
    Create a synthetic DEM resembling lunar south polar terrain.
    
    Creates:
    - Generally flat terrain with elevation ~0 m
    - A large impact crater (doubly shadowed region)
    - Smaller craters and boulder fields
    """
    print(f"Generating synthetic DEM: {output_path}")
    
    # Create coordinate grids
    x = np.arange(width) * resolution
    y = np.arange(height) * resolution
    xv, yv = np.meshgrid(x, y)
    
    # Base elevation (slightly negative for polar region)
    dem = np.full((height, width), -50.0, dtype=np.float32)
    
    # Add a large crater (20km diameter) - potential doubly shadowed region
    center_x, center_y = width // 2, height // 2
    crater_radius = 20000.0 / resolution  # 20 km in pixels
    
    for i in range(height):
        for j in range(width):
            dist = np.sqrt((i - center_y)**2 + (j - center_x)**2) * resolution
            if dist < crater_radius:
                # Crater shape: parabolic depression
                depth = 100.0 * (1 - (dist / crater_radius)**2)
                dem[i, j] -= depth
    
    # Add smaller craters and boulder fields
    np.random.seed(42)  # For reproducibility
    for _ in range(50):
        # Random crater
        cx = np.random.randint(0, width)
        cy = np.random.randint(0, height)
        radius = np.random.uniform(50, 500) / resolution  # 50-500m radius
        depth = np.random.uniform(5, 50)
        
        for i in range(max(0, cy - int(radius)), min(height, cy + int(radius))):
            for j in range(max(0, cx - int(radius)), min(width, cx + int(radius))):
                dist = np.sqrt((i - cy)**2 + (j - cx)**2) * resolution
                if dist < radius:
                    # Semi-elliptical crater
                    depth_factor = 1 - (dist / radius)**2
                    dem[i, j] -= depth * depth_factor
    
    # Add boulder fields as positive anomalies
    for _ in range(100):
        bx = np.random.randint(0, width)
        by = np.random.randint(0, height)
        bwidth = np.random.randint(5, 20)
        bheight = np.random.randint(5, 20)
        boulder_height = np.random.uniform(2, 10)
        
        x1 = max(0, bx - bwidth//2)
        x2 = min(width, bx + bwidth//2)
        y1 = max(0, by - bheight//2)
        y2 = min(height, by + bheight//2)
        
        dem[y1:y2, x1:x2] += boulder_height
    
    # Add some noise
    dem += np.random.normal(0, 2, dem.shape)
    
    # Create GeoTIFF
    transform = from_origin(lon0, lat0, resolution, resolution)
    
    with rasterio.open(
        output_path, 'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=dem.dtype,
        crs='EPSG:4326',
        transform=transform,
    ) as dst:
        dst.write(dem, 1)
    
    print(f"DEM saved to {output_path}")
    print(f"  Size: {width} x {height} pixels")
    print(f"  Resolution: {resolution} m/pixel")
    print(f"  Elevation range: {np.min(dem):.1f} to {np.max(dem):.1f} m")
    

def create_sample_ohrc(output_path: str, width: int = 1000, height: int = 1000,
                      resolution: float = 0.5):
    """
    Create synthetic OHRC imagery (0.5 m resolution panchromatic).
    
    Simulates:
    - Regolith background with varying brightness
    - Craters and ejecta blankets
    - Boulder fields (bright spots)
    - Shadowed areas in craters
    """
    print(f"Generating synthetic OHRC imagery: {output_path}")
    
    # Start with baseline reflectance
    img = np.full((height, width), 0.15, dtype=np.float32)  # Lunar regolith albedo
    
    # Add crater features (similar to DEM but with albedo variations)
    center_x, center_y = width // 2, height // 2
    crater_radius = 20000.0 / resolution  # 20 km in pixels
    
    for i in range(height):
        for j in range(width):
            dist = np.sqrt((i - center_y)**2 + (j - center_x)**2) * resolution
            if dist < crater_radius:
                # Crater interior: darker in shadow, brighter on rims
                if dist < crater_radius * 0.7:  # Inner crater - shadowed
                    img[i, j] *= 0.3  # Much darker
                else:  # Crater wall and ejecta
                    # Brighter rim
                    rim_factor = 1.0 + 0.5 * np.exp(-((dist - crater_radius*0.8)**2) / (crater_radius*0.1)**2)
                    img[i, j] *= rim_factor
    
    # Add boulder fields as bright spots
    np.random.seed(42)
    for _ in range(200):
        bx = np.random.randint(0, width)
        by = np.random.randint(0, height)
        bsize = np.random.randint(3, 15)
        brightness = np.random.uniform(0.3, 0.8)
        
        x1 = max(0, bx - bsize//2)
        x2 = min(width, bx + bsize//2)
        y1 = max(0, by - bsize//2)
        y2 = min(height, by + bsize//2)
        
        # Add some variation to make it look natural
        boulder_patch = np.full((y2-y1, x2-x1), brightness, dtype=np.float32)
        boulder_patch += np.random.normal(0, 0.05, boulder_patch.shape)
        boulder_patch = np.clip(boulder_patch, 0, 1)
        
        img[y1:y2, x1:x2] = np.maximum(img[y1:y2, x1:x2], boulder_patch)
    
    # Add some texture noise
    img += np.random.normal(0, 0.02, img.shape)
    img = np.clip(img, 0, 1)
    
    # Create GeoTIFF
    # Note: For simplicity, using same geotransform as DEM but different resolution
    # In reality, OHRC would have different coverage and resolution
    transform = from_origin(0.0, -89.9, resolution, resolution)
    
    with rasterio.open(
        output_path, 'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=img.dtype,
        crs='EPSG:4326',
        transform=transform,
    ) as dst:
        dst.write(img, 1)
    
    print(f"OHRC image saved to {output_path}")
    print(f"  Size: {width} x {height} pixels")
    print(f"  Resolution: {resolution} m/pixel")
    print(f"  Reflectance range: {np.min(img):.3f} to {np.max(img):.3f}")


def create_sample_dfsar_slc(band: str, pol: str, output_path: str,
                           width: int = 1000, height: int = 1000,
                           resolution: float = 50.0):  # DFSAR is ~50m resolution
    """
    Create synthetic DFSAR SLC (Single Look Complex) data.
    
    Simulates polarimetric radar returns with:
    - Surface scattering (low CPR, high DOP)
    - Volume scattering from ice (high CPR, low DOP) 
    - Double bounce from rocky surfaces
    - Speckle noise
    """
    print(f"Generating synthetic DFSAR {band}-band {pol} polarization: {output_path}")
    
    # Create complex SAR image with speckle
    # Amplitude follows Rayleigh distribution, phase uniform [0, 2π]
    
    # Mean backscatter coefficient (sigma0) in linear units
    # Typical lunar values: -15 to -5 dB
    mean_sigma0_db = -10.0
    mean_sigma0 = 10**(mean_sigma0_db / 10)
    
    # Generate speckle
    amplitude = np.random.rayleigh(scale=np.sqrt(mean_sigma0/2), size=(height, width))
    phase = np.random.uniform(0, 2*np.pi, size=(height, width))
    
    # Complex signal
    slc = amplitude * np.exp(1j * phase)
    
    # Add polarimetric signatures based on ground truth
    # Simulate icy regions (high CPR) in crater interiors
    center_x, center_y = width // 2, height // 2
    crater_radius = 15000.0 / resolution  # 15 km radius
    
    for i in range(height):
        for j in range(width):
            dist = np.sqrt((i - center_y)**2 + (j - center_x)**2) * resolution
            
            if dist < crater_radius:
                # Enhance volume scattering in crater (potential ice)
                if dist < crater_radius * 0.6:  # Deep crater
                    # Increase cross-pol and same-pol for volume scattering
                    if pol in ['HH', 'VV']:
                        slc[i, j] *= 1.3  # Enhance co-pol
                    elif pol in ['HV', 'VH']:
                        slc[i, j] *= 1.8  # Enhance cross-pol more (volume scattering)
                else:
                    # Crater walls - more surface scattering
                    if pol in ['HH', 'VV']:
                        slc[i, j] *= 0.8
                    else:
                        slc[i, j] *= 0.5
            else:
                # Outside crater - typical regolith
                pass
    
    # Add some anisotropic features (simulate rock streaks)
    for _ in range(10):
        x1 = np.random.randint(0, width//2)
        y1 = np.random.randint(0, height//2)
        x2 = x1 + np.random.randint(50, 150)
        y2 = y1 + np.random.randint(10, 30)
        angle = np.random.uniform(0, np.pi)
        
        # Create a streak
        for i in range(y1, min(y2, height)):
            for j in range(x1, min(x2, width)):
                # Distance from line
                dx = x2 - x1
                dy = y2 - y1
                if dx == 0 and dy == 0:
                    continue
                dist = abs(dy*(j-x1) - dx*(i-y1)) / np.sqrt(dx*dx + dy*dy)
                if dist < 10:  # Within 10 pixels of line
                    enhancement = 1.0 + 0.5 * np.exp(-dist/5.0)
                    slc[i, j] *= enhancement
    
    # Add multiplicative speckle noise (more realistic)
    speckle = np.random.rayleigh(scale=0.5, size=(height, width)) * np.exp(1j * 2*np.pi * np.random.uniform(0, 1, size=(height, width)))
    slc = slc * speckle
    
    # Create GeoTIFF with complex64 data
    # Note: Standard GeoTIFF doesn't natively support complex, so we store as two bands
    # But for simplicity, we'll store magnitude only (as is often done for visualization)
    # In a real system, we'd store real and imaginary as separate bands
    
    magnitude = np.abs(slc).astype(np.float64)
    
    transform = from_origin(0.0, -89.9, resolution, resolution)
    
    with rasterio.open(
        output_path, 'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=magnitude.dtype,
        crs='EPSG:4326',
        transform=transform,
    ) as dst:
        dst.write(magnitude, 1)
    
    print(f"DSCAR {band}-band {pol} SLC saved to {output_path}")
    print(f"  Size: {width} x {height} pixels")
    print(f"  Resolution: {resolution} m/pixel")
    print(f"  Magnitude range: {np.min(magnitude):.2f} to {np.max(magnitude):.2f}")


def create_sample_passes(band: str, output_dir: str, num_passes: int = 3):
    """
    Create multiple DFSAR passes for repeat-pass consistency testing.
    """
    print(f"Generating {num_passes} DFSAR {band}-band passes...")
    
    polarizations = ['HH', 'HV', 'VH', 'VV']
    
    for pass_num in range(1, num_passes + 1):
        # Layout matches the production reader: radar/<pass>/<band>/<polarization>.tif
        pass_dir_pass = Path(output_dir) / f"pass_{pass_num:02d}" / band
        pass_dir_pass.mkdir(parents=True, exist_ok=True)
        
        for pol in polarizations:
            # Slightly vary each pass to simulate different looks
            filename = pass_dir_pass / f"dfsar_{band}_{pol}_pass{pass_num:02d}.tif"
            create_sample_dfsar_slc(
                band, pol, str(filename), width=128, height=128, resolution=10.0
            )
    
    print(f"Generated {num_passes} passes in {Path(output_dir).absolute()}")


def generate_all_sample_data(data_root: str = "data"):
    """
    Generate all sample data needed for the lunar ice detection system.
    """
    print("Generating sample data for Lunar Ice Detection System")
    print("=" * 60)
    
    base_path = Path(data_root)
    
    # Create directory structure
    (base_path / "dem").mkdir(parents=True, exist_ok=True)
    (base_path / "radar").mkdir(parents=True, exist_ok=True)
    (base_path / "ohrc").mkdir(parents=True, exist_ok=True)
    
    # Generate DEM (TMC-2 5m resolution)
    create_sample_dem(
        str(base_path / "dem" / "tmc2_dem.tif"),
        width=128, height=128, resolution=5.0
    )
    
    # Generate OHRC (0.5m resolution)
    create_sample_ohrc(
        str(base_path / "ohrc" / "ohrc_image.tif"),
        width=128, height=128, resolution=0.5
    )
    
    # Generate DFSAR L-band and S-band data (50m resolution)
    # Create multiple passes for repeat-pass consistency
    for band in ['L', 'S']:
        band_dir = base_path / "radar" / band
        band_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate 3 passes for each band
        create_sample_passes(band, str(base_path / "radar"), num_passes=3)
    
    print("\n" + "=" * 60)
    print("Sample data generation complete!")
    print(f"Data stored in: {base_path.absolute()}")
    print("\nDirectory structure:")
    print(f"  {base_path}/")
    print(f"    ├── dem/")
    print(f"    │   └── tmc2_dem.tif")
    print(f"    ├── ohrc/")
    print(f"    │   └── ohrc_image.tif")
    print(f"    └── radar/")
    print(f"        ├── L/")
    print(f"        │   ├── pass_01/")
    print(f"        │   │   ├── dfsar_L_HH_pass01.tif")
    print(f"        │   │   ├── dfsar_L_HV_pass01.tif")
    print(f"        │   │   ├── dfsar_L_VH_pass01.tif")
    print(f"        │   │   └── dfsar_L_VV_pass01.tif")
    print(f"        │   ├── pass_02/")
    print(f"        │   └── pass_03/")
    print(f"        └── S/")
    print(f"            ├── pass_01/")
    print(f"            │   ├── dfsar_S_HH_pass01.tif")
    print(f"        │   │   ├── dfsar_S_HV_pass01.tif")
    print(f"        │   │   ├── dfsar_S_VH_pass01.tif")
    print(f"        │   │   └── dfsar_S_VV_pass01.tif")
    print(f"        │   ├── pass_02/")
    print(f"        │   └── pass_03/")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_all_sample_data()