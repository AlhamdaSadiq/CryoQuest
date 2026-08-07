"""
Landing-Site Ranking and Rover Traverse Planning Module.

Ranks candidate landing sites by a weighted objective combining:
- Proximity to high-confidence, repeat-pass-validated ice cells
- Local slope below a stated safe-traverse threshold  
- Sufficient periodic illumination at the landing point itself

Computes a rover traverse from the selected site to the highest-confidence ice cells
via a weighted shortest-path search (A*) over a cost grid combining slope, boulder-hazard 
density, and a penalty for leaving the validated ice-probability region.
"""

import numpy as np
import rasterio
import heapq
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path
import logging
import csv
import json
from ..utils import load_config, ensure_dir, compute_slope_aspect, haversine_distance

logger = logging.getLogger(__name__)


class LandingSiteRanker:
    """Rank candidate landing sites based on multiple criteria."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        plan_config = config['planning']
        self.weights = plan_config['landing_weights']
        self.max_slope = plan_config['max_slope_degrees']
        self.min_illumination = plan_config['min_illumination_fraction']
        self.search_radius = plan_config['search_radius_meters']
        self.top_n = plan_config['top_n_sites']
        
    def load_ice_probability(self, prob_path: str) -> Tuple[np.ndarray, Dict]:
        """Load ice probability map."""
        with rasterio.open(prob_path) as src:
            prob = src.read(1)
            meta = src.meta.copy()
            transform = src.transform
            resolution = src.res[0]
        return prob, meta, transform, resolution
    
    def load_slope_map(self, dem_path: str, fallback_shape: Tuple[int, int]) -> np.ndarray:
        """Load or compute slope map from DEM."""
        try:
            with rasterio.open(dem_path) as src:
                dem = src.read(1)
                slope, _ = compute_slope_aspect(dem, src.res[0])
                return slope
        except:
            # If DEM not available, return zeros (flat terrain assumption)
            logger.warning("DEM not available for slope calculation, assuming flat terrain")
            return np.zeros(fallback_shape)
    
    def load_illumination_map(self, illum_path: str, fallback_shape: Tuple[int, int]) -> np.ndarray:
        """Load illumination fraction map."""
        try:
            with rasterio.open(illum_path) as src:
                return src.read(1)
        except:
            logger.warning("Illumination map not available, assuming full illumination")
            return np.ones(fallback_shape)
    
    def find_candidate_pixels(self, ice_prob: np.ndarray, 
                            confidence: np.ndarray) -> np.ndarray:
        """Find high-confidence ice pixels for landing site scoring."""
        # High confidence (level 3) or medium confidence (level 2)
        high_conf = (confidence >= 2) & (ice_prob > 0.5)
        return high_conf
    
    def compute_distance_transform(self, binary_mask: np.ndarray, 
                                 resolution: float) -> np.ndarray:
        """Compute distance to nearest True pixel in binary mask."""
        from scipy.ndimage import distance_transform_edt
        # Distance in pixels, convert to meters
        distance_pix = distance_transform_edt(~binary_mask)
        distance_m = distance_pix * resolution
        return distance_m
    
    def rank_landing_sites(self, ice_prob: np.ndarray, confidence: np.ndarray,
                          dem_path: str, illum_path: str,
                          output_dir: str) -> List[Dict]:
        """
        Rank landing sites based on weighted objective.
        Returns list of top N sites with scores and coordinates.
        """
        logger.info("Loading data for landing site ranking...")
        
        # Load required maps
        slope = self.load_slope_map(dem_path, ice_prob.shape)
        illumination = self.load_illumination_map(illum_path, ice_prob.shape)
        
        # Find ice-containing pixels (targets for proximity)
        ice_pixels = self.find_candidate_pixels(ice_prob, confidence)
        
        # The probability map is already loaded as an array; use the DEM
        # metadata for pixel scale and geographic coordinates.
        with rasterio.open(dem_path) as src:
            resolution = src.res[0]
            transform = src.transform
        distance_to_ice = self.compute_distance_transform(ice_pixels, resolution)
        
        # Normalize criteria to [0, 1] where 1 is best
        # 1. Proximity to ice (closer = better)
        max_dist = np.nanmax(distance_to_ice)
        if max_dist > 0:
            proximity_score = 1 - (distance_to_ice / max_dist)
        else:
            proximity_score = np.ones_like(distance_to_ice)
        
        # 2. Slope safety (lower slope = better)
        slope_score = np.where(slope <= self.max_slope, 
                              1 - (slope / self.max_slope), 0)
        slope_score = np.clip(slope_score, 0, 1)
        
        # 3. Illumination (more illumination = better)
        illumination_score = np.clip(illumination / self.min_illumination, 0, 1)
        
        # Combined weighted score
        w = self.weights
        total_score = (w['ice_proximity'] * proximity_score +
                      w['slope_safety'] * slope_score +
                      w['illumination'] * illumination_score)
        
        # Apply masks: must be outside ice region (lander needs illuminated ground)
        # and must meet minimum thresholds
        valid_landing = (ice_prob == 0) & (slope <= self.max_slope) & (illumination >= self.min_illumination)
        
        # Set invalid sites to zero score
        total_score = np.where(valid_landing, total_score, 0)
        
        # Find top N sites
        flat_scores = total_score.flatten()
        top_indices = np.argsort(flat_scores)[::-1][:self.top_n]
        
        # Convert to 2D coordinates
        height, width = total_score.shape
        top_sites = []
        
        for idx in top_indices:
            row = idx // width
            col = idx % width
            if total_score[row, col] > 0:  # Valid site
                # Get geographic coordinates
                lon, lat = rasterio.transform.xy(transform, row, col)
                
                site_info = {
                    'rank': len(top_sites) + 1,
                    'row': int(row),
                    'col': int(col),
                    'latitude': float(lat),
                    'longitude': float(lon),
                    'score': float(total_score[row, col]),
                    'proximity_score': float(proximity_score[row, col]),
                    'slope_score': float(slope_score[row, col]),
                    'illumination_score': float(illumination_score[row, col]),
                    'distance_to_ice_m': float(distance_to_ice[row, col]),
                    'slope_degrees': float(slope[row, col]),
                    'illumination_fraction': float(illumination[row, col]),
                    'ice_probability': float(ice_prob[row, col]),
                    'confidence_level': int(confidence[row, col])
                }
                top_sites.append(site_info)
        
        logger.info(f"Ranked {len(top_sites)} valid landing sites")
        return top_sites
    
    def save_landing_sites(self, sites: List[Dict], output_dir: str):
        """Save landing site rankings as CSV and GeoJSON."""
        ensure_dir(output_dir)
        
        # Save as CSV
        csv_path = Path(output_dir) / "landing_site_shortlist.csv"
        if sites:
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=sites[0].keys())
                writer.writeheader()
                writer.writerows(sites)
        logger.info(f"Saved landing site shortlist to {csv_path}")
        
        # Save as GeoJSON for mapping
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        for site in sites:
            feature = {
                "type": "Feature",
                "properties": {
                    "rank": site['rank'],
                    "score": site['score'],
                    "distance_to_ice_m": site['distance_to_ice_m'],
                    "slope_degrees": site['slope_degrees'],
                    "illumination_fraction": site['illumination_fraction']
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [site['longitude'], site['latitude']]
                }
            }
            geojson["features"].append(feature)
        
        geojson_path = Path(output_dir) / "landing_site_shortlist.geojson"
        with open(geojson_path, 'w') as f:
            json.dump(geojson, f, indent=2)
        logger.info(f"Saved landing site shortlist to {geojson_path}")
    
    def generate_planning_document(self, sites: List[Dict], output_path: str):
        """Generate documentation for landing site selection."""
        doc = f"""# Landing Site Selection for Lunar Ice Exploration

## Selection Criteria

Landing sites are ranked by a weighted combination of three factors:

1. **Proximity to Ice** ({self.config['planning']['landing_weights']['ice_proximity']*100:.0f}% weight)
   - Distance to nearest high-confidence, repeat-pass-validated ice cell
   - Closer = better (lander must be near ice for efficient access)
   - Lander must sit on illuminated ground adjacent to shadowed ice target

2. **Slope Safety** ({self.config['planning']['landing_weights']['slope_safety']*100:.0f}% weight)
   - Maximum allowable slope: {self.config['planning']['max_slope_degrees']}°
   - Score = 1 - (slope / max_slope) for slope ≤ max_slope, else 0
   - Ensures safe landing and egress for rover deployment

3. **Illumination** ({self.config['planning']['landing_weights']['illumination']*100:.0f}% weight)
   - Minimum illumination fraction: {self.config['planning']['min_illumination_fraction']*100:.0f}%
   - Score = illumination / min_illumination (capped at 1.0)
   - Lander requires solar power; ice target is in permanent shadow

## Top {len(sites)} Candidate Landing Sites

"""
        for site in sites:
            doc += f"""### Rank {site['rank']}
- **Location**: {site['latitude']:.4f}° N, {site['longitude']:.4f}° E
- **Overall Score**: {site['score']:.3f}
- **Component Scores**:
  - Proximity to Ice: {site['proximity_score']:.3f}
  - Slope Safety: {site['slope_score']:.3f} (slope: {site['slope_degrees']:.1f}°)
  - Illumination: {site['illumination_score']:.3f} (fraction: {site['illumination_fraction']:.3f})
- **Distance to Nearest Ice**: {site['distance_to_ice_m']:.0f} m
- **Ice Probability at Site**: {site['ice_probability']:.3f}
- **Confidence Level**: {site['confidence_level']} (0=none, 1=low, 2=medium, 3=high)

"""
        
        doc += f"""## Selection Rationale

The top-ranked site (#{sites[0]['rank'] if sites else 'N/A'}) provides the optimal balance:
- Close enough to ice for efficient rover traverse (< {sites[0]['distance_to_ice_m']:.0f} m)
- Sufficiently flat for safe landing (slope: {sites[0]['slope_degrees']:.1f}° < {self.config['planning']['max_slope_degrees']}°)
- Adequately illuminated for power generation ({sites[0]['illumination_fraction']*100:.1f}% > {self.config['planning']['min_illumination_fraction']*100:.0f}%)

## Constraints and Assumptions

1. Lander must be outside doubly-shadowed regions (requires illumination)
2. Rover must be able to descend from lander and ascend back to landing site
3. Traverse planning assumes rover can handle slopes up to {self.config['planning']['traverse']['max_slope_degrees']}°
4. Ice access requires staying within or near validated ice-probability regions
"""
        
        with open(output_path, 'w') as f:
            f.write(doc)
        logger.info(f"Landing site planning document saved to {output_path}")


class RoverTraversePlanner:
    """Plan rover traverse using A* search."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        traverse_config = config['planning']['traverse']
        self.max_slope = traverse_config['max_slope_degrees']
        self.hazard_weight = traverse_config['hazard_penalty_weight']
        self.ice_region_penalty = traverse_config['ice_region_penalty']
        self.grid_resolution = traverse_config['grid_resolution']  # meters
        
    def load_cost_layers(self, dem_path: str, ohrc_path: str, 
                        ice_prob_path: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Load or compute cost layers for traverse planning."""
        # Slope cost
        with rasterio.open(dem_path) as src:
            dem = src.read(1)
            slope, _ = compute_slope_aspect(dem, src.res[0])
            slope_cost = np.where(slope <= self.max_slope, 
                                 slope / self.max_slope,  # Normalized cost
                                 np.inf)  # Inf cost for unsafe slopes
        
        # Hazard cost (boulder density from OHRC)
        try:
            with rasterio.open(ohrc_path) as src:
                boulder_density = src.read(1)
                # Normalize hazard cost
                hazard_cost = np.clip(boulder_density, 0, 1)
        except:
            logger.warning("OHRC boulder density not available, assuming low hazard")
            with rasterio.open(dem_path) as src:
                shape = src.shape
            hazard_cost = np.zeros(shape)
        
        # Ice region preference (bonus for staying in validated ice zones)
        with rasterio.open(ice_prob_path) as src:
            ice_prob = src.read(1)
            # Negative cost (bonus) for being in ice region
            ice_cost = -np.clip(ice_prob, 0, 1) * 0.5  # Max -0.5 bonus
        
        return slope_cost, hazard_cost, ice_cost
    
    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Manhattan distance heuristic for A*."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def get_neighbors(self, pos: Tuple[int, int], shape: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get valid 8-connected neighbors."""
        neighbors = []
        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                if di == 0 and dj == 0:
                    continue
                ni, nj = pos[0] + di, pos[1] + dj
                if 0 <= ni < shape[0] and 0 <= nj < shape[1]:
                    neighbors.append((ni, nj))
        return neighbors
    
    def astar(self, start: Tuple[int, int], goal: Tuple[int, int],
              cost_grid: np.ndarray) -> Optional[List[Tuple[int, int]]]:
        """
        A* search for shortest path.
        Returns list of (row, col) tuples from start to goal, or None if no path.
        """
        if np.isinf(cost_grid[start]) or np.isinf(cost_grid[goal]):
            logger.warning("Start or goal is in impassable terrain")
            return None
        
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == goal:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path
            
            for neighbor in self.get_neighbors(current, cost_grid.shape):
                # Check if neighbor is traversable
                if np.isinf(cost_grid[neighbor]):
                    continue
                
                tentative_g = g_score[current] + cost_grid[neighbor]
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        logger.warning("No path found from start to goal")
        return None
    
    def plan_traverse(self, start_row: int, start_col: int,
                     goal_row: int, goal_col: int,
                     dem_path: str, ohrc_path: str,
                     ice_prob_path: str) -> Optional[Dict]:
        """
        Plan rover traverse from landing site to ice target.
        Returns dictionary with path and metrics.
        """
        logger.info("Loading cost layers for traverse planning...")
        
        # Load cost layers
        slope_cost, hazard_cost, ice_cost = self.load_cost_layers(
            dem_path, ohrc_path, ice_prob_path)
        
        # Combine costs: base + hazard penalty - ice bonus
        # Base cost is distance (1 per pixel for cardinal, sqrt(2) for diagonal)
        base_cost = np.ones_like(slope_cost)
        
        total_cost = base_cost + (self.hazard_weight * hazard_cost) + ice_cost
        
        # Apply slope constraints (impassable areas already set to inf in slope_cost)
        total_cost = np.where(np.isinf(slope_cost), np.inf, total_cost)
        
        logger.info(f"Planning traverse from ({start_row}, {start_col}) to ({goal_row}, {goal_col})")
        
        # Run A*
        path = self.astar((start_row, start_col), (goal_row, goal_col), total_cost)
        
        if path is None:
            return None
        
        # Calculate metrics
        total_distance = 0
        max_slope_along_path = 0
        total_hazard = 0
        ice_region_fraction = 0
        
        with rasterio.open(dem_path) as src:
            dem = src.read(1)
            slope, _ = compute_slope_aspect(dem, src.res[0])
            resolution = src.res[0]
        
        with rasterio.open(ohrc_path) as src:
            boulder_density = src.read(1)
        
        with rasterio.open(ice_prob_path) as src:
            ice_prob = src.read(1)
        
        for i in range(len(path) - 1):
            # Current pixel
            r, c = path[i]
            # Next pixel
            nr, nc = path[i+1]
            
            # Distance (approximate)
            dr = abs(nr - r)
            dc = abs(nc - c)
            if dr == 1 and dc == 1:  # Diagonal
                step_dist = resolution * np.sqrt(2)
            else:  # Cardinal
                step_dist = resolution
            total_distance += step_dist
            
            # Accumulate metrics
            max_slope_along_path = max(max_slope_along_path, slope[r, c])
            total_hazard += boulder_density[r, c]
            ice_region_fraction += ice_prob[r, c]
        
        # Average metrics
        if len(path) > 1:
            avg_hazard = total_hazard / len(path)
            avg_ice_prob = ice_region_fraction / len(path)
        else:
            avg_hazard = 0
            avg_ice_prob = 0
        
        return {
            'path': path,
            'length_pixels': len(path),
            'distance_m': total_distance,
            'max_slope_degrees': float(max_slope_along_path),
            'avg_hazard': float(avg_hazard),
            'avg_ice_probability': float(avg_ice_prob),
            'start': (start_row, start_col),
            'goal': (goal_row, goal_col)
        }
    
    def save_traverse(self, traverse: Dict, meta: Dict, output_dir: str):
        """Save traverse plan as GeoJSON and text summary."""
        ensure_dir(output_dir)
        
        if traverse is None:
            logger.warning("No traverse to save")
            return
        
        # Save as GeoJSON
        features = []
        # Path as LineString
        path_coords = []
        for row, col in traverse['path']:
            # Convert pixel to geographic (approximate)
            # Using center of pixel
            lon = meta['transform'][2] + (col + 0.5) * meta['transform'][0]
            lat = meta['transform'][5] + (row + 0.5) * meta['transform'][4]
            path_coords.append([lon, lat])
        
        features.append({
            "type": "Feature",
            "properties": {
                "distance_m": traverse['distance_m'],
                "max_slope_degrees": traverse['max_slope_degrees'],
                "avg_hazard": traverse['avg_hazard'],
                "avg_ice_probability": traverse['avg_ice_probability']
            },
            "geometry": {
                "type": "LineString",
                "coordinates": path_coords
            }
        })
        
        # Start and goal points
        start_point = {
            "type": "Feature",
            "properties": {
                "type": "start",
                "distance_m": 0
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                    meta['transform'][2] + (traverse['start'][1] + 0.5) * meta['transform'][0],
                    meta['transform'][5] + (traverse['start'][0] + 0.5) * meta['transform'][4]
                ]
            }
        }
        
        goal_point = {
            "type": "Feature",
            "properties": {
                "type": "goal",
                "distance_m": traverse['distance_m']
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                    meta['transform'][2] + (traverse['goal'][1] + 0.5) * meta['transform'][0],
                    meta['transform'][5] + (traverse['goal'][0] + 0.5) * meta['transform'][4]
                ]
            }
        }
        
        features.extend([start_point, goal_point])
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        geojson_path = Path(output_dir) / "rover_traverse_path.geojson"
        with open(geojson_path, 'w') as f:
            json.dump(geojson, f, indent=2)
        logger.info(f"Saved rover traverse path to {geojson_path}")
        
        # Save text summary
        summary_path = Path(output_dir) / "traverse_summary.txt"
        with open(summary_path, 'w') as f:
            f.write(f"""Rover Traverse Plan Summary
===========================

Start Point (Landing Site): Pixel {traverse['start']}
Goal Point (Ice Target): Pixel {traverse['goal']}

Path Length: {traverse['length_pixels']} pixels
Total Distance: {traverse['distance_m']:.1f} meters

Path Statistics:
- Maximum Slope Encountered: {traverse['max_slope_degrees']:.1f}°
- Average Hazard (Boulder Density): {traverse['avg_hazard']:.3f}
- Average Ice Probability Along Path: {traverse['avg_ice_probability']:.3f}

Assumptions:
- Maximum Traversable Slope: {self.config['planning']['traverse']['max_slope_degrees']}°
- Hazard Weight: {self.config['planning']['traverse']['hazard_penalty_weight']}
- Ice Region Bonus: {self.config['planning']['traverse']['ice_region_penalty']}
- Grid Resolution: {self.config['planning']['traverse']['grid_resolution']} m
""")
        logger.info(f"Saved traverse summary to {summary_path}")


def run_planning_pipeline(config_path: str = "config/config.yaml"):
    """Run the complete landing site and traverse planning pipeline."""
    import rasterio
    config = load_config(config_path)
    
    # Paths to required inputs
    ice_prob_path = Path(config['data']['output_dir']) / "fusion" / "fusion_ice_probability.tif"
    confidence_path = Path(config['data']['output_dir']) / "fusion" / "fusion_confidence_level.tif"
    dem_path = Path(config['data']['dem_dir']) / "tmc2_dem.tif"
    illum_path = Path(config['data']['output_dir']) / "illumination" / "illumination_direct_fraction.tif"
    ohrc_path = Path(config['data']['ohrc_dir']) / "ohrc_image.tif"
    planning_output_dir = Path(config['data']['output_dir']) / "planning"
    
    logger.info("Starting landing site and traverse planning pipeline...")
    
    # Load inputs
    logger.info(f"Loading ice probability from {ice_prob_path}")
    ice_prob, meta, transform, resolution = LandingSiteRanker(config).load_ice_probability(str(ice_prob_path))
    
    logger.info(f"Loading confidence from {confidence_path}")
    with rasterio.open(confidence_path) as src:
        confidence = src.read(1)
    
    logger.info(f"Loading DEM from {dem_path}")
    logger.info(f"Loading illumination from {illum_path}")
    logger.info(f"Loading OHRC from {ohrc_path}")
    
    # Rank landing sites
    ranker = LandingSiteRanker(config)
    landing_sites = ranker.rank_landing_sites(
        ice_prob, confidence, str(dem_path), str(illum_path), str(planning_output_dir))
    
    # Save landing site rankings
    ranker.save_landing_sites(landing_sites, str(planning_output_dir))
    ranker.generate_planning_document(
        landing_sites, str(planning_output_dir / "landing_site_selection.md"))
    
    # Plan traverse from best site to best ice (if we have sites)
    if landing_sites:
        best_site = landing_sites[0]  # Highest ranked site
        
        # Find best ice goal (highest confidence, highest probability)
        ice_candidates = (confidence >= 2) & (ice_prob > 0.5)
        if np.any(ice_candidates):
            # Find ice pixel with highest confidence*probability product
            ice_scores = confidence.astype(float) * ice_prob
            ice_scores[~ice_candidates] = 0
            max_idx = np.argmax(ice_scores)
            goal_row, goal_col = np.unravel_index(max_idx, ice_scores.shape)
            
            logger.info(f"Planning traverse from site {best_site['rank']} to best ice at ({goal_row}, {goal_col})")
            
            # Plan traverse
            planner = RoverTraversePlanner(config)
            traverse = planner.plan_traverse(
                best_site['row'], best_site['col'],
                goal_row, goal_col,
                str(dem_path), str(ohrc_path), str(ice_prob_path))
            
            if traverse:
                planner.save_traverse(traverse, meta, str(planning_output_dir))
            else:
                logger.warning("Could not plan traverse - no valid path found")
        else:
            logger.warning("No high-confidence ice pixels found for traverse planning")
    else:
        logger.warning("No valid landing sites found - cannot plan traverse")
    
    logger.info("Landing site and traverse planning completed")
    return landing_sites


if __name__ == "__main__":
    run_planning_pipeline()