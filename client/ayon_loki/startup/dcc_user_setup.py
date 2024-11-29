from ayon_core.pipeline import install_host
from ayon_loki.api import LokiHost


host = LokiHost()
install_host(host)
