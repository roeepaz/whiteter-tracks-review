import numpy as np
import json
import hashlib
from typing import List, Dict

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
