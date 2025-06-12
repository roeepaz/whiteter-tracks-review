
from typing import Dict, List
import numpy as np
import pandas as pd
from utils.distance_metrics import compute_distances_to_center
from sklearn.neighbors import NearestNeighbors
from config_loader import get_constants_config_value

K_NEIGHBORS = get_constants_config_value("K_NEIGHBORS")
RADIUS_SCALING_FACTOR = get_constants_config_value("RADIUS_SCALING_FACTOR")
MIN_CLUSTERING_EPSILON = get_constants_config_value("MIN_CLUSTERING_EPSILON")

ADAPTIVE_RADIUS = get_constants_config_value("ADAPTIVE_RADIUS")
MAX_CLUSTERING_EPSILON = get_constants_config_value("MAX_CLUSTERING_EPSILON")
ADAPTIVE_EPS_SCALING = get_constants_config_value("ADAPTIVE_EPS_SCALING")

DEFAULT_AVG_VELOCITY = get_constants_config_value("DEFAULT_AVG_VELOCITY")
DEFAULT_LAMBDA_T = get_constants_config_value("DEFAULT_LAMBDA_T")

# This method is geometrically simple but not ideal for dynamic spatiotemporal data.
# It estimates the clustering radius based only on spatial neighbor distances
def estimate_clustering_radius(coords, idx, k=K_NEIGHBORS, factor=RADIUS_SCALING_FACTOR) -> float:
    """
    Estimate a local clustering radius for a given point based on k nearest neighbors.

    This function calculates the average distance from a given point to its k nearest spatial neighbors,
    then scales it by a constant factor. It is commonly used as a simple proxy for local density.

    Limitations:
        - Time is not considered, so results may be inaccurate for dynamic or temporal data.
        - The scaling factor (`factor`) is arbitrary and may not generalize across datasets.
        - Assumes all spatial dimensions are equally relevant (ignores velocity or directionality).
        - Returns a hardcoded fallback (100.0) if there are too few points.

    Parameters:
    coords (List[List[float]]): All data points as coordinate vectors (e.g., [[x, y, z], ...])
    idx (int): Index of the current point for which to estimate the radius
    k (int): Number of nearest neighbors to consider (default: K_NEIGHBORS)
    factor (float): A scaling factor to stretch/shrink the average distance (default: RADIUS_SCALING_FACTOR)

    Returns:
        float: Estimated radius to be used for clustering algorithms like DBSCAN
    """
    if len(coords) <= k:
        return MIN_CLUSTERING_EPSILON
    nbrs = NearestNeighbors(n_neighbors=k + 1).fit(coords)
    distances, _ = nbrs.kneighbors([coords[idx]])
    avg = np.mean(distances[:, 1:])  # Exclude distance to self
    return avg * factor

def estimate_adaptive_clustering_radius(
    plots: List[Dict],
    center_plot: dict,
    radius: float = ADAPTIVE_RADIUS,
    max_eps: float = MAX_CLUSTERING_EPSILON,
    v_avg: float = DEFAULT_AVG_VELOCITY,
    factor: float = ADAPTIVE_EPS_SCALING,
    lambda_t: float = DEFAULT_LAMBDA_T
) -> float:
    """
    Estimate eps based on number of neighbors within a fixed spatial+temporal radius.

    The more neighbors → the smaller the eps.

    Parameters:
        plots (List[dict]): all plots
        center_plot (dict): the plot to evaluate
        radius (float): the fixed radius to check (with minkowski + time)
        max_eps (float): the maximum eps allowed (for very sparse areas)
        v_avg (float): average velocity to convert time to distance

    Returns:
        float: adaptive eps value
    """
    """Estimate eps based on count of neighbors within a given radius (vectorized)."""
    df_plots = pd.DataFrame(plots)
    distances = compute_distances_to_center(df_plots, center_plot, v_avg, lambda_t)

    # Exclude center itself
    mask = ~(
        (df_plots['plot_id'] == center_plot['plot_id']) &
        (df_plots['system_id'] == center_plot['system_id'])
    )
    count = np.count_nonzero(distances[mask] <= radius)

    if count == 0:
        return max_eps

    return (max_eps / (1 + np.sqrt(count))) * factor