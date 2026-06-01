from django.apps import AppConfig


class MainCrmConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.main_crm"
    verbose_name = "Main CRM"

    def ready(self):
        import apps.main_crm.modules.business.models  # noqa: F401
        import apps.main_crm.modules.admin.admin  # noqa: F401
