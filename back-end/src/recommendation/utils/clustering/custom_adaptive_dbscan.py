from typing import List, Dict
from collections import deque
import numpy as np
import pandas as pd
from recommendation.utils.math.distance_metrics import minkowski_distance_plus_time
from recommendation.utils.tree_cache.build_tree_cache import build_kdtree_with_cache
from config.config_loader import get_constants_config_value

DEFAULT_LAMBDA_T = get_constants_config_value("DEFAULT_LAMBDA_T")
NO_CLUSTER = get_constants_config_value("NO_CLUSTER")

DBSCAN_MIN_SAMPLES = get_constants_config_value("DBSCAN_MIN_SAMPLES")
DEFAULT_LAMBDA_T = get_constants_config_value("DEFAULT_LAMBDA_T")
DEFAULT_TIME_WEIGHT = get_constants_config_value("DEFAULT_TIME_WEIGHT")
MAX_KDTREE_RADIUS = get_constants_config_value("MAX_KDTREE_RADIUS")

def custom_adaptive_dbscan(
    df_plots: pd.DataFrame,
    plots: List[Dict],
    v_avg_list: np.ndarray,
    eps_list: np.ndarray,
    min_samples: int = DBSCAN_MIN_SAMPLES,
    lambda_t: float = DEFAULT_LAMBDA_T
) -> np.ndarray:
    """Perform adaptive DBSCAN clustering using local eps and velocity.

    Parameters:
        df_plots: DataFrame containing all event plots.
        plots: List of plot records corresponding to `df_plots`.
        v_avg_list: Array of local average speeds for each plot.
        eps_list: Array of local epsilon values for each plot.
        max_dist_from_root: KDTree search radius for neighbors (default: 15000).
        min_samples: Minimum number of samples to form a core point (default: 5).
        lambda_t: Weight for the temporal dimension in distance calculation (default: 0.8).

    Returns:
        Cluster labels for each plot (−1 indicates noise).

    Notes:
        - Builds a KDTree over coordinates [x, y, z, t * lambda_t].
        - Adapts `eps` and `v_avg` per point for clustering.
        - Uses a combined spatial–temporal distance metric.
    """
    n = len(plots)
    cluster_array = np.full(n, NO_CLUSTER)
    visited = set()
    cluster_id = 0

    tree, _ = build_kdtree_with_cache(df_plots, time_weight=DEFAULT_TIME_WEIGHT)
    kd_coords = df_plots[['x', 'y', 'z', 't']].to_numpy()

    for i in range(n):
        if i in visited or cluster_array[i] != NO_CLUSTER:
            continue

        visited.add(i)
        root_plot = plots[i]
        v_avg_root = v_avg_list[i]
        eps_root = eps_list[i]

        candidate_idxs = tree.query_ball_point(kd_coords[i], r=MAX_KDTREE_RADIUS)
        neighbors = [
            j for j in candidate_idxs if j != i and
            minkowski_distance_plus_time(root_plot, plots[j], v_avg=v_avg_root, lambda_t=lambda_t) <= eps_root
        ]

        cluster_array[i] = cluster_id
        queue = deque(neighbors)

        while queue:
            curr_idx = queue.popleft()
            if curr_idx not in visited:
                visited.add(curr_idx)
                curr_plot = plots[curr_idx]
                curr_eps = eps_list[curr_idx]
                curr_v_avg = v_avg_list[curr_idx]

                candidate_idxs = tree.query_ball_point(kd_coords[curr_idx], r=MAX_KDTREE_RADIUS)
                new_neighbors = [
                    j for j in candidate_idxs if j != curr_idx and
                    minkowski_distance_plus_time(curr_plot, plots[j], v_avg=curr_v_avg, lambda_t=lambda_t) <= curr_eps
                ]

                if len(new_neighbors) >= min_samples:
                    queue.extend([j for j in new_neighbors if j not in queue])

            if cluster_array[curr_idx] == NO_CLUSTER:
                cluster_array[curr_idx] = cluster_id

        cluster_id += 1

    return cluster_array
