import os
import json
from typing import Dict, Any, Optional


class ConfigManager:
    """
    Manages application configuration settings.
    
    This class handles loading, saving, and accessing configuration settings
    from a JSON file, with fallback to default values when needed.
    """
    
    DEFAULT_CONFIG: Dict[str, Any] = {
        "base_dir": "saved_websites",
        "max_concurrent_downloads": 8,
        "timeout": 30,
        "respect_robots_txt": True,
        "sanitize_html": False,
        "user_agent": "WebArchiver/2.0",
        "selenium_headless": True,
        "download_images": True,
        "download_css": True,
        "download_js": True,
        "download_fonts": True,
        "preferred_engine": "requests",  # "requests", "selenium", or "playwright"
        "database_path": "websites.db"
    }
    
    def __init__(self, config_path: str = "config.json") -> None:
        """
        Initialize the ConfigManager.
        
        Args:
            config_path: Path to the configuration file. Defaults to "config.json".
        """
        self.config_path: str = config_path
        self.config: Dict[str, Any] = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default if file doesn't exist.
        
        Returns:
            Dict containing configuration settings.
            
        Raises:
            No exceptions are raised as errors fall back to default config.
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    config = self.DEFAULT_CONFIG.copy()
                    config.update(user_config)
                    return config
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                return self._create_default_config()
        else:
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """
        Create and save default configuration.
        
        Returns:
            Dict containing default configuration settings.
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.DEFAULT_CONFIG, f, indent=4)
        except Exception as e:
            print(f"Warning: Could not save default config: {e}")
        return self.DEFAULT_CONFIG.copy()
    
    def save_config(self) -> bool:
        """
        Save current configuration to file.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key to retrieve.
            default: Value to return if key is not found.
            
        Returns:
            The configuration value or default.
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: The configuration key to set.
            value: The value to set.
        """
        self.config[key] = value
        self.save_config()