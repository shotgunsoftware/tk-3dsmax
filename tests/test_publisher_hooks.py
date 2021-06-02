# Copyright (c) 2019 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import contextlib
import logging
import pprint

import mock

import sgtk

from tank_test.tank_test_base import TankTestBase
from tank_test.tank_test_base import setUpModule

from pymxs import runtime as rt


class TestPublisherHooks(TankTestBase):
    """
    Tests the publisher hooks.
    """

    def setUp(self):
        """
        Set up the configuration and start the engine.
        """
        super(TestPublisherHooks, self).setUp()
        self.setup_fixtures()

        # Cleanup the scene before the test run so we don't get poluted with
        # the current scene content.
        self._reset_scene()
        # Always cleanup the scene after tests have run to have a clean slate.
        self.addCleanup(self._reset_scene)

        self.current_max_project = os.path.join(self.tank_temp, self.short_test_name)

        # Set the current project so we can have a place to write
        # previews and exports.
        rt.pathConfig.setCurrentProjectFolder(self.current_max_project)
        # Make sure the autoback folder exists or we'll get warnings during saveMaxFile
        os.makedirs(os.path.join(self.current_max_project, "autoback"))

        # Start the engine and ensure it is destroyed
        self.context = self.tk.context_from_entity("Project", self.project["id"])
        self.engine = sgtk.platform.start_engine("tk-3dsmax", self.tk, self.context)
        self.addCleanup(self.engine.destroy)

        # Capture all logs emitted by the engine!
        self._logs = []
        patcher = mock.patch.object(
            self.engine, "_emit_log_message", side_effect=self._emit_log
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        # We're going to use a publish manager for these tests, so
        # prepare one.
        publisher = self.engine.apps["tk-multi-publish2"]
        self.manager = publisher.create_publish_manager()

        # Mock the upload method so the upload preview task works.
        patcher = mock.patch.object(self.mockgun, "upload", return_value=None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        """
        Tears down and ensure something was logged. This is mainly to make sure
        that logging is still captured by the test.
        """
        assert len(self._logs) > 0
        super(TestPublisherHooks, self).tearDown()

    def _emit_log(self, handler, record):
        """
        Accumulate logs.
        """
        self._logs.append(record)

    def _reset_scene(self):
        """
        Reset the current scene without prompting the user.
        """
        rt.resetMaxFile(rt.Name("noprompt"))

    def _create_file(self, folder, filename):
        """
        Create a file in the given project folder.
        """
        location = os.path.join(self.current_max_project, folder, filename)

        # Make sure the folder exists.
        folder = os.path.dirname(location)
        if not os.path.exists(folder):
            os.makedirs(folder)

        # Write a file with the location as it's content.
        with open(location, "wt") as fh:
            fh.write(location)

    def _create_preview(self, preview_file):
        """
        Create a preview file.
        """
        self._create_file("previews", preview_file)

    def _create_export(self, export_file):
        """
        Create an export
        """
        self._create_file("export", export_file)

    def _dump_logs(self):
        """
        Prints all the logs. Used for debugging.
        """
        pprint.pprint([l.msg for l in self._logs])

    def _find_log_action(self, msg):
        """
        Retrieve the log action attached to a message matching the passed in substring.

        :param str msg: Substring to match.

        :returns: The dictionary of the action.
        """
        for record in self._logs:
            if msg in record.msg:
                return record.action_button
        raise RuntimeError("Could not find message '{0}'".format(msg))

    def _validate_manager(self):
        """
        Wrap the call self.manager.validate() so the method returns error strings
        instead of exceptions, which makes it easier for asserting.
        """
        return [(error[0], str(error[1])) for error in self.manager.validate()]

    def test_publish_unsaved_scene(self):
        """
        Publish item should be current max session, not named after
        file.
        """
        self.manager.collect_session()

        action = self._find_log_action("The Max session has not been saved.")
        assert action["label"] == "Save As..."
        assert action["tooltip"] == "Save the current session"

        items = list(self.manager.tree)
        assert len(items) == 1

        items[0].name = "Current Max Session"
        items[0].type_display == "3dsmax Session"
        assert [task.name for task in items[0].tasks] == [
            "Begin file versioning",
            "Publish to ShotGrid",
        ]

        tasks = list(items[0].tasks)
        errors = self._validate_manager()

        assert errors == [(tasks[1], "The Max session has not been saved.")]

    def test_publish_scene(self):
        """
        Try to publish a sphere.
        """
        # Create a publishable scene
        sphere = rt.Sphere()
        rt.saveMaxFile(os.path.join(self.current_max_project, "scene.max"))

        self._create_preview("rendering.mp4")
        self._create_export("scene.abc")

        # Collect the scene.
        self.manager.collect_session()
        self.manager.tree.pprint()

        # Ensure all items are present
        items = list(self.manager.tree)
        assert len(items) == 4

        items[0].name == "scene.max"
        items[0].type_display == "3dsmax Session"
        assert [task.name for task in items[0].tasks] == [
            "Begin file versioning",
            "Publish to ShotGrid",
        ]

        items[1].name == "rendering.mp4"
        items[1].type_display == "preview"
        assert [task.name for task in items[1].tasks] == [
            "Publish to ShotGrid",
            "Upload for review",
        ]

        items[2].name == "scene.abc"
        items[2].type_display == "Alembic Cache"
        assert [task.name for task in items[2].tasks] == ["Publish to ShotGrid"]

        items[3].name == "All Session Geometry"
        items[3].type_display == "Geometry"

        assert list(items[3].tasks) == []

        self.manager.validate()

        # Publish the scene
        self.manager.publish()

        # Mockgun does not set this property, so set it!
        publish_id = items[0].properties.sg_publish_data["id"]
        self.mockgun._db["PublishedFile"][publish_id]["path"]["link_type"] = "local"

        publish_id = items[1].properties.sg_publish_data["id"]
        self.mockgun._db["PublishedFile"][publish_id]["path"]["link_type"] = "local"

        publish_id = items[2].properties.sg_publish_data["id"]
        self.mockgun._db["PublishedFile"][publish_id]["path"]["link_type"] = "local"

        self.manager.finalize()

    def test_set_project_command(self):
        self.manager.collect_session()

        action = self._find_log_action("Current Max project is:")
        assert action["label"] == "Change Project"
        assert action["tooltip"] == "Change to a different Max project"

        new_project_location = os.path.join(self.tank_temp, "new_project_location")
        os.makedirs(new_project_location)

        with mock.patch("sgtk.platform.qt.QtGui.QFileDialog.exec_", return_value=True):
            with mock.patch(
                "sgtk.platform.qt.QtGui.QFileDialog.selectedFiles",
                return_value=[new_project_location],
            ):
                action["callback"]()

        assert rt.pathConfig.getCurrentProjectFolder() == new_project_location
