"""Fast smoke tests for core mathematical and planning components."""

from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from lunar_ice_detection.utils import compute_slope_aspect
from lunar_ice_detection.radar.radar_features import RadarProcessor
from lunar_ice_detection.fusion.fusion import FusionEngine
from lunar_ice_detection.volume.volume_estimation import DielectricMixingModel
from lunar_ice_detection.planning.planning import RoverTraversePlanner


def config():
    import yaml
    with open(Path(__file__).parents[1] / "config" / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_slope_flat_surface():
    slope, aspect = compute_slope_aspect(np.zeros((8, 8), dtype=np.float32), 5.0)
    assert np.allclose(slope, 0)
    assert aspect.shape == slope.shape


def test_radar_features_are_bounded():
    cfg = config()
    proc = RadarProcessor(cfg)
    shape = (8, 8)
    slc = {
        "HH": np.ones(shape, dtype=np.complex64),
        "HV": np.full(shape, 0.2, dtype=np.complex64),
        "VH": np.full(shape, 0.2, dtype=np.complex64),
        "VV": np.full(shape, 0.8, dtype=np.complex64),
    }
    features = proc.compute_polarimetric_features(slc)
    assert set(features) == {"cpr", "dop", "backscatter"}
    assert np.all((features["dop"] >= 0) & (features["dop"] <= 1))
    assert np.isfinite(features["cpr"]).all()


def test_fusion_respects_candidate_mask():
    cfg = config()
    engine = FusionEngine(cfg)
    mask = np.zeros((4, 4), dtype=bool)
    mask[1:3, 1:3] = True
    radar = {
        "radar_L_cpr_mean": np.full((4, 4), 2.0),
        "radar_L_dop_mean": np.full((4, 4), 0.1),
        "radar_L_backscatter_mean": np.full((4, 4), -5.0),
    }
    optical = {"ohrc_freshness_index": np.zeros((4, 4))}
    consistency = {"L": {"consistent_mask": mask}}
    result = engine.fuse_all(radar, optical, consistency, mask)
    assert np.all(result["ice_probability"][~mask] == 0)
    assert np.isfinite(result["ice_probability"]).all()


def test_maxwell_garnett_inversion_is_consistent():
    model = DielectricMixingModel(config())
    expected_fraction = 0.35
    effective = model.forward_model(expected_fraction, eps_host=3.0, eps_incl=3.15)
    recovered = model.invert_model(effective, eps_host=3.0, eps_incl=3.15)
    assert abs(recovered - expected_fraction) < 1e-4


def test_astar_finds_path_around_obstacle():
    planner = RoverTraversePlanner(config())
    grid = np.ones((10, 10), dtype=float)
    grid[4, 1:9] = np.inf
    path = planner.astar((1, 1), (8, 8), grid)
    assert path is not None
    assert path[0] == (1, 1)
    assert path[-1] == (8, 8)
    assert all(np.isfinite(grid[p]) for p in path)


if __name__ == "__main__":
    tests = [
        test_slope_flat_surface,
        test_radar_features_are_bounded,
        test_fusion_respects_candidate_mask,
        test_maxwell_garnett_inversion_is_consistent,
        test_astar_finds_path_around_obstacle,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} smoke tests passed")
