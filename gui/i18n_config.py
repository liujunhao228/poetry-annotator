# gui/i18n_config.py
import gettext

_ = gettext.gettext

CONFIG_KEY_MAP = {
    # GlobalLLMConfig
    "max_workers": _("Max Workers"),
    "max_model_pipelines": _("Max Model Pipelines"),
    "max_retries": _("Max Retries"),
    "retry_delay": _("Retry Delay"),
    "breaker_fail_max": _("Breaker Fail Max"),
    "breaker_reset_timeout": _("Breaker Reset Timeout"),
    "save_full_response": _("Save Full Response"),

    # GlobalDatabaseConfig
    "available_configs": _("Available Configs"),
    "separate_db_template": _("Separate DB Template"),

    # GlobalDataPathConfig
    # "available_configs" is already defined

    # GlobalPromptConfig
    # "available_configs" is already defined

    # GlobalLoggingConfig
    "console_log_level": _("Console Log Level"),
    "file_log_level": _("File Log Level"),
    "enable_file_log": _("Enable File Log"),
    "log_file": _("Log File"),
    "enable_console_log": _("Enable Console Log"),
    "max_file_size": _("Max File Size (MB)"),
    "backup_count": _("Backup Count"),
    "quiet_third_party": _("Quiet Third Party"),

    # GlobalVisualizerConfig
    "enable_custom_download": _("Enable Custom Download"),

    # GlobalCategoriesConfig
    "xml_path": _("XML Path"),
    "md_path": _("MD Path"),

    # GlobalModelConfigTemplate
    "provider": _("Provider"),
    "model_name": _("Model Name"),
    "api_key": _("API Key"),
    "base_url": _("Base URL"),
    "request_delay": _("Request Delay"),
    "temperature": _("Temperature"),
    "max_tokens": _("Max Tokens"),
    "timeout": _("Timeout"),

    # ProjectDatabaseConfig
    "config_name": _("Config Name"),
    "db_paths": _("DB Paths"),
    "db_path": _("DB Path"),
    "separate_db_paths": _("Separate DB Paths"),

    # ProjectDataPathConfig
    # "config_name" is already defined
    "source_dir": _("Source Directory"),
    "output_dir": _("Output Directory"),

    # ProjectPromptConfig
    # "config_name" is already defined

    # ProjectModelConfig
    "model_names": _("Model Names"),

    # ProjectPluginsConfig
    "enabled_plugins": _("Enabled Plugins"),
    "plugin_paths": _("Plugin Paths"),
    
    # Sections
    "llm": _("LLM"),
    "database": _("Database"),
    "data_path": _("Data Path"),
    "prompt": _("Prompt"),
    "logging": _("Logging"),
    "visualizer": _("Visualizer"),
    "categories": _("Categories"),
    "model_template": _("Model Template"),
    "model": _("Model"),
    "plugins": _("Plugins"),
}

def translate_config_key(k):
    """Translates a configuration key using a mapping, with a fallback."""
    return CONFIG_KEY_MAP.get(k, k.replace('_', ' ').title())
