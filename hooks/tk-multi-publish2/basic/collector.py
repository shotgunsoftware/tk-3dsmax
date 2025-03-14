# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sgtk
from sgtk.platform.qt import QtGui

import pymxs


HookBaseClass = sgtk.get_hook_baseclass()


class MaxSessionCollector(HookBaseClass):
    """
    Collector that operates on the max session. Should inherit from the basic
    collector hook.
    """

    @property
    def settings(self):
        """
        Dictionary defining the settings that this collector expects to receive
        through the settings parameter in the process_current_session and
        process_file methods.

        A dictionary on the following form::

            {
                "Settings Name": {
                    "type": "settings_type",
                    "default": "default_value",
                    "description": "One line description of the setting"
            }

        The type string should be one of the data types that toolkit accepts as
        part of its environment configuration.
        """

        # grab any base class settings
        collector_settings = super().settings or {}

        # settings specific to this collector
        max_session_settings = {
            "Work Template": {
                "type": "template",
                "default": None,
                "description": "Template path for artist work files. Should "
                "correspond to a template defined in "
                "templates.yml. If configured, is made available"
                "to publish plugins via the collected item's "
                "properties. ",
            }
        }

        # update the base settings with these settings
        collector_settings.update(max_session_settings)

        return collector_settings

    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current session open in Max and parents a subtree of
        items under the parent_item passed in.

        :param parent_item: Root item instance
        """

        # create an item representing the current max session
        item = self.collect_current_max_session(settings, parent_item)
        project_root = item.properties["project_root"]

        # if we can determine a project root, collect other files to publish
        if project_root:

            self.logger.info(
                "Current Max project is: %s." % (project_root,),
                extra={
                    "action_button": {
                        "label": "Change Project",
                        "tooltip": "Change to a different Max project",
                        "callback": _set_project,
                    }
                },
            )

            self.collect_previews(item, project_root)
            self.collect_exports(item, project_root)

        else:

            self.logger.warning(
                "Could not determine the current Max project.",
                extra={
                    "action_button": {
                        "label": "Set Project",
                        "tooltip": "Set the Max project",
                        "callback": _set_project,
                    }
                },
            )

        self.collect_session_geometry(item)

    def collect_current_max_session(self, settings, parent_item):
        """
        Creates an item that represents the current max session.

        :param parent_item: Parent Item instance
        :returns: Item of type max.session
        """

        publisher = self.parent

        path = _session_path()

        # determine the display name for the item
        if path:
            file_info = publisher.util.get_file_path_components(path)
            display_name = file_info["filename"]
        else:
            display_name = "Current Max Session"

        # create the session item for the publish hierarchy
        session_item = parent_item.create_item(
            "3dsmax.session", "3dsmax Session", display_name
        )

        # get the icon path to display for this item
        icon_path = os.path.join(self.disk_location, os.pardir, "icons", "3dsmax.png")
        session_item.set_icon_from_path(icon_path)

        # discover the project root which helps in discovery of other
        # publishable items
        project_root = _get_project_folder_dir()
        session_item.properties["project_root"] = project_root

        # if a work template is defined, add it to the item properties so
        # that it can be used by attached publish plugins
        work_template_setting = settings.get("Work Template")
        if work_template_setting:
            work_template = publisher.engine.get_template_by_name(
                work_template_setting.value
            )

            # store the template on the item for use by publish plugins. we
            # can't evaluate the fields here because there's no guarantee the
            # current session path won't change once the item has been created.
            # the attached publish plugins will need to resolve the fields at
            # execution time.
            session_item.properties["work_template"] = work_template
            self.logger.debug("Work template defined for Maya collection.")

        self.logger.info("Collected current 3dsMax session")

        return session_item

    def collect_exports(self, parent_item, project_root):
        """
        Creates items for exported files

        :param parent_item: Parent Item instance
        :param str project_root: The Max project root to search for exports
        """

        # ensure the alembic cache dir exists
        cache_dir = os.path.join(project_root, "export")
        if not os.path.exists(cache_dir):
            return

        self.logger.info(
            "Processing export folder: %s" % (cache_dir,),
            extra={"action_show_folder": {"path": cache_dir}},
        )

        # look for alembic files in the cache folder
        for filename in os.listdir(cache_dir):
            export_path = os.path.join(cache_dir, filename)

            # allow the base class to collect and create the item. it knows how
            # to handle various files
            super()._collect_file(parent_item, export_path)

    def collect_previews(self, parent_item, project_root):
        """
        Creates items for previews.

        Looks for a 'project_root' property on the parent item, and if such
        exists, look for movie files in a 'movies' subfolder.

        :param parent_item: Parent Item instance
        :param str project_root: The Max project root to search for previews
        """

        # ensure the movies dir exists
        movies_dir = _get_preview_dir()
        if not os.path.exists(movies_dir):
            return

        self.logger.info(
            "Processing movies folder: %s" % (movies_dir,),
            extra={"action_show_folder": {"path": movies_dir}},
        )

        # look for movie files in the movies folder
        for filename in os.listdir(movies_dir):

            # do some early pre-processing to ensure the file is of the right
            # type. use the base class item info method to see what the item
            # type would be.
            item_info = self._get_item_info(filename)
            if item_info["item_type"] != "file.video":
                continue

            movie_path = os.path.join(movies_dir, filename)

            # allow the base class to collect and create the item. it knows how
            # to handle movie files
            item = super()._collect_file(parent_item, movie_path)

            # the item has been created. update the display name to include
            # the an indication of what it is and why it was collected
            item.name = "%s (%s)" % (item.name, "preview")

    def collect_session_geometry(self, parent_item):
        """
        Creates items for session geometry to be exported.

        :param parent_item: Parent Item instance
        """

        # If there are objects in the scene, then we will register
        # a geometry item. This is a bit simplistic in it's approach
        # to determining whether there's exportable data in the scene
        # that's useful when exported as an Alembic cache, but it will
        # work in most cases.
        if _is_empty_scene():
            return

        geo_item = parent_item.create_item(
            "3dsmax.session.geometry", "Geometry", "All Session Geometry"
        )

        # get the icon path to display for this item
        icon_path = os.path.join(self.disk_location, os.pardir, "icons", "geometry.png")

        geo_item.set_icon_from_path(icon_path)


def _session_path():
    """
    Return the path to the current session
    :return:
    """
    if pymxs.runtime.maxFilePath and pymxs.runtime.maxFileName:
        return os.path.join(pymxs.runtime.maxFilePath, pymxs.runtime.maxFileName)
    else:
        return None


def _is_empty_scene():
    return len(pymxs.runtime.rootNode.Children) == 0


def _get_project_folder_dir():
    return pymxs.runtime.pathConfig.getCurrentProjectFolder()


def _set_project_folder_dir(path):
    pymxs.runtime.pathConfig.setCurrentProjectFolder(path)


def _get_preview_dir():
    return pymxs.runtime.pathConfig.GetDir(pymxs.runtime.Name("preview"))


def _set_project():
    """
    Pop up a Qt file browser to select a path. Then set that as the project root
    """

    # max doesn't provide the set project browser via python, so open our own
    # Qt file dialog.
    file_dialog = QtGui.QFileDialog(
        parent=QtGui.QApplication.activeWindow(),
        caption="Save As",
        directory=_get_project_folder_dir(),
        filter="3dsMax Files (*.max)",
    )
    file_dialog.setFileMode(QtGui.QFileDialog.Directory)
    file_dialog.setOption(QtGui.QFileDialog.ShowDirsOnly, True)
    file_dialog.setLabelText(QtGui.QFileDialog.Accept, "Set")
    file_dialog.setLabelText(QtGui.QFileDialog.Reject, "Cancel")
    file_dialog.setOption(QtGui.QFileDialog.DontResolveSymlinks)
    file_dialog.setOption(QtGui.QFileDialog.DontUseNativeDialog)
    if not file_dialog.exec_():
        return
    path = file_dialog.selectedFiles()[0]
    _set_project_folder_dir(path)
