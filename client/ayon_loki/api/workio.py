"""Host API required Work Files tool"""
from typing import Optional
from pxr import Sdf

import opendcc.core
import opendcc.file_menu
import opendcc.stage_utils

from .lib import get_current_stage, get_session


def file_extensions() -> list[str]:
    return [".usd", ".usda", ".usdc", ".usdz"]


def has_unsaved_changes() -> bool:
    stage = get_current_stage()
    if not stage:
        return False

    # Based on `opendcc.close_event_filter` we check the edit target layer
    layer = stage.GetEditTarget().GetLayer()
    if layer.anonymous or layer.dirty:
        return True

    # And for sake of completeness we check the root layer
    layer = stage.GetRootLayer()
    if layer.anonymous or layer.dirty:
        return True
    return False


def save_file(filepath=None):
    session = get_session()
    stage = get_current_stage()
    if stage is None:
        raise RuntimeError(
            "No active stage to save. Create or open a stage first.")

    layer = stage.GetRootLayer()
    if filepath is None:
        layer.Save()

    # Based on opendcc.file_menu `on_save` logic
    # Check if saving to different suffix, if so we reopen the layer
    old_suffix = layer.GetFileFormat().formatId.lower()
    new_suffix = filepath.split(".")[-1].lower()
    if old_suffix != new_suffix:
        new_layer = Sdf.Layer.FindOrOpen(filepath)
        if new_layer:
            new_layer.Clear()
        else:
            new_layer = Sdf.Layer.CreateNew(filepath)
        new_layer.TransferContent(layer)
        new_layer.Save()
        opendcc.file_menu.add_recent_file(new_layer.identifier)
        opendcc.stage_utils.open_stage(new_layer.identifier)

    # Otherwise just update current layer
    layer.identifier = filepath
    layer.Save()
    opendcc.file_menu.add_recent_file(layer.identifier)

    # force ui update
    session.force_update_stage_list()


def open_file(filepath):
    result = get_session().open_stage(filepath)
    opendcc.file_menu.add_recent_file(filepath)


def current_file() -> Optional[str]:
    stage = get_current_stage()
    if not stage:
        return
    return stage.GetRootLayer().identifier
