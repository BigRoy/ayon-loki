import pyblish.api

from ayon_loki.api import lib


class CollectCurrentStage(pyblish.api.ContextPlugin):
    """Inject the session's current stage into context"""

    order = pyblish.api.CollectorOrder - 0.5
    label = "Loki Stage"
    hosts = ['loki']

    def process(self, context):
        context.data['stage'] = lib.get_current_stage()
