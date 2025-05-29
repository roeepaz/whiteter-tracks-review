import sys
from typing import List
import numpy as np
from custom_types.TimedPoint import TimedPoint

def compute_average_axis_speed_by_start_and_end(cluster: List[dict]) -> np.ndarray:
    """
    Computes the average speed in x, y, z axes based on start and end points.

    Input:
        cluster: List[dict] - List of plots with 'x', 'y', 'z', 't'

    Output:
        np.ndarray - [vx, vy, vz], the average velocity vector

    Explanation:
        Sorts the cluster by time, takes the first and last points,
        and computes the velocity along each axis over the time duration.
    """
    sorted_cluster = sorted(cluster, key=lambda p: p['t'])
    start = sorted_cluster[0]
    end = sorted_cluster[-1]
    dt = max(end['t'] - start['t'], sys.float_info.min)  # Avoid division by zero

    vx = (end['x'] - start['x']) / dt
    vy = (end['y'] - start['y']) / dt
    vz = (end['z'] - start['z']) / dt

    return np.array([vx, vy, vz])

def calc_representative_center_of_mass(cluster: List[dict], k=8):
    """
    Calculates the 4D center of mass of the first k points in the cluster.

    Input:
        cluster: List[dict] - Cluster of plots
        k: int - Number of initial plots to consider

    Output:
        TimedPoint - Center of mass (x, y, z, t)

    Explanation:
        Sorts the cluster by time, uses the first k plots (or fewer if not enough),
        and returns the mean position and time as a TimedPoint.
    """
    if not cluster:
        print("Warning: empty cluster passed to calc_representative_center_of_mass")
        print("\n", cluster)
        return None

    sorted_cluster = sorted(cluster, key=lambda p: p['t'])
    segment = sorted_cluster[:k] if len(sorted_cluster) >= k else sorted_cluster

    coords_array = np.array([[p['x'], p['y'], p['z'], p['t']] for p in segment])
    center_full = coords_array.mean(axis=0)
    x, y, z, t = center_full
    center_of_mass = TimedPoint(x, y, z, t)

    return center_of_mass

def create_motion_vector(cluster: List[dict], k: int = 7):
    """
    Creates a motion vector and center of mass from a cluster.

    Input:
        cluster: List[dict] - List of plot points
        k: int - Number of latest plots to use for the vector

    Output:
        Tuple[np.ndarray, TimedPoint] - (motion vector, center of mass)

    Explanation:
        Uses the last k points in the cluster to:
        - Estimate average speed
        - Compute direction using SVD (principal component)
        - Compute center of mass (x, y, z, t)
    """
    if len(cluster) < 2:
        raise RuntimeError("Cluster must contain at least 2 plots to compute motion vector.")

    sorted_cluster = sorted(cluster, key=lambda p: p['t'])
    segment = sorted_cluster[-k:] if len(sorted_cluster) >= k else sorted_cluster

    v_vector = compute_average_axis_speed_by_start_and_end(segment)
    speed = np.linalg.norm(v_vector)

    cluster_array = np.array([[p['x'], p['y'], p['z']] for p in segment])
    center_xyz = cluster_array.mean(axis=0)
    centered = cluster_array - center_xyz
    _, _, vv = np.linalg.svd(centered)
    u = vv[0]
    u_normalized = u / np.linalg.norm(u)

    coords_array = np.array([[p['x'], p['y'], p['z'], p['t']] for p in segment])
    center_full = coords_array.mean(axis=0)
    x, y, z, t = center_full
    center_of_mass = TimedPoint(x, y, z, t)

    aligned_vector = u_normalized * speed
    return aligned_vector, center_of_mass

def calc_future_center_of_mass(aligned_vector: np.ndarray, center: TimedPoint, delta_t: float) -> TimedPoint:
    """
    Projects the center of mass into the future using the motion vector.

    Input:
        aligned_vector: np.ndarray - Motion vector [vx, vy, vz]
        center: TimedPoint - Current center of mass
        delta_t: float - Time delta to project forward

    Output:
        TimedPoint - Projected future center of mass

    Explanation:
        Multiplies the vector by delta_t and adds to the center's (x, y, z, t).
    """
    dx, dy, dz = aligned_vector * delta_t
    return TimedPoint(center.x + dx, center.y + dy, center.z + dz, center.t + delta_t)

def calc_distance_between_two_center_mass(
    p1: TimedPoint,
    p2: TimedPoint,
    v_avg: float,
    lambda_t: float = 0.8,
    p: int = 2
) -> float:
    """
    Calculates Minkowski-style distance between two TimedPoints with time weighted.

    Input:
        p1: TimedPoint - First center
        p2: TimedPoint - Second center
        v_avg: float - Average velocity to scale time
        lambda_t: float - Time weighting factor
        p: int - Power for Minkowski distance (e.g. p=2 for Euclidean)

    Output:
        float - Combined distance

    Explanation:
        Time difference is converted to meters using v_avg and scaled by lambda_t.
        All four components (x, y, z, time) are combined using Minkowski formula.
    """
    dt = abs(p1.t - p2.t) * v_avg * lambda_t
    dx = abs(p1.x - p2.x)
    dy = abs(p1.y - p2.y)
    dz = abs(p1.z - p2.z)
    distance = (dx**p + dy**p + dz**p + dt**p) ** (1/p)

    return distance
