"""
OHRC Optical Morphology and Freshness Extraction Module.

Computes crater-freshness/roughness indicator using standard texture/edge-density
measures (local variance, boulder-edge density via threshold-based blob detection)
to flag terrain consistent with fresh, blocky ejecta - the known cause of CPR>1
with no ice present.
"""

import numpy as np
import rasterio
from scipy import ndimage
from skimage import filters, feature, morphology, measure
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
import logging
from ..utils import load_config, ensure_dir, clip_percentile, robust_normalize

logger = logging.getLogger(__name__)


class OHRCProcessor:
    """Process OHRC imagery to extract morphology and freshness features."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        opt_config = config['optical']
        self.variance_window = opt_config['local_variance_window']
        self.edge_threshold = opt_config['edge_detection_threshold']
        self.boulder_min_area = opt_config['boulder_detection']['min_area_pixels']
        self.boulder_max_area = opt_config['boulder_detection']['max_area_pixels']
        self.boulder_intensity_thresh = opt_config['boulder_detection']['intensity_threshold']
        self.glcm_distances = opt_config['glcm_distances']
        self.glcm_angles = opt_config['glcm_angles']
        
    def load_ohrc_image(self, image_path: str) -> Tuple[np.ndarray, Dict]:
        """Load OHRC image from GeoTIFF."""
        with rasterio.open(image_path) as src:
            # OHRC is panchromatic, single band
            image = src.read(1).astype(np.float32)
            meta = src.meta.copy()
            transform = src.transform
            resolution = src.res[0]
        return image, meta, transform, resolution
    
    def compute_local_variance(self, image: np.ndarray) -> np.ndarray:
        """Compute local variance as texture/roughness measure."""
        # Use uniform filter for efficient local variance
        mean = ndimage.uniform_filter(image, size=self.variance_window)
        mean_sq = ndimage.uniform_filter(image**2, size=self.variance_window)
        variance = mean_sq - mean**2
        return variance
    
    def compute_edge_density(self, image: np.ndarray) -> np.ndarray:
        """Compute edge density using Canny edge detector."""
        # Normalize image for edge detection
        norm_image = robust_normalize(image)
        
        # Canny edge detection
        edges = feature.canny(norm_image, sigma=2.0, 
                              low_threshold=self.edge_threshold * 0.5,
                              high_threshold=self.edge_threshold)
        
        # Local edge density (fraction of edge pixels in window)
        edge_density = ndimage.uniform_filter(edges.astype(float), 
                                               size=self.variance_window)
        return edge_density
    
    def detect_boulders(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Detect boulders using threshold-based blob detection.
        Returns (boulder_mask, boulder_density_map)
        """
        # Normalize
        norm_image = robust_normalize(image)
        
        # Threshold for bright boulders
        boulder_candidates = norm_image > self.boulder_intensity_thresh
        
        # Label connected components
        labeled, num_features = ndimage.label(boulder_candidates)
        
        # Filter by size
        boulder_mask = np.zeros_like(image, dtype=bool)
        for i in range(1, num_features + 1):
            component = (labeled == i)
            area = np.sum(component)
            if self.boulder_min_area <= area <= self.boulder_max_area:
                boulder_mask |= component
        
        # Boulder density map
        boulder_density = ndimage.uniform_filter(boulder_mask.astype(float), 
                                                  size=self.variance_window * 2)
        
        return boulder_mask, boulder_density
    
    def compute_glcm_features(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """Compute GLCM (Gray Level Co-occurrence Matrix) texture features."""
        from skimage.feature import graycomatrix, graycoprops
        
        # Quantize image to 16 levels for GLCM
        norm_image = robust_normalize(image)
        quantized = (norm_image * 15).astype(np.uint8)
        
        features = {}
        
        for dist in self.glcm_distances:
            for angle in self.glcm_angles:
                angle_rad = np.radians(angle)
                glcm = graycomatrix(quantized, distances=[dist], angles=[angle_rad], 
                                   levels=16, symmetric=True, normed=True)
                
                # Compute properties
                props = ['contrast', 'dissimilarity', 'homogeneity', 'energy', 'correlation', 'ASM']
                for prop in props:
                    key = f"glcm_{prop}_d{dist}_a{angle}"
                    features[key] = graycoprops(glcm, prop)[0, 0] * np.ones_like(image)
        
        return features
    
    def compute_freshness_index(self, image: np.ndarray) -> np.ndarray:
        """
        Compute composite freshness/roughness index.
        High values = fresh, blocky ejecta terrain (CPR>1 false positive risk)
        Low values = mature, smooth terrain
        """
        # Compute component features
        variance = self.compute_local_variance(image)
        edge_density = self.compute_edge_density(image)
        _, boulder_density = self.detect_boulders(image)
        
        # Normalize each component
        var_norm = robust_normalize(variance)
        edge_norm = robust_normalize(edge_density)
        boulder_norm = robust_normalize(boulder_density)
        
        # Weighted combination (weights from config or defaults)
        # Fresh terrain: high variance, high edges, high boulder density
        freshness = 0.4 * var_norm + 0.3 * edge_norm + 0.3 * boulder_norm
        
        return freshness.astype(np.float32)
    
    def compute_roughness_index(self, image: np.ndarray) -> np.ndarray:
        """
        Compute general roughness index (not freshness-specific).
        Uses local slope from image gradients.
        """
        # Gradient magnitude as roughness
        gy, gx = np.gradient(image)
        roughness = np.sqrt(gx**2 + gy**2)
        
        # Local mean roughness
        roughness_local = ndimage.uniform_filter(roughness, size=self.variance_window)
        
        return robust_normalize(roughness_local).astype(np.float32)
    
    def apply_candidate_mask(self, features: Dict[str, np.ndarray], 
                             mask: np.ndarray) -> Dict[str, np.ndarray]:
        """Restrict features to candidate region."""
        masked = {}
        for key, data in features.items():
            masked[key] = np.where(mask, data, np.nan)
        return masked
    
    def process_ohrc(self, image_path: str, candidate_mask: np.ndarray) -> Dict[str, np.ndarray]:
        """Process OHRC image and extract all morphology features."""
        logger.info(f"Loading OHRC image from {image_path}")
        image, meta, transform, resolution = self.load_ohrc_image(image_path)
        
        logger.info(f"Image shape: {image.shape}, resolution: {resolution}m")
        
        # Compute features
        logger.info("Computing local variance...")
        variance = self.compute_local_variance(image)
        
        logger.info("Computing edge density...")
        edge_density = self.compute_edge_density(image)
        
        logger.info("Detecting boulders...")
        boulder_mask, boulder_density = self.detect_boulders(image)
        
        logger.info("Computing freshness index...")
        freshness = self.compute_freshness_index(image)
        
        logger.info("Computing roughness index...")
        roughness = self.compute_roughness_index(image)
        
        features = {
            'variance': variance.astype(np.float32),
            'edge_density': edge_density.astype(np.float32),
            'boulder_mask': boulder_mask.astype(np.uint8),
            'boulder_density': boulder_density.astype(np.float32),
            'freshness_index': freshness,
            'roughness_index': roughness
        }
        
        # Apply candidate mask
        features = self.apply_candidate_mask(features, candidate_mask)
        
        return features, meta, transform, resolution
    
    def save_features(self, features: Dict[str, np.ndarray], meta: Dict, 
                      output_dir: str, prefix: str = "ohrc"):
        """Save OHRC features as GeoTIFFs."""
        ensure_dir(output_dir)
        
        for name, data in features.items():
            out_path = Path(output_dir) / f"{prefix}_{name}.tif"
            meta_out = meta.copy()
            meta_out.update(dtype='float32' if data.dtype == np.float32 else 'uint8', count=1)
            with rasterio.open(out_path, 'w', **meta_out) as dst:
                dst.write(data, 1)
            logger.info(f"Saved {out_path}")


def run_optical_pipeline(config_path: str = "config/config.yaml",
                         ohrc_path: Optional[str] = None,
                         candidate_mask_path: Optional[str] = None,
                         output_dir: Optional[str] = None):
    """Run the complete OHRC optical processing pipeline."""
    import rasterio
    config = load_config(config_path)
    
    if ohrc_path is None:
        ohrc_path = Path(config['data']['ohrc_dir']) / "ohrc_image.tif"
    if output_dir is None:
        output_dir = Path(config['data']['output_dir']) / "optical"
    if candidate_mask_path is None:
        candidate_mask_path = Path(config['data']['output_dir']) / "illumination" / "candidate_region_mask.tif"
    
    logger.info(f"Loading candidate mask from {candidate_mask_path}")
    with rasterio.open(candidate_mask_path) as src:
        candidate_mask = src.read(1).astype(bool)
    
    logger.info(f"Processing OHRC data from {ohrc_path}")
    processor = OHRCProcessor(config)
    features, meta, transform, resolution = processor.process_ohrc(str(ohrc_path), candidate_mask)
    
    logger.info("Saving results")
    processor.save_features(features, meta, str(output_dir))
    
    return features


if __name__ == "__main__":
    run_optical_pipeline()