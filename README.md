# 🌑 Lunar Ice Detection & Characterization — Chandrayaan-2

**PS-8: Detection & Characterization of Subsurface Ice in Lunar South Polar Regions Using Chandrayaan-2 Radar and Imagery Data**

A transparent, physics-based pipeline that fuses illumination geometry, dual-frequency radar, and optical imagery from Chandrayaan-2 to map subsurface water ice in the Moon's permanently shadowed south-polar craters — **no black-box ML anywhere in the loop.**

---

## The Problem

Water ice in the Moon's permanently shadowed south-polar craters is a critical resource for future crewed missions (water, oxygen, fuel) — but it can't be photographed directly. It has to be *inferred* by fusing several imperfect signals into one defensible answer.

## Why Not Machine Learning?

No reliable **labelled** ice/non-ice dataset exists for this terrain, so a trained classifier would be unvalidatable. Instead, every stage below is a transparent, physically grounded rule — a judge can trace exactly why any pixel scored the way it did.

## The Pipeline

| # |            Stage           |                                                       Does                                                               |
|---|----------------------------|--------------------------------------------------------------------------------------------------------------------------|
| 1 |         Illumination       | Ray-traces the Sun over a full cycle (DEM + ephemeris) to flag *doubly-shadowed* terrain — the target-region definition. |
| 2 |        Radar Features      | DFSAR L/S-band: Circular Polarization Ratio (CPR) and Degree of Polarization (DOP) per pass — ice shows anomalous CPR>1. |
| 3 |      Optical Freshness     | OHRC texture/edge analysis flags fresh, blocky ejecta — the known cause of false CPR>1 positives.                        |
| 4 |           Fusion           | Combines the shadow mask + radar criteria + freshness suppression into one documented, weighted ice-likelihood score.    |
| 5 | Repeat-Pass Check + Volume | Keeps only pixels consistent across independent passes; converts probability to ice volume via a Maxwell-Garnett         |                          | dielectric mixing model (top ~5 m, with uncertainty range).                                                              |
| 6 |    Landing & Traverse      | Ranks landing sites by ice proximity, slope safety, and illumination; plans a rover path with A* search.                 |
|

**Architecture:** four sequential modules — 
    illumination  →  radar  →  optical  →  fusion/volume/path-planning — each single-purpose and independently interpretable. (IIRS was excluded: it needs light, so it can't see inside the shadowed target terrain.)

## Validation (no ground truth needed)

- **Repeat-pass agreement** across independent radar passes (primary check)
- **Literature cross-check** against published candidate ice sites
- **Sensitivity analysis** — volume reported as a range across plausible dielectric constants, not a false-precision number

## Deliverables

Ice-probability map · documented radar detection framework · ranked landing-site shortlist · rover traverse path · ice-volume estimate with uncertainty range.

## Two UIs, One Backend

	            Streamlit ( app.py , :8501)	  Lunar Command ( ui/ , React
                                                    +Express, :3000)
    Purpose 	Raw scientific inspection	Polished mission-control demo view


Both read live from the same `data/output/` — nothing duplicated or mocked. (A few flavor elements like the mission clock and battery % are cosmetic and documented as such; the science-critical outputs — ice map, dielectric constant, landing sites, volume — are all real.)

## Running It

```bash
# Terminal 1 — pipeline + Streamlit
pip install -r requirements.txt
python -m streamlit run app.py        # http://localhost:8501

# Terminal 2 — Lunar Command UI
cd ui && npm install && npm run dev   # http://localhost:3000
```
Click **Run Pipeline** in either UI to re-run `main.py` live; both dashboards update together. The illumination stage is slow (~10+ min) — show pre-generated outputs first, then trigger a live re-run to prove it's real.

## Key Assumptions

- Multi-pass DFSAR coverage exists over candidate craters (single-pass pixels are flagged lower-confidence, not excluded).
- Published regolith/ice dielectric constants are representative of actual south-polar conditions.
- The classical freshness detector is a simplification, refinable once real OHRC tiles are inspected at scale.

**On skipping ML:** a learned model without reliable labels isn't actually higher-performing — it's unvalidatable. An interpretable, physics-based rule with repeat-pass validation is the more defensible choice given the data that genuinely exists today.
