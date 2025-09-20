# gui/config_manager.py
# Manages GUI-specific configuration logic, interacting with backend configuration systems.

import logging
import os
from typing import Dict, Any, Optional, List
from src.config.manager import get_config_manager, ConfigManager as BackendConfigManager
from src.config.schema import GlobalConfig, ProjectConfig # Assuming these are needed for type hinting or direct manipulation
from src.config.model_manager import ModelManager
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
                        if section_name == 'plugins':
                            # Special handling for ProjectPluginsConfig
                            section_obj.plugins = section_data.plugins
                        elif section_name == 'model':
                            # Special handling for ProjectModelConfig
                            section_obj.model_names = section_data.model_names
                        else:
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

    def get_llm_models(self) -> Dict[str, Any]:
        """
        Retrieves the LLM models configuration.
        """
        models = {}
        model_names = self._backend_config_manager.model_manager.list_model_configs()
        for name in model_names:
            models[name] = self._backend_config_manager.model_manager.get_model_config(name)
        return models

    def save_llm_models(self, models_data: Dict[str, Any]):
        """
        Saves the LLM models configuration.
        """
        try:
            # This is a simplified approach. A more robust implementation would
            # handle additions and removals of models properly.
            for model_name, model_config in models_data.items():
                self._backend_config_manager.model_manager.add_model_section(model_name, model_config)
            logging.info("LLM models configuration saved successfully.")
            return True
        except Exception as e:
            logging.error(f"Failed to save LLM models configuration: {e}")
            return False

    def list_all_model_names(self) -> List[str]:
        """
        Lists all available model configuration names from the ModelManager.
        """
        return self._backend_config_manager.model_manager.list_model_configs()

    def get_single_model_config(self, model_name: str) -> Dict[str, Any]:
        """
        Retrieves the detailed configuration for a single model from the ModelManager.
        """
        return self._backend_config_manager.model_manager.get_model_config(model_name)

    def save_single_model_config(self, model_name: str, config_data: Dict[str, Any]) -> bool:
        """
        Saves or updates the configuration for a single model using the ModelManager.
        """
        try:
            self._backend_config_manager.model_manager.add_model_section(model_name, config_data)
            logging.info(f"Model configuration for '{model_name}' saved successfully.")
            return True
        except Exception as e:
            logging.error(f"Failed to save model configuration for '{model_name}': {e}")
            return False

    def delete_single_model_config(self, model_name: str) -> bool:
        """
        Deletes a single model configuration using the ModelManager.
        """
        try:
            self._backend_config_manager.model_manager.remove_model_section(model_name)
            logging.info(f"Model configuration for '{model_name}' deleted successfully.")
            return True
        except Exception as e:
            logging.error(f"Failed to delete model configuration for '{model_name}': {e}")
            return False

    def get_plugins_config(self):
        """
        Retrieves the project plugins configuration.
        """
        return self._backend_config_manager.get_project_plugins_config()

    def get_database_name(self) -> Optional[str]:
        """
        Extracts the database name from the project's output_dir path.
        """
        project_config = self.get_project_config()
        if project_config and project_config.data_path and project_config.data_path.output_dir:
            # e.g., "data/SocialPoemAnalysis" -> "SocialPoemAnalysis"
            return os.path.basename(project_config.data_path.output_dir)
        return None
