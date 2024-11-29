from ayon_server.settings import BaseSettingsModel, SettingsField

from .imageio import LokiImageIOModel

DEFAULT_VALUES = {
    "imageio": {
        "activate_host_color_management": True,
        "file_rules": {
            "enabled": False,
            "rules": []
        }
    },
}


class LokiSettings(BaseSettingsModel):
    imageio: LokiImageIOModel = SettingsField(
        default_factory=LokiImageIOModel,
        title="Color Management (ImageIO)"
    )
