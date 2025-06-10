
import numpy as np
import pandas as pd
from utils.distance_metrics import minkowski_distance_plus_time, compute_distances_to_center
from sklearn.neighbors import NearestNeighbors

def estimate_clustering_radius(coords, idx, k=6, factor=1.5) -> float:
    if len(coords) <= k:
        return 100.0
    nbrs = NearestNeighbors(n_neighbors=k+1).fit(coords)
    distances, _ = nbrs.kneighbors([coords[idx]])
    avg = np.mean(distances[:, 1:])
    return avg * factor

def estimate_adaptive_clustering_radius(
    df: pd.DataFrame,
    center_plot: dict,
    radius: float = 5000,
    max_eps: float = 3000,
    v_avg: float = 600,
    factor: float = 3.5,
    lambda_t: float = 0.8
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
    distances = compute_distances_to_center(df, center_plot, v_avg, lambda_t)

    # Exclude center itself
    mask = ~(
        (df['plot_id'] == center_plot['plot_id']) &
        (df['system_id'] == center_plot['system_id'])
    )
    count = np.count_nonzero(distances[mask] <= radius)

    if count == 0:
        return max_eps

    return (max_eps / (1 + np.sqrt(count))) * factor