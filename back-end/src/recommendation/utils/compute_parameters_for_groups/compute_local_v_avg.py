import numpy as np
from typing import List, Dict
from threading import Lock
from collections import OrderedDict
from recommendation.utils.helpers.make_hashable_kay import make_hashable_key_v_avg
from recommendation.utils.math.distance_metrics import estimate_velocity_from_density
# Cache settings
MAX_CACHE_SIZE = 128

local_v_avg_cache: OrderedDict[str, List[float]] = OrderedDict()
v_avg_lock = Lock()

def compute_list_v_avg(
    plots: List[Dict],
    coords: np.ndarray,
    radius: float = 5000,
    max_velocity: float = 1000
) -> List[float]:
    """Estimate local average velocity for each plot based on neighbor density.

    Parameters:
        plots: List of plot records.
        coords: Array of shape (N, 3) containing [x, y, z] coordinates.
        radius: Distance threshold for neighbor search (default: 5000).
        max_velocity: Upper bound for velocity estimation (default: 1000).

    Returns:
        Estimated local velocity values for each plot.

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