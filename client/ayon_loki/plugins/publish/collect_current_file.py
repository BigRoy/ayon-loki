import pyblish.api
from ayon_loki import api


class CollectLokiCurrentFile(pyblish.api.ContextPlugin):
    """Inject the current working file into context"""

    order = pyblish.api.CollectorOrder - 0.5
    label = "Loki Current File"
    hosts = ["loki"]

    def process(self, context):
        """Inject the current working file"""

        current_file = api.current_file()
        context.data['currentFile'] = current_file
        if not current_file:
            self.log.warning(
                "Current file is not saved. Save the file before continuing."
            )
