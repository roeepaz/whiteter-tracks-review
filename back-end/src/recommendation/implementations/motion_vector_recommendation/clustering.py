from typing import List, Optional, Tuple
from collections import deque
import numpy as np
import pandas as pd
from recommendation.utils.math.distance_metrics import minkowski_distance_plus_time
from recommendation.utils.helpers.find_index import find_plot_index
from config.config_loader import get_constants_config_value

DEFAULT_LAMBDA_T = get_constants_config_value("DEFAULT_LAMBDA_T")
EPS_SCALING_FACTOR = get_constants_config_value("EPS_SCALING_FACTOR")
MAX_EUCLIDEAN_DISTANCE_TO_CENTER = get_constants_config_value("MAX_EUCLIDEAN_DISTANCE_TO_CENTER")
NO_CLUSTER = get_constants_config_value("NO_CLUSTER")

def split_initial_clusters(
    selected_plots: List[dict],
    df_plots: pd.DataFrame,
    coords: np.ndarray,
    lambda_t: float = DEFAULT_LAMBDA_T
) -> Tuple[List[List[dict]], List[Tuple[float, float]]]:
    """Cluster user-selected plots using space-time distance.

    Parameters:
        selected_plots: List of user-selected plot records.
        df_plots: DataFrame of all event plots.
        coords: Array of shape (N, 3) with [x, y, z] coordinates.
        lambda_t: Time-weight factor for distance calculation (default 0.8).

    Returns:
        Tuple[List[List[dict]], List[Tuple[float, float]]]:
            - First element: list of clusters, each a list of plot dicts.
            - Second element: list of (eps, v_avg) tuples for each cluster.

    Notes:
        - Performs a BFS expansion to group plots that are close in both space and time.
        - Assigns cluster IDs in-place on `df_plots` as it builds each cluster.
    """
    clustered_ids = set()
    clusters = []
    cluster_params = []
    cluster_id = 0

    for plot in selected_plots:
        plot_key = (plot['plot_id'], plot['system_id'])
        if plot_key in clustered_ids:
            continue

        queue = deque([plot])
        cluster = []
        clustered_ids.add(plot_key)

        root_idx = find_plot_index(df_plots,plot)

        eps = df_plots.iloc[root_idx]['eps'] * EPS_SCALING_FACTOR #I want a slightly larger search radius.
        v_avg = df_plots.iloc[root_idx]['v_avg']
        cluster_params.append((eps, v_avg))

        while queue:
            current = queue.popleft()
            cluster.append(current)

            for neighbor in selected_plots:
                neighbor_key = (neighbor['plot_id'], neighbor['system_id'])
                if neighbor_key in clustered_ids:
                    continue

                dist = minkowski_distance_plus_time(current, neighbor, lambda_t=lambda_t, v_avg=v_avg)
                if dist <= eps:
                    queue.append(neighbor)
                    clustered_ids.add(neighbor_key)

        for p in cluster:
            df_plots.loc[
                (df_plots['plot_id'] == p['plot_id']) &
                (df_plots['system_id'] == p['system_id']),
                'cluster'
            ] = cluster_id

        clusters.append(cluster)
        cluster_id += 1

    print("number of the user cluster:", len(clusters))
    return clusters, cluster_params


def expand_cluster(
    cluster: List[dict],
    df_plots: pd.DataFrame,
    eps: float,
    v_avg: float,
    extra_candidates: Optional[List[List[dict]]] = None,
    max_eucliden_distance_to_center: float = MAX_EUCLIDEAN_DISTANCE_TO_CENTER
) -> List[dict]:
    """Expand a user cluster by absorbing nearby plots.

    Parameters:
        cluster: Initial list of plot records assigned to the cluster.
        df_plots: DataFrame containing all event plot data.
        eps: Expansion radius based on local density.
        v_avg: Average speed used for time-weighted distance calculation.
        extra_candidates : Additional small clusters to consider for expansion.
        max_d: Maximum allowed Euclidean distance from the cluster center (default: 7000).

    Returns:
        The expanded cluster as a list of plot records.

    Notes:
        - Uses breadth-first search to include neighboring plots that satisfy both
          the Minkowski+time distance criteria and the Euclidean distance limit.
        - Updates the 'cluster' column in `df_plots` to reflect newly added plots.
    """
    
    expanded = list(cluster)
    queue = deque(cluster)

    cluster_id = df_plots.loc[
        (df_plots['plot_id'] == cluster[0]['plot_id']) &
        (df_plots['system_id'] == cluster[0]['system_id']),
        'cluster'
    ].values[0]

    visited_ids = {(p['plot_id'], p['system_id']) for p in expanded}

    while queue:
        core = queue.popleft()
        coords = np.array([[p['x'], p['y'], p['z']] for p in expanded])
        center = coords.mean(axis=0)

        df_unassigned = df_plots[df_plots['cluster'] == NO_CLUSTER]
        candidates = df_unassigned.to_dict(orient='records')

        if extra_candidates:
            extra_plots = [p for cluster in extra_candidates for p in cluster]
            candidates += [p for p in extra_plots if (p['plot_id'], p['system_id']) not in visited_ids]

        for candidate in candidates:
            key = (candidate['plot_id'], candidate['system_id'])
            if key in visited_ids:
                continue

            dist = minkowski_distance_plus_time(core, candidate, lambda_t=1.0, v_avg=v_avg)
            dist_to_center = np.linalg.norm([
                candidate['x'] - center[0],
                candidate['y'] - center[1],
                candidate['z'] - center[2],
            ])

            if dist <= eps and dist_to_center <= max_eucliden_distance_to_center:
                df_plots.loc[
                    (df_plots['plot_id'] == candidate['plot_id']) &
                    (df_plots['system_id'] == candidate['system_id']),
                    'cluster'
                ] = cluster_id
                expanded.append(candidate)
                queue.append(candidate)
                visited_ids.add(key)

    return expanded

