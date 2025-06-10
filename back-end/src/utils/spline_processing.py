from typing import List
import pandas as pd
import numpy as np
from utils.coordinate_transforms import convert_ecef_to_lla
from csaps import csaps
from config_loader import get_config_value  

def handle_selected_plots(selected_plots, smoothing_factor) -> List:
    """Generate a smoothing spline from the user-selected plots.

    Parameters:
        selected_plots (list[dict]): List of plot records, each containing spatial and temporal fields
            (e.g., keys 'x', 'y', 'z', 't').
        smoothing_factor (float): Parameter controlling spline smoothness; higher values yield smoother curves.

    Returns:
        List.
    """
    
    # Convert selected plots to a DataFrame
    selected_plots_df = pd.DataFrame(selected_plots)


    # Sort the DataFrame by the 't' column in ascending order
    selected_plots_df = selected_plots_df.sort_values(by='t')

    # Extract x, y, z, and t values
    x_list = selected_plots_df['x'].tolist()
    y_list = selected_plots_df['y'].tolist()
    z_list = selected_plots_df['z'].tolist()
    u = selected_plots_df['t'].tolist()
    # Generate spline
    points = np.array([x_list, y_list, z_list])
    spline_points = generate_smoothing_spline(points, u, smoothing_factor)

    return spline_points


def generate_smoothing_spline(points, u, smoothing_factor) -> List:
    """Compute a smoothing spline line for given control points.

    Parameters:
        points (Sequence[Sequence[float]]): Sequence of control points, each specified as a coordinate sequence
            (e.g., [x, y, z]).
        u (array-like): Parameter values at which to evaluate the spline (e.g., a linspace between 0 and 1).
        smoothing_factor (float): Positive smoothing factor for the spline algorithm; larger values yield smoother curves.

    Returns:
        numpy.ndarray: Array of evaluated spline points with shape (len(u), dims).
    """

     # Ensure `u` is sorted and remove duplicates
    u, unique_indices = np.unique(u, return_index=True)
    
    # Apply sorting and remove duplicates to points
    points = np.array(points)[:, unique_indices]  # Select unique indices for x, y, z
    spline = csaps(u, points, smooth=smoothing_factor)

    min_t = u[0]
    max_t = u[-1]
    sampling_rate = get_config_value('sampling_rate_per_second_for_spline')
    num_points = int((max_t - min_t) * sampling_rate)
    u_fine = np.linspace(min_t, max_t,num_points)
    x_spline, y_spline, z_spline = spline(u_fine)
    # Convert sampled ECEF points to LLA for frontend visualization
    spline_points = []
    for i in range(num_points):
        latitude, longitude, altitude = convert_ecef_to_lla(x_spline[i], y_spline[i], z_spline[i])
        spline_points.append({
            'latitude': latitude,
            'longitude': longitude,
            'altitude': altitude,
            'time' : u_fine[i]
        })
    return spline_points
