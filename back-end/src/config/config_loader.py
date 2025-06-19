from pathlib import Path
import yaml

# Base Config Directory
CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
APP_CONFIG_PATH = CONFIG_DIR / "app_config.yaml"
CONSTANTS_DIR = CONFIG_DIR / "constants"

def load_yaml_config(path: Path) -> dict:
    """Load a single YAML file into a dictionary."""
    try:
        with path.open("r") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading config at {path}: {e}")
        return {}

def load_all_constants(config_dir: Path) -> dict:
    """Load all YAML files under the constants directory into a single merged dictionary."""
    combined = {}
    for yaml_file in config_dir.glob("*.yaml"):
        data = load_yaml_config(yaml_file)
        if data:
            combined.update(data)
    return combined

# Load configs at startup
APP_CONFIG = load_yaml_config(APP_CONFIG_PATH)
CONSTANTS_CONFIG = load_all_constants(CONSTANTS_DIR)

# Accessors
def load_app_config() -> dict:
    return load_yaml_config(APP_CONFIG_PATH)

def get_app_config_value(key: str, default=None):
    return APP_CONFIG.get(key, default)

def get_constants_config_value(key: str, default=None):
    return CONSTANTS_CONFIG.get(key, default)
