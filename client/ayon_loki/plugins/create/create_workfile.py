import ayon_api
from ayon_core.pipeline import CreatedInstance, AutoCreator, AYON_INSTANCE_ID
from ayon_loki.api import lib


class CreateWorkfile(AutoCreator):
    """Workfile auto-creator.

    The workfile instance stores its data on the `AYON_CONTAINERS` collection
    as custom attributes, because unlike other instances it doesn't have an
    instance node of its own.

    """
    identifier = "io.ayon.creators.loki.workfile"
    label = "Workfile"
    product_type = "workfile"
    icon = "fa5.file"

    data_key = "AYON_workfile"

    def create(self):
        """Create workfile instances."""
        workfile_instance = next(
            (
                instance for instance in self.create_context.instances
                if instance.creator_identifier == self.identifier
            ),
            None,
        )

        project_name = self.project_name
        folder_path = self.create_context.get_current_folder_path()
        task_name = self.create_context.get_current_task_name()
        host_name = self.create_context.host_name

        existing_folder_path = None
        if workfile_instance is not None:
            existing_folder_path = workfile_instance.get("folderPath")

        if not workfile_instance:
            folder_entity = ayon_api.get_folder_by_path(
                project_name, folder_path
            )
            task_entity = ayon_api.get_task_by_name(
                project_name, folder_entity["id"], task_name
            )
            product_name = self.get_product_name(
                project_name,
                folder_entity,
                task_entity,
                task_name,
                host_name,
            )
            data = {
                "folderPath": folder_path,
                "task": task_name,
                "variant": task_name,
            }

            # Enforce forward compatibility to avoid the instance to default
            # to the legacy `AVALON_INSTANCE_ID`
            data["id"] = AYON_INSTANCE_ID

            data.update(
                self.get_dynamic_data(
                    project_name,
                    folder_entity,
                    task_entity,
                    task_name,
                    host_name,
                    workfile_instance,
                )
            )
            self.log.info("Auto-creating workfile instance...")
            workfile_instance = CreatedInstance(
                self.product_type, product_name, data, self
            )
            self._add_instance_to_context(workfile_instance)

        elif (
            existing_folder_path != folder_path
            or workfile_instance["task"] != task_name
        ):
            # Update instance context if it's different
            folder_entity = ayon_api.get_folder_by_path(
                project_name, folder_path
            )
            task_entity = ayon_api.get_task_by_name(
                project_name, folder_entity["id"], task_name
            )
            product_name = self.get_product_name(
                project_name,
                folder_entity,
                task_entity,
                self.default_variant,
                host_name,
            )

            workfile_instance["folderPath"] = folder_path
            workfile_instance["task"] = task_name
            workfile_instance["productName"] = product_name

    def collect_instances(self):
        stage = lib.get_current_stage()
        if not stage:
            return

        workfile_data = stage.GetRootLayer().customLayerData.get(self.data_key)
        if not workfile_data:
            return

        # Add instance
        created_instance = CreatedInstance.from_existing(workfile_data, self)

        # Add instance to create context
        self._add_instance_to_context(created_instance)

    def update_instances(self, update_list):
        stage = lib.get_current_stage()
        if not stage:
            return

        root_layer = stage.GetRootLayer()
        layer_data = root_layer.customLayerData
        for created_inst, _changes in update_list:
            new_data = created_inst.data_to_store()
            layer_data[self.data_key] = new_data
        root_layer.customLayerData = layer_data

    def remove_instances(self, instances):
        stage = lib.get_current_stage()
        if not stage:
            return

        # Remove the custom data
        root_layer = stage.GetRootLayer()
        layer_data = root_layer.customLayerData
        layer_data.pop(self.data_key, None)
        root_layer.customLayerData = layer_data

        # Remove the instance (should only ever be one)
        for instance in instances:
            self._remove_instance_from_context(instance)
