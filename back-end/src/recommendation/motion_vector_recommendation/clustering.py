from typing import List, Dict, Optional, Tuple
from collections import deque, defaultdict
import numpy as np
import pandas as pd

from api_utils import minkowski_distance_plus_time
from recommendation.build_tree_cache import build_kdtree_with_cache


def split_initial_clusters(
    selected_plots: List[dict],
    df_plots: pd.DataFrame,
    coords: np.ndarray,
    lambda_t: float = 0.8
) -> Tuple[List[List[dict]], List[Tuple[float, float]]]:
    """Cluster user-selected plots using space-time distance.

    Parameters:
        selected_plots (List[dict]): List of user-selected plot records.
        df_plots (pd.DataFrame): DataFrame of all event plots.
        coords (np.ndarray): Array of shape (N, 3) with [x, y, z] coordinates.
        lambda_t (float): Time-weight factor for distance calculation (default 0.8).

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

        root_idx = next(
            (i for i, p in enumerate(df_plots.to_dict(orient='records'))
             if all(np.isclose(p[k], plot[k]) for k in ['x', 'y', 'z', 't'])),
            None
        )

        eps = df_plots.iloc[root_idx]['eps'] *1.5
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
    max_d: float = 7000
) -> List[dict]:
    """Expand a user cluster by absorbing nearby plots.

    Parameters:
        cluster (List[dict]): Initial list of plot records assigned to the cluster.
        df_plots (pd.DataFrame): DataFrame containing all event plot data.
        eps (float): Expansion radius based on local density.
        v_avg (float): Average speed used for time-weighted distance calculation.
        extra_candidates (Optional[List[List[dict]]]): Additional small clusters to consider for expansion.
        max_d (float): Maximum allowed Euclidean distance from the cluster center (default: 7000).

    Returns:
        List[dict]: The expanded cluster as a list of plot records.

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

        df_unassigned = df_plots[df_plots['cluster'] == -1]
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

            if dist <= eps and dist_to_center <= max_d:
                df_plots.loc[
                    (df_plots['plot_id'] == candidate['plot_id']) &
                    (df_plots['system_id'] == candidate['system_id']),
                    'cluster'
                ] = cluster_id
                expanded.append(candidate)
                queue.append(candidate)
                visited_ids.add(key)

    return expanded


def custom_adaptive_dbscan(
    df_plots: pd.DataFrame,
    plots: List[Dict],
    v_avg_list: np.ndarray,
    eps_list: np.ndarray,
    max_dist_from_root: float = 15_000,
    min_samples: int = 5,
    lambda_t: float = 0.8
) -> np.ndarray:
    """Perform adaptive DBSCAN clustering using local eps and velocity.

    Parameters:
        df_plots (pd.DataFrame): DataFrame containing all event plots.
        plots (List[Dict]): List of plot records corresponding to `df_plots`.
        v_avg_list (np.ndarray): Array of local average speeds for each plot.
        eps_list (np.ndarray): Array of local epsilon values for each plot.
        max_dist_from_root (float): KDTree search radius for neighbors (default: 15000).
        min_samples (int): Minimum number of samples to form a core point (default: 5).
        lambda_t (float): Weight for the temporal dimension in distance calculation (default: 0.8).

    Returns:
        np.ndarray: Cluster labels for each plot (−1 indicates noise).

    Notes:
        - Builds a KDTree over coordinates [x, y, z, t * lambda_t].
        - Adapts `eps` and `v_avg` per point for clustering.
        - Uses a combined spatial–temporal distance metric.
    """
    n = len(plots)
    cluster_array = np.full(n, -1)
    visited = set()
    cluster_id = 0

    tree, _ = build_kdtree_with_cache(df_plots, time_weight=1.0)
    kd_coords = df_plots[['x', 'y', 'z', 't']].to_numpy()

    for i in range(n):
        if i in visited or cluster_array[i] != -1:
            continue

        visited.add(i)
        root_plot = plots[i]
        v_avg_root = v_avg_list[i]
        eps_root = eps_list[i]

        candidate_idxs = tree.query_ball_point(kd_coords[i], r=max_dist_from_root)
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

                candidate_idxs = tree.query_ball_point(kd_coords[curr_idx], r=max_dist_from_root)
                new_neighbors = [
                    j for j in candidate_idxs if j != curr_idx and
                    minkowski_distance_plus_time(curr_plot, plots[j], v_avg=curr_v_avg, lambda_t=lambda_t) <= curr_eps
                ]

                if len(new_neighbors) >= min_samples:
                    queue.extend([j for j in new_neighbors if j not in queue])

            if cluster_array[curr_idx] == -1:
                cluster_array[curr_idx] = cluster_id

        cluster_id += 1

    return cluster_array
