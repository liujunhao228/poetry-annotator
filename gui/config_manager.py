# gui/config_manager.py
# Manages GUI-specific configuration logic, interacting with backend configuration systems.

import logging
from typing import Dict, Any, Optional, List
from src.config.manager import get_config_manager, ConfigManager as BackendConfigManager
from src.config.schema import GlobalConfig, ProjectConfig # Assuming these are needed for type hinting or direct manipulation

class ConfigHandler:
    """
    Handles GUI-specific configuration logic, acting as an interface
    to the backend configuration system.
    """
    def __init__(self):
        self._backend_config_manager: BackendConfigManager = get_config_manager()
        logging.info("ConfigHandler initialized, connected to backend ConfigManager.")

    def get_global_config(self) -> GlobalConfig:
        """
        Retrieves the current global configuration.
        """
        self._backend_config_manager._load_global_config() # Ensure latest is loaded
        return self._backend_config_manager.global_config

    def save_global_config(self, config_data: Dict[str, Any]):
        """
        Saves the provided global configuration data to the backend.
        Note: This method assumes config_data is a dictionary that can be
        mapped to the GlobalConfig structure. A more robust solution might
        involve updating individual fields or using a schema-driven approach.
        For now, we'll directly update the backend's global_config object.
        """
        try:
            # Update the backend's global_config object with new values
            # This is a simplified approach. A more detailed implementation
            # would parse config_data and update specific attributes of GlobalConfig.
            # For now, we assume config_data keys directly map to GlobalConfig attributes.
            current_global_config = self._backend_config_manager.global_config
            for section_name, section_data in config_data.items():
                if hasattr(current_global_config, section_name):
                    section_obj = getattr(current_global_config, section_name)
                    for key, value in section_data.items():
                        if hasattr(section_obj, key):
                            setattr(section_obj, key, value)
            
            self._backend_config_manager.save_global_config()
            logging.info("Global configuration saved successfully.")
            return True
        except Exception as e:
            logging.error(f"Failed to save global configuration: {e}")
            return False

    def get_project_config(self) -> Optional[ProjectConfig]:
        """
        Retrieves the current project configuration.
        """
        if self._backend_config_manager.project_config:
            self._backend_config_manager._load_project_config() # Ensure latest is loaded
        return self._backend_config_manager.project_config

    def save_project_config(self, config_data: Dict[str, Any]):
        """
        Saves the provided project configuration data to the backend.
        Similar to save_global_config, this is a simplified approach.
        """
        try:
            current_project_config = self._backend_config_manager.project_config
            if current_project_config:
                for section_name, section_data in config_data.items():
                    if hasattr(current_project_config, section_name):
                        section_obj = getattr(current_project_config, section_name)
                        for key, value in section_data.items():
                            if hasattr(section_obj, key):
                                setattr(section_obj, key, value)
                self._backend_config_manager.save_project_config()
                logging.info("Project configuration saved successfully.")
                return True
            else:
                logging.warning("No project configuration loaded to save.")
                return False
        except Exception as e:
            logging.error(f"Failed to save project configuration: {e}")
            return False

    def get_available_projects(self) -> List[str]:
        """
        Retrieves a list of available project configuration names.
        """
        return self._backend_config_manager.get_available_project_configs()

    def get_active_project(self) -> str:
        """
        Retrieves the name of the currently active project.
        """
        return self._backend_config_manager.get_active_project_config()

    def switch_project(self, project_name: str) -> bool:
        """
        Switches the active project configuration.
        """
        return self._backend_config_manager.switch_project_config(project_name)

    # Potentially add methods to get schema for dynamic UI generation
    # For now, we'll assume a fixed UI structure for config panels.
