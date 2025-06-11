import sys
from typing import List, Tuple, Optional
import numpy as np
from custom_types.TimedPoint import TimedPoint
from config.constants import (
    REPRESENTATIVE_COM_SIZE,
    MOTION_VECTOR_SIZE,
    DEFAULT_LAMBDA_T,
)
def compute_average_axis_speed_by_start_and_end(cluster: List[dict]) -> np.ndarray:
    """Computes the average speed vector in the x, y, and z axes using the first and last points of a cluster.

    Parameters:
    cluster : List[dict]
        List of points, each a dict with keys 'x', 'y', 'z', and 't'.

    Returns;
    np.ndarray
        A 3-element array [vx, vy, vz] representing the average velocity.
    """
    sorted_cluster = sorted(cluster, key=lambda p: p['t'])
    start = sorted_cluster[0]
    end = sorted_cluster[-1]
    dt = max(end['t'] - start['t'], sys.float_info.min)

    vx = (end['x'] - start['x']) / dt
    vy = (end['y'] - start['y']) / dt
    vz = (end['z'] - start['z']) / dt

    return np.array([vx, vy, vz])


def calc_representative_center_of_mass(cluster: List[dict], k: int = REPRESENTATIVE_COM_SIZE) -> Optional[TimedPoint]:
    """Calculates the 4D center of mass for the initial segment of a cluster.

    Parameters:
    cluster : List[dict]
        Cluster of points, each with 'x', 'y', 'z', and 't'.
    k : int, optional
        Number of earliest points to include (default is 8).

    Returns:
    TimedPoint or None
        The computed center of mass as a TimedPoint, or None if the cluster is empty.
    """
    if not cluster:
        print("Warning: empty cluster passed to calc_representative_center_of_mass")
        return None

    sorted_cluster = sorted(cluster, key=lambda p: p['t'])
    segment = sorted_cluster[:k]
    coords = np.array([[p['x'], p['y'], p['z'], p['t']] for p in segment])
    x, y, z, t = coords.mean(axis=0)
    return TimedPoint(x, y, z, t)


def create_motion_vector(cluster: List[dict], k: int = MOTION_VECTOR_SIZE) -> Tuple[np.ndarray, TimedPoint]:
    """Generates a motion vector and center of mass from the latest points of a cluster.

    Parameters:
    cluster : List[dict]
        List of points with 'x', 'y', 'z', and 't'.
    k : int, optional
        Number of most recent points to use (default is 7).

    Returns;
    tuple of (np.ndarray, TimedPoint)
        - aligned_vector: The normalized direction vector scaled by speed.
        - center_of_mass: The 4D center of mass of the segment.

    Raises;
    RuntimeError
        If the cluster has fewer than 2 points.
    """
    if len(cluster) < 2:
        raise RuntimeError("Cluster must contain at least 2 plots to compute motion vector.")

    sorted_cluster = sorted(cluster, key=lambda p: p['t'])
    segment = sorted_cluster[-k:]

    v_vector = compute_average_axis_speed_by_start_and_end(segment)
    speed = np.linalg.norm(v_vector)

    pts = np.array([[p['x'], p['y'], p['z']] for p in segment])
    center_xyz = pts.mean(axis=0)
    _, _, vh = np.linalg.svd(pts - center_xyz)
    direction = vh[0] / np.linalg.norm(vh[0])

    x, y, z, t = np.array([[p['x'], p['y'], p['z'], p['t']] for p in segment]).mean(axis=0)
    center_of_mass = TimedPoint(x, y, z, t)

    aligned_vector = direction * speed
    return aligned_vector, center_of_mass


def calc_future_center_of_mass(aligned_vector: np.ndarray, center: TimedPoint, delta_t: float) -> TimedPoint:
    """Projects a center of mass point into the future given a motion vector.

    Parameters:
    aligned_vector : np.ndarray
        Motion vector [vx, vy, vz].
    center : TimedPoint
        Current 4D center of mass.
    delta_t : float
        Time increment for projection.

    Returns;
    TimedPoint
        The future center of mass after delta_t seconds.
    """
    dx, dy, dz = aligned_vector * delta_t
    return TimedPoint(center.x + dx, center.y + dy, center.z + dz, center.t + delta_t)


def calc_distance_between_two_center_mass(
    p1: TimedPoint,
    p2: TimedPoint,
    v_avg: float,
    lambda_t: float = DEFAULT_LAMBDA_T,
) -> float:
    """Computes a time-weighted Minkowski distance between two 4D points.

    Parameters;
    p1 : TimedPoint
        First center point.
    p2 : TimedPoint
        Second center point.
    v_avg : float
        Average velocity to convert time difference into distance.
    lambda_t : float, optional
        Weighting factor for time component (default is 0.8).
    p : int, optional
        Power parameter for Minkowski distance (default is 2 for Euclidean).

    Returns:
    float
        The combined space-time distance.
    """
    dt = abs(p1.t - p2.t) * v_avg * lambda_t
    dx = abs(p1.x - p2.x)
    dy = abs(p1.y - p2.y)
    dz = abs(p1.z - p2.z)
    return (dx**2 + dy**2 + dz**2 + dt**2) ** (1 / 2)
