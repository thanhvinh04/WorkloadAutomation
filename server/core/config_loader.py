import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class ConfigLoader:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        config_path = Path(__file__).parent.parent / "config.json"
        if config_path.exists():
            self._config = json.loads(config_path.read_text(encoding="utf-8"))
        else:
            self._config = {}

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def get_task_config(self, task_code: str) -> Optional[Dict[str, Any]]:
        tasks = self.get("tasks", {})
        return tasks.get(task_code)

    def get_all_tasks(self) -> Dict[str, Any]:
        return self.get("tasks", {})


config_loader = ConfigLoader()