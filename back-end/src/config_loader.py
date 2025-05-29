import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__),"app_config.json")

def load_config():
    """Load the JSON config file and return it as a dictionary."""
    try:
        with open(CONFIG_PATH, "r") as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

# Load config at startup
CONFIG = load_config()

def get_config_value(key, default=None):
    """Get a specific value from the config by key."""
    return CONFIG.get(key, default)
