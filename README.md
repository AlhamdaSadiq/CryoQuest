**Team Name: AIS**

**Team Leader:  
Alhamda Sadiq | 25sadiqai@rbunagpur.in**

**Team Member 1:  
Siddhi Ade | 25adess@rbunagpur.in**

**Team Member 2:  
Riddhima Chachra | 25chachrar@rbunagpur.in**
#  
# Lunar Ice Detection System

### Detection and Characterization of Subsurface Ice in Lunar South Polar Regions Using Chandrayaan-2 Radar and Imagery Data for Landing Site and Rover Traverse Planning

## Overview

This system implements an end-to-end pipeline for detecting and characterizing subsurface ice in the lunar south polar regions using Chandrayaan-2 data.

## System Architecture

The system consists of six sequential, single-purpose stages:

1. **Geometric Illumination/Candidate-Region Module** (DEM + ephemeris only)
   - Identifies doubly-shadowed terrain using ray-tracing illumination model
   - Input: TMC-2 (5m) and OHRC-derived stereo DEM (sub-meter)
   - Output: Doubly-shadowed candidate mask

2. **Radar Feature Module** (DFSAR-derived)
   - Extracts CPR, DOP, and backscatter from L/S-band full-pol passes
   - Input: DFSAR data
   - Output: Radar features per pass

3. **Optical Morphology Module** (OHRC-derived)
   - Computes crater-freshness/roughness indicator
   - Input: OHRC imagery
   - Output: Freshness/roughness metrics

4. **Fusion, Volume-Estimation, and Path-Planning Module**
   - Multi-criteria weighted fusion (transparent scoring rule)
   - Repeat-pass consistency check
   - Ice-probability map and volume estimation (dielectric mixing model)
   - Landing-site ranking and rover traverse planning (A* search)
   - Input: All previous outputs
   - Output: Ice probability map, volume estimate, landing sites, traverse path

## Key Innovations

- **No Supervised Machine Learning**: Uses transparent physics-based scoring rule instead of black-box classifier due to lack of reliable training labels
- **Explicit False Positive Modeling**: Uses OHRC-derived freshness index as suppression term to distinguish ice-induced CPR>1 from fresh ejecta-induced CPR>1
- **Repeat-Pass Validation**: Uses internal consistency across independent DFSAR passes as ground-truth-free validation
- **Physics-Based Volume Estimation**: Employs Maxwell-Garnett dielectric mixing model with uncertainty propagation
- **Mission-Planning Outputs**: Provides ranked landing sites and A*-planned rover traverse

## Files and Directories

```
lunar_ice_detection/
├── config/
│   └── config.yaml              # Configuration parameters
├── data/
│   ├── dem/                     # Digital Elevation Models (TMC-2)
│   ├── ohrc/                    # OHRC imagery
│   ├── radar/                   # DFSAR L/S-band data (organized by pass/band)
│   └── output/                  # All outputs organized by processing stage
│       ├── illumination/        # DEM processing results
│       ├── radar/               # Radar feature extraction (L/, S/ subdirs)
│       ├── optical/             # OHRC morphology results
│       ├── fusion/              # Multi-criteria fusion outputs
│       ├── volume/              # Ice volume estimation
│       └── planning/            # Landing site & traverse planning
├── scripts/
│   ├── generate_sample_data.py  # Synthetic data generator for testing
│   └── render_preview_png.py    # Renders fusion_ice_probability.tif -> PNG for the web UI
├── ui/                          # Lunar Command web dashboard (React + Express)
│   ├── server.ts                # Express server + /api/pipeline/* bridge to this project
│   └── src/                     # React app (mission control, trajectory planner, hazards)
├── src/
│   └── lunar_ice_detection/     # Source code
│       ├── __init__.py
│       ├── main.py              # CLI entry point
│       ├── utils/               # Shared utilities
│       ├── dem/                 # DEM processing
│       │   └── illumination.py
│       ├── radar/               # Radar feature extraction
│       │   └── radar_features.py
│       ├── optical/             # OHRC processing
│       │   └── morphology.py
│       ├── fusion/              # Multi-criteria fusion
│       │   └── fusion.py
│       ├── volume/              # Volume estimation
│       │   └── volume_estimation.py
│       └── planning/            # Landing site & traverse planning
│           └── planning.py
├── docs/                        # Documentation
├── tests/                       # Unit tests
└── README.md
```

## Installation

### Prerequisites
- Python 3.8+
- Required packages: numpy, rasterio, scipy, scikit-image, pyyaml

### Setup
```bash
# Clone repository
git clone <repository-url>
cd lunar_ice_detection

# Install dependencies
pip install -r requirements.txt

# Generate sample data (optional, for testing)
python scripts/generate_sample_data.py

# Or place real Chandrayaan-2 data in the appropriate directories:
#   data/dem/tmc2_dem.tif
#   data/ohrc/ohrc_image.tif
#   data/radar/<pass>/<band>/*.tif
```

## Usage

### Run Complete Pipeline
```bash
python -m lunar_ice_detection.main
```

### Run Individual Stages
```bash
python -m lunar_ice_detection.main --stage illumination
python -m lunar_ice_detection.main --stage radar
python -m lunar_ice_detection.main --stage optical
python -m lunar_ice_detection.main --stage fusion
python -m lunar_ice_detection.main --stage volume
python -m lunar_ice_detection.main --stage planning
```

### Create Sample Data for Testing
```bash
python scripts/generate_sample_data.py
```

## Real Chandrayaan-2 Data Preview

Alongside the fully synthetic demo pipeline, `data/real_inputs/` bundles real
Chandrayaan-2 product previews so the dashboards have something authentic to
show without any manual setup:

- **DFSAR** CPR / SRD / TRT derived layers (`ch2_sar_ndxl_20250630...`)
- **OHRC** calibrated browse image (`ch2_ohr_ncp_20240812T1306075730...`)

Both `app.py` and the `ui/` web dashboard read this automatically — no
Downloads-folder path or extra config needed. Set `LUNAR_REAL_DATA_ROOT` if
you want to point at a different local copy of the ISRO product packages
instead (e.g. a larger, non-bundled download).

**Important:** these are raw instrument previews only. The fused
ice-probability, volume, and landing-site outputs elsewhere in this project
are generated from the *synthetic* sample dataset for demonstration, and
must not be presented as measured lunar ice findings — a real DEM, product
co-registration step, and a dedicated ISRO-product adapter are still
required to run the fusion pipeline on real data end-to-end.

## Web Dashboard (Lunar Command UI)

The `ui/` folder contains **Lunar Command** — a full mission-control style web
dashboard (React + Express) that connects directly to this pipeline. It reads
`data/output/` live (landing-site shortlist, volume estimate, fusion
ice-probability map rendered to PNG) and can trigger a full pipeline re-run
from the browser.

```bash
# from the lunar_ice_detection project root
pip install -r requirements.txt        # pipeline deps, if not already installed

cd ui
npm install
npm run dev
```

Open `http://localhost:3000`. No configuration needed — `ui/` defaults to
treating its parent folder as the pipeline root. If you've moved `ui/`
elsewhere, copy `ui/.env.example` to `ui/.env.local` and set `PIPELINE_DIR`
(and `PYTHON_BIN` if the pipeline deps live in a virtualenv) accordingly.

Optional: set `GEMINI_API_KEY` in `ui/.env.local` to enable the AI tactical
crater-analysis and diagnostics features; without it those fall back to
canned responses and the rest of the dashboard still works normally.

### Legacy Streamlit Dashboard

A lighter, Python-only dashboard (`app.py`) is also included:
```bash
PYTHONPATH=src streamlit run app.py
```
or double-click `Run Lunar Ice Detection UI.bat` on Windows. This has no
Node/npm dependency but lacks the Lunar Command UI's live pipeline-run
button and mission-control styling.

## Expected Outputs

Upon successful completion, the system generates:

1. **Ice Probability Map** (`data/output/fusion/fusion_ice_probability.tif`)
   - Per-pixel ice likelihood score [0-1]
   - Explicitly restricted to doubly-shadowed candidate region

2. **Radar Detection Framework** (`data/output/fusion/radar_detection_framework.md`)
   - Documented multi-criteria scoring rule with thresholds and weights
   - Physics-based justification for each term

3. **Landing Site Shortlist** (`data/output/planning/landing_site_shortlist.csv`)
   - Ranked candidate landing sites with scores and coordinates
   - GeoJSON version for mapping applications

4. **Rover Traverse Path** (`data/output/planning/rover_traverse_path.geojson`)
   - A*-planned path from best landing site to highest-confidence ice
   - Includes distance, slope, and hazard metrics

5. **Volume Estimate** (`data/output/volume/volume_estimate.json`)
   - Area-integrated ice volume for top ~5m regolith
   - Uncertainty range from dielectric constant variations
   - Human-readable summary in Markdown format

6. **Validation Report** (`docs/validation_report.md`)
   - Repeat-pass consistency statistics
   - Comparison with published literature candidates
   - Sensitivity analysis

## Scientific Basis

### Why No Machine Learning?
As stated in the problem?
- No reliable ground truth exists for lunar polar ice
- Trained models cannot be validated without labels
- Physically interpretable parameters enable expert review
- Internal repeat-pass validation provides ground-truth-free verification

### Key Algorithms

**Illumination Modeling**: Geometric ray-tracing over full lunar day using known solar ephemeris to compute cumulative illumination fraction and identify permanently shadowed regions.

**Radar Features**:
- **CPR** (Circular Polarization Ratio): >1 indicates same-sense circular polarization enhancement from volume scattering
- **DOP** (Degree of Polarization): <0.3 indicates depolarization from volume scattering vs. surface scattering
- **Backscatter**: Moderate-to-high values consistent with ice-containing regolith

**Optical Features**:
- **Local Variance**: Texture measure indicating roughness
- **Edge Density**: Canny edge detector output indicating blockiness
- **Boulder Density**: Threshold-based blob detection for fresh ejecta

**Fusion Score**: Weighted combination
```
Score = 0.35*CPR_score + 0.25*DOP_score + 0.20*Backscatter_score - 0.20*Freshness_suppression
```

**Repeat-Pass Validation**: Requires ice-likelihood criteria to be met in ≥60% of independent DFSAR passes.

**Volume Estimation**: Maxwell-Garnett dielectric mixing model:
```
ε_eff = ε_h * (1 + 3*f*β) / (1 - f*β)
where β = (ε_i - ε_h) / (ε_i + 2*ε_h)
```
Solved for ice fraction f with uncertainty propagation.

**Landing Site Ranking**: Weighted objective
```
Score = 0.40*Proximity + 0.30*Safety + 0.30*Illumination
```

**Traverse Planning**: A* search minimizing:
```
Cost = Distance + λ*Hazard - μ*IcePreference
```

## Validation Approach

1. **Internal Consistency**: Repeat-pass agreement statistic (fraction of pixels meeting criteria in ≥2 of N passes)
2. **Cross-Check**: Consistency with independently published candidate ice-bearing locations from lunar polar radar literature
3. **Sensitivity Analysis**: Volume estimate across literature range of regolith/ice dielectric constants

## Deliverables

1. **Technical Report**: This README plus generated documentation files
2. **Software**: This repository with sample data or instructions for real data
3. **Results**:
   - [Ice probability map](data/output/fusion/fusion_ice_probability.tif) (GeoTIFF)
   - [Radar detection framework](data/output/fusion/radar_detection_framework.md) (Markdown)
   - Landing site shortlist: [CSV](data/output/planning/landing_site_shortlist.csv) / [GeoJSON](data/output/planning/landing_site_shortlist.geojson)
   - Rover traverse path: [GeoJSON](data/output/planning/rover_traverse_path.geojson)
   - Volume estimate: [JSON](data/output/volume/volume_estimate.json) / [summary](data/output/volume/volume_estimate_summary.md)
   - [Documentation and validation report](docs/)

## Acknowledgements

- ISRO for providing Chandrayaan-2 data through the Bhuvan portal

## License

This software is released under the MIT License for educational and research purposes.

## Contact

For questions regarding this system, please open an issue in this repository.
