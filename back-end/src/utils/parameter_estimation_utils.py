
import numpy as np
from utils.distance_metrics import minkowski_distance_plus_time
from sklearn.neighbors import NearestNeighbors

def estimate_clustering_radius(coords, idx, k=6, factor=1.5) -> float:
    if len(coords) <= k:
        return 100.0
    nbrs = NearestNeighbors(n_neighbors=k+1).fit(coords)
    distances, _ = nbrs.kneighbors([coords[idx]])
    avg = np.mean(distances[:, 1:])
    return avg * factor

def estimate_adaptive_clustering_radius(plots, center_plot, radius=5000, max_eps=3000, v_avg=600,factor=3.5) -> float:
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
    count = 0
    for plot in plots:
        if plot == center_plot:
            continue
        d = minkowski_distance_plus_time(center_plot, plot, v_avg=v_avg)
        if d <= radius:
            count += 1

    # Avoid division by zero
    if count == 0:
        return max_eps

    # Inverse relationship: more neighbors → smaller eps
    eps = (max_eps / (1 + count**0.5)) * factor

    return eps
