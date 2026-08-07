"""Render a PNG preview of the fused ice-probability raster.

This lets any downstream UI (e.g. a web dashboard) display the fusion output
without needing a GeoTIFF/rasterio stack of its own -- it just serves the PNG.

Usage:
    python scripts/render_preview_png.py [--config config/config.yaml]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_detection.utils import load_config  # noqa: E402


def render_ice_probability_png(tif_path: Path, out_path: Path, size: int = 900) -> None:
    with rasterio.open(tif_path) as src:
        arr = src.read(1).astype("float64")

    mn, mx = float(np.nanmin(arr)), float(np.nanmax(arr))
    norm = np.clip((arr - mn) / (mx - mn + 1e-9), 0, 1)

    # Dark navy (low) -> cyan/white (high) "ice" colormap.
    r = np.clip(1.4 * norm - 0.2, 0, 1)
    g = np.clip(1.3 * norm, 0, 1)
    b = np.clip(0.35 + 0.75 * norm, 0, 1)
    rgb = (np.stack([r, g, b], axis=-1) * 255).astype("uint8")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb, "RGB").resize((size, size), Image.NEAREST).save(out_path)
    print(f"Wrote {out_path} (source range {mn:.4f}-{mx:.4f})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(ROOT / "config" / "config.yaml"))
    args = parser.parse_args()

    config = load_config(args.config)
    output_dir = ROOT / config["data"]["output_dir"]
    tif_path = output_dir / "fusion" / "fusion_ice_probability.tif"
    out_path = output_dir / "fusion" / "fusion_ice_probability_preview.png"

    if not tif_path.exists():
        raise SystemExit(f"Missing {tif_path} -- run the fusion stage first.")

    render_ice_probability_png(tif_path, out_path)


if __name__ == "__main__":
    main()
