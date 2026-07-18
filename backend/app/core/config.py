import os
from pathlib import Path

# Base paths
BACKEND_ROOT = Path(__file__).parent.parent.parent
TEMPLATES_DIR = BACKEND_ROOT / "templates"
# User data dirs - platform aware
def get_user_data_root() -> Path:
    # Allow override via env
    if env := os.getenv("DIORITE_DATA_DIR"):
        return Path(env)
    home = Path.home()
    if os.name == "nt":
        base = Path(os.getenv("APPDATA", home / "AppData" / "Roaming"))
        return base / "Diorite"
    else:
        # Linux / macOS - use ~/.diorite for simplicity in dev
        return home / ".diorite"

def get_projects_dir() -> Path:
    return get_user_data_root() / "projects"

def get_cache_dir() -> Path:
    return get_user_data_root() / "cache"

def get_settings_file() -> Path:
    return get_user_data_root() / "settings.json"

# Ensure dirs exist
for p in [get_user_data_root(), get_projects_dir(), get_cache_dir()]:
    p.mkdir(parents=True, exist_ok=True)

# Cache subdirectories
CACHE_SUBDIRS = ["java", "gradle", "minecraft", "mappings", "loaders", "mods"]

for sub in CACHE_SUBDIRS:
    (get_cache_dir() / sub).mkdir(parents=True, exist_ok=True)

# Supported versions / loaders
SUPPORTED_LOADERS = ["fabric", "neoforge", "forge", "quilt"]
SUPPORTED_MC_VERSIONS = ["1.21.1", "1.21", "1.20.6", "1.20.1", "1.19.4"]

DEFAULT_JAVA_VERSIONS = {
    "1.21.1": 21,
    "1.21": 21,
    "1.20.6": 17,
    "1.20.1": 17,
    "1.19.4": 17,
}

# Build settings
GRADLE_DISTRIBUTION_CACHE_TIMEOUT = 3600
MAX_LOG_HISTORY = 5000
