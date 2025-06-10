import numpy as np
import json
import hashlib
from typing import List, Dict
from threading import Lock
from collections import OrderedDict
from utils.parameter_estimation_utils import estimate_adaptive_clustering_radius
from utils.distance_metrics import estimate_velocity_from_density
# Cache settings
MAX_CACHE_SIZE = 128

local_v_avg_cache: OrderedDict[str, List[float]] = OrderedDict()
v_avg_lock = Lock()

local_eps_cache: OrderedDict[str, List[float]] = OrderedDict()
eps_lock = Lock()

def make_hashable_key_v_avg(
    plots: List[Dict],
    coords: np.ndarray,
    radius: float,
    max_velocity: float
) -> str:
    ids = [p.get("id", i) for i, p in enumerate(plots)]
    coords_hash = hashlib.sha256(coords.tobytes()).hexdigest()
    return json.dumps({
        "ids": ids,
        "coords": coords_hash,
        "radius": radius,
        "max_velocity": max_velocity
    }, sort_keys=True)

def make_hashable_key_eps(
    plots: List[Dict],
    v_avg_list: List[float]
) -> str:
    ids = [p.get("id", i) for i, p in enumerate(plots)]
    return json.dumps({
        "ids": ids,
        "v_avg": [round(v, 3) for v in v_avg_list]
    }, sort_keys=True)

def compute_local_v_avg(
    plots: List[Dict],
    coords: np.ndarray,
    radius: float = 5000,
    max_velocity: float = 1000
) -> List[float]:
    """Estimate local average velocity for each plot based on neighbor density.

    Parameters:
        plots (List[Dict]): List of plot records.
        coords (np.ndarray): Array of shape (N, 3) containing [x, y, z] coordinates.
        radius (float): Distance threshold for neighbor search (default: 5000).
        max_velocity (float): Upper bound for velocity estimation (default: 1000).

    Returns:
        List[float]: Estimated local velocity values for each plot.

    Notes:
        - Uses an LRU cache with thread-safe access.
    """
    key = make_hashable_key_v_avg(plots, coords, radius, max_velocity)

    with v_avg_lock:
        if key in local_v_avg_cache:
            local_v_avg_cache.move_to_end(key)
            return local_v_avg_cache[key]

    local_v_avg: List[float] = []
    for i, p in enumerate(plots):
        dists = np.linalg.norm(coords - coords[i], axis=1)
        neighbor_idxs = np.where(dists < radius)[0]
        neighbor_plots = [plots[j] for j in neighbor_idxs]
        v = estimate_velocity_from_density(neighbor_plots, max_velocity=max_velocity)
        local_v_avg.append(v)

    with v_avg_lock:
        local_v_avg_cache[key] = local_v_avg
        local_v_avg_cache.move_to_end(key)
        if len(local_v_avg_cache) > MAX_CACHE_SIZE:
            local_v_avg_cache.popitem(last=False)

    return local_v_avg


def compute_local_eps(
    plots: List[Dict],
    v_avg_list: List[float]
) -> List[float]:
    """Estimate local epsilon values for DBSCAN per plot based on velocity.

    Parameters:
        plots (List[Dict]): List of plot records.
        v_avg_list (List[float]): Estimated velocity for each plot.

    Returns:
        List[float]: Epsilon values (neighborhood radius) per plot.

    Notes:
        - Uses an LRU cache with thread-safe access.
    """
    key = make_hashable_key_eps(plots, v_avg_list)

    with eps_lock:
        if key in local_eps_cache:
            local_eps_cache.move_to_end(key)
            return local_eps_cache[key]

    local_eps: List[float] = []
    for i, plot in enumerate(plots):
        eps = estimate_adaptive_clustering_radius(plots, plot, v_avg=v_avg_list[i])
        local_eps.append(eps)

    with eps_lock:
        local_eps_cache[key] = local_eps
        local_eps_cache.move_to_end(key)
        if len(local_eps_cache) > MAX_CACHE_SIZE:
            local_eps_cache.popitem(last=False)

    return local_eps
