from ayon_core.pipeline import load
from ayon_loki.api import lib

from pxr import Sdf


def _set_frame_range(frame_start: int, frame_end: int, fps: float):
    stage = lib.get_current_stage()
    if not stage:
        return

    stage.SetFramesPerSecond(fps)
    stage.SetStartTimeCode(frame_start)
    stage.SetEndTimeCode(frame_end)

    # Set custom metadata specific to Loki for internal animation frame range
    if stage.HasAuthoredMetadata("minTimeCode"):
        stage.SetMetadata("minTimeCode", Sdf.TimeCode(frame_start))
    if stage.HasAuthoredMetadata("maxTimeCode"):
        stage.SetMetadata("maxTimeCode", Sdf.TimeCode(frame_end))


class SetFrameRangeLoader(load.LoaderPlugin):
    """Set frame range excluding pre- and post-handles"""

    product_types = {
        "animation",
        "camera",
        "pointcache",
        "vdbcache",
        "usd",
        "render",
        "plate",
        "mayaScene",
        "review"
    }
    representations = {"*"}

    label = "Set frame range"
    order = 11
    icon = "clock-o"
    color = "white"

    def load(self, context, name=None, namespace=None, options=None):

        version_attributes = context["version"]["attrib"]

        frame_start = version_attributes.get("frameStart")
        frame_end = version_attributes.get("frameEnd")
        if frame_start is None or frame_end is None:
            print(
                "Skipping setting frame range because start or "
                "end frame data is missing.."
            )
            return

        fps = version_attributes["fps"]
        _set_frame_range(frame_start, frame_end, fps)


class SetFrameRangeWithHandlesLoader(load.LoaderPlugin):
    """Set frame range including pre- and post-handles"""

    product_types = {
        "animation",
        "camera",
        "pointcache",
        "vdbcache",
        "usd",
        "render",
        "plate",
        "mayaScene",
        "review"
    }
    representations = {"*"}

    label = "Set frame range (with handles)"
    order = 12
    icon = "clock-o"
    color = "white"

    def load(self, context, name=None, namespace=None, options=None):

        version_attributes = context["version"]["attrib"]

        frame_start = version_attributes.get("frameStart")
        frame_end = version_attributes.get("frameEnd")
        if frame_start is None or frame_end is None:
            print(
                "Skipping setting frame range because start or "
                "end frame data is missing.."
            )
            return

        # Include handles
        frame_start -= version_attributes.get("handleStart", 0)
        frame_end += version_attributes.get("handleEnd", 0)

        fps = version_attributes["fps"]
        _set_frame_range(frame_start, frame_end, fps)
