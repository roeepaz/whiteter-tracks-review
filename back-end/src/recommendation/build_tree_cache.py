from typing import List, Dict, Tuple
import hashlib
import pandas as pd
import numpy as np
from threading import Lock
from scipy.spatial import KDTree
from cachetools import LRUCache
from config_loader import get_constants_config_value

KDTREE_CACHE_MAXSIZE = get_constants_config_value("KDTREE_CACHE_MAXSIZE")
DEFAULT_TIME_WEIGHT = get_constants_config_value("DEFAULT_TIME_WEIGHT")
DEFAULT_FILTER_RADIUS = get_constants_config_value("DEFAULT_FILTER_RADIUS")

_kdtree_cache: LRUCache = LRUCache(maxsize=KDTREE_CACHE_MAXSIZE)
_kdtree_lock: Lock = Lock()

def df_hash(df: pd.DataFrame) -> str:
    """Generate a stable MD5 hash for a DataFrame.

    Parameters:
        df: The DataFrame to compute the hash for.

    Returns:
        str: MD5 hash string representing the DataFrame’s content, suitable as a cache key.
    """
    return hashlib.md5(
        pd.util.hash_pandas_object(df, index=True).values
    ).hexdigest()

def build_kdtree_with_cache(df_plots: pd.DataFrame, time_weight: float = DEFAULT_TIME_WEIGHT) -> Tuple[KDTree, List[Tuple[int, int]]]:
    """Build or retrieve a cached 4D KDTree with time-weighted coordinates.

    Parameters:
        df: Source DataFrame containing columns 'x', 'y', 'z', and 't'.
        time_weight: Multiplier applied to the time dimension (default is 1.0).

    Returns:
        Tuple
            - KDTree: A tree built on coordinates [x, y, z, t * time_weight].
            - List[Tuple[int, int]]: Keys for each row as (plot_id, system_id).

    Notes:
        - Computes a stable hash of the DataFrame to use as a cache key.
        - Uses a thread-safe lock to guard concurrent cache access.
    """
    key = df_hash(df_plots)

    with _kdtree_lock:
        if key in _kdtree_cache:
            return _kdtree_cache[key]

    coords = df_plots[['x', 'y', 'z', 't']].copy()
    coords['t'] *= time_weight
    kd_coords = coords.to_numpy()
    tree = KDTree(kd_coords)
    all_keys = list(zip(df_plots['plot_id'], df_plots['system_id']))

    with _kdtree_lock:
        if key not in _kdtree_cache:
            _kdtree_cache[key] = (tree, all_keys)

    return _kdtree_cache[key]


def filter_relevant_plots(
    df_plots: pd.DataFrame,
    tree: KDTree,
    all_keys: List[Tuple[int, int]],
    selected_plots: List[Dict],
    filter_radius: float = DEFAULT_FILTER_RADIUS,
    time_weight: float = DEFAULT_TIME_WEIGHT
) -> pd.DataFrame:
    """Filter plots within a time-weighted 4D radius of selected plots.

    Parameters:
        df: DataFrame of all plots with columns ['x', 'y', 'z', 't'].
        tree: KDTree built on coordinates [x, y, z, t * time_weight].
        all_keys: List of (plot_id, system_id) tuples matching df rows.
        selected_plots: List of plot dicts with keys 'x', 'y', 'z', 't'.
        radius: Search radius in the 4D space (default: 15000).
        time_weight: Multiplier for the time dimension (default: 1.0).

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
        result_indices = tree.query_ball_point(point, r=filter_radius)
        matching_keys.update(all_keys[i] for i in result_indices)

    df_plots = df_plots.copy()
    df_plots['key'] = list(zip(df_plots['plot_id'], df_plots['system_id']))
    filtered_df = df_plots[df_plots['key'].isin(matching_keys)].drop(columns=['key'])

    return filtered_df