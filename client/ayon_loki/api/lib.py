"""Library functions for ShapeFX Loki."""
import contextlib

from ayon_core.lib import NumberDef
from ayon_core.pipeline.context_tools import get_current_task_entity

from pxr import Sdf, Usd

import opendcc.core

AYON_CONTAINERS = "AYON_CONTAINERS"
JSON_PREFIX = "JSON::"

# USD ReferenceList/PayloadList keys
USD_LIST_ATTRS = [
    "addedItems", 
    "appendedItems", 
    "deletedItems", 
    "explicitItems",
    "orderedItems", 
    "prependedItems"
]


def get_session() -> opendcc.core.Session:
    app = opendcc.core.Application.instance()
    return app.get_session()


def get_current_stage() -> Usd.Stage:
    return get_session().get_current_stage()


def collect_animation_defs(create_context, fps=False):
    """Get the basic animation attribute definitions for the publisher.

    Arguments:
        create_context (CreateContext): The context of publisher will be
            used to define the defaults for the attributes to use the current
            context's entity frame range as default values.
        step (bool): Whether to include `step` attribute definition.
        fps (bool): Whether to include `fps` attribute definition.

    Returns:
        List[NumberDef]: List of number attribute definitions.

    """

    # use task entity attributes to set defaults based on current context
    task_entity = create_context.get_current_task_entity()
    attrib: dict = task_entity["attrib"]
    frame_start: int = attrib["frameStart"]
    frame_end: int = attrib["frameEnd"]
    handle_start: int = attrib["handleStart"]
    handle_end: int = attrib["handleEnd"]

    # build attributes
    defs = [
        NumberDef("frameStart",
                  label="Frame Start",
                  default=frame_start,
                  decimals=0),
        NumberDef("frameEnd",
                  label="Frame End",
                  default=frame_end,
                  decimals=0),
        NumberDef("handleStart",
                  label="Handle Start",
                  tooltip="Frames added before frame start to use as handles.",
                  default=handle_start,
                  decimals=0),
        NumberDef("handleEnd",
                  label="Handle End",
                  tooltip="Frames added after frame end to use as handles.",
                  default=handle_end,
                  decimals=0),
    ]

    if fps:
        stage = get_current_stage()
        if stage:
            current_fps = stage.GetFramesPerSecond()
        else:
            # Assume USD default
            current_fps = 24.0
        fps_def = NumberDef(
            "fps", label="FPS", default=current_fps, decimals=5
        )
        defs.append(fps_def)

    return defs


def get_main_window():
    """Get ShapeFX Loki Qt Main Window"""
    app = opendcc.core.Application.instance()
    return app.get_main_window()


@contextlib.contextmanager
def maintained_selection():
    """Maintain selection during context."""
    app = opendcc.core.Application.instance()
    selection = app.get_selection()
    try:
        yield
    finally:
        opendcc.cmds.select(selection, replace=True)


def reset_frame_range():
    task_entity = get_current_task_entity()

    frame_start = task_entity["attrib"]["frameStart"]
    frame_end = task_entity["attrib"]["frameEnd"]
    handle_start = task_entity["attrib"]["handleStart"]
    handle_end = task_entity["attrib"]["handleEnd"]
    fps = task_entity["attrib"]["fps"]
    frame_start_handle = frame_start - handle_start
    frame_end_handle = frame_end + handle_end

    stage = get_current_stage()

    stage.SetStartTimeCode(frame_start_handle)
    stage.SetEndTimeCode(frame_end_handle)
    stage.SetFramesPerSecond(fps)

    # Set custom metadata specific to Loki for internal animation frame range
    stage.SetMetadata("minTimeCode", Sdf.TimeCode(frame_start))
    stage.SetMetadata("maxTimeCode", Sdf.TimeCode(frame_end))


def unique_path(stage: Usd.Stage, prim_path: Sdf.Path) -> Sdf.Path:
    """Return Sdf.Path that is unique under the current composed stage.

    Note that this technically does not ensure that the Sdf.Path does not
    exist in any of the layers, e.g. it could be defined within a currently
    unselected variant or a muted layer.

    """
    src = prim_path.pathString.rstrip("123456789")
    i = 1
    while stage.GetPrimAtPath(prim_path):
        prim_path = Sdf.Path(f"{src}{i}")
        i += 1
    return prim_path


def remove_prim(prim: Usd.Prim):
    specs = prim.GetPrimStack()
    with Sdf.ChangeBlock():
        for spec in specs:
            if spec.expired:
                continue

            # Warning: This would also remove it from layers from
            #   references/payloads!
            # TODO: Filter specs for which their `.getLayer()` is a layer
            #   from the Stage's layer stack?
            remove_spec(spec)


def remove_spec(spec):
    """Remove Sdf.Spec authored opinion."""
    if spec.expired:
        return

    if isinstance(spec, Sdf.PrimSpec):
        # PrimSpec
        parent = spec.nameParent
        if parent:
            view = parent.nameChildren
        else:
            # Assume PrimSpec is root prim
            view = spec.layer.rootPrims
        del view[spec.name]

    elif isinstance(spec, Sdf.PropertySpec):
        # Relationship and Attribute specs
        del spec.owner.properties[spec.name]

    elif isinstance(spec, Sdf.VariantSetSpec):
        # Owner is Sdf.PrimSpec (or can also be Sdf.VariantSpec)
        del spec.owner.variantSets[spec.name]

    elif isinstance(spec, Sdf.VariantSpec):
        # Owner is Sdf.VariantSetSpec
        spec.owner.RemoveVariant(spec)

    else:
        raise TypeError(f"Unsupported spec type: {spec}")
