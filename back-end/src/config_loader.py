import os
import yaml  # PyYAML

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "app_config.yaml")

def load_config() -> dict:
    """Load the YAML config file and return it as a dictionary."""
    try:
        with open(CONFIG_PATH, "r") as file:
            return yaml.safe_load(file) or {}
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

# Load config at startup
CONFIG = load_config()

def get_config_value(key: str, default=None) -> dict[dict]:
    """Get a specific value from the config by key."""
    return CONFIG.get(key, default)
