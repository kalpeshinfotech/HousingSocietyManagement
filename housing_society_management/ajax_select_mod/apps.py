from django.apps import AppConfig


class AjaxSelectConfig(AppConfig):

    """
    Django 1.7+ enables initializing installed applications
    and autodiscovering modules.

    On startup, search for and import any modules called `lookups.py` in all installed apps.
    Your LookupClass subclass may register itself.
    """

    name = 'ajax_select'
    verbose_name = 'Ajax Selects'

    def ready(self):
        from .registry import registry
        registry.load_channels()
