"""
DEM Processing and Geometric Illumination Modelling Module.

Implements ray-tracing illumination model against solar ephemeris over a full
illumination cycle to compute per-pixel cumulative illumination fraction and
explicit identification of doubly shadowed terrain.
"""

import numpy as np
import rasterio
from rasterio.windows import Window
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path
import logging
from ..utils import load_config, compute_slope_aspect, ensure_dir

logger = logging.getLogger(__name__)


class SolarEphemeris:
    """Lunar solar ephemeris calculator for south pole."""
    
    def __init__(self, latitude: float = -90.0, longitude: float = 0.0):
        self.latitude = np.radians(latitude)
        self.longitude = np.radians(longitude)
        # Lunar orbital parameters
        self.lunar_day_hours = 29.53 * 24  # hours
        self.obliquity = np.radians(1.543)  # Lunar axial tilt
        
    def sun_position(self, time_hours: float) -> Tuple[float, float]:
        """
        Calculate sun azimuth and elevation at given time.
        Returns (azimuth_deg, elevation_deg) where azimuth is from north, clockwise.
        """
        # Simplified model: sun circles horizon at poles
        # At south pole, sun moves in spiral over lunar day
        phase = 2 * np.pi * time_hours / self.lunar_day_hours
        
        # Elevation varies with season (obliquity)
        elevation = self.obliquity * np.sin(phase)
        
        # Azimuth progresses through 360 degrees over lunar day
        azimuth = np.degrees(phase) % 360
        
        return azimuth, np.degrees(elevation)


class RayTracer:
    """Geometric horizon ray-tracing for illumination modelling."""
    
    def __init__(self, dem: np.ndarray, resolution: float, transform):
        self.dem = dem
        self.resolution = resolution
        self.transform = transform
        self.height, self.width = dem.shape
        
    def trace_ray(self, row: int, col: int, azimuth: float, elevation: float, 
                  max_distance: float = 10000.0) -> bool:
        """
        Trace a single ray from pixel to sun direction.
        Returns True if illuminated, False if in shadow.
        """
        if elevation <= 0:
            return False  # Sun below horizon
            
        # Convert azimuth to direction vector (azimuth from north, clockwise)
        az_rad = np.radians(azimuth)
        # East = +x, North = -y in image coordinates
        dx = np.sin(az_rad)
        dy = -np.cos(az_rad)
        
        # Step along ray
        step = self.resolution
        max_steps = int(max_distance / step)
        
        current_z = self.dem[row, col]
        r, c = float(row), float(col)
        
        for _ in range(max_steps):
            r += dy * step / self.resolution
            c += dx * step / self.resolution
            
            ir, ic = int(round(r)), int(round(c))
            
            if ir < 0 or ir >= self.height or ic < 0 or ic >= self.width:
                return True  # Ray left DEM - illuminated
                
            terrain_z = self.dem[ir, ic]
            # Height of ray at this distance
            dist = np.sqrt((ir - row)**2 + (ic - col)**2) * self.resolution
            ray_z = current_z + dist * np.tan(np.radians(elevation))
            
            if terrain_z > ray_z:
                return False  # Terrain blocks sun
                
        return True  # No obstruction found
    
    def compute_illumination_map(self, azimuth: float, elevation: float) -> np.ndarray:
        """Compute binary illumination map for given sun position."""
        illuminated = np.zeros_like(self.dem, dtype=bool)
        
        # Vectorized approach for better performance
        # Process in chunks to manage memory
        chunk_size = 512
        for r_start in range(0, self.height, chunk_size):
            r_end = min(r_start + chunk_size, self.height)
            for c_start in range(0, self.width, chunk_size):
                c_end = min(c_start + chunk_size, self.width)
                chunk = self.dem[r_start:r_end, c_start:c_end]
                illum_chunk = self._trace_chunk(r_start, c_start, chunk, azimuth, elevation)
                illuminated[r_start:r_end, c_start:c_end] = illum_chunk
                
        return illuminated
    
    def _trace_chunk(self, r0: int, c0: int, chunk: np.ndarray, 
                     azimuth: float, elevation: float) -> np.ndarray:
        """Trace rays for a chunk of pixels."""
        h, w = chunk.shape
        illuminated = np.zeros((h, w), dtype=bool)
        
        az_rad = np.radians(azimuth)
        dx = np.sin(az_rad)
        dy = -np.cos(az_rad)
        tan_elev = np.tan(np.radians(elevation))
        step = self.resolution
        max_distance = 10000.0
        max_steps = int(max_distance / step)
        
        for i in range(h):
            for j in range(w):
                row, col = r0 + i, c0 + j
                current_z = chunk[i, j]
                r, c = float(row), float(col)
                
                for _ in range(max_steps):
                    r += dy * step / self.resolution
                    c += dx * step / self.resolution
                    ir, ic = int(round(r)), int(round(c))
                    
                    if ir < 0 or ir >= self.height or ic < 0 or ic >= self.width:
                        illuminated[i, j] = True
                        break
                        
                    terrain_z = self.dem[ir, ic]
                    dist = np.sqrt((ir - row)**2 + (ic - col)**2) * self.resolution
                    ray_z = current_z + dist * tan_elev
                    
                    if terrain_z > ray_z:
                        break
                else:
                    illuminated[i, j] = True
                    
        return illuminated


class IlluminationModel:
    """Full illumination cycle modelling for doubly-shadowed terrain identification."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        illum_config = config['illumination']
        self.latitude = illum_config['latitude']
        self.longitude = illum_config['longitude']
        self.cycle_days = illum_config['cycle_days']
        self.time_step_hours = illum_config['time_step_hours']
        self.secondary_angle = illum_config['secondary_illumination_angle']
        
        self.ephemeris = SolarEphemeris(self.latitude, self.longitude)
        
    def load_dem(self, dem_path: str) -> Tuple[np.ndarray, Dict]:
        """Load DEM from GeoTIFF."""
        with rasterio.open(dem_path) as src:
            dem = src.read(1)
            meta = src.meta.copy()
            transform = src.transform
            resolution = src.res[0]  # assumes square pixels
        return dem, meta, transform, resolution
    
    def run_illumination_cycle(self, dem: np.ndarray, resolution: float, 
                               transform) -> Dict[str, np.ndarray]:
        """
        Run full illumination cycle ray-tracing.
        Returns dict with cumulative illumination fractions and shadow masks.
        """
        height, width = dem.shape
        n_steps = int(self.cycle_days * 24 / self.time_step_hours)
        
        logger.info(f"Running illumination cycle: {n_steps} time steps")
        
        # Accumulators
        direct_illum_count = np.zeros((height, width), dtype=np.uint16)
        secondary_illum_count = np.zeros((height, width), dtype=np.uint16)
        total_steps = 0
        
        tracer = RayTracer(dem, resolution, transform)
        
        for step in range(n_steps):
            time_hours = step * self.time_step_hours
            azimuth, elevation = self.ephemeris.sun_position(time_hours)
            
            if step % 50 == 0:
                logger.info(f"  Step {step}/{n_steps}: azimuth={azimuth:.1f}, elevation={elevation:.1f}")
            
            # Direct illumination
            direct_map = tracer.compute_illumination_map(azimuth, elevation)
            direct_illum_count += direct_map.astype(np.uint16)
            
            # Secondary illumination (terrain-reflected, lower angle)
            if elevation > -self.secondary_angle:
                secondary_map = tracer.compute_illumination_map(azimuth, self.secondary_angle)
                secondary_illum_count += secondary_map.astype(np.uint16)
            
            total_steps += 1
        
        # Compute fractions
        direct_fraction = direct_illum_count / total_steps
        secondary_fraction = secondary_illum_count / total_steps
        
        # Doubly shadowed: never direct AND never secondary
        max_direct = self.config['illumination']['doubly_shadowed_criteria']['max_direct_fraction']
        max_secondary = self.config['illumination']['doubly_shadowed_criteria']['max_secondary_fraction']
        
        doubly_shadowed = (direct_fraction <= max_direct) & (secondary_fraction <= max_secondary)
        
        results = {
            'direct_fraction': direct_fraction.astype(np.float32),
            'secondary_fraction': secondary_fraction.astype(np.float32),
            'doubly_shadowed_mask': doubly_shadowed.astype(np.uint8),
            'total_steps': total_steps
        }
        
        logger.info(f"Doubly shadowed pixels: {np.sum(doubly_shadowed)} / {height * width}")
        
        return results
    
    def save_results(self, results: Dict[str, np.ndarray], meta: Dict, 
                     output_dir: str):
        """Save illumination results as GeoTIFFs."""
        ensure_dir(output_dir)
        
        for name, data in results.items():
            if name == 'total_steps':
                continue
            out_path = Path(output_dir) / f"illumination_{name}.tif"
            meta_out = meta.copy()
            meta_out.update(dtype='float32' if data.dtype == np.float32 else 'uint8', count=1)
            with rasterio.open(out_path, 'w', **meta_out) as dst:
                dst.write(data, 1)
            logger.info(f"Saved {out_path}")


def run_illumination_pipeline(config_path: str = "config/config.yaml",
                              dem_path: Optional[str] = None,
                              output_dir: Optional[str] = None):
    """Run the complete illumination modelling pipeline."""
    config = load_config(config_path)
    
    if dem_path is None:
        dem_path = Path(config['data']['dem_dir']) / "tmc2_dem.tif"
    if output_dir is None:
        output_dir = Path(config['data']['output_dir']) / "illumination"
    
    logger.info(f"Loading DEM from {dem_path}")
    model = IlluminationModel(config)
    dem, meta, transform, resolution = model.load_dem(str(dem_path))
    
    logger.info(f"DEM shape: {dem.shape}, resolution: {resolution}m")
    
    results = model.run_illumination_cycle(dem, resolution, transform)
    model.save_results(results, meta, str(output_dir))
    
    # Also save the doubly-shadowed mask as candidate region
    candidate_mask = results['doubly_shadowed_mask']
    candidate_path = Path(output_dir) / "candidate_region_mask.tif"
    meta_out = meta.copy()
    meta_out.update(dtype='uint8', count=1)
    with rasterio.open(candidate_path, 'w', **meta_out) as dst:
        dst.write(candidate_mask, 1)
    
    logger.info(f"Candidate region mask saved to {candidate_path}")
    
    return results, candidate_path


if __name__ == "__main__":
    run_illumination_pipeline()