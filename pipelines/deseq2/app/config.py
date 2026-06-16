from pathlib import Path
import yaml


BASE_DIR = Path(__file__).resolve().parent.parent


class DynamicConfig:

    def __init__(self, config_path):

        self.config_path = config_path

    def _load(self):

        with open(self.config_path, "r") as f:

            return yaml.safe_load(f)

    def __getitem__(self, item):

        return self._load()[item]

    def get(self, key, default=None):

        return self._load().get(key, default)

    def to_dict(self):

        return self._load()


SETTINGS = DynamicConfig(
    BASE_DIR / "configs" / "settings.yaml"
)

DATASETS = DynamicConfig(
    BASE_DIR / "configs" / "datasets.yaml"
)

SELECTIONS = DynamicConfig(
    BASE_DIR / "configs" / "selections.yaml"
)