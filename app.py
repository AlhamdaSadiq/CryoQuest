"""Streamlit dashboard for the Lunar Ice Detection System."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import rasterio
import streamlit as st
from PIL import Image

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "data" / "output"
CONFIG = ROOT / "config" / "demo.yaml"
DOWNLOADS = Path.home() / "Downloads"
# Prefer the real Chandrayaan-2 product previews bundled with this project
# (data/real_inputs/); fall back to a Downloads folder for local dev setups
# where the raw ISRO product packages were downloaded but not copied in.
REAL_ROOT = Path(os.environ.get("LUNAR_REAL_DATA_ROOT", str(ROOT / "data" / "real_inputs")))
if not REAL_ROOT.exists():
    REAL_ROOT = DOWNLOADS
REAL_SAR = REAL_ROOT / "ch2_sar_ndxl_20250630mpcpspeast_d_fp_xxx" / "data" / "derived" / "20250630"
REAL_OHRC = REAL_ROOT / "ch2_ohr_ncp_20240812T1306075730_d_img_d18"

st.set_page_config(page_title="Lunar Ice Detection System", page_icon="🌑", layout="wide")
st.markdown("""
<style>
body, .stApp { background:#050505; color:#e5e5e5; }
.block-container { padding:1.25rem 2rem 3rem; max-width:1600px; }
[data-testid="stSidebar"] { background:#090909; border-right:1px solid #1f1f1f; }
[data-testid="stSidebar"] .block-container { padding:1.4rem 1rem; }
.hero { padding:1.35rem 1.6rem; border:1px solid #252525; border-radius:20px; background:linear-gradient(135deg,#0f0f0f,#151515); color:#f4f4f4; margin-bottom:1rem; box-shadow:0 0 30px rgba(30,95,180,.08); }
.hero h1 { margin:0; font-size:2.15rem; letter-spacing:-.04em; }
.hero p { margin:.5rem 0 0; color:#8f98a3; font-size:.98rem; }
.hero-meta { margin-top:1rem; display:flex; gap:.55rem; flex-wrap:wrap; color:#8f98a3; font:700 .72rem ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.08em; }
.hero-meta span { padding:.35rem .55rem; border:1px solid #2a2a2a; border-radius:999px; background:#0b0b0b; }
.hero-meta .live { color:#6ba8ff; border-color:#24528c; }
.metric-card { background:#0f0f0f; border:1px solid #222; border-radius:18px; padding:1rem 1.1rem; min-height:98px; transition:.2s ease; }
.metric-card:hover { border-color:#3b82f6; box-shadow:0 0 22px rgba(59,130,246,.12); }
.metric-card h2 { margin:.25rem 0; font-size:1.55rem; letter-spacing:-.04em; color:#f2f2f2; }
.small { color:#78818b; font-size:.75rem; font-family:ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.03em; }
.real-badge { background:#0d211d; border:1px solid #237a60; color:#9ee6c8; padding:.8rem 1rem; border-radius:12px; font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }
.demo-badge { background:#21190c; border:1px solid #936b24; color:#f4d28a; padding:.8rem 1rem; border-radius:12px; font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }
[data-testid="stMetric"] { background:#0f0f0f; border:1px solid #222; border-radius:16px; padding:.85rem; }
button[kind="primary"] { background:#2563eb !important; border:1px solid #4b8cff !important; }
div[data-baseweb="tab-list"] { gap:.35rem; border-bottom:1px solid #222; }
button[data-baseweb="tab"] { color:#7d8792; font-weight:700; letter-spacing:.02em; }
button[data-baseweb="tab"][aria-selected="true"] { color:#75aaff; }
.stPlotlyChart, [data-testid="stDataFrame"] { border:1px solid #222; border-radius:18px; overflow:hidden; background:#0b0b0b; }
code, pre { background:#0b0b0b !important; border:1px solid #222; }
.section-label { color:#6b7280; font:700 .7rem ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.12em; text-transform:uppercase; }
</style>
""", unsafe_allow_html=True)


def output_path(relative: str) -> Path:
    return OUTPUT / relative


def has_demo_results() -> bool:
    return output_path("fusion/fusion_ice_probability.tif").exists()


def read_raster(relative: str):
    with rasterio.open(OUTPUT / relative) as src:
        return src.read(1), src.transform


def read_real_raster(path: Path, max_size: int = 700):
    """Read a downsampled view so the 626 MB ISRO mosaic is not loaded fully."""
    with rasterio.open(path) as src:
        scale = min(1.0, max_size / max(src.width, src.height))
        out_h = max(1, int(src.height * scale))
        out_w = max(1, int(src.width * scale))
        array = src.read(1, out_shape=(1, out_h, out_w), masked=True)
        meta = {
            "width": src.width, "height": src.height, "count": src.count,
            "dtype": src.dtypes[0], "resolution_m": src.res[0],
            "crs": str(src.crs), "bounds": tuple(round(v, 2) for v in src.bounds),
            "nodata": src.nodata,
        }
    return np.asarray(array.filled(np.nan), dtype=float), meta


def plot_array(array: np.ndarray, title: str, colorscale: str = "IceFire", label: str = "Value"):
    finite = np.nan_to_num(array, nan=0.0, posinf=0.0, neginf=0.0)
    fig = go.Figure(go.Heatmap(z=finite, colorscale=colorscale, colorbar=dict(title=label)))
    fig.update_layout(title=title, height=540, margin=dict(l=10, r=10, t=50, b=10), yaxis_autorange="reversed")
    return fig


def run_pipeline() -> tuple[bool, str]:
    command = [sys.executable, "-m", "lunar_ice_detection.main", "--config", str(CONFIG)]
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=900)
    return result.returncode == 0, (result.stdout + "\n" + result.stderr)[-12000:]


st.markdown("""
<div class="hero">
<h1>🌑 LUNAR COMMAND / ICE OPS</h1>
<p>Chandrayaan-2 DFSAR + OHRC south-polar analysis, landing-site selection, and rover traverse planning.</p>
<div class="hero-meta"><span class="live">● SYSTEM ONLINE</span><span>SECTOR: SOUTH POLAR</span><span>MODE: INSPECT / PRESENT</span><span>DATA: REAL + DEMO LABELLED</span></div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Mission Control")
    st.caption("Chandrayaan-2 DFSAR + OHRC · South Polar Ice Detection")
    st.link_button("🌐 Open Lunar Command Web Dashboard", "http://localhost:3000", width="stretch")
    if st.button("▶ Run Demo Pipeline", type="primary", width="stretch"):
        with st.spinner("Running six-stage synthetic demonstration pipeline…"):
            ok, log = run_pipeline()
        st.session_state["pipeline_log"] = log
        if ok:
            st.success("Demo pipeline completed")
            st.rerun()
        else:
            st.error("Pipeline failed")
            st.code(log)
    st.divider()
    st.markdown("**Stages**")
    st.markdown("1. Illumination and shadow mask\n2. DFSAR radar features\n3. OHRC freshness\n4. Transparent fusion\n5. Ice volume\n6. Landing and rover planning")
    st.divider()
    st.caption(f"Project: `{ROOT}`")

real_cpr = REAL_SAR / "ch2_sar_ndxl_20250630mpcpspeast_d_cpr_xx_fp_xx_xxx.tif"
real_srd = REAL_SAR / "ch2_sar_ndxl_20250630mpcpspeast_d_srd_xx_fp_xx_xxx.tif"
real_trt = REAL_SAR / "ch2_sar_ndxl_20250630mpcpspeast_d_trt_xx_fp_xx_xxx.tif"
real_ohrc_browse = REAL_OHRC / "browse" / "calibrated" / "20240812" / "ch2_ohr_ncp_20240812T1306075730_b_brw_d18.png"
real_data_available = real_cpr.exists() and real_srd.exists() and real_trt.exists()

if not has_demo_results():
    st.warning("No demo outputs found. Run the Demo Pipeline from the sidebar.")

volume = {}
volume_file = output_path("volume/volume_estimate.json")
if volume_file.exists():
    volume = json.loads(volume_file.read_text(encoding="utf-8"))

if has_demo_results():
    probability, _ = read_raster("fusion/fusion_ice_probability.tif")
    confidence, _ = read_raster("fusion/fusion_confidence_level.tif")
    mask, _ = read_raster("illumination/candidate_region_mask.tif")
    cards = st.columns(4)
    values = [
        ("Candidate pixels", f"{np.count_nonzero(mask):,}", "demo doubly-shadowed terrain"),
        ("High-confidence cells", f"{np.count_nonzero(confidence >= 3):,}", "demo repeat-pass score"),
        ("Medium-confidence cells", f"{np.count_nonzero(confidence == 2):,}", "requires expert review"),
        ("Estimated ice volume", f"{volume.get('total_volume_m3', 0):,.0f} m³", "demo top-5 m model scope"),
    ]
    for col, (label, value, detail) in zip(cards, values):
        col.markdown(f'<div class="metric-card"><div class="small">{label}</div><h2>{value}</h2><div class="small">{detail}</div></div>', unsafe_allow_html=True)

st.write("")
tabs = st.tabs(["🛰 Real ISRO Data", "🧊 Demo Ice Map", "🚀 Landing Sites", "📊 Volume", "🛠 Run Log"])

with tabs[0]:
    st.markdown('<div class="real-badge"><b>REAL DATA FOUND ON THIS COMPUTER</b><br>These are official-looking Chandrayaan-2 product files found in Downloads. They are shown separately from the synthetic demo outputs.</div>', unsafe_allow_html=True)
    st.write("")
    if not real_data_available:
        st.error(f"DFSAR products not found at {REAL_SAR}")
    else:
        st.subheader("Chandrayaan-2 DFSAR L4 Mosaic")
        st.code(str(REAL_SAR), language="text")
        real_tabs = st.tabs(["CPR", "SRD", "TRT", "Metadata"])
        for tab, path, title, scale, label in [
            (real_tabs[0], real_cpr, "Real DFSAR Circular Polarization Ratio (CPR)", "IceFire", "CPR"),
            (real_tabs[1], real_srd, "Real DFSAR Single-bounce Eigenvalue Relative Difference (SRD)", "Viridis", "SRD"),
            (real_tabs[2], real_trt, "Real DFSAR T-Ratio (TRT)", "Plasma", "TRT"),
        ]:
            with tab:
                try:
                    array, meta = read_real_raster(path)
                    st.plotly_chart(plot_array(array, title, scale, label), width="stretch")
                    st.caption(f"{path.name} · downsampled display {array.shape[1]}×{array.shape[0]} · source raster {meta['width']}×{meta['height']} at {meta['resolution_m']} m/pixel")
                    st.caption(f"Source file remains available locally at: {path}")
                except Exception as exc:
                    st.error(f"Could not display {path.name}: {exc}")
        with real_tabs[3]:
            _, meta = read_real_raster(real_cpr, max_size=50)
            st.json(meta)
            st.info("This derived mosaic contains CPR/SRD/TRT products. It is not raw complex HH/HV/VH/VV SLC input, so the software must not relabel SRD as DOP.")
    st.subheader("Real OHRC product")
    st.code(str(REAL_OHRC), language="text")
    if real_ohrc_browse.exists():
        st.image(str(real_ohrc_browse), caption="Official OHRC browse image from the downloaded product", width="stretch")
    st.warning("The calibrated OHRC .img is a 1.2 GB PDS4 raw image. It requires XML-guided conversion and cropping before the morphology module can process it safely.")

with tabs[1]:
    if has_demo_results():
        st.markdown('<div class="demo-badge"><b>SYNTHETIC DEMONSTRATION OUTPUT</b><br>These maps are generated from sample data and must not be presented as measured lunar ice.</div>', unsafe_allow_html=True)
        st.plotly_chart(plot_array(probability, "Composite Ice-Likelihood Probability — Demo", "IceFire", "Score"), width="stretch")
        c1, c2, c3 = st.columns(3)
        c1.metric("Peak probability", f"{float(np.nanmax(probability)):.3f}")
        c2.metric("Mean probability", f"{float(np.nanmean(probability)):.3f}")
        c3.metric("Candidate coverage", f"{np.count_nonzero(mask) / probability.size:.1%}")
    else:
        st.info("Run the demo pipeline to generate outputs.")

with tabs[2]:
    sites_file = output_path("planning/landing_site_shortlist.csv")
    if sites_file.exists():
        sites = pd.read_csv(sites_file)
        st.dataframe(sites, width="stretch", hide_index=True)
    else:
        st.info("Run the pipeline to generate landing-site results.")
    traverse = output_path("planning/rover_traverse_path.geojson")
    if traverse.exists():
        st.download_button("Download rover traverse GeoJSON", traverse.read_bytes(), "rover_traverse_path.geojson", "application/geo+json")
    else:
        st.warning("No safe traverse was emitted for the current synthetic terrain under the configured slope constraints.")

with tabs[3]:
    if volume:
        a, b = st.columns(2)
        a.metric("Demo total volume", f"{volume['total_volume_m3']:,.0f} m³")
        b.metric("Demo uncertainty", f"±{volume['total_volume_uncertainty_m3']:,.0f} m³")
        st.json(volume)
    fraction_file = output_path("volume/ice_fraction_map.tif")
    if fraction_file.exists():
        fraction, _ = read_raster("volume/ice_fraction_map.tif")
        st.plotly_chart(plot_array(fraction, "Estimated Volumetric Ice Fraction — Demo", "Blues", "Fraction"), width="stretch")

with tabs[4]:
    st.code(st.session_state.get("pipeline_log", "No pipeline run in this UI session."), language="text")
    st.caption("The real-data tab is for presentation and inspection. Scientific fusion requires the DEM, co-registration, and a dedicated adapter for the ISRO product formats.")
