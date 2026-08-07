# Lunar Command — Web Dashboard

Mission-control style web UI for the [Lunar Ice Detection](../README.md)
pipeline: dielectric/ice-probability overlay, crater depth profiling, hazard
log, and trajectory planning, backed by live pipeline outputs.

This folder is meant to live inside the `lunar_ice_detection` project (as
`lunar_ice_detection/ui`) — `server.ts` defaults to treating its parent
directory as the pipeline root.

## Run Locally

**Prerequisites:** Node.js, and the pipeline's Python deps installed
(`pip install -r ../requirements.txt`) if you want to use the "Run Pipeline"
button.

1. Install dependencies:
   `npm install`
2. (Optional) Copy `.env.example` to `.env.local` to set `GEMINI_API_KEY`
   (enables AI tactical analysis), or override `PIPELINE_DIR` / `PYTHON_BIN`
   if this folder isn't nested inside the pipeline project.
3. Run the app:
   `npm run dev`

Open `http://localhost:3000`.

## Pipeline bridge

`server.ts` exposes:

| Endpoint | Purpose |
|---|---|
| `GET /api/pipeline/status` | Whether the pipeline dir + outputs are found |
| `GET /api/pipeline/landing-sites` | `data/output/planning/landing_site_shortlist.geojson` |
| `GET /api/pipeline/volume-estimate` | `data/output/volume/volume_estimate.json` |
| `GET /api/pipeline/ice-probability-map.png` | Rendered PNG of the fused ice-probability raster |
| `POST /api/pipeline/run` | Runs `main.py` then `scripts/render_preview_png.py`, streaming logs back |

The React app (`src/App.tsx`) fetches these on load and after a pipeline run,
replacing the original demo/simulated telemetry with real fusion results.
