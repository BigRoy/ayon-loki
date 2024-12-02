"""Loki specific plugin definitions."""
from abc import (
    ABCMeta
)
import six

import pyblish.api

from ayon_core.pipeline import (
    CreatorError,
    Creator,
    CreatedInstance,
    AYON_INSTANCE_ID,
    AVALON_INSTANCE_ID,
    load,
    publish
)
from ayon_core.lib import BoolDef

from .lib import get_current_stage
# from .lib import imprint, read, lsattr

import opendcc.core
from pxr import Usd


SETTINGS_CATEGORY = "loki"


class LokiCreatorBase(object):
    @staticmethod
    def cache_instance_data(shared_data):
        """Cache instances for Creators to shared data.

        Create `loki_cached_instances` key when needed in shared data and
        fill it with all collected instances from the scene under its
        respective creator identifiers.

        Args:
            Dict[str, Any]: Shared data.

        """
        if shared_data.get("loki_cached_instances") is None:
            cache = dict()
            nodes = []
            for id_type in [AYON_INSTANCE_ID, AVALON_INSTANCE_ID]:
                nodes.extend(lsattr("id", id_type))
            for node in nodes:

                creator_identifier_parm = node.parm("creator_identifier")
                if creator_identifier_parm:
                    # creator instance
                    creator_id = creator_identifier_parm.eval()
                    cache.setdefault(creator_id, []).append(node)

            shared_data["loki_cached_instances"] = cache

        return shared_data

    @staticmethod
    def create_instance_node(
        folder_path,
        product_name,
        pre_create_data=None
    ):
        """Create node representing instance.

        Arguments:
            folder_path (str): Folder path.
            product_name (str): Name of the new node.
            pre_create_data (Optional[Dict]): Pre create data.

        Returns:
            Usd.Prim: Newly created instance prim that acts as the creator
                instance with a USD Collection API applied.

        """
        stage = get_current_stage()
        if not stage:
            raise CreatorError("No current stage found.")

        # Define parent as scope if not exists
        if not stage.GetPrimAtPath("/AYON_Instances"):
            stage.DefinePrim("/AYON_Instances", "Scope")

        # TODO: Define unique name for the instance
        prim = stage.DefinePrim(f"/AYON_Instances/{product_name}", "Scope")
        Usd.CollectionAPI.Apply(prim)
        return prim


@six.add_metaclass(ABCMeta)
class LokiCreator(Creator, LokiCreatorBase):
    """Base class for most of the Loki creator plugins."""
    settings_category = SETTINGS_CATEGORY

    def create(self, product_name, instance_data, pre_create_data):

        # Convert use selection into selection pre_create_data
        if pre_create_data.get("use_selection"):
            app = opendcc.core.Application.instance()
            pre_create_data["selection"] = app.get_selection()

        # Create prim
        instance_node = self.create_instance_node(
            instance_data["folderPath"],
            product_name,
            pre_create_data
        )

        # Define instance
        instance_data["instance_node"] = instance_node.path()
        instance_data["instance_id"] = instance_node.path()
        instance_data["families"] = self.get_publish_families()
        instance = CreatedInstance(
            self.product_type,
            product_name,
            instance_data,
            self)
        self._add_instance_to_context(instance)

        # Imprint instance data to the prim
        self.imprint(instance_node, instance.data_to_store())

        return instance

    def collect_instances(self):
        # cache instances  if missing
        self.cache_instance_data(self.collection_shared_data)
        for instance in self.collection_shared_data[
                "loki_cached_instances"].get(self.identifier, []):

            node_data = read(instance)

            # Node paths are always the full node path since that is unique
            # Because it's the node's path it's not written into attributes
            # but explicitly collected
            node_path = instance.path()
            node_data["instance_id"] = node_path
            node_data["instance_node"] = node_path
            node_data["families"] = self.get_publish_families()

            created_instance = CreatedInstance.from_existing(
                node_data, self
            )
            self._add_instance_to_context(created_instance)

    def update_instances(self, update_list):
        for created_inst, changes in update_list:
            instance_node = hou.node(created_inst.get("instance_node"))
            new_values = {
                key: changes[key].new_value
                for key in changes.changed_keys
            }
            # Update parm templates and values
            self.imprint(
                instance_node,
                new_values,
                update=True
            )

    def imprint(self, node, values, update=False):
        # Never store instance node and instance id since that data comes
        # from the node's path
        values.pop("instance_node", None)
        values.pop("instance_id", None)
        values.pop("families", None)
        imprint(node, values, update=update)

    def remove_instances(self, instances):
        """Remove specified instance from the scene.

        This is only removing `id` parameter so instance is no longer
        instance, because it might contain valuable data for artist.

        """
        for instance in instances:
            instance_node = instance.data.get("instance_node")

            # Remove the primitive from the relevant layers in the stage's
            # layer stack
            # TODO: Implement
            if instance_node:
                instance_node.destroy()

            self._remove_instance_from_context(instance)

    def get_pre_create_attr_defs(self):
        return [
            BoolDef("use_selection", default=True, label="Use selection")
        ]

    def get_publish_families(self):
        """Return families for the instances of this creator.

        Allow a Creator to define multiple families so that a creator can
        e.g. specify `usd` and `usdrop`.

        There is no need to override this method if you only have the
        primary family defined by the `product_type` property as that will
        always be set.

        Returns:
            List[str]: families for instances of this creator
        """
        return []


class LokiLoader(load.LoaderPlugin):
    """Base class for Loki load plugins."""

    hosts = ["loki"]
    settings_category = SETTINGS_CATEGORY


class LokiInstancePlugin(pyblish.api.InstancePlugin):
    """Base class for Loki instance publish plugins."""

    hosts = ["loki"]
    settings_category = SETTINGS_CATEGORY


class LokiContextPlugin(pyblish.api.ContextPlugin):
    """Base class for Loki context publish plugins."""

    hosts = ["loki"]
    settings_category = SETTINGS_CATEGORY


class LokiExtractorPlugin(publish.Extractor):
    """Base class for Loki extract plugins.

    Note:
        The `LokiExtractorPlugin` is a subclass of `publish.Extractor`,
            which in turn is a subclass of `pyblish.api.InstancePlugin`.
        Should there be a requirement to create an extractor that operates
            as a context plugin, it would be beneficial to incorporate
            the functionalities present in `publish.Extractor`.
    """

    hosts = ["loki"]
    settings_category = SETTINGS_CATEGORY
