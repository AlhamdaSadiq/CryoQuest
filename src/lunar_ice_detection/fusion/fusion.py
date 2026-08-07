"""
Multi-Criteria Fusion and Ice-Probability Map Module.

Combines radar criteria (CPR>1, DOP below threshold) with freshness indicator
as explicit suppression term into one documented, weighted composite ice-likelihood
score. Uses transparent scoring rule (not trained classifier) because no reliable
labelled ice/non-ice training set exists.
"""

import numpy as np
import rasterio
from typing import Dict, Any, Tuple, Optional, List
from pathlib import Path
import logging
from ..utils import load_config, ensure_dir, normalize_array, clip_percentile

logger = logging.getLogger(__name__)


class FusionEngine:
    """Multi-criteria fusion for ice likelihood scoring."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        fusion_config = config['fusion']
        self.weights = fusion_config['weights']
        self.score_min = fusion_config['score_min']
        self.score_max = fusion_config['score_max']
        self.high_confidence_threshold = fusion_config['high_confidence_threshold']
        
        # Radar thresholds
        self.cpr_threshold = config['radar']['cpr_threshold']
        self.dop_threshold = config['radar']['dop_threshold']
        
    def load_features(self, feature_dirs: Dict[str, str]) -> Dict[str, np.ndarray]:
        """Load all feature maps from GeoTIFFs."""
        features = {}
        
        for name, dir_path in feature_dirs.items():
            dir_path = Path(dir_path)
            for tif_file in dir_path.glob("*.tif"):
                key = f"{name}_{tif_file.stem}"
                with rasterio.open(tif_file) as src:
                    features[key] = src.read(1)
                    if 'meta' not in features:
                        features['meta'] = src.meta.copy()
                        
        return features
    
    def compute_radar_score(self, cpr: np.ndarray, dop: np.ndarray, 
                            backscatter: np.ndarray) -> np.ndarray:
        """
        Compute radar component of ice-likelihood score.
        High CPR (>1) and low DOP indicate potential ice.
        """
        # CPR score: 1 when CPR > threshold, scaled above threshold
        cpr_score = np.where(cpr > self.cpr_threshold, 
                            np.clip((cpr - self.cpr_threshold) / (3.0 - self.cpr_threshold), 0, 1),
                            0)
        
        # DOP score: 1 when DOP < threshold (low polarization = volume scattering)
        dop_score = np.where(dop < self.dop_threshold,
                            np.clip((self.dop_threshold - dop) / self.dop_threshold, 0, 1),
                            0)
        
        # Backscatter score: moderate-high backscatter
        bs_clipped = clip_percentile(backscatter, 5, 95)
        bs_norm = normalize_array(bs_clipped)
        
        # Weighted radar score
        w = self.weights
        radar_score = (w['cpr'] * cpr_score + 
                      w['dop'] * dop_score + 
                      w['backscatter'] * bs_norm) / (w['cpr'] + w['dop'] + w['backscatter'])
        
        return radar_score
    
    def compute_freshness_suppression(self, freshness: np.ndarray) -> np.ndarray:
        """
        Compute freshness suppression term.
        High freshness = fresh blocky ejecta = CPR>1 false positive risk
        Suppression increases with freshness.
        """
        # Normalize freshness to [0, 1]
        fresh_norm = clip_percentile(freshness, 5, 95)
        fresh_norm = normalize_array(fresh_norm)
        
        # Suppression term (negative weight in config)
        suppression = fresh_norm
        return suppression
    
    def compute_composite_score(self, radar_score: np.ndarray, 
                                freshness_suppression: np.ndarray) -> np.ndarray:
        """
        Compute final composite ice-likelihood score.
        Score = radar_score + w_freshness * freshness_suppression
        (where w_freshness is negative)
        """
        w_fresh = self.weights.get('freshness_suppression', -0.2)
        
        composite = radar_score + w_fresh * freshness_suppression
        
        # Clip to valid range
        composite = np.clip(composite, self.score_min, self.score_max)
        
        return composite
    
    def apply_consistency_filter(self, composite_score: np.ndarray,
                                 consistency_masks: Dict[str, np.ndarray],
                                 band: str = 'L') -> np.ndarray:
        """
        Apply repeat-pass consistency filter.
        Only retain pixels where consistency mask is True for the primary band.
        """
        if band in consistency_masks:
            consistent = consistency_masks[band]['consistent_mask'].astype(bool)
            filtered = np.where(consistent, composite_score, 0)
            return filtered
        return composite_score
    
    def compute_confidence_levels(self, score: np.ndarray) -> np.ndarray:
        """Classify score into confidence levels."""
        confidence = np.zeros_like(score, dtype=np.uint8)
        confidence[score >= self.high_confidence_threshold] = 3  # High
        confidence[(score >= 0.5) & (score < self.high_confidence_threshold)] = 2  # Medium
        confidence[(score > 0) & (score < 0.5)] = 1  # Low
        # 0 = no ice likelihood / outside candidate region
        return confidence
    
    def fuse_all(self, radar_features: Dict[str, np.ndarray],
                 optical_features: Dict[str, np.ndarray],
                 consistency_masks: Dict[str, np.ndarray],
                 candidate_mask: np.ndarray,
                 primary_band: str = 'L') -> Dict[str, np.ndarray]:
        """
        Run complete fusion pipeline.
        """
        # Extract required features (use primary band, typically L-band for penetration)
        cpr_key = f"radar_{primary_band}_cpr_mean"
        dop_key = f"radar_{primary_band}_dop_mean"
        bs_key = f"radar_{primary_band}_backscatter_mean"
        fresh_key = "ohrc_freshness_index"
        
        # Handle missing keys gracefully
        cpr = radar_features.get(cpr_key, np.zeros_like(candidate_mask, dtype=float))
        dop = radar_features.get(dop_key, np.zeros_like(candidate_mask, dtype=float))
        backscatter = radar_features.get(bs_key, np.zeros_like(candidate_mask, dtype=float))
        freshness = optical_features.get(fresh_key, np.zeros_like(candidate_mask, dtype=float))
        
        # Apply candidate mask
        cpr = np.where(candidate_mask, cpr, 0)
        dop = np.where(candidate_mask, dop, 1)  # High DOP outside = no ice
        backscatter = np.where(candidate_mask, backscatter, 0)
        freshness = np.where(candidate_mask, freshness, 1)  # High freshness outside = suppress
        
        logger.info("Computing radar score...")
        radar_score = self.compute_radar_score(cpr, dop, backscatter)
        
        logger.info("Computing freshness suppression...")
        suppression = self.compute_freshness_suppression(freshness)
        
        logger.info("Computing composite score...")
        composite = self.compute_composite_score(radar_score, suppression)
        
        logger.info("Applying repeat-pass consistency filter...")
        composite = self.apply_consistency_filter(composite, consistency_masks, primary_band)
        
        logger.info("Computing confidence levels...")
        confidence = self.compute_confidence_levels(composite)
        
        results = {
            'ice_probability': composite.astype(np.float32),
            'confidence_level': confidence,
            'radar_score': radar_score.astype(np.float32),
            'freshness_suppression': suppression.astype(np.float32),
            'cpr': cpr.astype(np.float32),
            'dop': dop.astype(np.float32),
            'backscatter': backscatter.astype(np.float32),
            'freshness': freshness.astype(np.float32)
        }
        
        return results
    
    def save_results(self, results: Dict[str, np.ndarray], meta: Dict, 
                     output_dir: str):
        """Save fusion results as GeoTIFFs."""
        ensure_dir(output_dir)
        
        for name, data in results.items():
            out_path = Path(output_dir) / f"fusion_{name}.tif"
            meta_out = meta.copy()
            meta_out.update(dtype='float32' if data.dtype == np.float32 else 'uint8', count=1)
            with rasterio.open(out_path, 'w', **meta_out) as dst:
                dst.write(data, 1)
            logger.info(f"Saved {out_path}")
    
    def generate_framework_document(self, output_path: str):
        """Generate the documented multi-criteria radar detection framework."""
        doc = f"""# Multi-Criteria Radar Detection Framework for Lunar Subsurface Ice

## Overview
This document describes the transparent, physics-based scoring framework used to 
detect subsurface ice in lunar south polar permanently shadowed regions using 
Chandrayaan-2 DFSAR data. No supervised machine learning is used because no 
reliable labelled ice/non-ice training set exists for this terrain.

## Detection Criteria

### 1. Circular Polarization Ratio (CPR)
- **Threshold**: CPR > {self.cpr_threshold}
- **Physics**: CPR > 1 indicates same-sense circular polarization enhancement, 
  characteristic of volume scattering from subsurface ice or fresh blocky ejecta
- **Score contribution**: Weight = {self.weights['cpr']}
- **Normalization**: Linear ramp from threshold to CPR=3.0

### 2. Degree of Polarization (DOP)
- **Threshold**: DOP < {self.dop_threshold}
- **Physics**: Low DOP indicates depolarization from volume scattering, 
  distinguishing ice from surface scattering (which preserves polarization)
- **Score contribution**: Weight = {self.weights['dop']}
- **Normalization**: Linear ramp from threshold to DOP=0

### 3. Total Backscatter (σ⁰)
- **Physics**: Moderate-to-high backscatter consistent with volume scattering
- **Score contribution**: Weight = {self.weights['backscatter']}
- **Normalization**: Percentile-clipped (5th-95th) and normalized to [0,1]

### 4. Freshness/Roughness Suppression (Critical)
- **Physics**: Fresh blocky ejecta from young craters produces CPR>1 with NO ice 
  (known false positive mechanism)
- **Implementation**: OHRC-derived freshness index (local variance + edge density + 
  boulder density) used as explicit suppression term
- **Weight**: {self.weights['freshness_suppression']} (negative = suppression)
- **Rationale**: This is the key innovation - explicitly modelling the primary 
  false positive mechanism rather than hoping a classifier learns it

## Composite Ice-Likelihood Score

```
Score = w_cpr * CPR_score + w_dop * DOP_score + w_bs * BS_score + w_fresh * Freshness_suppression
```

Where:
- w_cpr = {self.weights['cpr']}
- w_dop = {self.weights['dop']}
- w_bs = {self.weights['backscatter']}
- w_fresh = {self.weights['freshness_suppression']}

Score range: [{self.score_min}, {self.score_max}]

## Repeat-Pass Consistency Validation

- **Requirement**: Ice-likelihood criteria must be met consistently across 
  independent DFSAR passes
- **Minimum passes**: {self.config['radar']['min_passes']}
- **Agreement threshold**: {self.config['radar']['agreement_threshold']*100:.0f}% of passes
- **Implementation**: Per-pixel agreement fraction computed, thresholded
- **No external ground truth needed**: Real subsurface signature repeats; 
  noise-driven false positives generally do not

## Confidence Levels

- **High (3)**: Score ≥ {self.high_confidence_threshold}
- **Medium (2)**: 0.5 ≤ Score < {self.high_confidence_threshold}
- **Low (1)**: 0 < Score < 0.5
- **None (0)**: Score = 0 (outside candidate region or failed consistency)

## Why No Supervised Classifier?

1. **No reliable labels**: No ground truth ice maps exist for lunar PSRs
2. **Unvalidatable**: A trained model without labels cannot be validated
3. **Interpretability**: Transparent scoring rule allows expert review of each term
4. **Physics-based**: Each term has clear physical justification
5. **Internal validation**: Repeat-pass consistency provides ground-truth-free validation

## References

- Multi-parameter lunar radar studies (CPR-DOP joint analysis)
- Maxwell-Garnett dielectric mixing for volume estimation
- Chandrayaan-2 DFSAR L/S-band full-pol specifications
"""
        with open(output_path, 'w') as f:
            f.write(doc)
        logger.info(f"Framework document saved to {output_path}")


def run_fusion_pipeline(config_path: str = "config/config.yaml",
                        radar_dir: Optional[str] = None,
                        optical_dir: Optional[str] = None,
                        candidate_mask_path: Optional[str] = None,
                        output_dir: Optional[str] = None):
    """Run the complete fusion pipeline."""
    import rasterio
    config = load_config(config_path)
    
    if radar_dir is None:
        radar_dir = Path(config['data']['output_dir']) / "radar"
    if optical_dir is None:
        optical_dir = Path(config['data']['output_dir']) / "optical"
    if output_dir is None:
        output_dir = Path(config['data']['output_dir']) / "fusion"
    if candidate_mask_path is None:
        candidate_mask_path = Path(config['data']['output_dir']) / "illumination" / "candidate_region_mask.tif"
    
    logger.info(f"Loading candidate mask from {candidate_mask_path}")
    with rasterio.open(candidate_mask_path) as src:
        candidate_mask = src.read(1).astype(bool)
        meta = src.meta.copy()
    
    # Load radar features (consistency maps)
    radar_features = {}
    consistency_masks = {}
    
    for band in config['radar']['bands']:
        band_dir = Path(radar_dir) / band
        if band_dir.exists():
            for tif_file in band_dir.glob("*.tif"):
                key = f"radar_{band}_{tif_file.stem.replace(f'radar_{band}_', '')}"
                with rasterio.open(tif_file) as src:
                    radar_features[key] = src.read(1)
                    if 'consistent_mask' in tif_file.stem:
                        consistency_masks[band] = {
                            'consistent_mask': src.read(1)
                        }
    
    # Load optical features
    optical_features = {}
    for tif_file in Path(optical_dir).glob("*.tif"):
        key = f"ohrc_{tif_file.stem.replace('ohrc_', '')}"
        with rasterio.open(tif_file) as src:
            optical_features[key] = src.read(1)
    
    logger.info("Running multi-criteria fusion...")
    engine = FusionEngine(config)
    results = engine.fuse_all(radar_features, optical_features, consistency_masks, candidate_mask)
    
    logger.info("Saving fusion results...")
    engine.save_results(results, meta, str(output_dir))
    
    logger.info("Generating framework document...")
    engine.generate_framework_document(str(Path(output_dir) / "radar_detection_framework.md"))
    
    return results


if __name__ == "__main__":
    run_fusion_pipeline()