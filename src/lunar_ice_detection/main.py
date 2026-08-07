"""
Main CLI and Pipeline Orchestration for Lunar Ice Detection System.

This module provides a command-line interface to run the complete end-to-end
pipeline or individual stages of the lunar subsurface ice detection system.
"""

import argparse
import sys
import os
from pathlib import Path
import logging
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lunar_ice_detection.dem.illumination import run_illumination_pipeline
from lunar_ice_detection.radar.radar_features import run_radar_pipeline
from lunar_ice_detection.optical.morphology import run_optical_pipeline
from lunar_ice_detection.fusion.fusion import run_fusion_pipeline
from lunar_ice_detection.volume.volume_estimation import run_volume_pipeline
from lunar_ice_detection.planning.planning import run_planning_pipeline
from lunar_ice_detection.utils import load_config, ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lunar_ice_detection.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def setup_directories(config_path: str = "config/config.yaml"):
    """Create necessary directory structure."""
    config = load_config(config_path)
    
    dirs_to_create = [
        config['data']['dem_dir'],
        config['data']['radar_dir'],
        config['data']['ohrc_dir'],
        config['data']['output_dir'],
        os.path.join(config['data']['output_dir'], "illumination"),
        os.path.join(config['data']['output_dir'], "radar", "L"),
        os.path.join(config['data']['output_dir'], "radar", "S"),
        os.path.join(config['data']['output_dir'], "optical"),
        os.path.join(config['data']['output_dir'], "fusion"),
        os.path.join(config['data']['output_dir'], "volume"),
        os.path.join(config['data']['output_dir'], "planning"),
        "docs",
        "scripts",
        "tests"
    ]
    
    for dir_path in dirs_to_create:
        ensure_dir(dir_path)
        logger.info(f"Ensured directory exists: {dir_path}")


def run_complete_pipeline(config_path: str = "config/config.yaml"):
    """Run the complete end-to-end pipeline."""
    logger.info("=" * 60)
    logger.info("STARTING COMPLETE LUNAR ICE DETECTION PIPELINE")
    logger.info("=" * 60)
    
    try:
        # Stage 1: DEM processing and illumination modelling
        logger.info("\nStage 1: DEM Processing and Illumination Modelling")
        logger.info("-" * 50)
        illumination_results, candidate_mask_path = run_illumination_pipeline(config_path)
        
        # Stage 2: Radar feature extraction
        logger.info("\nStage 2: DFSAR Radar Feature Extraction")
        logger.info("-" * 50)
        radar_results = run_radar_pipeline(config_path)
        
        # Stage 3: OHRC optical processing
        logger.info("\nStage 3: OHRC Optical Morphology Processing")
        logger.info("-" * 50)
        optical_results = run_optical_pipeline(config_path)
        
        # Stage 4: Multi-criteria fusion
        logger.info("\nStage 4: Multi-Criteria Fusion and Ice-Likelihood Scoring")
        logger.info("-" * 50)
        fusion_results = run_fusion_pipeline(config_path)
        
        # Stage 5: Volume estimation
        logger.info("\nStage 5: Ice Volume Estimation")
        logger.info("-" * 50)
        volume_results = run_volume_pipeline(config_path)
        
        # Stage 6: Landing site and traverse planning
        logger.info("\nStage 6: Landing Site Ranking and Rover Traverse Planning")
        logger.info("-" * 50)
        planning_results = run_planning_pipeline(config_path)
        
        logger.info("\n" + "=" * 60)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"Results saved to: {Path(config_path).parent / 'data' / 'output'}")
        
        # Print summary
        print_summary(volume_results, planning_results)
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)


def run_stage(stage: str, config_path: str = "config/config.yaml"):
    """Run an individual pipeline stage."""
    logger.info(f"Running stage: {stage}")
    
    stage_functions = {
        'illumination': run_illumination_pipeline,
        'radar': run_radar_pipeline,
        'optical': run_optical_pipeline,
        'fusion': run_fusion_pipeline,
        'volume': run_volume_pipeline,
        'planning': run_planning_pipeline
    }
    
    if stage not in stage_functions:
        logger.error(f"Unknown stage: {stage}")
        logger.info(f"Available stages: {list(stage_functions.keys())}")
        sys.exit(1)
    
    try:
        result = stage_functions[stage](config_path)
        logger.info(f"Stage '{stage}' completed successfully")
        return result
    except Exception as e:
        logger.error(f"Stage '{stage}' failed with error: {e}", exc_info=True)
        sys.exit(1)


def print_summary(volume_results: dict, planning_results: list):
    """Print a summary of the pipeline results."""
    print("\n" + "=" * 60)
    print("LUNAR ICE DETECTION SYSTEM - RESULTS SUMMARY")
    print("=" * 60)
    
    if volume_results:
        print(f"\nICE VOLUME ESTIMATE:")
        print(f"  Total Volume: {volume_results.get('total_volume_m3', 0):.2e} m³")
        print(f"  Uncertainty Range: {volume_results.get('total_volume_range_m3', [0, 0])[0]:.2e} - "
              f"{volume_results.get('total_volume_range_m3', [0, 0])[1]:.2e} m³")
        print(f"  Area: {volume_results.get('total_area_m2', 0):.2e} m²")
        print(f"  Mean Ice Fraction: {volume_results.get('mean_ice_fraction', 0):.3f}")
        print(f"  Valid Pixels: {volume_results.get('n_pixels', 0)}")
    
    if planning_results:
        print(f"\nLANDING SITE RANKING:")
        print(f"  Top {len(planning_results)} candidate sites identified")
        if planning_results:
            best = planning_results[0]
            print(f"  Best Site (Rank #{best['rank']}):")
            print(f"    Location: {best['latitude']:.4f}° N, {best['longitude']:.4f}° E")
            print(f"    Score: {best['score']:.3f}")
            print(f"    Distance to Ice: {best['distance_to_ice_m']:.0f} m")
            print(f"    Slope: {best['slope_degrees']:.1f}°")
            print(f"    Illumination: {best['illumination_fraction']*100:.1f}%")
    
    print(f"\nOUTPUT FILES:")
    print(f"  Ice Probability Map: data/output/fusion/fusion_ice_probability.tif")
    print(f"  Landing Site Shortlist: data/output/planning/landing_site_shortlist.csv")
    print(f"  Rover Traverse Path: data/output/planning/rover_traverse_path.geojson")
    print(f"  Volume Estimate: data/output/volume/volume_estimate.json")
    print(f"  Radar Detection Framework: data/output/fusion/radar_detection_framework.md")
    print(f"  Landing Site Selection Doc: data/output/planning/landing_site_selection.md")
    
    print("\n" + "=" * 60)


def create_sample_data(config_path: str = "config/config.yaml"):
    """Create sample data for testing and demonstration."""
    logger.info("Creating sample data for demonstration...")
    
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin
    
    config = load_config(config_path)
    
    # Create sample DEM (TMC-2 5m resolution)
    dem_dir = Path(config['data']['dem_dir'])
    ensure_dir(dem_dir)
    
    # Simple crater-like DEM for south pole region
    height, width = 1000, 1000
    dem = np.full((height, width), -100.0, dtype=np.float32)  # Baseline elevation
    
    # Add a circular crater (doubly shadowed candidate)
    center_y, center_x = height // 2, width // 2
    radius = 100  # pixels
    for i in range(height):
        for j in range(width):
            dist = np.sqrt((i - center_y)**2 + (j - center_x)**2)
            if dist < radius:
                # Crater shape: parabolic depression
                depth = -50.0 * (1 - (dist/radius)**2)
                dem[i, j] += depth
    
    # Add some boulders (bright spots)
    np.random.seed(42)
    for _ in range(50):
        y, x = np.random.randint(0, height, 2), np.random.randint(0, width, 2)
        dem[y, x] += np.random.uniform(5, 15)  # Boulders
    
    # Save DEM
    transform = from_origin(-1000, 1000, 5, 5)  # 5m/pixel
    meta = {
        'driver': 'GTiff',
        'dtype': 'float32',
        'nodata': None,
        'width': width,
        'height': height,
        'count': 1,
        'crs': 'EPSG:32612',  # UTM zone 12N (approximate for lunar)
        'transform': transform
    }
    
    dem_path = dem_dir / "tmc2_dem.tif"
    with rasterio.open(dem_path, 'w', **meta) as dst:
        dst.write(dem, 1)
    logger.info(f"Created sample DEM: {dem_path}")
    
    # Create sample OHRC image (0.5m resolution)
    ohrc_dir = Path(config['data']['ohrc_dir'])
    ensure_dir(ohrc_dir)
    
    # Simulate OHRC image with texture
    ohrc_height, ohrc_width = height * 10, width * 10  # 10x resolution
    ohrc_image = np.random.normal(100, 20, (ohrc_height, ohrc_width)).astype(np.float32)
    
    # Add crater pattern
    for i in range(ohrc_height):
        for j in range(ohrc_width):
            dist = np.sqrt((i - center_y*10)**2 + (j - center_x*10)**2)
            if dist < radius*10:
                # Darker in crater shadow
                ohrc_image[i, j] *= 0.7
    
    # Add boulders as bright spots
    for _ in range(200):
        y, x = np.random.randint(0, ohrc_height, 2), np.random.randint(0, ohrc_width, 2)
        ohrc_image[y, x] += np.random.uniform(50, 100)
    
    # Save OHRC
    ohrc_transform = from_origin(-1000, 1000, 0.5, 0.5)  # 0.5m/pixel
    ohrc_meta = meta.copy()
    ohrc_meta.update({
        'width': ohrc_width,
        'height': ohrc_height,
        'transform': ohrc_transform
    })
    
    ohrc_path = ohrc_dir / "ohrc_image.tif"
    with rasterio.open(ohrc_path, 'w', **ohrc_meta) as dst:
        dst.write(ohrc_image, 1)
    logger.info(f"Created sample OHRC image: {ohrc_path}")
    
    # Create sample radar data (L and S band)
    radar_dir = Path(config['data']['radar_dir'])
    ensure_dir(radar_dir)
    
    # Create two passes for repeat-pass consistency
    for pass_id in ['pass1', 'pass2']:
        pass_dir = radar_dir / pass_id
        ensure_dir(pass_dir)
        
        for band in ['L', 'S']:
            band_dir = pass_dir / band
            ensure_dir(band_dir)
            
            # Create dummy SLC data (complex)
            # In reality, these would be complex GeoTIFFs
            # For demo, we'll create simple amplitude data
            slc_height, slc_width = height // 2, width // 2  # Lower resolution
            
            # Create polarimetric channels with ice-like signature in crater
            HH = np.random.exponential(10, (slc_height, slc_width)).astype(np.complex64)
            HV = np.random.exponential(5, (slc_height, slc_width)).astype(np.complex64)
            VH = HV.copy()  # Reciprocity
            VV = np.random.exponential(8, (slc_height, slc_width)).astype(np.complex64)
            
            # Enhance returns in crater region for ice-like signature
            for i in range(slc_height):
                for j in range(slc_width):
                    orig_i, orig_j = i*2, j*2  # Map back to full res
                    if orig_i < height and orig_j < width:
                        dist = np.sqrt((orig_i - center_y)**2 + (orig_j - center_x)**2)
                        if dist < radius:
                            # Ice-like enhancement: more volume scattering
                            HH[i, j] *= (1.5 + 0.5j)  # Enhanced same-pol
                            VV[i, j] *= (1.3 + 0.3j)
                            HV[i, j] *= (2.0 + 1.0j)  # Much enhanced cross-pol (volume scattering)
                            VH[i, j] = HV[i, j].copy()
            
            # Save as simple amplitude (for demo - real data would be complex)
            # We'll save the real part as placeholder
            for pol_name, pol_data in [('HH', HH), ('HV', HV), ('VH', VH), ('VV', VV)]:
                amp = np.abs(pol_data).astype(np.float32)
                # Simple GeoTIFF
                pol_meta = meta.copy()
                pol_meta.update({
                    'width': slc_width,
                    'height': slc_height,
                    'transform': from_origin(-1000, 1000, 10, 10),  # 10m/pixel for radar
                    'dtype': 'float32'
                })
                
                pol_path = band_dir / f"{pol_name}.tif"
                with rasterio.open(pol_path, 'w', **pol_meta) as dst:
                    dst.write(amp, 1)
    
    logger.info(f"Created sample radar data in: {radar_dir}")
    
    # Create sample data manifest
    manifest_path = Path(config['data']['output_dir']) / "SAMPLE_DATA_README.md"
    with open(manifest_path, 'w') as f:
        f.write(f"""# Sample Data for Lunar Ice Detection System

This directory contains synthetically generated sample data for testing and demonstration
of the lunar ice detection pipeline. The data mimics:

- TMC-2 DEM: 5 m resolution regional digital elevation model
- OHRC Imagery: 0.5 m resolution stereo-derived image  
- DFSAR Radar: L-band and S-band full-polarimetric SLC data (2 passes)

## Data Structure

```
data/
├── dem/
│   └── tmc2_dem.tif              # TMC-2 5m DEM
├── ohrc/
│   └── ohrc_image.tif            # OHRC 0.5m image
├── radar/
│   ├── pass1/
│   │   ├── L/
│   │   │   ├── HH.tif
│   │   │   ├── HV.tif
│   │   │   ├── VH.tif
│   │   │   └── VV.tif
│   │   └── S/
│   │       ├── HH.tif
│   │       ├── HV.tif
│   │       ├── VH.tif
│   │       └── VV.tif
│   └── pass2/
│       ├── L/
│       │   ├── HH.tif
│       │   ├── HV.tif
│       │   ├── VH.tif
│       │   └── VV.tif
│       └── S/
│           ├── HH.tif
│           ├── HV.tif
│           ├── VH.tif
│           └── VV.tif
└── output/
    ├── illumination/
    ├── radar/
    ├── optical/
    ├── fusion/
    ├── volume/
    └── planning/
```

## Notes
- The sample data contains a circular crater feature with ice-like radar signatures
- This is for demonstration purposes only - real mission data would be substituted
- To run with real data, replace the sample files with actual Chandrayaan-2 datasets
""")
    
    logger.info("Sample data creation completed")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Lunar Ice Detection System - End-to-end pipeline for detecting "
                    "subsurface ice in lunar south polar regions using Chandrayaan-2 data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline
  python -m lunar_ice_detection.main

  # Run individual stages
  python -m lunar_ice_detection.main --stage illumination
  python -m lunar_ice_detection.main --stage radar
  python -m lunar_ice_detection.main --stage optical
  python -m lunar_ice_detection.main --stage fusion
  python -m lunar_ice_detection.main --stage volume
  python -m lunar_ice_detection.main --stage planning

  # Create sample data for testing
  python -m lunar_ice_detection.main --create-samples

  # Show configuration
  python -m lunar_ice_detection.main --show-config
        """
    )
    
    parser.add_argument(
        '--config', 
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )
    
    parser.add_argument(
        '--stage',
        choices=['illumination', 'radar', 'optical', 'fusion', 'volume', 'planning'],
        help='Run individual pipeline stage'
    )
    
    parser.add_argument(
        '--create-samples',
        action='store_true',
        help='Create sample data for testing and demonstration'
    )
    
    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Show current configuration and exit'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Ensure config directory exists
    config_dir = Path(args.config).parent
    ensure_dir(str(config_dir))
    
    # Create default config if it doesn't exist
    if not Path(args.config).exists():
        logger.info(f"Creating default configuration at {args.config}")
        # Config is created by the setup() function called below
    
    if args.show_config:
        if Path(args.config).exists():
            config = load_config(args.config)
            print("Current Configuration:")
            print("=" * 50)
            import yaml
            print(yaml.dump(config, default_flow_style=False))
        else:
            print(f"Configuration file not found: {args.config}")
            print("Run without --show-config to create default config")
        return
    
    if args.create_samples:
        create_sample_data(args.config)
        return
    
    # Setup directories
    setup_directories(args.config)
    
    if args.stage:
        # Run individual stage
        run_stage(args.stage, args.config)
    else:
        # Run complete pipeline
        run_complete_pipeline(args.config)


if __name__ == "__main__":
    main()