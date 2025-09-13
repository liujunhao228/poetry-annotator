import gettext
import os

LOCALE_DIR = os.path.join(os.path.dirname(__file__), 'locale')
DOMAIN = 'app'
LANG = 'zh_CN' # Default to Chinese, or detect from config/system

def setup_i18n():
    """
    Sets up the gettext translation system.
    """
    gettext.bindtextdomain(DOMAIN, LOCALE_DIR)
    gettext.textdomain(DOMAIN)
    try:
        translator = gettext.translation(DOMAIN, LOCALE_DIR, languages=[LANG])
        translator.install()
    except FileNotFoundError:
        print(f"Warning: Translation file for {LANG} not found in {LOCALE_DIR}")

# Initialize gettext when this module is imported
setup_i18n()

# Expose the translation function
_ = gettext.gettext
