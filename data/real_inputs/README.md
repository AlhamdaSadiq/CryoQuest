# Real-data input location

The repository includes a complete synthetic dataset so the UI and demo pipeline run on another computer without downloading satellite archives.

For real Chandrayaan-2 products, either:

1. Copy the extracted product folders below this directory, preserving their names:

```text
data/real_inputs/
├── ch2_sar_ndxl_20250630mpcpspeast_d_fp_xxx/
└── ch2_ohr_ncp_20240812T1306075730_d_img_d18/
```

2. Or set the environment variable `LUNAR_REAL_DATA_ROOT` to the folder containing those two product directories.

The application expects the DFSAR derived CPR/SRD/TRT GeoTIFFs and the OHRC product browse image. The raw OHRC `.img` and large DFSAR archives are deliberately not committed to GitHub because they exceed practical repository limits. The real-data tab remains available and reports missing inputs when they are not installed.

The tracked demo outputs and synthetic inputs are not real lunar measurements and must be labeled as synthetic in presentations.
