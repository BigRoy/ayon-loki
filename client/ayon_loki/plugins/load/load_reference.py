from ayon_core.pipeline import AYON_CONTAINER_ID
from ayon_loki.api import plugin, lib

from pxr import Sdf


class ReferenceLoader(plugin.LokiLoader):
    """Load the camera."""

    color = "orange"
    product_types = {"*"}
    icon = "code-fork"
    label = "Load Reference"
    order = -10
    representations = {"usd", "abc"}

    def load(self, context, name=None, namespace=None, options=None):

        stage = lib.get_current_stage()
        if not stage:
            return

        filepath = self.filepath_from_context(context)

        name = name or context["product"]["name"]

        path = lib.unique_path(stage, Sdf.Path(f"/{name}"))
        prim = stage.DefinePrim(path)

        data = {}
        data["AYON"] = {
            "schema": "ayon:container-3.0",
            "id": AYON_CONTAINER_ID,
            "loader": self.__class__.__name__,
            "representation": context["representation"]["id"],
            "project_name": context["project"]["name"],
        }

        reference = Sdf.Reference(
            assetPath=filepath,
            primPath=Sdf.Path(),
            layerOffset=Sdf.LayerOffset(),
            customData=data
        )
        prim.GetReferences().AddReference(reference)

    def remove(self, container):
        spec: Sdf.PrimSpec = container["spec"]
        lib.remove_spec(spec)

    def update(self, container, context):
        spec: Sdf.PrimSpec = container["spec"]
        reference: Sdf.Reference = container["reference"]

        filepath = self.filepath_from_context(context)

        # Replace the Sdf.Reference with a new one
        for key in lib.USD_LIST_ATTRS:
            reference_list = getattr(spec.referenceList, key)
            for index, ref in enumerate(reference_list):
                if ref != reference:
                    continue

                data = ref.customData

                # Update representation data
                data["AYON"]["representation"] = context["representation"]["id"]
                data["AYON"]["project_name"] = context["project"]["name"]

                # Replace this index with the new SdfReference
                reference_list[index] = Sdf.Reference(
                    assetPath=filepath,
                    primPath=ref.primPath,
                    layerOffset=ref.layerOffset,
                    customData=data
                )

                # We should only ever update one
                return

    def switch(self, container, context):
        self.update(container, context)