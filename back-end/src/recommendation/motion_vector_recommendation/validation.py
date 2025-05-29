from typing import List

def is_valid_cluster(cluster: List[dict], min_size: int) -> bool:
    return len(cluster) > min_size