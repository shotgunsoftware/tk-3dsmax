# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os

import pymxs

import tank
from tank import Hook
from tank import TankError


class SceneOperation(Hook):
    """
    Hook called to perform an operation with the
    current scene
    """

    def execute(self, operation, file_path, **kwargs):
        """
        Main hook entry point

        :operation: String
                    Scene operation to perform

        :file_path: String
                    File path to use if the operation
                    requires it (e.g. open)

        :returns:   Depends on operation:
                    'current_path' - Return the current scene
                                     file path as a String
                    all others     - None
        """
        if operation == "current_path":
            # return the current scene path
            file_path = _session_path()
            if not file_path:
                return ""
            return file_path
        elif operation == "open":
            # open the specified scene
            _open_file(file_path)
        elif operation == "save":
            # save the current scene:
            _save_file()


def _session_path():
    """
    Return the path to the current session
    :return:
    """
    if pymxs.runtime.maxFilePath and pymxs.runtime.maxFileName:
        return os.path.join(pymxs.runtime.maxFilePath, pymxs.runtime.maxFileName)
    else:
        return None


def _open_file(file_path):
    pymxs.runtime.loadMaxFile(file_path)


def _save_file(file_path=None):
    pymxs.runtime.saveMaxFile(_session_path())
