import numpy as np
"""convert methods"""

def convert_ecef_to_lla(x_ecef, y_ecef, z_ecef) -> tuple:
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

    p = np.sqrt(x_ecef ** 2 + y_ecef ** 2)
    theta = np.arctan2(z_ecef * a, p * b)

    lon = np.arctan2(y_ecef, x_ecef)
    lat = np.arctan2(z_ecef + ep ** 2 * b * np.sin(theta) ** 3, p - e2 * a * np.cos(theta) ** 3)
    N = a / np.sqrt(1 - e2 * np.sin(lat) ** 2)
    alt = p / np.cos(lat) - N

    lat = np.degrees(lat)
    lon = np.degrees(lon)
    return lat, lon, alt
