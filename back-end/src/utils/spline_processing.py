from typing import List, Dict, Sequence
import pandas as pd
import numpy as np
from utils.coordinate_transforms import convert_ecef_to_lla
from csaps import csaps
from config_loader import get_app_config_value  

def generate_smoothed_track_from_plots(selected_plots: List[Dict], smoothing_factor: float) -> List[Dict]:
    """Generate a smoothing spline from the user-selected plots.

    Parameters:
        selected_plots (list[dict]): List of plot records, each containing spatial and temporal fields
            (e.g., keys 'x', 'y', 'z', 't').
        smoothing_factor (float): Parameter controlling spline smoothness; higher values yield smoother curves.

    Returns:
        List.
    """
    
    # Convert selected plots to a DataFrame
    selected_df_plots = pd.DataFrame(selected_plots)


    # Sort the DataFrame by the 't' column in ascending order
    selected_df_plots = selected_df_plots.sort_values(by='t')

    # Extract x, y, z, and t values
    x_list = selected_df_plots['x'].tolist()
    y_list = selected_df_plots['y'].tolist()
    z_list = selected_df_plots['z'].tolist()
    u = selected_df_plots['t'].tolist()
    # Generate spline
    points = np.array([x_list, y_list, z_list])
    spline_xyz = generate_ecef_spline_with_time(points, u, smoothing_factor)
    return convert_ecef_track_to_lla(spline_xyz)


def generate_ecef_spline_with_time(points: Sequence[Sequence[float]],
    u: Sequence[float],
    smoothing_factor: float
) -> np.ndarray:    
    """Compute a smoothing spline line for given control points.

    Parameters:
        points (Sequence[Sequence[float]]): Sequence of control points, each specified as a coordinate sequence
            (e.g., [x, y, z]).
        u (array-like): Parameter values at which to evaluate the spline (e.g., a linspace between 0 and 1).
        smoothing_factor (float): Positive smoothing factor for the spline algorithm; larger values yield smoother curves.

    Returns:
        numpy.ndarray: Array of evaluated spline points with shape (len(u), dims).
    """

    u, unique_indices = np.unique(u, return_index=True)
    points = np.array(points)[:, unique_indices]

    spline = csaps(u, points, smooth=smoothing_factor)

    min_t, max_t = u[0], u[-1]
    sampling_rate = get_app_config_value('sampling_rate_per_second_for_spline')
    num_points = int((max_t - min_t) * sampling_rate)
    u_fine = np.linspace(min_t, max_t, num_points)

    x_spline, y_spline, z_spline = spline(u_fine)
    return np.stack([x_spline, y_spline, z_spline, u_fine], axis=1)  # shape: (N, 4)

def convert_ecef_track_to_lla(spline_xyz: np.ndarray) -> List[Dict]:
    """
    Convert a spline track in ECEF coordinates to LLA.
    """
    return [
        {
            'latitude': lat,
            'longitude': lon,
            'altitude': alt,
            'time': t
        }
        for x, y, z, t in spline_xyz
        for lat, lon, alt in [convert_ecef_to_lla(x, y, z)]
    ]
