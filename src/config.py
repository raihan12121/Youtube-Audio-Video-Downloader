"""
Configuration manager for YouTube Downloader.
Persists settings into a JSON config file.
"""

import json
from pathlib import Path
from typing import Any, Dict
from src.core.utils import get_default_download_dir


CONFIG_FILE = Path(__file__).resolve().parent.parent / "settings.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "download_dir": get_default_download_dir(),
    "appearance_mode": "Dark",
    "theme_color": "blue",
    "max_concurrent_downloads": 3,
    "default_mode": "video",          # "video" or "audio"
    "default_video_resolution": "Best Available", # "Best Available", "2160p (4K)", "1440p (2K)", "1080p", "720p", "480p", "360p"
    "default_video_container": "mp4", # "mp4", "mkv", "webm"
    "default_audio_format": "mp3",    # "mp3", "m4a", "wav", "flac", "opus"
    "default_audio_quality": "320 kbps", # "320 kbps", "256 kbps", "192 kbps", "128 kbps"
    "embed_thumbnail": True,
    "embed_metadata": True,
    "download_subtitles": False,
    "subtitles_lang": "en",
    "organize_playlists_in_subfolders": True,
    "number_playlist_items": True,
    "browser_cookies": "none",        # "none", "chrome", "firefox", "edge", "brave"
    "custom_cookies_path": "",
    "rate_limit_mb": 0,               # 0 = unlimited
}


class ConfigManager:
    """Manages application settings loading and saving."""

    def __init__(self, config_path: Path = CONFIG_FILE):
        self.config_path = config_path
        self._config: Dict[str, Any] = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        """Loads configuration from disk."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._config.update(data)
            except Exception as e:
                print(f"Error loading config, using defaults: {e}")
        else:
            self.save()

    def save(self):
        """Saves current configuration to disk."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default if default is not None else DEFAULT_CONFIG.get(key))

    def set(self, key: str, value: Any, auto_save: bool = True):
        self._config[key] = value
        if auto_save:
            self.save()

    @property
    def download_dir(self) -> str:
        d = self.get("download_dir", get_default_download_dir())
        Path(d).mkdir(parents=True, exist_ok=True)
        return d

    @download_dir.setter
    def download_dir(self, value: str):
        self.set("download_dir", value)


# Global singleton
config = ConfigManager()
