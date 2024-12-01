import os
import logging
import contextlib

import pyblish.api

from ayon_core.host import HostBase, IWorkfileHost, ILoadHost, IPublishHost
from ayon_core.pipeline import (
    register_loader_plugin_path,
    register_creator_plugin_path,
    AYON_CONTAINER_ID, get_current_context,
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
    menu.addAction("Set Colorspace")

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
        """
        if not data:
            return

        context_node = self._get_context_node(create_if_not_exists=True)
        data["id"] = plugin.AYON_INSTANCE_ID
        data["creator_identifier"] = AYON_CONTEXT_CREATOR_IDENTIFIER
        lib.imprint(context_node, data)
        """
        # TODO: Implement
        return

    def get_context_data(self):
        """
        context_node = self._get_context_node()
        if context_node is None:
            return {}

        data = lib.read(context_node)

        # Pop our custom data that we use to find the node again
        data.pop("id", None)
        data.pop("creator_identifier", None)

        return data
        """
        # TODO: Implement
        return {}


def parse_container(container):
    """Return the container node's full container data.

    Args:
        container (str): A container node name.

    Returns:
        dict[str, Any]: The container schema data for this container node.

    """
    return {}
    # TODO: Implement
    # data = lib.read(container)
    #
    # # Backwards compatibility pre-schemas for containers
    # data["schema"] = data.get("schema", "ayon:container-3.0")
    #
    # # Append transient data
    # data["objectName"] = container.GetName()
    # data["node"] = container
    #
    # return data


def iter_containers(doc=None):
    """Yield all objects in the active document that have 'id' attribute set
    matching an AYON container ID"""
    if False:
        yield
    return
    # TODO: Implement
    # for container in containers:
    #     if container_id != AYON_CONTAINER_ID:  # noqa
    #         continue
    #
    #     data = parse_container(container)
    #     yield data


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
    pass
    # container_name = lib.get_unique_namespace(
    #     name,
    #     prefix=namespace + "_",
    #     suffix=suffix
    # )
    # with lib.undo_chunk():
    #     container = c4d.BaseObject(c4d.Oselection)
    #     container.SetName(container_name)
    #     in_exclude_data = container[c4d.SELECTIONOBJECT_LIST]
    #     for node in nodes:
    #         in_exclude_data.InsertObject(node, 1)
    #     container[c4d.SELECTIONOBJECT_LIST] = in_exclude_data
    #     doc = lib.active_document()
    #     doc.InsertObject(container)
    #
    #     imprint_container(
    #         container,
    #         name,
    #         namespace,
    #         context,
    #         loader
    #     )
    #
    #     # Add the container to the AYON_CONTAINERS layer
    #     avalon_layer = get_containers_layer(doc=doc)
    #     container.SetLayerObject(avalon_layer)
    #     # Hide the container in the Object Manager
    #     # container.ChangeNBit(c4d.NBIT_OHIDE, c4d.NBITCONTROL_SET)
    #     c4d.EventAdd()
    #
    # return container


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
    # TODO: implement
    # lib.imprint(container, data, group="AYON")
