name = "loki"
title = "Loki"
version = "0.1.0+dev"

# Name of client code directory imported in AYON launcher
# - do not specify if there is no client code
client_dir = "ayon_loki"
app_host_name = "loki"

# Version compatibility with AYON server
# ayon_server_version = ">=1.0.7"
# Version compatibility with AYON launcher
# ayon_launcher_version = ">=1.0.2"

# Mapping of addon name to version requirements
# - addon with specified version range must exist to be able to use this addon
ayon_required_addons = {
    "core": ">0.4.4",
}
# Mapping of addon name to version requirements
# - if addon is used in same bundle the version range must be valid
ayon_compatible_addons = {}
