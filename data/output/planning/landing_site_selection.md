# Landing Site Selection for Lunar Ice Exploration

## Selection Criteria

Landing sites are ranked by a weighted combination of three factors:

1. **Proximity to Ice** (40% weight)
   - Distance to nearest high-confidence, repeat-pass-validated ice cell
   - Closer = better (lander must be near ice for efficient access)
   - Lander must sit on illuminated ground adjacent to shadowed ice target

2. **Slope Safety** (30% weight)
   - Maximum allowable slope: 15.0°
   - Score = 1 - (slope / max_slope) for slope ≤ max_slope, else 0
   - Ensures safe landing and egress for rover deployment

3. **Illumination** (30% weight)
   - Minimum illumination fraction: 70%
   - Score = illumination / min_illumination (capped at 1.0)
   - Lander requires solar power; ice target is in permanent shadow

## Top 5 Candidate Landing Sites

### Rank 1
- **Location**: -177.4000° N, 27.5000° E
- **Overall Score**: 0.934
- **Component Scores**:
  - Proximity to Ice: 0.917
  - Slope Safety: 0.889 (slope: 1.7°)
  - Illumination: 1.000 (fraction: 1.000)
- **Distance to Nearest Ice**: 5 m
- **Ice Probability at Site**: 0.000
- **Confidence Level**: 0 (0=none, 1=low, 2=medium, 3=high)

### Rank 2
- **Location**: -557.4000° N, 372.5000° E
- **Overall Score**: 0.917
- **Component Scores**:
  - Proximity to Ice: 0.917
  - Slope Safety: 0.834 (slope: 2.5°)
  - Illumination: 1.000 (fraction: 1.000)
- **Distance to Nearest Ice**: 5 m
- **Ice Probability at Site**: 0.000
- **Confidence Level**: 0 (0=none, 1=low, 2=medium, 3=high)

### Rank 3
- **Location**: -97.4000° N, 22.5000° E
- **Overall Score**: 0.880
- **Component Scores**:
  - Proximity to Ice: 0.751
  - Slope Safety: 0.933 (slope: 1.0°)
  - Illumination: 1.000 (fraction: 1.000)
- **Distance to Nearest Ice**: 15 m
- **Ice Probability at Site**: 0.000
- **Confidence Level**: 0 (0=none, 1=low, 2=medium, 3=high)

### Rank 4
- **Location**: -172.4000° N, 252.5000° E
- **Overall Score**: 0.867
- **Component Scores**:
  - Proximity to Ice: 0.814
  - Slope Safety: 0.804 (slope: 2.9°)
  - Illumination: 1.000 (fraction: 1.000)
- **Distance to Nearest Ice**: 11 m
- **Ice Probability at Site**: 0.000
- **Confidence Level**: 0 (0=none, 1=low, 2=medium, 3=high)

### Rank 5
- **Location**: -112.4000° N, 147.5000° E
- **Overall Score**: 0.852
- **Component Scores**:
  - Proximity to Ice: 0.834
  - Slope Safety: 0.729 (slope: 4.1°)
  - Illumination: 1.000 (fraction: 1.000)
- **Distance to Nearest Ice**: 10 m
- **Ice Probability at Site**: 0.000
- **Confidence Level**: 0 (0=none, 1=low, 2=medium, 3=high)

## Selection Rationale

The top-ranked site (#1) provides the optimal balance:
- Close enough to ice for efficient rover traverse (< 5 m)
- Sufficiently flat for safe landing (slope: 1.7° < 15.0°)
- Adequately illuminated for power generation (100.0% > 70%)

## Constraints and Assumptions

1. Lander must be outside doubly-shadowed regions (requires illumination)
2. Rover must be able to descend from lander and ascend back to landing site
3. Traverse planning assumes rover can handle slopes up to 20.0°
4. Ice access requires staying within or near validated ice-probability regions
