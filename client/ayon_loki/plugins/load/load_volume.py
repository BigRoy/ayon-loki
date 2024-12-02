from ayon_core.pipeline import AYON_CONTAINER_ID
from ayon_loki.api import plugin, lib

from pxr import Sdf, Usd, UsdVol


class LoadOpenVDBAsset(plugin.LokiLoader):
    """Load OpenVDB Asset"""

    color = "orange"
    product_types = {"*"}
    icon = "cloud"
    label = "Load OpenVDB Asset"
    order = -10
    representations = {"vdb"}

    def load(self, context, name=None, namespace=None, options=None):

        stage = lib.get_current_stage()
        if not stage:
            return

        name = name or context["product"]["name"]

        path = lib.unique_path(stage, Sdf.Path(f"/{name}"))

        volume = UsdVol.OpenVDBAsset.Define(stage, path)
        self._set_filepath(volume, context)

        # TODO: We must set the following attributes on the OpenVDBAsset:
        #  fieldIndex, fieldName, fieldClass, fieldDataType
        #  For this we must parse the VDB file and get the field information
        #  However, `pyopenvdb` is not included with Loki

        # Imprint property with container metadata
        attr = volume.GetFilePathAttr()
        data = attr.GetCustomData()
        data["AYON"] = {
            "schema": "ayon:container-3.0",
            "id": AYON_CONTAINER_ID,
            "loader": self.__class__.__name__,
            "representation": context["representation"]["id"],
            "project_name": context["project"]["name"],
        }
        attr.SetCustomData(data)

    def remove(self, container):
        # TODO: Remove the volume loader from all layers in layer stack?
        spec: Sdf.PropertySpec = container["spec"]
        prim_spec: Sdf.PrimSpec = spec.owner
        lib.remove_spec(prim_spec)

    def update(self, container, context):
        # TODO: Should we update in the spec only instead of via the stage?
        spec: Sdf.PropertySpec = container["spec"]
        stage = lib.get_current_stage()
        prim = stage.GetPrimAtPath(spec.owner.path)
        volume = UsdVol.OpenVDBAsset(prim)
        self._set_filepath(volume, context)

        # Update imprinted data like representation id, project name
        data = spec.customData
        data["AYON"]["representation"] = context["representation"]["id"]
        data["AYON"]["project_name"] = context["project"]["name"]
        spec.customData = data

    def switch(self, container, context):
        self.update(container, context)

    def _set_filepath(self, volume: UsdVol.OpenVDBAsset, context):
        attr = volume.GetFilePathAttr()
        attr.Set(self.filepath_from_context(context))

    def _get_filepaths(self, context):
        # TODO: Return individual frames if a sequence so we instead set the
        #  individual frames as timesamples for all frames (or somehow use a
        #  loki expression?)
        return self.filepath_from_context(context)