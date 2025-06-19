from pyproj import Transformer

# Reuse the transformer for performance
_ecef_to_lla_transformer = Transformer.from_crs(
    crs_from="epsg:4978",  # ECEF
    crs_to="epsg:4326",    # WGS84: lat/lon/alt
    always_xy=True
)

def convert_ecef_to_lla(x_ecef: float, y_ecef: float, z_ecef: float) ->  tuple[float, float, float]:
    """Convert ECEF (Earth-Centered Earth-Fixed) coordinates to geodetic coordinates (lat, lon, alt).
    
    Parameters:
        x_ecef: X coordinate in meters
        y_ecef: Y coordinate in meters
        z_ece: Z coordinate in meters
    
    Returns:
        tuple: (latitude, longitude, altitude) in degrees and meters
    """
    lon, lat, alt = _ecef_to_lla_transformer.transform(x_ecef, y_ecef, z_ecef)
    return lat, lon, alt
