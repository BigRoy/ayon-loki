import os
from ayon_core.addon import AYONAddon, IHostAddon

from .version import __version__

LOKI_ADDON_ROOT = os.path.dirname(os.path.abspath(__file__))


class LokiAddon(AYONAddon, IHostAddon):
    name = "loki"
    version = __version__
    host_name = "loki"

    def add_implementation_envs(self, env, app):
        # Set default values if are not already set via settings
        defaults = {"AYON_LOG_NO_COLORS": "1"}
        for key, value in defaults.items():
            if not env.get(key):
                env[key] = value

        # Add the startup to PYTHONPATH
        env["PYTHONPATH"] = os.pathsep.join([
            os.path.join(LOKI_ADDON_ROOT, "startup"),
            env.get("PYTHONPATH", "")
        ])

    def get_workfile_extensions(self):
        return [".usd", ".usda", ".usdc", ".usdz"]
