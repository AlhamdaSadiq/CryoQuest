"""
DFSAR Radar Feature Extraction Module.

Computes per-pixel CPR, DOP, and total backscatter for DFSAR L/S-band
full-pol passes, retained per independent pass for repeat-pass consistency.
"""

import numpy as np
import rasterio
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path
import logging
from ..utils import load_config, ensure_dir, clip_percentile

logger = logging.getLogger(__name__)


class RadarProcessor:
    """Process DFSAR full-polarimetric data to extract radar features."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        radar_config = config['radar']
        self.bands = radar_config['bands']
        self.cpr_threshold = radar_config['cpr_threshold']
        self.dop_threshold = radar_config['dop_threshold']
        self.min_passes = radar_config['min_passes']
        self.agreement_threshold = radar_config['agreement_threshold']
        
    def load_slc_stack(self, slc_dir: str, band: str) -> Dict[str, np.ndarray]:
        """
        Load Single Look Complex (SLC) data for a band.
        Expected files: HH, HV, VH, VV (complex64 GeoTIFFs)
        """
        slc_path = Path(slc_dir) / band
        pols = ['HH', 'HV', 'VH', 'VV']
        slc_data = {}
        
        for pol in pols:
            files = list(slc_path.glob(f"*{pol}*.tif"))
            if not files:
                files = list(slc_path.glob(f"*{pol.lower()}*.tif"))
            if files:
                with rasterio.open(files[0]) as src:
                    slc_data[pol] = src.read(1)
                    if 'meta' not in slc_data:
                        slc_data['meta'] = src.meta.copy()
                        slc_data['transform'] = src.transform
            else:
                logger.warning(f"No {pol} file found for {band} band")
                
        return slc_data
    
    def compute_stokes_vector(self, slc: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        Compute Stokes vector elements from full-pol SLC.
        S0 = |HH|^2 + |VV|^2 + 2|HV|^2 (assuming reciprocity HV=VH)
        S1 = |HH|^2 - |VV|^2
        S2 = 2*Re(HH*VV*)
        S3 = 2*Im(HH*VV*)
        """
        HH = slc['HH']
        VV = slc['VV']
        HV = slc.get('HV', slc.get('VH', np.zeros_like(HH)))
        
        HH_mag2 = np.abs(HH)**2
        VV_mag2 = np.abs(VV)**2
        HV_mag2 = np.abs(HV)**2
        
        S0 = HH_mag2 + VV_mag2 + 2 * HV_mag2
        S1 = HH_mag2 - VV_mag2
        S2 = 2 * np.real(HH * np.conj(VV))
        S3 = 2 * np.imag(HH * np.conj(VV))
        
        return {'S0': S0, 'S1': S1, 'S2': S2, 'S3': S3}
    
    def compute_cpr(self, slc: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Compute Circular Polarization Ratio (CPR).
        CPR = |RR|^2 / |LL|^2 = (|HH|^2 + |VV|^2 + 2*Re(HH*VV*)) / (|HH|^2 + |VV|^2 - 2*Re(HH*VV*))
        For monostatic radar with reciprocity: CPR = (S0 + S2) / (S0 - S2)
        """
        stokes = self.compute_stokes_vector(slc)
        S0 = stokes['S0']
        S2 = stokes['S2']
        
        # Avoid division by zero
        denom = S0 - S2
        denom = np.where(denom == 0, 1e-10, denom)
        cpr = (S0 + S2) / denom
        
        return cpr
    
    def compute_dop(self, slc: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Compute Degree of Polarization (DOP).
        DOP = sqrt(S1^2 + S2^2 + S3^2) / S0
        """
        stokes = self.compute_stokes_vector(slc)
        S0 = stokes['S0']
        S1 = stokes['S1']
        S2 = stokes['S2']
        S3 = stokes['S3']
        
        dop = np.sqrt(S1**2 + S2**2 + S3**2) / (S0 + 1e-10)
        return np.clip(dop, 0, 1)
    
    def compute_backscatter(self, slc: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Compute total backscatter (sigma0 in dB).
        sigma0 = 10 * log10(S0) + calibration_constant
        """
        stokes = self.compute_stokes_vector(slc)
        S0 = stokes['S0']
        
        # Convert to dB (add calibration constant if available)
        sigma0_db = 10 * np.log10(S0 + 1e-10)
        return sigma0_db
    
    def compute_polarimetric_features(self, slc: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Compute all polarimetric features for one pass."""
        cpr = self.compute_cpr(slc)
        dop = self.compute_dop(slc)
        backscatter = self.compute_backscatter(slc)
        
        return {
            'cpr': cpr.astype(np.float32),
            'dop': dop.astype(np.float32),
            'backscatter': backscatter.astype(np.float32)
        }
    
    def apply_candidate_mask(self, features: Dict[str, np.ndarray], 
                             mask: np.ndarray) -> Dict[str, np.ndarray]:
        """Restrict features to candidate region (doubly-shadowed mask)."""
        masked = {}
        for key, data in features.items():
            masked[key] = np.where(mask, data, np.nan)
        return masked


class MultiPassRadarProcessor:
    """Process multiple independent DFSAR passes for repeat-pass consistency."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.processor = RadarProcessor(config)
        
    def load_pass_data(self, radar_dir: str, pass_id: str, band: str) -> Optional[Dict]:
        """Load SLC data for a specific pass and band."""
        pass_dir = Path(radar_dir) / pass_id / band
        if not pass_dir.exists():
            logger.warning(f"Pass directory not found: {pass_dir}")
            return None
        return self.processor.load_slc_stack(str(Path(radar_dir) / pass_id), band)
    
    def process_all_passes(self, radar_dir: str, candidate_mask: np.ndarray,
                           bands: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Process all available passes for all bands.
        Returns dict with per-pass features and consistency analysis.
        """
        if bands is None:
            bands = self.config['radar']['bands']
            
        radar_path = Path(radar_dir)
        pass_dirs = [d for d in radar_path.iterdir() if d.is_dir()]
        pass_ids = [d.name for d in pass_dirs]
        
        logger.info(f"Found {len(pass_ids)} passes: {pass_ids}")
        
        all_features = {band: {} for band in bands}
        
        for pass_id in pass_ids:
            for band in bands:
                slc = self.load_pass_data(radar_dir, pass_id, band)
                if slc is None:
                    continue
                    
                features = self.processor.compute_polarimetric_features(slc)
                features = self.processor.apply_candidate_mask(features, candidate_mask)
                all_features[band][pass_id] = features
                
        return all_features
    
    def compute_repeat_pass_consistency(self, all_features: Dict[str, Any]) -> Dict[str, np.ndarray]:
        """
        Compute repeat-pass consistency for ice detection criteria.
        A pixel is consistent if criteria met in >= agreement_threshold fraction of passes.
        """
        bands = list(all_features.keys())
        pass_ids = list(next(iter(all_features.values())).keys())
        n_passes = len(pass_ids)
        
        if n_passes < self.config['radar']['min_passes']:
            logger.warning(f"Only {n_passes} passes available, min_passes={self.config['radar']['min_passes']}")
        
        # Get shape from first pass
        first_band = bands[0]
        first_pass = pass_ids[0]
        shape = all_features[first_band][first_pass]['cpr'].shape
        
        # Ice criteria per pass: CPR > threshold AND DOP < threshold
        cpr_thresh = self.config['radar']['cpr_threshold']
        dop_thresh = self.config['radar']['dop_threshold']
        
        consistency_maps = {}
        
        for band in bands:
            # Stack criteria across passes
            cpr_stack = np.stack([all_features[band][pid]['cpr'] for pid in pass_ids], axis=0)
            dop_stack = np.stack([all_features[band][pid]['dop'] for pid in pass_ids], axis=0)
            
            # Criteria met per pass
            cpr_met = cpr_stack > cpr_thresh
            dop_met = dop_stack < dop_thresh
            ice_criteria_met = cpr_met & dop_met
            
            # Fraction of passes meeting criteria
            agreement_fraction = np.nanmean(ice_criteria_met.astype(float), axis=0)
            
            # Consistency mask
            agreement_thresh = self.config['radar']['agreement_threshold']
            consistent = agreement_fraction >= agreement_thresh
            
            consistency_maps[band] = {
                'agreement_fraction': agreement_fraction.astype(np.float32),
                'consistent_mask': consistent.astype(np.uint8),
                'n_passes': n_passes,
                'cpr_mean': np.nanmean(cpr_stack, axis=0).astype(np.float32),
                'dop_mean': np.nanmean(dop_stack, axis=0).astype(np.float32),
                'backscatter_mean': np.nanmean(
                    np.stack([all_features[band][pid]['backscatter'] for pid in pass_ids], axis=0), 
                    axis=0
                ).astype(np.float32)
            }
            
        return consistency_maps
    
    def save_features(self, features: Dict[str, Any], meta: Dict, 
                      output_dir: str, prefix: str = "radar"):
        """Save radar features as GeoTIFFs."""
        ensure_dir(output_dir)
        
        for band, band_data in features.items():
            band_dir = Path(output_dir) / band
            ensure_dir(band_dir)
            
            for name, data in band_data.items():
                if not isinstance(data, np.ndarray):
                    continue
                out_path = band_dir / f"{prefix}_{band}_{name}.tif"
                meta_out = meta.copy()
                meta_out.update(dtype='float32' if data.dtype == np.float32 else 'uint8', count=1)
                with rasterio.open(out_path, 'w', **meta_out) as dst:
                    dst.write(data, 1)
                logger.info(f"Saved {out_path}")


def run_radar_pipeline(config_path: str = "config/config.yaml",
                       radar_dir: Optional[str] = None,
                       candidate_mask_path: Optional[str] = None,
                       output_dir: Optional[str] = None):
    """Run the complete radar feature extraction pipeline."""
    import rasterio
    config = load_config(config_path)
    
    if radar_dir is None:
        radar_dir = config['data']['radar_dir']
    if output_dir is None:
        output_dir = Path(config['data']['output_dir']) / "radar"
    if candidate_mask_path is None:
        candidate_mask_path = Path(config['data']['output_dir']) / "illumination" / "candidate_region_mask.tif"
    
    logger.info(f"Loading candidate mask from {candidate_mask_path}")
    with rasterio.open(candidate_mask_path) as src:
        candidate_mask = src.read(1).astype(bool)
        meta = src.meta.copy()
    
    logger.info(f"Processing radar data from {radar_dir}")
    processor = MultiPassRadarProcessor(config)
    all_features = processor.process_all_passes(radar_dir, candidate_mask)
    
    logger.info("Computing repeat-pass consistency")
    consistency = processor.compute_repeat_pass_consistency(all_features)
    
    logger.info("Saving results")
    processor.save_features(consistency, meta, str(output_dir))
    
    return consistency


if __name__ == "__main__":
    run_radar_pipeline()