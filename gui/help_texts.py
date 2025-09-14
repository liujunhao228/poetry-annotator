# gui/help_texts.py
# Centralized help texts for GUI components.

from .i18n import _

HELP_TEXTS = {
    # Global Configurations
    "Global.llm.service": _("The LLM service to use (e.g., 'openai', 'gemini')."),
    "Global.llm.model": _("The specific model name to use for the selected service."),
    "Global.llm.api_key": _("Your API key for the selected LLM service."),
    "Global.llm.base_url": _("The base URL for the API, if not using the default."),
    "Global.database.type": _("The type of database to use (e.g., 'sqlite')."),
    "Global.database.path": _("The file path for the database."),
    "Global.data_path.source_json_dir": _("Directory containing the source JSON files."),
    "Global.data_path.log_dir": _("Directory where logs should be stored."),
    "Global.data_path.output_dir": _("Directory for application output."),
    "Global.prompt.prompt_template_dir": _("Directory containing prompt templates."),
    "Global.logging.level": _("The logging level (e.g., 'INFO', 'DEBUG')."),
    "Global.logging.file": _("The file path for the log file."),

    # Project Configurations
    "Project.llm.service": _("Override the global LLM service for this project."),
    "Project.llm.model": _("Override the global LLM model for this project."),
    "Project.llm.models": _("Manage individual LLM model configurations, including API keys and base URLs."),
    "Project.llm.api_key": _("Override the global API key for this project."),
    "Project.llm.base_url": _("Override the global base URL for this project."),
    "Project.database.type": _("Override the global database type for this project."),
    "Project.database.path": _("Override the global database path for this project."),
    "Project.data_path.source_json_dir": _("Override the global source JSON directory for this project."),
    "Project.data_path.log_dir": _("Override the global log directory for this project."),
    "Project.data_path.output_dir": _("Override the global output directory for this project."),
    "Project.prompt.prompt_template_dir": _("Override the global prompt template directory for this project."),
    "Project.logging.level": _("Override the global logging level for this project."),
    "Project.logging.file": _("Override the global log file for this project."),
    "Project.plugins": _("Enable or disable plugins for the current project."),
}
