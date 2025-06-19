
from typing import List, Dict
from threading import Lock
from collections import OrderedDict
from recommendation.utils.helpers.make_hashable_kay import make_hashable_key_eps
from recommendation.utils.processing.parameter_estimation_utils import estimate_adaptive_clustering_radius
# Cache settings
MAX_CACHE_SIZE = 128


local_eps_cache: OrderedDict[str, List[float]] = OrderedDict()
eps_lock = Lock()

def compute_list_eps(
    plots: List[Dict],
    v_avg_list: List[float]
) -> List[float]:
    """Estimate local epsilon values for DBSCAN per plot based on velocity.

    Parameters:
        plots: List of plot records.
        v_avg_list: Estimated velocity for each plot.

    Returns:
        Epsilon values (neighborhood radius) per plot.

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

