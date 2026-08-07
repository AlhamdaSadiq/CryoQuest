# Lunar Ice Detection — Judge Package

## Run the working system

1. Extract this ZIP.
2. Double-click **Run UI.bat**.
3. Open `http://localhost:8502` if the browser does not open automatically.
4. Click **Run Demo Pipeline** in the sidebar if you want to regenerate the outputs.

## What to show

- **Real ISRO Data**: real Chandrayaan-2 DFSAR CPR/SRD/TRT preview layers and OHRC browse image.
- **Demo Ice Map**: complete end-to-end synthetic demonstration output.
- **Landing Sites**: ranked candidate sites.
- **Volume**: model estimate and uncertainty.
- **Run Log**: execution trace.

## Scientific labeling

The DFSAR/OHRC preview layers are derived from real Chandrayaan-2 products found in the developer's downloaded ISRO product packages. The end-to-end fused probability, volume, and planning outputs in this package are synthetic-data demonstration outputs. They must not be presented as measured lunar ice findings. A real DEM, product co-registration, and a dedicated ISRO-product adapter are still required for a scientific real-data fusion run.

## Offline fallback

The synthetic dataset and generated outputs are included, so the UI works without internet access or satellite downloads. Python 3.10+ is recommended.
