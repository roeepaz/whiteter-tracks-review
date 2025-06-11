# === General Constants ===

EVENTS_CACHE_MAXSIZE = 20  # Max number of events to cache in memory

# Time weighting factor for space-time distance calculations
DEFAULT_LAMBDA_T = 0.8

# Default average velocity used for time-to-distance conversion (m/s)
DEFAULT_AVG_VELOCITY = 600.0

# Velocity fallback when only 1 point is available
FALLBACK_VELOCITY = 700.0

# Minimal velocity used to avoid division by zero when dt = 0
MINIMAL_VELOCITY = 1.0

# Maximum velocity in very sparse environments
MAX_POSSIBLE_VELOCITY = 1000.0

# Density-to-velocity conversion sensitivity (higher → more reactive)
VELOCITY_ALPHA = 0.4


# === Clustering Radius Estimation ===

K_NEIGHBORS = 6  # Number of neighbors used for radius estimation
RADIUS_SCALING_FACTOR = 1.5  # Multiplier for the base radius
MIN_CLUSTERING_EPSILON = 1000  # Lower bound for epsilon in clustering


# === Adaptive DBSCAN Parameters ===

ADAPTIVE_RADIUS = 5000  # Radius for estimating local density
MAX_CLUSTERING_EPSILON = 3000  # Cap for epsilon in sparse areas
ADAPTIVE_EPS_SCALING = 3.5  # Scale factor to convert neighbor count to eps


# === KDTree & Plot Filtering ===

DEFAULT_TIME_WEIGHT = 1.0  # Time dimension multiplier in KDTree coordinates
DEFAULT_FILTER_RADIUS = 15000  # Radius for selecting nearby plots
KDTREE_CACHE_MAXSIZE = 10  # Max trees in KDTree cache


# === Motion Vector Recommendation ===

# Cluster validation
MIN_VALID_CLUSTER_SIZE = 7  # Minimum plots required in a valid cluster
MAX_CLUSTER_EXPANSION_ATTEMPTS = 9  # Max attempts to grow small clusters
EVENT_CLUSTER_ID_START = 1000  # Start index for system-generated clusters

# Cluster matching thresholds
SPATIOTEMPORAL_JUMP_LIMIT = 10_000  # Max distance allowed between clusters (space-time)
MATCHING_LAMBDA_T = 1.0  # Time weight when comparing cluster centers
CENTER_MATCH_LAMBDA_T = 0.3  # Time weight when calculating average deflection

# Dynamic deflection limits
DEFLECTION_BASE = 6000  # Base deflection allowance (meters)
DEFLECTION_PER_SECOND = 750  # Increase per second of time gap
DEFLECTION_MAX = 9000  # Maximum allowed deflection


# === Motion Vector Clustering ===

# Initial clustering of selected plots
EPS_SCALING_FACTOR = 1.5  # Increase eps slightly for initial clustering

# Cluster expansion constraints
MAX_EUCLIDEAN_DISTANCE_TO_CENTER = 7000  # Max distance from cluster center (meters)

# Adaptive DBSCAN settings
MAX_KDTREE_RADIUS = 15000  # Search radius in KDTree for neighbors
DBSCAN_MIN_SAMPLES = 5  # Min neighbors required to form a core point


# === Motion Vector Segments ===
REPRESENTATIVE_COM_SIZE = 8  # First K points for representative center of mass
MOTION_VECTOR_SIZE = 7  # Last K points used to compute motion vector
