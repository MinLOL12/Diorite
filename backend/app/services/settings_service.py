import json
from pathlib import Path
from ..core.config import get_settings_file
from ..models.schemas import Settings

class SettingsService:
    def __init__(self):
        self.settings_file = get_settings_file()

    def get_settings(self) -> Settings:
        if not self.settings_file.exists():
            s = Settings()
            self.save_settings(s)
            return s
        try:
            data = json.loads(self.settings_file.read_text())
            return Settings(**data)
        except Exception:
            return Settings()

    def save_settings(self, settings: Settings) -> Settings:
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        self.settings_file.write_text(json.dumps(settings.model_dump(), indent=2))
        return settings

    def update_settings(self, updates: dict) -> Settings:
        current = self.get_settings()
        data = current.model_dump()
        data.update(updates)
        new_settings = Settings(**data)
        return self.save_settings(new_settings)
