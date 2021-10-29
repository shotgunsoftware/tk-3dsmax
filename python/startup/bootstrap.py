# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.
from __future__ import print_function
import os
import sys


import pymxs

# the version of max when a working SSL python
# started to be distributed with it.
SSL_INCLUDED_VERSION = 20000


def error(msg):
    """
    Error Repost
    :param msg: Error message string to show
    """
    print("ERROR: %s" % msg)


def bootstrap_sgtk_classic():
    """
    Parse environment variables for an engine name and
    serialized Context to use to startup Toolkit and
    the tk-3dsmax engine and environment.
    """

    try:
        import sgtk
    except Exception as e:
        error("Could not import sgtk! Disabling for now: %s" % e)
        return

    sgtk.LogManager().initialize_base_file_handler("tk-3dsmax")
    logger = sgtk.LogManager.get_logger(__name__)

    if not "TANK_ENGINE" in os.environ:
        logger.error("Missing required environment variable TANK_ENGINE.")
        error("ShotGrid: Missing required environment variable TANK_ENGINE.")
        return

    engine_name = os.environ.get("TANK_ENGINE")
    try:
        context = sgtk.context.deserialize(os.environ.get("TANK_CONTEXT"))
    except Exception as e:
        logger.exception("Could not create context! sgtk will be disabled.")
        error(
            "ShotGrid: Could not create context! sgtk will be disabled. Details: %s" % e
        )
        return

    try:
        sgtk.platform.start_engine(engine_name, context.tank, context)
    except Exception as e:
        logger.exception("Could not start engine")
        error("ShotGrid: Could not start engine: %s" % e)
        return


def bootstrap_sgtk_with_plugins():
    """
    Parse environment variables for a list of plugins to load that will
    ultimately startup Toolkit and the tk-3dsmax engine and environment.
    """
    import sgtk

    logger = sgtk.LogManager.get_logger(__name__)

    logger.debug("Launching 3dsMax in plugin mode")

    # Load all plugins by calling the 'load()' entry point.
    for plugin_path in os.environ["SGTK_LOAD_MAX_PLUGINS"].split(os.pathsep):
        plugin_python_path = os.path.join(plugin_path, "python")
        for module_name in os.listdir(plugin_python_path):
            sys.path.append(plugin_python_path)
            module = __import__(module_name)
            try:
                module.load(plugin_path)
            except AttributeError:
                logger.error(
                    "Missing 'load()' method in plugin %s.  Plugin won't be loaded"
                    % plugin_path
                )


def bootstrap_sgtk():
    """
    Bootstrap. This is called when preparing to launch by multi-launch.
    """
    import sgtk

    if sgtk.util.is_windows():

        # get the version number from max
        version_number = pymxs.runtime.maxVersion()[0]

        if version_number < SSL_INCLUDED_VERSION:
            # our version of 3dsmax does not have ssl included.
            # patch this up by adding to the pythonpath
            resources = os.path.join(os.path.dirname(__file__), "..", "..", "resources")
            ssl_path = os.path.join(resources, "ssl_fix")
            sys.path.insert(0, ssl_path)
            path_parts = os.environ.get("PYTHONPATH", "").split(";")
            path_parts = [ssl_path] + path_parts
            os.environ["PYTHONPATH"] = ";".join(path_parts)
    else:
        error("ShotGrid: Unknown platform - cannot setup ssl")
        return

    if os.environ.get("SGTK_LOAD_MAX_PLUGINS"):
        bootstrap_sgtk_with_plugins()
    else:
        bootstrap_sgtk_classic()

    # clean up temp env vars
    for var in [
        "TANK_ENGINE",
        "TANK_CONTEXT",
        "SGTK_FILE_TO_OPEN",
        "SGTK_LOAD_MAX_PLUGINS",
    ]:
        if var in os.environ:
            del os.environ[var]


def adjust_sys_path():
    """
    Adjust sys.path list to include the os.environ["PYTHONPATH"] values

    3DSMax remove intentionally the usage of the environment variable
    PYTHONPATH so we need to add the values to sys.path manually.
    """
    python_path = os.environ.get("PYTHONPATH", None)
    if not python_path:
        return

    values = reversed(python_path.split(os.pathsep))

    for value in values:
        if value not in sys.path:
            sys.path.insert(0, value)


adjust_sys_path()
bootstrap_sgtk()
