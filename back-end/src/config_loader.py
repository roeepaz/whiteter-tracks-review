from pathlib import Path
import yaml

# Config Paths
CONFIG_DIR = Path(__file__).resolve().parent / "config"
APP_CONFIG_PATH = CONFIG_DIR / "app_config.yaml"
CONSTANTS_CONFIG_PATH = CONFIG_DIR / "constants.yaml"

# YAML Loader
def load_yaml_config(path: Path) -> dict:
    """Load a YAML file into a dictionary."""
    try:
        with path.open("r") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading config at {path}: {e}")
        return {}

# Load Both Configs at Startup
APP_CONFIG = load_yaml_config(APP_CONFIG_PATH)
CONSTANTS_CONFIG = load_yaml_config(CONSTANTS_CONFIG_PATH)

# Accessors 
def load_app_config() -> dict:
    return load_yaml_config(APP_CONFIG)

def get_app_config_value(key: str, default=None):
    """Fetch a key from the app config, with optional fallback."""
    return APP_CONFIG.get(key, default)

def get_constants_config_value(key: str, default=None):
    """Fetch a key from the constants config, with optional fallback."""
    return CONSTANTS_CONFIG.get(key, default)
