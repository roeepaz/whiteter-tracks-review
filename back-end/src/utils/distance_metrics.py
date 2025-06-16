from typing import Dict, List
import pandas as pd
import numpy as np
from config_loader import get_constants_config_value

DEFAULT_LAMBDA_T = get_constants_config_value("DEFAULT_LAMBDA_T")
DEFAULT_AVG_VELOCITY = get_constants_config_value("DEFAULT_AVG_VELOCITY")
FALLBACK_VELOCITY = get_constants_config_value("FALLBACK_VELOCITY")
MINIMAL_VELOCITY = get_constants_config_value("MINIMAL_VELOCITY")
MAX_POSSIBLE_VELOCITY = get_constants_config_value("MAX_POSSIBLE_VELOCITY")
VELOCITY_ALPHA = get_constants_config_value("VELOCITY_ALPHA")


def minkowski_distance_plus_time(point1, point2,  lambda_t=DEFAULT_LAMBDA_T, v_avg=DEFAULT_AVG_VELOCITY) -> float:
    """Calculate Minkowski distance for two plots (x, y, z coordinates + time).

    Parameters:
    - point1, point2: Dictionaries with keys 'x', 'y', 'z', 't'
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
    df_plots: pd.DataFrame,
    center_plot: dict,
    v_avg: float = DEFAULT_AVG_VELOCITY,
    lambda_t: float = DEFAULT_LAMBDA_T
) -> np.ndarray:
    """Vectorize computation of combined spatial + temporal distances to a center plot.

        Uses Euclidean distance for spatial dimensions (x, y, z) and converts time difference
        to an equivalent spatial distance using `v_avg` and `lambda_t`.

        **Assumption:** `df` contains columns ['plot_id', 'system_id', 'x', 'y', 'z', 't'].

        Parameters:
            df_plots: DataFrame of all plots, indexed arbitrarily but containing the required columns.
            center_plot: A dict with keys 'plot_id' and 'system_id' identifying the center row in `df`.
            v_avg: Average velocity (m/s) for converting time differences into distances.
            lambda_t:Weight applied to the time component.

        Returns:
            np.ndarray:
                Array of length N (number of rows in `df`), where each element is
                sqrt(‖Δxyz‖² + (Δt · v_avg · λ)²) relative to the center plot.
    """
    mask = (
        (df_plots['plot_id'] == center_plot['plot_id']) &
        (df_plots['system_id'] == center_plot['system_id'])
    )
    if not mask.any():
        raise ValueError("Center plot not found")
    idx = df_plots.index[mask][0]

    coords = df_plots[['x', 'y', 'z']].to_numpy()     # shape (N,3)
    times  = df_plots['t'].to_numpy()                 # shape (N,)

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
            neighbor_plots:
                A list of dictionaries, each containing:
                - 'x', 'y', 'z' (float): spatial coordinates in meters
                - 't' (float): timestamp in seconds

        Returns:
                - If fewer than 2 points are provided: returns 700.0 as a fallback.
                - If total elapsed time is zero (all timestamps identical): returns 1.0.
                - Otherwise: (total spatial distance) / (total time elapsed).
        """    
    # 1. Early exit for too few samples
    if len(neighbor_plots) < 2:
        return FALLBACK_VELOCITY

    # 2. Sort by timestamp to ensure forward progression
    sorted_plots = sorted(neighbor_plots, key=lambda p: p['t'])

    # 3. Convert to numpy array: shape (N, 4)
    coords = np.array([[p['x'], p['y'], p['z'], p['t']] for p in sorted_plots])

    # 4. Compute deltas between consecutive rows
    deltas = np.diff(coords, axis=0)  # shape: (N-1, 4)

    # Euclidean distances (x, y, z)
    spatial_dists = np.linalg.norm(deltas[:, :3], axis=1)

    # Time deltas
    time_deltas = deltas[:, 3]

    # 5. Mask valid time intervals (dt > 0)
    valid_mask = time_deltas > 0
    total_dist = np.sum(spatial_dists[valid_mask])
    total_time = np.sum(time_deltas[valid_mask])

    if total_time == 0:
        return MINIMAL_VELOCITY

    return total_dist / total_time

def estimate_velocity_from_density(neighbor_plots: List[Dict], max_velocity : float=MAX_POSSIBLE_VELOCITY, alpha: float=VELOCITY_ALPHA) -> float:
    """
    Estimate velocity based on number of neighbor plots (density).

    The more plots → the lower the velocity.

    Parameters:
        neighbor_plots: plots around a central point
        max_velocity: maximum possible velocity
        alpha: density sensitivity factor (higher → more aggressive drop)
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
