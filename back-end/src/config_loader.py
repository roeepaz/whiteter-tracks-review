import os
import yaml  # PyYAML
from functools import lru_cache

APP_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config/app_config.yaml")

def load_app_config() -> dict:
    """Load the YAML config file and return it as a dictionary."""
    try:
        with open(APP_CONFIG_PATH, "r") as file:
            return yaml.safe_load(file) or {}
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

# Load config at startup
CONFIG = load_app_config()

def get_app_config_value(key: str, default=None) -> dict[dict]:
    """Get a specific value from the config by key."""
    return CONFIG.get(key, default)
