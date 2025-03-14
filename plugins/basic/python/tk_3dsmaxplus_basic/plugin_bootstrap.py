# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.
from pymxs import runtime as rt
import os
import sys
import hashlib

from . import constants
from . import __name__ as PLUGIN_PACKAGE_NAME

try:
    from PySide6 import QtCore
except ImportError:
    from PySide2 import QtCore


class PluginProperties(object):
    plugin_root_path = None
    running_as_standalone_plugin = False


def load(root_path):
    """
    Entry point for plugin loading. Called by startup.py.

    :param str root_path: Path to the root folder of the plugin
    """
    bootstrap_toolkit(root_path)


def bootstrap_toolkit(root_path):
    """
    Entry point for toolkit bootstrap in 3dsmax.
    Called by the bootstrap.ms max script.

    :param str root_path: Path to the root folder of the plugin
    """

    # --- Import Core ---
    #
    # - If we are running the plugin built as a stand-alone unit,
    #   try to retrieve the path to sgtk core and add that to the pythonpath.
    #   When the plugin has been built, there is a sgtk_plugin_basic_3dsmax
    #   module which we can use to retrieve the location of core and add it
    #   to the pythonpath.
    # - If we are running toolkit as part of a larger zero config workflow
    #   and not from a standalone workflow, we are running the plugin code
    #   directly from the engine folder without a bundle cache and with this
    #   configuration, core already exists in the pythonpath.

    # Display temporary message in prompt line for maximum 5 secs.
    rt.displayTempPrompt("Loading PTR integration...", 5000)

    # Remember path, to handle logout/login
    PluginProperties.plugin_root_path = root_path

    try:
        from sgtk_plugin_basic_3dsmax import manifest

        PluginProperties.running_as_standalone_plugin = True
    except ImportError:
        PluginProperties.running_as_standalone_plugin = False

    if PluginProperties.running_as_standalone_plugin:
        # Retrieve the Shotgun toolkit core included with the plug-in and
        # prepend its python package path to the python module search path.
        tkcore_python_path = manifest.get_sgtk_pythonpath(
            PluginProperties.plugin_root_path
        )
        sys.path.insert(0, tkcore_python_path)
        import sgtk

    else:
        # Running as part of the the launch process and as part of zero
        # config. The launch logic that started 3dsmax has already
        # added sgtk to the pythonpath.
        import sgtk

    # start logging to log file
    sgtk.LogManager().initialize_base_file_handler("tk-3dsmax")

    # get a logger for the plugin
    sgtk_logger = sgtk.LogManager.get_logger(PLUGIN_PACKAGE_NAME)
    sgtk_logger.debug("Booting up toolkit plugin.")

    if sgtk.authentication.ShotgunAuthenticator().get_default_user():
        # When the user is already authenticated, automatically log him/her in.
        _login_user()
    else:
        # When the user is not yet authenticated, display a login menu.
        _create_login_menu()


def progress_callback(invoker, progress_value, message):
    """
    Called whenever toolkit reports progress.

    :param progress_value: The current progress value as float number.
                           values will be reported in incremental order
                           and always in the range 0.0 to 1.0
    :param message:        Progress message string
    """

    print("Flow Production Tracking: %s" % message)
    # Make sure this is invoked in the main thread, as pymxs can't be
    # used from background threads.
    # Display temporary message in prompt line for maximum 2 secs.
    invoker.invoke(rt.displayTempPrompt, "Flow Production Tracking: %s" % message, 2000)


def handle_bootstrap_completed(engine):
    """
    Callback function that handles cleanup after successful completion of the bootstrap.

    This function is executed in the main thread by the main event loop.

    :param engine: Launched :class:`sgtk.platform.Engine` instance.
    """

    print("Flow Production Tracking: Bootstrap successfully.")

    # Add a logout menu item to the engine context menu only when
    # running as standalone plugin.
    if PluginProperties.running_as_standalone_plugin:
        engine.register_command(
            "Log Out of Flow Production Tracking", _on_logout, {"type": "context_menu"}
        )
        engine.update_shotgun_menu()


def handle_bootstrap_failed(phase, exception):
    """
    Callback function that handles cleanup after failed completion of the bootstrap.

    This function is executed in the main thread by the main event loop.

    :param phase: Bootstrap phase that raised the exception,
                  ``ToolkitManager.TOOLKIT_BOOTSTRAP_PHASE`` or ``ToolkitManager.ENGINE_STARTUP_PHASE``.
    :param exception: Python exception raised while bootstrapping.
    """

    print("Flow Production Tracking: Bootstrap failed. %s" % exception)
    _create_login_menu()


def shutdown_toolkit():
    """
    Shutdown the Shotgun toolkit and its 3dsMax engine.
    """
    import sgtk

    logger = sgtk.LogManager.get_logger(PLUGIN_PACKAGE_NAME)
    engine = sgtk.platform.current_engine()

    if engine:
        logger.info("Stopping the PTR engine.")
        # Close the various windows (dialogs, panels, etc.) opened by the engine.
        engine.close_windows()
        # Turn off your engine! Step away from the car!
        engine.destroy()
    else:
        logger.debug("The PTR engine was already stopped!")


def _on_logout():
    """
    Logs the user out and displays login menu
    """

    _logout_user()
    _create_login_menu()


def _logout_user():
    """
    Shuts down the engine and logs out the user of Shotgun.
    """
    import sgtk

    # Shutting down the engine also get rid of the engine menu.
    shutdown_toolkit()

    # Clear the user's credentials to log him/her out.
    sgtk.authentication.ShotgunAuthenticator().clear_default_user()


class AsyncInvoker(QtCore.QObject):
    """
    Invoker class - implements a mechanism to execute a function with arbitrary
    args in the main thread asynchronously.

    This was copied from tk-core and should probably be refactored into
    a component that users could invoke.
    """

    __signal = QtCore.Signal(object)

    def __init__(self):
        """
        Construction
        """
        QtCore.QObject.__init__(self)
        self.__signal.connect(self.__execute_in_main_thread)

    def invoke(self, fn, *args, **kwargs):
        """
        Invoke the specified function with the specified args in the main thread

        :param fn:          The function to execute in the main thread
        :param *args:       Args for the function
        :param **kwargs:    Named arguments for the function
        :returns:           The result returned by the function
        """

        self.__signal.emit(lambda: fn(*args, **kwargs))

    def __execute_in_main_thread(self, fn):
        fn()


def _login_user():
    """
    Logs in the user to Shotgun and starts the engine.
    """
    import sgtk

    sgtk_logger = sgtk.LogManager.get_logger(PLUGIN_PACKAGE_NAME)

    try:
        # When the user is not yet authenticated,
        # pop up the Shotgun login dialog to get the user's credentials,
        # otherwise, get the cached user's credentials.
        user = sgtk.authentication.ShotgunAuthenticator().get_user()

    except sgtk.authentication.AuthenticationCancelled:
        # When the user cancelled the Shotgun login dialog,
        # keep around the displayed login menu.
        sgtk_logger.info("PTR login was cancelled by the user.")
        return

    _delete_login_menu()

    # get information about this plugin (plugin id & base config)
    plugin_info = _get_plugin_info()

    # Create a boostrap manager for the logged in user with the plug-in configuration data.
    toolkit_mgr = sgtk.bootstrap.ToolkitManager(user)
    toolkit_mgr.base_configuration = plugin_info["base_configuration"]
    toolkit_mgr.plugin_id = plugin_info["plugin_id"]
    toolkit_mgr.bundle_cache_fallback_paths = [
        os.path.join(PluginProperties.plugin_root_path, "bundle_cache")
    ]

    # Retrieve the Shotgun entity type and id when they exist in the environment.
    # these are passed down through the app launcher when running in zero config
    entity = toolkit_mgr.get_entity_from_environment()
    sgtk_logger.debug("Will launch the engine with entity: %s" % entity)

    # This is getting instantiated from the main thread, so this is where
    # emitted signals will get executed. This property is important
    # as we need to update the Max status bar from a background thead,
    # but pymxs can't be called anywhere else than the main thead.
    #
    # Note that we can't call engine.async_execute_in_main_thread because
    # the engine is not started yet.
    invoker = AsyncInvoker()

    # set up a simple progress reporter
    toolkit_mgr.progress_callback = lambda percent, msg: progress_callback(
        invoker, percent, msg
    )

    # start engine
    sgtk_logger.info("Starting the 3dsmax engine.")

    toolkit_mgr.bootstrap_engine_async(
        "tk-3dsmax",
        entity,
        completed_callback=handle_bootstrap_completed,
        failed_callback=handle_bootstrap_failed,
    )


def _add_to_menu(menu, title, callback):
    """
    Add a new action item to the menu and invokes the given callback when selected.

    :param menu: MaxScript menu object to add to.
    :param str title: Name of the action item
    :param callable callback: Method to call when the menu item is selected.
    """
    try:
        from tank_vendor import sgutils
    except ImportError:
        from tank_vendor import six as sgutils

    # Hash the macro name just like we do in the engine for consistency.
    macro_name = (
        "sg_" + hashlib.md5(sgutils.ensure_binary(callback.__name__)).hexdigest()
    )
    category = "PTR Bootstrap Menu Actions"
    # The createActionItem expects a macro and not some MaxScript, so create a
    # macro first...
    rt.execute(
        """
        macroScript {macro_name}
        category: "{category}"
        tooltip: "{title}"
        (
            on execute do
            (
                python.execute "from tk_3dsmax_basic import plugin_bootstrap; plugin_bootstrap.{method_name}()"
            )
        )
    """.format(
            macro_name=macro_name,
            category=category,
            title=title,
            method_name=callback.__name__,
        )
    )
    # ... and then pass its name down to the createActionItem menu.
    menu_action = rt.menuMan.createActionItem(macro_name, category)
    menu_action.setUseCustomTitle(True)
    menu_action.setTitle(title)
    menu.addItem(menu_action, -1)


def _add_separator(menu):
    """
    Add a separator at the bottom of the menu.

    :param menu: MaxScript menu object to add to.
    """
    sep = rt.menuMan.createSeparatorItem()
    menu.addItem(sep, -1)


def _add_to_main_menu_bar(menu):
    """
    Add the given menu to the main menu bar.

    :param menu: MaxScript menu object to add to the main menu bar..
    """
    # Retrieve the main menu bar.
    main_menu = rt.menuMan.GetMainMenuBar()

    # Create an item that will be inserted right before the help menu.
    sub_menu_index = main_menu.numItems() - 1
    sub_menu_item = rt.menuMan.createSubMenuItem(constants.SG_MENU_LABEL, menu)

    # Insert the item in the menu and refresh the menu bar.
    main_menu.addItem(sub_menu_item, sub_menu_index)
    rt.menuMan.updateMenuBar()


def _create_login_menu():
    """
    Creates and displays a Shotgun user login menu.
    """
    _delete_login_menu()

    if rt.maxVersion()[0] >= constants.MAX_2025_MENU_SYSTEM:
        _add_to_2025_menu()
    else:
        sg_menu = rt.menuMan.createMenu(constants.SG_MENU_LABEL)

        _add_to_menu(sg_menu, "Log In to Flow Production Tracking...", _login_user)
        _add_separator(sg_menu)
        _add_to_menu(
            sg_menu, "Learn about Flow Production Tracking...", _jump_to_website
        )
        _add_separator(sg_menu)
        _add_to_menu(sg_menu, "Try PTR for Free...", _jump_to_signup)
        _add_to_main_menu_bar(sg_menu)


def _delete_login_menu():
    """
    Deletes the displayed Shotgun user login menu.
    """
    if rt.maxVersion()[0] >= constants.MAX_2025_MENU_SYSTEM:
        return

    old_menu = rt.menuMan.findMenu(constants.SG_MENU_LABEL)
    if old_menu is not None:
        rt.menuMan.unregisterMenu(old_menu)


def _jump_to_website():
    """
    Jumps to the Shotgun website in the default web browser.
    """

    # At this point, the engine is not launched, so "QtCore" and
    # "QtGui" variables are not defined in sgtk.platform.qt yet.
    from sgtk.util.qt_importer import QtImporter

    qt_importer = QtImporter()
    QtCore = qt_importer.QtCore
    QtGui = qt_importer.QtGui

    QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://www.shotgridsoftware.com"))


def _jump_to_signup():
    """
    Jumps to the Shotgun signup page in the default web browser.
    """

    # At this point, the engine is not launched, so "QtCore" and
    # "QtGui" variables are not defined in sgtk.platform.qt yet.
    from sgtk.util.qt_importer import QtImporter

    qt_importer = QtImporter()
    QtCore = qt_importer.QtCore
    QtGui = qt_importer.QtGui

    QtGui.QDesktopServices.openUrl(
        QtCore.QUrl("https://www.shotgridsoftware.com/signup")
    )


def _get_plugin_info():
    """
    Returns a dictionary of information about the plugin of the form:

        {
            plugin_id: <plugin id>,
            base_configuration: <config descriptor>
        }
    """

    try:
        # first, see if we can get the info from the manifest. if we can, no
        # need to parse info.yml
        from sgtk_plugin_basic_3dsmax import manifest

        plugin_id = manifest.plugin_id
        base_configuration = manifest.base_configuration
    except ImportError:
        # no manifest, running in situ from the engine. just parse the info.yml
        # file to get at the info we need.

        # import the yaml parser
        from tank_vendor import yaml

        # build the path to the info.yml file
        plugin_info_yml = os.path.abspath(
            os.path.join(__file__, "..", "..", "..", "info.yml")
        )

        # open the yaml file and read the data
        with open(plugin_info_yml, "r") as plugin_info_fh:
            info_yml = yaml.load(plugin_info_fh, Loader=yaml.FullLoader)
            plugin_id = info_yml["plugin_id"]
            base_configuration = info_yml["base_configuration"]

    # return a dictionary with the required info
    return dict(plugin_id=plugin_id, base_configuration=base_configuration)


def _menu_items_2025():
    return {
        3001: {
            "name": "Log In to Flow Production Tracking...",
            "action": _login_user,
        },
        3002: {
            "name": "Learn about Flow Production Tracking...",
            "action": _jump_to_website,
        },
        3003: {
            "name": "Try PTR for Free...",
            "action": _jump_to_signup,
        },
    }


def _add_to_2025_menu():
    import sgtk

    def populate_menu(menuroot):
        for code, menu_item in _menu_items_2025().items():
            menuroot.additem(code, menu_item["name"])

    def menu_item_selected(itemid):
        _menu_items_2025()[itemid]["action"]()

    rt.populate_menu = populate_menu
    rt.menu_item_selected = menu_item_selected

    mxswrapper = """
        macroscript Python_Action_Item category:"Menu Category" buttonText:"Options..."
        (
            on populateDynamicMenu menuRoot do
            (
                populate_menu menuRoot
            )
            on dynamicMenuItemSelected id do
            (
                menu_item_selected id
            )
        )
    """
    rt.execute(mxswrapper)

    def create_menu_callback():
        engine = sgtk.platform.current_engine()
        menumgr = rt.callbacks.notificationparam()
        mainmenubar = menumgr.mainmenubar
        newsubmenu = mainmenubar.createsubmenu(
            rt.genguid(), constants.SG_MENU_LABEL, beforeid=engine.HELPMENU_ID
        )
        newsubmenu.createaction(
            rt.genguid(), 647394, "Python_Action_Item`Menu Category"
        )

    MENU_DEMO_SCRIPT = rt.name("sgtk_menu_main")
    rt.callbacks.removescripts(id=MENU_DEMO_SCRIPT)
    rt.callbacks.addscript(
        rt.name("cuiRegisterMenus"), create_menu_callback, id=MENU_DEMO_SCRIPT
    )
