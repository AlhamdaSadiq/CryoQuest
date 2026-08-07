"""Build a judge-ready portable ZIP with real-data preview layers."""
from pathlib import Path
import shutil
import zipfile

import rasterio

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = Path.home() / "Downloads"
real_sar = DOWNLOADS / "ch2_sar_ndxl_20250630mpcpspeast_d_fp_xxx" / "data" / "derived" / "20250630"
real_ohrc = DOWNLOADS / "ch2_ohr_ncp_20240812T1306075730_d_img_d18"
package_real_sar = ROOT / "data" / "real_inputs" / "ch2_sar_ndxl_20250630mpcpspeast_d_fp_xxx" / "data" / "derived" / "20250630"
package_real_ohrc = ROOT / "data" / "real_inputs" / "ch2_ohr_ncp_20240812T1306075730_d_img_d18" / "browse" / "calibrated" / "20240812"

sar_names = {
    "ch2_sar_ndxl_20250630mpcpspeast_d_cpr_xx_fp_xx_xxx.tif": "cpr",
    "ch2_sar_ndxl_20250630mpcpspeast_d_srd_xx_fp_xx_xxx.tif": "srd",
    "ch2_sar_ndxl_20250630mpcpspeast_d_trt_xx_fp_xx_xxx.tif": "trt",
}

for filename, label in sar_names.items():
    source = real_sar / filename
    destination = package_real_sar / filename
    if not source.exists():
        print(f"SKIP missing real product: {source}")
        continue
    with rasterio.open(source) as src:
        scale = min(1.0, 700 / max(src.width, src.height))
        height = max(1, int(src.height * scale))
        width = max(1, int(src.width * scale))
        data = src.read(1, out_shape=(1, height, width), masked=True)
        transform = src.transform * src.transform.scale(src.width / width, src.height / height)
        profile = src.profile.copy()
        profile.update(height=height, width=width, transform=transform, compress="deflate", tiled=False)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(destination, "w", **profile) as dst:
            dst.write(data.filled(src.nodata if src.nodata is not None else 0), 1)
    print(f"WROTE real {label} preview: {destination}")

browse = real_ohrc / "browse" / "calibrated" / "20240812" / "ch2_ohr_ncp_20240812T1306075730_b_brw_d18.png"
if browse.exists():
    package_real_ohrc.mkdir(parents=True, exist_ok=True)
    shutil.copy2(browse, package_real_ohrc / browse.name)
    print(f"WROTE real OHRC browse preview: {package_real_ohrc / browse.name}")

readme = ROOT / "JUDGE_README.md"
readme.write_text("""# Lunar Ice Detection — Judge Package

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
""", encoding="utf-8")

archive = Path.home() / "Desktop" / "Lunar Ice Detection - Judge Submission.zip"
if archive.exists():
    archive.unlink()
exclude_parts = {".git", "__pycache__", ".pytest_cache"}
exclude_suffixes = {".log", ".pyc"}
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in exclude_parts for part in relative.parts):
            continue
        if path.suffix.lower() in exclude_suffixes:
            continue
        output.write(path, Path("Lunar Ice Detection") / relative)
print(f"JUDGE_ARCHIVE={archive}")
print(f"JUDGE_ARCHIVE_BYTES={archive.stat().st_size}")
