# Validation Report

## Execution Status

The end-to-end pipeline was executed against the synthetic demonstration dataset using `config/demo.yaml`.

- Illumination/candidate-region stage: **PASS**
- DFSAR radar feature stage: **PASS**
- OHRC morphology stage: **PASS**
- Multi-criteria fusion stage: **PASS**
- Dielectric volume estimation stage: **PASS**
- Landing-site ranking stage: **PASS**
- Rover traverse stage: **SAFE FAILURE** for this synthetic DEM because the selected target was separated by cells above the configured maximum rover slope; no unsafe path was emitted.

## Demonstration Outputs

- Doubly-shadowed candidate pixels: 13,283 / 16,384
- Ranked landing sites: 5
- Demonstration volume estimate: approximately 3.38 × 10⁴ m³
- Demonstration uncertainty range: approximately 2.36 × 10⁴–4.39 × 10⁴ m³

These values are synthetic-data outputs and are not scientific estimates for the Moon.

## Validation Methodology

### Repeat-pass consistency

The radar module computes, per pixel, the fraction of independent DFSAR passes satisfying the configured CPR and DOP criteria. The final fusion map retains only pixels meeting the configured agreement threshold.

### Literature cross-check

A real mission run should compare the retained candidate locations with independently published lunar polar radar candidates. This demonstration does not claim a literature match because it uses synthetic geometry and radar data.

### Dielectric sensitivity

The volume module samples the configured regolith and ice dielectric ranges and reports a propagated uncertainty interval. Maxwell–Garnett inversion uses a closed-form solution for performance and reproducibility.

## Important Scientific Limitations

1. The sample data is synthetic and only verifies software execution.
2. Real DFSAR data must preserve calibration, georeferencing, polarization conventions, and independent-pass metadata.
3. Real OHRC and DEM products may have different grids and must be co-registered/resampled before fusion.
4. Dielectric constants at lunar polar temperatures remain a model-domain assumption.
5. A successful software run is not evidence of lunar ice; scientific interpretation requires real data and expert review.
