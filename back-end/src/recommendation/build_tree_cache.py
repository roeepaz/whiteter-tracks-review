from typing import List, Dict, Tuple
import hashlib
import pandas as pd
import numpy as np
from threading import Lock
from scipy.spatial import KDTree
from cachetools import LRUCache

_kdtree_cache: LRUCache = LRUCache(maxsize=10)
_kdtree_lock: Lock = Lock()

def df_hash(df: pd.DataFrame) -> str:
    """Generate a stable MD5 hash for a DataFrame.

    Parameters:
        df (pd.DataFrame): The DataFrame to compute the hash for.

    Returns:
        str: MD5 hash string representing the DataFrame’s content, suitable as a cache key.
    """
    return hashlib.md5(
        pd.util.hash_pandas_object(df, index=True).values
    ).hexdigest()

def build_kdtree_with_cache(df: pd.DataFrame, time_weight: float = 1.0) -> Tuple[KDTree, List[Tuple[int, int]]]:
    """Build or retrieve a cached 4D KDTree with time-weighted coordinates.

    Parameters:
        df (pd.DataFrame): Source DataFrame containing columns 'x', 'y', 'z', and 't'.
        time_weight (float): Multiplier applied to the time dimension (default is 1.0).

    Returns:
        Tuple[KDTree, List[Tuple[int, int]]]:
            - KDTree: A tree built on coordinates [x, y, z, t * time_weight].
            - List[Tuple[int, int]]: Keys for each row as (plot_id, system_id).

    Notes:
        - Computes a stable hash of the DataFrame to use as a cache key.
        - Uses a thread-safe lock to guard concurrent cache access.
    """
    key = df_hash(df)

    with _kdtree_lock:
        if key in _kdtree_cache:
            return _kdtree_cache[key]

    coords = df[['x', 'y', 'z', 't']].copy()
    coords['t'] *= time_weight
    kd_coords = coords.to_numpy()
    tree = KDTree(kd_coords)
    all_keys = list(zip(df['plot_id'], df['system_id']))

    with _kdtree_lock:
        if key not in _kdtree_cache:
            _kdtree_cache[key] = (tree, all_keys)

    return _kdtree_cache[key]


def filter_relevant_plots(
    df: pd.DataFrame,
    tree: KDTree,
    all_keys: List[Tuple[int, int]],
    selected_plots: List[Dict],
    radius: float = 15000,
    time_weight: float = 1.0
) -> pd.DataFrame:
    """Filter plots within a time-weighted 4D radius of selected plots.

    Parameters:
        df (pd.DataFrame): DataFrame of all plots with columns ['x', 'y', 'z', 't'].
        tree (KDTree): KDTree built on coordinates [x, y, z, t * time_weight].
        all_keys (List[Tuple[int, int]]): List of (plot_id, system_id) tuples matching df rows.
        selected_plots (List[dict]): List of plot dicts with keys 'x', 'y', 'z', 't'.
        radius (float): Search radius in the 4D space (default: 15000).
        time_weight (float): Multiplier for the time dimension (default: 1.0).

    Returns:
        pd.DataFrame: Subset of df containing all plots found within the given radius of any selected plot.

    Notes:
        - Queries the KDTree for each selected plot to find neighbors in 4D.
        - Maps neighbor indices back to df via all_keys.
    """
    if not selected_plots:
        raise ValueError("selected_plots must not be empty")

    selected_df = pd.DataFrame(selected_plots)
    selected_coords = selected_df[['x', 'y', 'z', 't']].copy()
    selected_coords['t'] *= time_weight
    query_points = selected_coords.to_numpy()

    matching_keys = set()
    for point in query_points:
        result_indices = tree.query_ball_point(point, r=radius)
        matching_keys.update(all_keys[i] for i in result_indices)

    df = df.copy()
    df['key'] = list(zip(df['plot_id'], df['system_id']))
    filtered_df = df[df['key'].isin(matching_keys)].drop(columns=['key'])

    return filtered_df