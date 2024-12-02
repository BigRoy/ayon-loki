import os
import logging
import contextlib
from typing import Any

import pyblish.api

from ayon_core.host import HostBase, IWorkfileHost, ILoadHost, IPublishHost
from ayon_core.pipeline import (
    register_loader_plugin_path,
    register_creator_plugin_path,
    AYON_CONTAINER_ID,
    get_current_context,
)
from ayon_core.tools.utils import host_tools

from .workio import (
    open_file,
    save_file,
    file_extensions,
    has_unsaved_changes,
    current_file
)
import ayon_loki

from qtpy import QtCore
from pxr import Sdf, Usd

from . import lib

log = logging.getLogger("ayon_loki")

HOST_DIR = os.path.dirname(os.path.abspath(ayon_loki.__file__))
PLUGINS_DIR = os.path.join(HOST_DIR, "plugins")
PUBLISH_PATH = os.path.join(PLUGINS_DIR, "publish")
LOAD_PATH = os.path.join(PLUGINS_DIR, "load")
CREATE_PATH = os.path.join(PLUGINS_DIR, "create")
INVENTORY_PATH = os.path.join(PLUGINS_DIR, "inventory")

AYON_CONTAINERS = lib.AYON_CONTAINERS
AYON_CONTEXT_CREATOR_IDENTIFIER = "io.ayon.create.context"
AYON_CONTEXT_DATA_KEY = "AYON_Context"


def defer(fn):
    """Defer the callable function.

    This allows us to run the code at the time the
    main window has initialized, so we can customize
    the UI to our needs - like adding a menu entry.
    """
    QtCore.QTimer.singleShot(0, fn)


def get_current_context_label() -> str:
    # Return folder path, task name
    context = get_current_context()
    folder_path = context["folder_path"]
    task_name = context["task_name"]
    return f"{folder_path}, {task_name}"


def install_menu():
    main_window = lib.get_main_window()
    menubar = main_window.menuBar()

    menu = menubar.addMenu("AYON")

    # Current context
    menu.addSection("Context")
    context_action = menu.addAction("<context>")

    def _update_context_label():
        context_action.setText(get_current_context_label())
    menu.aboutToShow.connect(_update_context_label)

    # Tools
    menu.addSection("Tools")
    menu.addAction(
        "Create...",
        lambda: host_tools.show_publisher(
            parent=main_window,
            tab="create"
        )
    )
    menu.addAction(
        "Load...",
        lambda: host_tools.show_loader(
            parent=main_window,
            use_context=True
        )
    )
    menu.addAction(
        "Manage...",
        lambda: host_tools.show_scene_inventory(parent=main_window)
    )
    menu.addAction(
        "Publish...",
        lambda: host_tools.show_publisher(
            parent=main_window,
            tab="publish"
        )
    )

    # Workfiles
    menu.addSection("Workfiles")
    menu.addAction(
        "Workfiles",
        lambda: host_tools.show_workfiles(parent=main_window)
    )
    menu.addAction("Set Frame Range", lib.reset_frame_range)
    # menu.addAction("Set Colorspace")  # TODO: Implement

    menu.addSection("Experimental")
    menu.addAction(
        "Experimental Tools...",
        lambda: host_tools.show_experimental_tools_dialog(parent=main_window)
    )


class LokiHost(HostBase, IWorkfileHost, ILoadHost, IPublishHost):
    name = "loki"

    def __init__(self):
        super(LokiHost, self).__init__()

    def install(self):
        # process path mapping
        # dirmap_processor = LokiDirmap("loki", project_settings)
        # dirmap_processor.process_dirmap()

        pyblish.api.register_plugin_path(PUBLISH_PATH)
        pyblish.api.register_host("loki")

        register_loader_plugin_path(LOAD_PATH)
        register_creator_plugin_path(CREATE_PATH)
        # TODO: Register only when any inventory actions are created
        # register_inventory_action_path(INVENTORY_PATH)

        defer(install_menu)

    def open_workfile(self, filepath):
        return open_file(filepath)

    def save_workfile(self, filepath=None):
        return save_file(filepath)

    def get_current_workfile(self):
        return current_file()

    def workfile_has_unsaved_changes(self):
        return has_unsaved_changes()

    def get_workfile_extensions(self):
        return file_extensions()

    def get_containers(self):
        return iter_containers()

    @contextlib.contextmanager
    def maintained_selection(self):
        with lib.maintained_selection():
            yield

    def update_context_data(self, data, changes):
        if not data:
            return

        stage = lib.get_current_stage()
        if not stage:
            return

        root_layer = stage.GetRootLayer()
        layer_data = root_layer.customLayerData
        layer_data[AYON_CONTEXT_DATA_KEY] = data
        root_layer.customLayerData = layer_data

    def get_context_data(self):
        stage = lib.get_current_stage()
        if not stage:
            return {}

        root_layer = stage.GetRootLayer()
        return root_layer.customLayerData.get(AYON_CONTEXT_DATA_KEY, {})


def iter_containers():
    """Yield all objects in the active document that have 'id' attribute set
    matching an AYON container ID"""

    stage = lib.get_current_stage()
    if not stage:
        return

    # Iterate all "local scene layers" which we'll consider to be the root
    # layer and any sublayers. We do not traverse into references or payloads
    # assuming they are completely external.
    root_layer = stage.GetRootLayer()
    layers: list[Sdf.Layer] = [root_layer] + list(root_layer.subLayerPaths)
    for layer in layers:
        containers: list[dict[str, Any]] = []

        def _collect_containers(path: Sdf.Path):
            spec = layer.GetObjectAtPath(path)

            # Check for AYON metadata on property specs
            if isinstance(spec, Sdf.PropertySpec):
                data = spec.customData.get("AYON", {})
                if data.get("id") != AYON_CONTAINER_ID:
                    return

                spec_container = data
                spec_container["spec"] = spec

                # TODO: Are these required values?
                spec_container["objectName"] = spec.name
                spec_container["namespace"] = path.pathString
                spec_container["name"] = layer.identifier

                containers.append(spec_container)

            if isinstance(spec, Sdf.PrimSpec):
                # Query references for potential containers from their metadata

                for key in lib.USD_LIST_ATTRS:
                    for ref in getattr(spec.referenceList, key):
                        data = ref.customData.get("AYON", {})
                        if data.get("id") != AYON_CONTAINER_ID:
                            continue

                        spec_container = data
                        spec_container["spec"] = spec
                        spec_container["reference"] = ref

                        # TODO: Are these required values?
                        spec_container["objectName"] = spec.name
                        spec_container["namespace"] = path.pathString
                        spec_container["name"] = layer.identifier

                        containers.append(spec_container)

        layer.Traverse("/", _collect_containers)
        for container in containers:
            yield container


def containerise(name,
                 namespace,
                 nodes,
                 context,
                 loader,
                 suffix="_CON"):
    """Bundle `nodes` into an assembly and imprint it with metadata

    Containerisation enables a tracking of version, author and origin
    for loaded assets.

    Arguments:
        name (str): Name of resulting assembly
        namespace (str): Namespace under which to host container
        nodes (list): Long names of nodes to containerise
        context (dict): Asset information
        loader (str): Name of loader used to produce this container.
        suffix (str, optional): Suffix of container, defaults to `_CON`.

    Returns:
        container (Usd.Prim): USD Primitive representing the container

    """
    # TODO: Implement
    pass


def imprint_container(
    container,
    name,
    namespace,
    context,
    loader
):
    """Imprints an object with container metadata and hides it from the user
    by adding it into a hidden layer.
    Arguments:
        container (Usd.Prim): The object to imprint.
        name (str): Name of resulting assembly
        namespace (str): Namespace under which to host container
        context (dict): Asset information
        loader (str): Name of loader used to produce this container.
    """
    data = {
        "schema": "ayon:container-3.0",
        "id": AYON_CONTAINER_ID,
        "name": name,
        "namespace": namespace,
        "loader": str(loader),
        "representation": context["representation"]["id"],
        "project_name": context["project"]["name"],
    }

    # Use custom data of a property if we can
    if isinstance(container, Usd.Property):
        custom_data = container.GetCustomData()
        custom_data["AYON"] = data
        container.SetCustomData(custom_data)
        return True

    # TODO: implement imprinting prim
    # lib.imprint(container, data, group="AYON")

    return False
