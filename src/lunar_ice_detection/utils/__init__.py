"""
Utility functions for the Lunar Ice Detection System.
"""

import numpy as np
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def save_config(config: Dict[str, Any], config_path: str = "config/config.yaml"):
    """Save configuration to YAML file."""
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


def ensure_dir(path: str):
    """Ensure directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)


def read_geotiff(path: str) -> Tuple[np.ndarray, Dict]:
    """Read GeoTIFF file and return array and metadata."""
    import rasterio
    with rasterio.open(path) as src:
        data = src.read(1)
        meta = src.meta.copy()
    return data, meta


def write_geotiff(path: str, data: np.ndarray, meta: Dict, dtype=None):
    """Write array to GeoTIFF with metadata."""
    import rasterio
    meta = meta.copy()
    if dtype:
        meta['dtype'] = dtype
    else:
        meta['dtype'] = data.dtype
    meta['count'] = 1
    with rasterio.open(path, 'w', **meta) as dst:
        dst.write(data.astype(meta['dtype']), 1)


def normalize_array(arr: np.ndarray, min_val: float = 0.0, max_val: float = 1.0) -> np.ndarray:
    """Normalize array to [min_val, max_val] range."""
    arr_min, arr_max = np.nanmin(arr), np.nanmax(arr)
    if arr_max == arr_min:
        return np.full_like(arr, min_val)
    normalized = (arr - arr_min) / (arr_max - arr_min)
    return normalized * (max_val - min_val) + min_val


def clip_percentile(arr: np.ndarray, low: float = 2, high: float = 98) -> np.ndarray:
    """Clip array to percentile range."""
    low_val = np.nanpercentile(arr, low)
    high_val = np.nanpercentile(arr, high)
    return np.clip(arr, low_val, high_val)


def compute_slope_aspect(dem: np.ndarray, resolution: float) -> Tuple[np.ndarray, np.ndarray]:
    """Compute slope and aspect from DEM using Horn's method."""
    # Gradient in x and y directions
    dzdx = (np.roll(dem, -1, axis=1) - np.roll(dem, 1, axis=1)) / (2 * resolution)
    dzdy = (np.roll(dem, -1, axis=0) - np.roll(dem, 1, axis=0)) / (2 * resolution)
    
    # Slope in degrees
    slope = np.degrees(np.arctan(np.sqrt(dzdx**2 + dzdy**2)))
    
    # Aspect in degrees (0 = north, clockwise)
    aspect = np.degrees(np.arctan2(-dzdx, dzdy))
    aspect = np.where(aspect < 0, aspect + 360, aspect)
    
    return slope, aspect


def hillshade(dem: np.ndarray, resolution: float, azimuth: float = 315, altitude: float = 45) -> np.ndarray:
    """Compute hillshade for visualization."""
    slope, aspect = compute_slope_aspect(dem, resolution)
    azimuth_rad = np.radians(azimuth)
    altitude_rad = np.radians(altitude)
    slope_rad = np.radians(slope)
    aspect_rad = np.radians(aspect)
    
    shaded = np.sin(altitude_rad) * np.sin(slope_rad) + \
             np.cos(altitude_rad) * np.cos(slope_rad) * np.cos(azimuth_rad - aspect_rad)
    return np.clip(shaded * 255, 0, 255).astype(np.uint8)


def geographic_to_pixel(lat: float, lon: float, transform) -> Tuple[int, int]:
    """Convert geographic coordinates to pixel coordinates."""
    import rasterio
    row, col = rasterio.transform.rowcol(transform, lon, lat)
    return row, col


def pixel_to_geographic(row: int, col: int, transform) -> Tuple[float, float]:
    """Convert pixel coordinates to geographic coordinates."""
    import rasterio
    lon, lat = rasterio.transform.xy(transform, row, col)
    return lat, lon


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in meters."""
    R = 1737400  # Moon radius in meters
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


def mad_std(arr: np.ndarray) -> float:
    """Median Absolute Deviation as robust standard deviation estimator."""
    median = np.nanmedian(arr)
    return 1.4826 * np.nanmedian(np.abs(arr - median))


def robust_normalize(arr: np.ndarray, n_mad: float = 3.0) -> np.ndarray:
    """Normalize using robust statistics (median/MAD)."""
    median = np.nanmedian(arr)
    mad = mad_std(arr)
    if mad == 0:
        return np.zeros_like(arr)
    clipped = np.clip(arr, median - n_mad * mad, median + n_mad * mad)
    return (clipped - np.nanmin(clipped)) / (np.nanmax(clipped) - np.nanmin(clipped) + 1e-10)