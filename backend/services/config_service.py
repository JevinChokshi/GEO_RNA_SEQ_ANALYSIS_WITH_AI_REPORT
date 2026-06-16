import os
import yaml
from pathlib import Path

# ==================================================
# ATOMIC ROOT RESOLUTION
# ==================================================
# Forces Python to look at the real underlying disk space, bypassing virtualized symlinks
BACKEND_DIR = Path(__file__).parent.parent.resolve(strict=True)
PROJECT_ROOT = BACKEND_DIR.parent.resolve(strict=True)

CONFIG_DIR = PROJECT_ROOT / "pipelines" / "deseq2" / "configs"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_settings():
    file_path = CONFIG_DIR / "settings.yaml"
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def load_datasets():
    file_path = CONFIG_DIR / "datasets.yaml"
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def load_selections():
    file_path = CONFIG_DIR / "selections.yaml"
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def save_yaml(filename, data):
    if isinstance(filename, Path):
        final_path = filename.resolve()
    else:
        final_path = (CONFIG_DIR / filename).resolve()
        
    # ATOMIC WRITE: Write to a temporary file first, then force-replace 
    # to break past Windows/OneDrive file sync hooks
    temp_path = final_path.with_suffix(".tmp")
    
    with open(temp_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False)
        f.flush()
        os.fsync(f.fileno())  # Physical hardware level drive synchronization
        
    if final_path.exists():
        os.remove(final_path)  # Delete old lock file explicitly
    os.rename(temp_path, final_path)
