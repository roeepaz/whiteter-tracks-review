import numpy as np

def minkowski_distance_plus_time(point1, point2, p=2, lambda_t=0.8, v_avg=1.0) -> float:
    """
    Calculate Minkowski distance for two plots (x, y, z coordinates + time).

    Parameters:
    - point1, point2: Dictionaries with keys 'x', 'y', 'z', 't'
    - p: Minkowski power parameter (p=1: Manhattan, p=2: Euclidean, p>2: Higher penalty on large differences)
    - lambda_t: Weight for time importance
    - v_avg: Average velocity (meters/second) for converting time into distance

    Returns:
    - Minkowski distance considering spatial and temporal components
    """
    point1_coords = np.array([point1['x'], point1['y'], point1['z'], point1['t']])
    point2_coords = np.array([point2['x'], point2['y'], point2['z'], point2['t']])
    
    # Compute distance including time weight
    dt_distance = abs(point1_coords[3] - point2_coords[3]) * v_avg * lambda_t
    distance = (np.sum(np.abs(point1_coords[:3] - point2_coords[:3]) ** p) + dt_distance**p) ** (1/p)

    return distance


def calculate_average_velocity(neighbor_plots) -> float:
    if len(neighbor_plots) < 2:
        return 700
    total_dist, total_time = 0, 0
    for i in range(len(neighbor_plots) - 1):
        p1, p2 = neighbor_plots[i], neighbor_plots[i + 1]
        d = np.linalg.norm([p2['x'] - p1['x'], p2['y'] - p1['y'], p2['z'] - p1['z']])
        dt = abs(p2['t'] - p1['t'])
        if dt > 0:
            total_dist += d
            total_time += dt
    return total_dist / total_time if total_time > 0 else 1.0

def estimate_velocity_from_density(neighbor_plots, max_velocity=1000, alpha=0.1) -> float:
    """
    Estimate velocity based on number of neighbor plots (density).

    The more plots → the lower the velocity.

    Parameters:
        neighbor_plots (List[Dict]): plots around a central point
        max_velocity (float): maximum possible velocity
        alpha (float): density sensitivity factor (higher → more aggressive drop)

    Returns:
        float: estimated average velocity
    """
    num_neighbors = len(neighbor_plots)

    if num_neighbors == 0:
        return max_velocity  # No data → assume max speed

    # Inverse relationship
    velocity = max_velocity / (1 + alpha * num_neighbors)

    return velocity
