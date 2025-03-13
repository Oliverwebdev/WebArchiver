import os
import json
from typing import Dict, List, Any, Optional, Union


class SessionManager:
    """
    Manages application session state.
    
    This class handles loading, saving, and accessing session data such as
    recent URLs, UI state, and pending operations to provide continuity
    between application runs.
    """
    
    def __init__(self, session_file: str = "session.json") -> None:
        """
        Initialize the SessionManager.
        
        Args:
            session_file: Path to the session file. Defaults to "session.json".
        """
        self.session_file: str = session_file
        self.session_data: Dict[str, Any] = self._load_session()
    
    def _load_session(self) -> Dict[str, Any]:
        """
        Load session data from file or create new session if file doesn't exist.
        
        Returns:
            Dict containing session data.
        """
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._create_new_session()
        else:
            return self._create_new_session()
    
    def _create_new_session(self) -> Dict[str, Any]:
        """
        Create a new session with default values.
        
        Returns:
            Dict containing default session data.
        """
        return {
            "recent_urls": [],
            "last_batch_urls": "",
            "pending_downloads": [],
            "ui_state": {
                "selected_tab": 0,
                "search_term": ""
            }
        }
        
    def save_session(self) -> bool:
        """
        Save current session data to file.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False
    
    def add_recent_url(self, url: str) -> None:
        """
        Add a URL to the recent URLs list.
        
        If the URL is already in the list, it will be moved to the top.
        The list is limited to 10 items.
        
        Args:
            url: The URL to add.
        """
        if url in self.session_data["recent_urls"]:
            self.session_data["recent_urls"].remove(url)
        self.session_data["recent_urls"].insert(0, url)
        self.session_data["recent_urls"] = self.session_data["recent_urls"][:10]
        self.save_session()
    
    def get_recent_urls(self) -> List[str]:
        """
        Get the list of recent URLs.
        
        Returns:
            List of recent URLs.
        """
        return self.session_data["recent_urls"]
    
    def set_batch_urls(self, urls_text: str) -> None:
        """
        Set the batch URLs text.
        
        Args:
            urls_text: Text containing multiple URLs, typically one per line.
        """
        self.session_data["last_batch_urls"] = urls_text
        self.save_session()
    
    def get_batch_urls(self) -> str:
        """
        Get the batch URLs text.
        
        Returns:
            Text containing multiple URLs.
        """
        return self.session_data["last_batch_urls"]
    
    def set_ui_state(self, key: str, value: Any) -> None:
        """
        Set a UI state value.
        
        Args:
            key: The UI state key to set.
            value: The value to set.
        """
        self.session_data["ui_state"][key] = value
        self.save_session()
    
    def get_ui_state(self, key: str, default: Any = None) -> Any:
        """
        Get a UI state value.
        
        Args:
            key: The UI state key to retrieve.
            default: Value to return if key is not found.
            
        Returns:
            The UI state value or default.
        """
        return self.session_data["ui_state"].get(key, default)