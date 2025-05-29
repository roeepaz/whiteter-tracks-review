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
    """
    Generate a stable hash for a DataFrame to use as a cache key.

    Input:
        df: pd.DataFrame -  The DataFrame to hash

    Output:
        str - MD5 hash string

    Explanation:
        Creates a hash based on DataFrame content to use for caching KDTree results.
    """
    return hashlib.md5(pd.util.hash_pandas_object(df, index=True).values).hexdigest()


def build_kdtree_with_cache(df: pd.DataFrame, time_weight: float = 1.0) -> Tuple[KDTree, List[Tuple[int, int]]]:
    """
    Build or retrieve a cached KDTree and associated keys from a DataFrame.

    Input:
        df: pd.DataFrame - The source DataFrame with x, y, z, t
        time_weight: float - A multiplier for the time dimension

    Output:
        Tuple of:
            - KDTree - 4D KDTree with time-weighted coordinates
            - List of keys (plot_id, system_id) for all rows

    Explanation:
        Builds a KDTree on 4D coordinates (x, y, z, t*time_weight) and caches it using a stable hash.
        Thread-safe with a lock to support parallel requests.
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
    radius: float = 15_000,
    time_weight: float = 1.0
) -> pd.DataFrame:
    """
    Filter plots in df that are within a 4D radius of selected_plots using an existing KDTree.

    Input:
        df: pd.DataFrame - All plots
        tree: KDTree - KDTree built from df
        all_keys: List[Tuple[int, int]] - (plot_id, system_id) for each plot
        selected_plots: List[dict] - User-selected plots
        radius: float - Search radius in 4D
        time_weight: float - Weight applied to time dimension

    Output:
        pd.DataFrame - Filtered DataFrame of relevant plots

    Explanation:
        For each selected plot, finds nearby points using KDTree in 4D space.
        Returns only those points in the original df that fall within this radius.
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