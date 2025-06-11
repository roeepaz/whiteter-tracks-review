from typing import Dict, List
import pandas as pd
import numpy as np
from config.constants import (
    DEFAULT_LAMBDA_T,
    DEFAULT_AVG_VELOCITY,
    FALLBACK_VELOCITY,
    MINIMAL_VELOCITY,
    MAX_POSSIBLE_VELOCITY,
    VELOCITY_ALPHA
)

def minkowski_distance_plus_time(point1, point2,  lambda_t=DEFAULT_LAMBDA_T, v_avg=DEFAULT_AVG_VELOCITY) -> float:
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
    distance = (np.sum(np.abs(point1_coords[:3] - point2_coords[:3]) ** 2) + dt_distance**2) ** (1/2)

    return distance

def compute_distances_to_center(
    df: pd.DataFrame,
    center_plot: dict,
    v_avg: float = DEFAULT_AVG_VELOCITY,
    lambda_t: float = DEFAULT_LAMBDA_T
) -> np.ndarray:
    """Vectorize computation of combined spatial + temporal distances to a center plot.

        Uses Euclidean distance for spatial dimensions (x, y, z) and converts time difference
        to an equivalent spatial distance using `v_avg` and `lambda_t`.

        **Assumption:** `df` contains columns ['plot_id', 'system_id', 'x', 'y', 'z', 't'].

        Parameters:
            df (pd.DataFrame):
                DataFrame of all plots, indexed arbitrarily but containing the required columns.
            center_plot (Dict[str, Any]):
                A dict with keys 'plot_id' and 'system_id' identifying the center row in `df`.
            v_avg (float):
                Average velocity (m/s) for converting time differences into distances.
            lambda_t (float):
                Weight applied to the time component.

        Returns:
            np.ndarray:
                Array of length N (number of rows in `df`), where each element is
                sqrt(‖Δxyz‖² + (Δt · v_avg · λ)²) relative to the center plot.
    """
    mask = (
        (df['plot_id'] == center_plot['plot_id']) &
        (df['system_id'] == center_plot['system_id'])
    )
    if not mask.any():
        raise ValueError("Center plot not found")
    idx = df.index[mask][0]

    coords = df[['x', 'y', 'z']].to_numpy()     # shape (N,3)
    times  = df['t'].to_numpy()                 # shape (N,)

    diff_spatial = coords - coords[idx]         # shape (N,3)
    spatial_dist = np.linalg.norm(diff_spatial, axis=1)  # Euclidean spatial

    dt = np.abs(times - times[idx]) * v_avg * lambda_t

    # Minkowski p=2: sqrt(spatial^2 + dt^2)
    return np.sqrt(spatial_dist**2 + dt**2)

def calculate_average_velocity(neighbor_plots: List[Dict[str, float]]) -> float:
    """Compute the average speed over a time‐series of 3D points.

        This function measures the Euclidean distance between each pair of consecutive
        points and divides the total distance by the total elapsed time.

        **Assumption:** The input list `neighbor_plots` **must be sorted** in ascending
        order by the `'t'` timestamp. Sorting ensures that each distance and time
        interval reflects forward progression, avoiding negative or out‐of‐order intervals.

        Parameters:
            neighbor_plots (List[Dict[str, float]]):
                A list of dictionaries, each containing:
                - 'x', 'y', 'z' (float): spatial coordinates in meters
                - 't' (float): timestamp in seconds

        Returns:
            float:
                - If fewer than 2 points are provided: returns 700.0 as a fallback.
                - If total elapsed time is zero (all timestamps identical): returns 1.0.
                - Otherwise: (total spatial distance) / (total time elapsed).
        """    
    # 1. Early exit for too few samples
    if len(neighbor_plots) < 2:
        return FALLBACK_VELOCITY

    # 2. Sort by timestamp to ensure forward progression
    sorted_plots = sorted(neighbor_plots, key=lambda p: p['t'])

    # 3. Accumulate distance and time
    total_dist = 0.0
    total_time = 0.0
    for p1, p2 in zip(sorted_plots, sorted_plots[1:]):
        # 3a. Spatial distance (Euclidean in 3D)
        d = np.linalg.norm([p2['x']-p1['x'], p2['y']-p1['y'], p2['z']-p1['z']])
        # 3b. Time interval (always positive after sorting)
        dt = p2['t'] - p1['t']
        if dt > 0:
            total_dist += d
            total_time += dt

    # 4. Handle zero total time
    if total_time == 0:
        return MINIMAL_VELOCITY

    # 5. Final average speed
    return total_dist / total_time

def estimate_velocity_from_density(neighbor_plots, max_velocity=MAX_POSSIBLE_VELOCITY, alpha=VELOCITY_ALPHA) -> float:
    """
    Estimate velocity based on number of neighbor plots (density).

    The more plots → the lower the velocity.

    Parameters:
        neighbor_plots (List[Dict]): plots around a central point
        max_velocity (float): maximum possible velocity
        alpha (float): density sensitivity factor (higher → more aggressive drop)
            When to Adjust alpha?
                Increase alpha when:
                You want to penalize dense clusters more (e.g., sharp turns, stationarity).

                Decrease alpha when:
                You want to be more tolerant of density and assume more uniform velocity across different regions
    Returns:
        float: estimated average velocity
    """
    num_neighbors = len(neighbor_plots)

    if num_neighbors == 0:
        return max_velocity  # No data → assume max speed

    # Inverse relationship
    velocity = max_velocity / (1 + alpha * num_neighbors)

    return velocity
