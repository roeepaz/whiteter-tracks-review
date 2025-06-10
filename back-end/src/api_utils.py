import pandas as pd
import json
import numpy as np
import json
import os
from flask import jsonify
from config_loader import get_config_value



def minkowski_distance_plus_time(plot1, plot2, p=2, lambda_t=0.8, v_avg=1.0):
    """
    Calculate Minkowski distance for two plots (x, y, z coordinates + time).

    Parameters:
    - plot1, plot2: Dictionaries with keys 'x', 'y', 'z', 't'
    - p: Minkowski power parameter (p=1: Manhattan, p=2: Euclidean, p>2: Higher penalty on large differences)
    - lambda_t: Weight for time importance
    - v_avg: Average velocity (meters/second) for converting time into distance

    Returns:
    - Minkowski distance considering spatial and temporal components
    """
    coords1 = np.array([plot1['x'], plot1['y'], plot1['z'], plot1['t']])
    coords2 = np.array([plot2['x'], plot2['y'], plot2['z'], plot2['t']])
    
    # Compute distance including time weight
    dt_distance = abs(coords1[3] - coords2[3]) * v_avg * lambda_t
    distance = (np.sum(np.abs(coords1[:3] - coords2[:3]) ** p) + dt_distance**p) ** (1/p)

    return distance


from sklearn.neighbors import NearestNeighbors

def estimate_local_eps(coords, idx, k=6, factor=1.5):
    if len(coords) <= k:
        return 100.0
    nbrs = NearestNeighbors(n_neighbors=k+1).fit(coords)
    distances, _ = nbrs.kneighbors([coords[idx]])
    avg = np.mean(distances[:, 1:])
    return avg * factor

def estimate_local_eps_with_density(plots, center_plot, radius=5000, max_eps=3000, v_avg=600,factor=3.5):
    """
    Estimate eps based on number of neighbors within a fixed spatial+temporal radius.

    The more neighbors → the smaller the eps.

    Parameters:
        plots (List[dict]): all plots
        center_plot (dict): the plot to evaluate
        radius (float): the fixed radius to check (with minkowski + time)
        max_eps (float): the maximum eps allowed (for very sparse areas)
        v_avg (float): average velocity to convert time to distance

    Returns:
        float: adaptive eps value
    """
    count = 0
    for plot in plots:
        if plot == center_plot:
            continue
        d = minkowski_distance_plus_time(center_plot, plot, v_avg=v_avg)
        if d <= radius:
            count += 1

    # Avoid division by zero
    if count == 0:
        return max_eps

    # Inverse relationship: more neighbors → smaller eps
    eps = (max_eps / (1 + count**0.5)) * factor

    return eps

def estimate_avg_velocity(neighbor_plots):
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

def estimate_velocity_from_density(neighbor_plots, max_velocity=1000, alpha=0.1):
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

def handle_selected_plots(selected_plots, smoothing_factor):
    """Generate a smoothing spline from the user-selected plots.

    Parameters:
        selected_plots (list[dict]): List of plot records, each containing spatial and temporal fields
            (e.g., keys 'x', 'y', 'z', 't').
        smoothing_factor (float): Parameter controlling spline smoothness; higher values yield smoother curves.

    Returns:
        object: A spline representation (e.g., SciPy BSpline or equivalent) that interpolates the input plots.
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
    spline_points = sp_line(points, u, smoothing_factor)

    return spline_points

def handle_error(e, status_code=500, error_type="UnexpectedError"):
    print(f"[ERROR] {type(e).__name__}: {str(e)}")
    return jsonify({
        "success": False,
        "error": {
            "type": error_type if error_type else type(e).__name__,
            "message": str(e)
        }
    }), status_code

from csaps import csaps
from config_loader import get_config_value  

def sp_line(points, u, smoothing_factor):
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
        latitude, longitude, altitude = ecef_to_lla(x_spline[i], y_spline[i], z_spline[i])
        spline_points.append({
            'latitude': latitude,
            'longitude': longitude,
            'altitude': altitude,
            'time' : u_fine[i]
        })
    return spline_points

"""convert methods"""

def ecef_to_lla(x, y, z):
    """Convert Earth-Centered Earth-Fixed (ECEF) coordinates to geodetic latitude, longitude, and altitude.

    Parameters:
        x (float): ECEF X coordinate in meters.
        y (float): ECEF Y coordinate in meters.
        z (float): ECEF Z coordinate in meters.

    Returns:
        tuple[float, float, float]:  
            latitude (float): Geodetic latitude in decimal degrees.  
            longitude (float): Geodetic longitude in decimal degrees.  
            altitude (float): Height above the WGS84 ellipsoid in meters.
    """
    a = 6378137  # Equatorial radius
    f = 1 / 298.257223563  # Flattening
    e2 = 2 * f - f ** 2  # Eccentricity squared
    b = a * (1 - f)
    ep = np.sqrt((a ** 2 - b ** 2) / (b ** 2))

    p = np.sqrt(x ** 2 + y ** 2)
    theta = np.arctan2(z * a, p * b)

    lon = np.arctan2(y, x)
    lat = np.arctan2(z + ep ** 2 * b * np.sin(theta) ** 3, p - e2 * a * np.cos(theta) ** 3)
    N = a / np.sqrt(1 - e2 * np.sin(lat) ** 2)
    alt = p / np.cos(lat) - N

    lat = np.degrees(lat)
    lon = np.degrees(lon)
    return lat, lon, alt


def ecef_enu_vectors(latitude, longitude, altitude=0):
    """
    Compute the East, North, and Up unit vectors in ECEF for a given geographic location.
    
    Parameters:
        latitude: Latitude in degrees.
        longitude: Longitude in degrees.
        altitude: Altitude in meters (default is 0).
    
    Returns:
        tuple: (east_vector, north_vector, up_vector), each a unit vector in ECEF coordinates.
    """
    # Convert degrees to radians
    lat_rad = np.radians(latitude)
    lon_rad = np.radians(longitude)
    
    # WGS84 ellipsoid constants
    a = 6378137.0  # Semi-major axis (m)
    b = 6356752.314245  # Semi-minor axis (m)
    e2 = 1 - (b**2 / a**2)  # Eccentricity squared
    
    # Radius of curvature in the prime vertical
    N = a / np.sqrt(1 - e2 * np.sin(lat_rad)**2)
    
    # ECEF coordinates for the point (for reference)
    x = (N + altitude) * np.cos(lat_rad) * np.cos(lon_rad)
    y = (N + altitude) * np.cos(lat_rad) * np.sin(lon_rad)
    z = (N * (1 - e2) + altitude) * np.sin(lat_rad)
    
    # Up vector (normalized normal to the ellipsoid)
    up_vector = np.array([x, y, z])
    up_vector /= np.linalg.norm(up_vector)
    
    # East vector (perpendicular to Up, pointing east)
    east_vector = np.array([-np.sin(lon_rad), np.cos(lon_rad), 0])
    east_vector /= np.linalg.norm(east_vector)  # Ensure it's a unit vector
    
    # North vector (perpendicular to both Up and East)
    north_vector = np.cross(up_vector, east_vector)
    north_vector /= np.linalg.norm(north_vector)  # Ensure it's a unit vector
    
    return east_vector, north_vector, up_vector