import os
import pyblish.api

from pxr import Usd


class CollectWorkfileData(pyblish.api.InstancePlugin):
    """Inject data into Workfile instance"""

    order = pyblish.api.CollectorOrder - 0.01
    label = "Loki Workfile"
    families = ["workfile"]

    def process(self, instance):
        """Inject the current working file"""

        context = instance.context
        current_file = context.data["currentFile"]
        if not current_file:
            self.log.warning(
                "Current file is not saved. Save the file before continuing."
            )
            return

        folder, file = os.path.split(current_file)
        filename, ext = os.path.splitext(file)
        self.log.info(current_file)

        stage: Usd.Stage = context.data["stage"]

        frame_start = stage.GetStartTimeCode()
        frame_end = stage.GetEndTimeCode()

        if stage.HasAuthoredMetadata("minTimeCode"):
            frame_start_handle: float = stage.GetMetadata(
                "minTimeCode").GetValue()
            handle_start = frame_start_handle - frame_start
        else:
            handle_start = 0

        if stage.HasAuthoredMetadata("maxTimeCode"):
            frame_end_handle: float = stage.GetMetadata(
                "minTimeCode").GetValue()
            handle_end = frame_end_handle - frame_start
        else:
            handle_end = 0

        instance.data.update({  # noqa
            "frameStart": int(frame_start),
            "frameEnd": int(frame_end),
            "handleStart": int(handle_start),
            "handleEnd": int(handle_end)
        })

        instance.data.setdefault("representations", []).append({
            'name': ext.lstrip("."),
            'ext': ext.lstrip("."),
            'files': file,
            "stagingDir": folder,
        })