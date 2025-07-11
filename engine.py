# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.
"""
A 3ds Max (2022+) engine for Toolkit based pymxs
"""
import os
import math
import sgtk

import pymxs

# Max versions compatibility constants
VERSION_OLDEST_COMPATIBLE = 2021
VERSION_OLDEST_SUPPORTED = 2023
VERSION_NEWEST_SUPPORTED = 2026
# Caution: make sure compatibility_dialog_min_version default value in info.yml
# is equal to VERSION_NEWEST_SUPPORTED


class MaxEngine(sgtk.platform.Engine):
    """
    The main Toolkit engine for 3ds Max
    """

    HELPMENU_ID = "cee8f758-2199-411b-81e7-d3ff4a80d143"
    MENU_LABEL = "Flow Production Tracking"

    @property
    def host_info(self):
        """
        :returns: A dictionary with information about the application hosting this engine.

        The returned dictionary is of the following form on success:
        Note that the version field refers to the release year.

            {
                "name": "3ds Max",
                "version": "2018",
            }

        The returned dictionary is of following form on an error preventing
        the version identification.

            {
                "name": "3ds Max",
                "version: "unknown"
            }

        References:
        https://help.autodesk.com/view/MAXDEV/2026/ENU/?guid=MAXDEV_Python_what_s_new_in_3ds_max_python_api_html
        """
        host_info = {"name": "3ds Max", "version": "unknown"}

        max_version_year = self.max_version_year
        if max_version_year:
            host_info["version"] = str(max_version_year)

        return host_info

    def __init__(self, *args, **kwargs):
        """
        Engine Constructor
        """

        # Add instance variables before calling our base class
        # __init__() because the initialization may need those
        # variables.
        self._parent_to_max = True
        self._dock_widgets = []

        self._max_version = None
        self._max_version_year = None

        # proceed about your business
        sgtk.platform.Engine.__init__(self, *args, **kwargs)

    ##########################################################################################
    # properties

    @property
    def context_change_allowed(self):
        """
        Tells the core API that context changes are allowed by this engine.
        """
        return True

    ##########################################################################################
    # init

    def pre_app_init(self):
        """
        Called before all apps have initialized
        """
        from sgtk.platform.qt import QtCore, QtGui

        self.log_debug("%s: Initializing..." % self)

        url_doc_supported_versions = "https://help.autodesk.com/view/SGDEV/ENU/?guid=SGD_si_integrations_engine_supported_versions_html"

        if self.max_version_year < VERSION_OLDEST_COMPATIBLE:
            # Old incompatible version
            message = """
Flow Production Tracking is no longer compatible with {product} versions older
than {version}.

For information regarding support engine versions, please visit this page:
{url_doc_supported_versions}
            """.strip()

            if self.has_ui:
                try:
                    QtGui.QMessageBox.critical(
                        None,  # parent
                        "Error - Flow Production Tracking Compatibility!".ljust(
                            # Padding to try to prevent the dialog being insanely narrow
                            70
                        ),
                        message.replace(
                            # Presence of \n breaks the Rich Text Format
                            "\n",
                            "<br>",
                        ).format(
                            product="3ds Max",
                            url_doc_supported_versions='<a href="{u}">{u}</a>'.format(
                                u=url_doc_supported_versions,
                            ),
                            version=VERSION_OLDEST_COMPATIBLE,
                        ),
                    )
                except:  # nosec B110
                    # It is unlikely that the above message will go through
                    # on old versions of Max (Python2, Qt4, ...).
                    # But there is nothing more we can do here.
                    pass

            raise sgtk.TankError(
                message.format(
                    product="3ds Max",
                    url_doc_supported_versions=url_doc_supported_versions,
                    version=VERSION_OLDEST_COMPATIBLE,
                )
            )

        elif self.max_version_year < VERSION_OLDEST_SUPPORTED:
            # Older than the oldest supported version
            self.logger.warning(
                "Flow Production Tracking no longer supports {product} "
                "versions older than {version}".format(
                    product="3ds Max",
                    version=VERSION_OLDEST_SUPPORTED,
                )
            )

            if self.has_ui:
                QtGui.QMessageBox.warning(
                    None,  # parent
                    "Warning - Flow Production Tracking Compatibility!".ljust(
                        # Padding to try to prevent the dialog being insanely narrow
                        70
                    ),
                    """
Flow Production Tracking no longer supports {product} versions older than
{version}.
You can continue to use Toolkit but you may experience bugs or instabilities.

For information regarding support engine versions, please visit this page:
{url_doc_supported_versions}
                    """.strip()
                    .replace(
                        # Presence of \n breaks the Rich Text Format
                        "\n",
                        "<br>",
                    )
                    .format(
                        product="3ds Max",
                        url_doc_supported_versions='<a href="{u}">{u}</a>'.format(
                            u=url_doc_supported_versions,
                        ),
                        version=VERSION_OLDEST_SUPPORTED,
                    ),
                )

        elif self.max_version_year <= VERSION_NEWEST_SUPPORTED:
            # Within the range of supported versions
            self.logger.debug(f"Running 3ds Max version {self.max_version_year}")
        else:  # Newer than the newest supported version (untested)
            self.logger.warning(
                "Flow Production Tracking has not yet been fully tested with "
                "{product} version {version}.".format(
                    product="3ds Max",
                    version=self.max_version_year,
                )
            )

            if self.has_ui and self.max_version_year >= self.get_setting(
                "compatibility_dialog_min_version"
            ):
                QtGui.QMessageBox.warning(
                    None,  # parent
                    "Warning - Flow Production Tracking Compatibility!".ljust(
                        # Padding to try to prevent the dialog being insanely narrow
                        70
                    ),
                    """
Flow Production Tracking has not yet been fully tested with {product} version
{version}.
You can continue to use Toolkit but you may experience bugs or instabilities.

Please report any issues to:
{support_url}
                    """.strip()
                    .replace(
                        # Presence of \n breaks the Rich Text Format
                        "\n",
                        "<br>",
                    )
                    .format(
                        product="3ds Max",
                        support_url='<a href="{u}">{u}</a>'.format(
                            u=sgtk.support_url,
                        ),
                        version=self.max_version_year,
                    ),
                )

        self._safe_dialog = []
        # Keep the dialog to prevent the garbage collector from delete it
        self._dialog = None

        # Add image formats since max doesn't add the correct paths by default and jpeg won't be readable
        maxpath = QtCore.QCoreApplication.applicationDirPath()
        pluginsPath = os.path.join(maxpath, "plugins")
        QtCore.QCoreApplication.addLibraryPath(pluginsPath)

        # Window focus objects are used to enable proper keyboard handling by the window instead of 3dsMax's accelerators
        engine = self

        class DialogEvents(QtCore.QObject):
            def eventFilter(self, obj, event):
                if event.type() == QtCore.QEvent.WindowActivate:
                    pymxs.runtime.enableAccelerators = False
                elif event.type() == QtCore.QEvent.WindowDeactivate:
                    pymxs.runtime.enableAccelerators = True
                # Remove from tracked dialogs
                if event.type() == QtCore.QEvent.Close:
                    if obj in engine._safe_dialog:
                        engine._safe_dialog.remove(obj)

                return False

        self.dialogEvents = DialogEvents()

        # set up a qt style sheet
        # note! - try to be smart about this and only run
        # the style setup once per session - it looks like
        # 3dsmax slows down if this is executed every engine restart.
        #
        # If we're in pre-Qt Max (before 2018) then we'll need to apply the
        # stylesheet to the QApplication. That's not safe in 2019.3+, as it's
        # possible that we'll get back a QCoreApplication from Max, which won't
        # carry references to a stylesheet. In that case, we apply our styling
        # to the dialog parent, which will be the top-level Max window.
        if self.max_version_year < 2018:
            parent_widget = sgtk.platform.qt.QtCore.QCoreApplication.instance()
        else:
            parent_widget = self._get_dialog_parent()

        curr_stylesheet = parent_widget.styleSheet()

        if "toolkit 3dsmax style extension" not in curr_stylesheet:
            # If we're in pre-2017 Max then we need to handle our own styling. Otherwise
            # we just inherit from Max.
            if self.max_version_year < 2017:
                self._initialize_dark_look_and_feel()

            curr_stylesheet += "\n\n /* toolkit 3dsmax style extension */ \n\n"
            curr_stylesheet += (
                "\n\n QDialog#TankDialog > QWidget { background-color: #343434; }\n\n"
            )
            parent_widget.setStyleSheet(curr_stylesheet)

        # This needs to be present for apps as it will be used in
        # show_dialog when perforce asks for login info very early on.
        self.tk_3dsmax = self.import_module("tk_3dsmax")

        # The "qss_watcher" setting causes us to monitor the engine's
        # style.qss file and re-apply it on the fly when it changes
        # on disk. This is very useful for development work,
        if self.get_setting("qss_watcher", False):
            self._qss_watcher = QtCore.QFileSystemWatcher(
                [
                    os.path.join(
                        self.disk_location,
                        sgtk.platform.constants.BUNDLE_STYLESHEET_FILE,
                    )
                ]
            )

            self._qss_watcher.fileChanged.connect(self.reload_qss)

    def _add_shotgun_menu(self):
        """
        Add Shotgun menu to the main menu bar.
        """
        self.log_debug("Adding the PTR menu to the main menu bar.")
        self._menu_generator.create_menu()
        self.tk_3dsmax.MaxScript.enable_menu()

    def _remove_shotgun_menu(self):
        """
        Remove Shotgun menu from the main menu bar.
        """
        self.log_debug("Removing the PTR menu from the main menu bar.")
        self._menu_generator.destroy_menu()

    def _on_menus_loaded(self):
        """
        Called when receiving postLoadingMenus from 3dsMax < 2025

        :param code: Notification code received
        """
        self._add_shotgun_menu()

    def post_app_init(self):
        """
        Called when all apps have initialized
        """
        # Make sure this gets executed from the main thread because pymxs can't be used
        # from a background thread.
        self.execute_in_main_thread(self._post_app_init)

    def _post_app_init(self):
        """
        Called from the main thread when all apps have initialized
        """
        # set up menu handler
        if self.max_version_year >= 2025:
            self._menu_generator = self.tk_3dsmax.MenuGenerator_callbacks(self)
            self._add_shotgun_menu()

            # This causes the menu manager to reload the current configuration,
            # causing the menu file chain to be loaded and the callback to occur.
            iCuiMenuMgr = pymxs.runtime.MaxOps.GetICuiMenuMgr()
            iCuiMenuMgr.LoadConfiguration(iCuiMenuMgr.GetCurrentConfiguration())
        else:
            self._menu_generator = self.tk_3dsmax.MenuGenerator_menuMan(self)
            self._add_shotgun_menu()

            # Register a callback for the postLoadingMenus event.
            python_code = "\n".join(
                [
                    "import sgtk",
                    "engine = sgtk.platform.current_engine()",
                    "engine._on_menus_loaded()",
                ]
            )
            # Unfortunately we can't pass in a Python function as a callback,
            # so we're passing in piece of MaxScript instead.
            pymxs.runtime.callbacks.addScript(
                pymxs.runtime.Name("postLoadingMenus"),
                'python.execute "{0}"'.format(python_code),
                id=pymxs.runtime.Name("sg_tk_on_menus_loaded"),
            )

        # Run a series of app instance commands at startup.
        self._run_app_instance_commands()

        # if a file was specified, load it now
        file_to_open = os.environ.get("SGTK_FILE_TO_OPEN")
        if file_to_open:
            try:
                pymxs.runtime.loadMaxFile(file_to_open)
            except Exception:
                self.logger.exception(
                    "Couldn't not open the requested file: {}".format(file_to_open)
                )

    def post_context_change(self, old_context, new_context):
        """
        Handles necessary processing after a context change has been completed
        successfully.

        :param old_context: The previous context.
        :param new_context: The current, new context.
        """
        # Replacing the menu will cause the old one to be removed
        # and the new one put into its place.
        self._add_shotgun_menu()

    def _run_app_instance_commands(self):
        """
        Runs the series of app instance commands listed in the 'run_at_startup' setting
        of the environment configuration yaml file.
        """

        # Build a dictionary mapping app instance names to dictionaries of commands they registered with the engine.
        app_instance_commands = {}
        for command_name, value in self.commands.items():
            app_instance = value["properties"].get("app")
            if app_instance:
                # Add entry 'command name: command function' to the command dictionary of this app instance.
                command_dict = app_instance_commands.setdefault(
                    app_instance.instance_name, {}
                )
                command_dict[command_name] = value["callback"]

        # Run the series of app instance commands listed in the 'run_at_startup' setting.
        for app_setting_dict in self.get_setting("run_at_startup", []):
            app_instance_name = app_setting_dict["app_instance"]
            # Menu name of the command to run or '' to run all commands of the given app instance.
            setting_command_name = app_setting_dict["name"]

            # Retrieve the command dictionary of the given app instance.
            command_dict = app_instance_commands.get(app_instance_name)

            if command_dict is None:
                self.log_warning(
                    "%s configuration setting 'run_at_startup' requests app '%s' that is not installed."
                    % (self.name, app_instance_name)
                )
            else:
                if not setting_command_name:
                    # Run all commands of the given app instance.
                    for command_name, command_function in command_dict.items():
                        self.log_debug(
                            "%s startup running app '%s' command '%s'."
                            % (self.name, app_instance_name, command_name)
                        )
                        command_function()
                else:
                    # Run the command whose name is listed in the 'run_at_startup' setting.
                    command_function = command_dict.get(setting_command_name)
                    if command_function:
                        self.log_debug(
                            "%s startup running app '%s' command '%s'."
                            % (self.name, app_instance_name, setting_command_name)
                        )
                        command_function()
                    else:
                        known_commands = ", ".join(
                            "'%s'" % name for name in command_dict
                        )
                        self.log_warning(
                            "%s configuration setting 'run_at_startup' requests app '%s' unknown command '%s'. "
                            "Known commands: %s"
                            % (
                                self.name,
                                app_instance_name,
                                setting_command_name,
                                known_commands,
                            )
                        )

    def destroy_engine(self):
        """
        Called when the engine is shutting down
        """
        self.log_debug("%s: Destroying..." % self)
        if self.max_version_year < 2025:
            pymxs.runtime.callbacks.removeScripts(
                pymxs.runtime.Name("postLoadingMenus"),
                id=pymxs.runtime.Name("sg_tk_on_menus_loaded"),
            )
        self._remove_shotgun_menu()

    def update_shotgun_menu(self):
        """
        Rebuild the shotgun menu displayed in the main menu bar
        """
        self._remove_shotgun_menu()
        self._add_shotgun_menu()

    ##########################################################################################
    # logging
    # Should only call logging function from the main thread, although output to listener is
    # supposed to be thread-safe.
    # Note From the max team: Python scripts run in MAXScript are not thread-safe.
    #                         Python commands are always executed in the main 3ds Max thread.
    #                         You should not attempt to spawn separate threads in your scripts
    #                         (for example, by using the Python threading module).
    def _emit_log_message(self, handler, record):
        """
        Emits a log message.
        """
        msg_str = handler.format(record)
        self.async_execute_in_main_thread(self._print_output, msg_str)

    def _print_output(self, msg):
        """
        Print the specified message to the maxscript listener
        :param msg: The message string to print
        """
        print(msg)

    ##########################################################################################
    # Engine

    def _get_dialog_parent(self):
        """
        Get the QWidget parent for all dialogs created through :meth:`show_dialog` :meth:`show_modal`.

        :return: QT Parent window (:class:`PySide.QtGui.QWidget`)
        """
        # Older versions of Max make use of special logic in _create_dialog
        # to handle window parenting. If we can, though, we should go with
        # the more standard approach to getting the main window.
        if self.max_version_year > 2020:
            # getMAXHWND returned a float instead of a long, which was completely
            # unusable with PySide in 2017 to 2020, but starting 2021
            # we can start using it properly.
            # This logic was taken from
            # https://help.autodesk.com/view/3DSMAX/2020/ENU/?guid=__developer_creating_python_uis_html
            from sgtk.platform.qt import QtGui, shiboken

            widget = QtGui.QWidget.find(pymxs.runtime.windows.getMAXHWND())
            return shiboken.wrapInstance(
                shiboken.getCppPointer(widget)[0], QtGui.QMainWindow
            )
        else:
            return super()._get_dialog_parent()

    def show_panel(self, panel_id, title, bundle, widget_class, *args, **kwargs):
        """
        Docks an app widget in a 3dsmax panel.

        :param panel_id: Unique identifier for the panel, as obtained by register_panel().
        :param title: The title of the panel
        :param bundle: The app, engine or framework object that is associated with this window
        :param widget_class: The class of the UI to be constructed. This must derive from QWidget.

        Additional parameters specified will be passed through to the widget_class constructor.

        :returns: the created widget_class instance
        """
        from sgtk.platform.qt import QtCore, QtGui

        self.log_debug("Begin showing panel %s" % panel_id)

        if self.max_version_year <= 2017:
            # Qt docking is supported in version 2018 and later.
            self.log_warning(
                "Panel functionality not implemented. Falling back to showing "
                "panel '%s' in a modeless dialog" % panel_id
            )
            return super().show_panel(
                panel_id, title, bundle, widget_class, *args, **kwargs
            )

        dock_widget_id = "sgtk_dock_widget_" + panel_id

        main_window = self._get_dialog_parent()
        # Check if the dock widget wrapper already exists.
        dock_widget = main_window.findChild(QtGui.QDockWidget, dock_widget_id)

        if dock_widget is None:
            # The dock widget wrapper cannot be found in the main window's
            # children list so that means it has not been created yet, so create it.
            widget_instance = widget_class(*args, **kwargs)
            widget_instance.setParent(self._get_dialog_parent())
            widget_instance.setObjectName(panel_id)

            class DockWidget(QtGui.QDockWidget):
                """
                Widget used for docking app panels that ensures the widget is closed when the dock is closed
                """

                closed = QtCore.Signal(QtCore.QObject)

                def closeEvent(self, event):
                    widget = self.widget()
                    if widget:
                        widget.close()
                    self.setParent(None)
                    self.closed.emit(self)

            dock_widget = DockWidget(title, parent=main_window)
            dock_widget.setObjectName(dock_widget_id)
            dock_widget.setWidget(widget_instance)
            # Add a callback to remove the dock_widget from the list of open panels and delete it
            dock_widget.closed.connect(self._remove_dock_widget)
            self.log_debug("Created new dock widget %s" % dock_widget_id)

            # Disable 3dsMax accelerators, in order for QTextEdit and QLineEdit
            # widgets to work properly.
            widget_instance.setProperty("NoMaxAccelerators", True)

            # Remember the dock widget, so we can delete it later.
            self._dock_widgets.append(dock_widget)
        else:
            # The dock widget wrapper already exists, so just get the
            # shotgun panel from it.
            widget_instance = dock_widget.widget()
            self.log_debug("Found existing dock widget %s" % dock_widget_id)

        # apply external stylesheet
        self._apply_external_stylesheet(bundle, widget_instance)

        if not main_window.restoreDockWidget(dock_widget):
            # The dock widget cannot be restored from the main window's state,
            # so dock it to the right dock area and make it float by default.
            main_window.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_widget)
            dock_widget.setFloating(True)

        dock_widget.show()
        return widget_instance

    def _remove_dock_widget(self, dock_widget):
        """
        Removes a docked widget (panel) opened by the engine
        """
        self._get_dialog_parent().removeDockWidget(dock_widget)
        self._dock_widgets.remove(dock_widget)
        dock_widget.deleteLater()

    def close_windows(self):
        """
        Closes the various windows (dialogs, panels, etc.) opened by the engine.
        """

        # Make a copy of the list of Tank dialogs that have been created by the engine and
        # are still opened since the original list will be updated when each dialog is closed.
        opened_dialog_list = self.created_qt_dialogs[:]

        # Loop through the list of opened Tank dialogs.
        for dialog in opened_dialog_list:
            dialog_window_title = dialog.windowTitle()
            try:
                # Close the dialog and let its close callback remove it from the original dialog list.
                self.log_debug("Closing dialog %s." % dialog_window_title)
                dialog.close()
            except Exception as exception:
                self.log_error(
                    "Cannot close dialog %s: %s" % (dialog_window_title, exception)
                )

        # Close all dock widgets previously added.
        for dock_widget in self._dock_widgets[:]:
            dock_widget.close()

    def _create_dialog(self, title, bundle, widget, parent):
        """
        Parent function override to install event filtering in order to allow proper events to
        reach window dialogs (such as keyboard events).
        """
        self._dialog = sgtk.platform.Engine._create_dialog(
            self, title, bundle, widget, parent
        )

        self._dialog.installEventFilter(self.dialogEvents)

        # Add to tracked dialogs (will be removed in eventFilter)
        self._safe_dialog.append(self._dialog)

        # Apply the engine-level stylesheet.
        self._apply_external_styleshet(self, self._dialog)

        return self._dialog

    def reload_qss(self):
        """
        Causes the style.qss file that comes with the tk-rv engine to
        be re-applied to all dialogs that the engine has previously
        launched.
        """
        self.log_warning("Reloading engine QSS...")
        for dialog in self.created_qt_dialogs:
            self._apply_external_styleshet(self, dialog)
            dialog.update()

    def show_modal(self, title, bundle, widget_class, *args, **kwargs):
        from sgtk.platform.qt import QtGui

        if not self.has_ui:
            self.log_error(
                "Sorry, this environment does not support UI display! Cannot show "
                "the requested window '%s'." % title
            )
            return None

        status = QtGui.QDialog.DialogCode.Rejected

        try:
            # Disable 'Shotgun' background menu while modals are there.
            self.tk_3dsmax.MaxScript.disable_menu()

            # create the dialog:
            try:
                self._parent_to_max = False
                dialog, widget = self._create_dialog_with_widget(
                    title, bundle, widget_class, *args, **kwargs
                )
            finally:
                self._parent_to_max = True

            # finally launch it, modal state
            status = dialog.exec_()
        except Exception:
            import traceback

            tb = traceback.format_exc()
            self.log_error("Exception in modal window: %s" % tb)
        finally:
            # Re-enable 'Shotgun' background menu after modal has been closed
            self.tk_3dsmax.MaxScript.enable_menu()

        # lastly, return the instantiated widget
        return (status, widget)

    def safe_dialog_exec(self, func):
        """
        If running a command from a dialog also creates a 3ds max window, this function tries to
        ensure that the dialog will stay alive and that the max modal window becomes visible
        and unobstructed.

        :param callable script: Function to execute
        """

        # Merge operation can cause max dialogs to pop up, and closing the window results in a crash.
        # So keep alive and hide all of our qt windows while this type of operations are occuring.
        from sgtk.platform.qt import QtGui

        toggled = []
        for sd in self._safe_dialog:
            try:
                self.log_debug("Processing dialog to hide: %r" % sd)
                dialog = sd
            except RuntimeError as e:
                # this should hide all visible sgtk dialogs
                # but in 3dsmax 2024/Python 3.10 they seem to be deleted by the garbage collector
                # so falling back to the last _dialog created on _create_dialog method
                self.log_warning(e)
                dialog = self._dialog
            finally:
                needs_toggling = dialog.isVisible()
                if needs_toggling:
                    self.log_debug("Toggling dialog off: %r" % dialog)
                    toggled.append(dialog)
                    dialog.hide()
                    dialog.lower()
                    QtGui.QApplication.processEvents()
                else:
                    self.log_debug("Dialog is already hidden: %r" % dialog)

        try:
            func()
        finally:
            for dialog in toggled:
                # Restore the window after the operation is completed
                self.log_debug("Toggling dialog on: %r" % dialog)
                dialog.show()
                dialog.activateWindow()  # for Windows
                dialog.raise_()  # for MacOS

    @property
    def max_version_year(self):
        """
        Get the max year from the max release version.
        """

        if self._max_version_year is None:
            max_version = self._get_max_version()
            try:
                assert isinstance(max_version[7], int)
                self._max_version_year = max_version[7]
            except (AssertionError, IndexError, TypeError) as err:
                self.log_debug("Unable to extract Max version {}".format(err))
                self._max_version_year = 0

        return self._max_version_year

    def _get_max_version(self):
        """
        Returns Version integer of max release number.
        """
        if self._max_version is None:
            # Make sure this gets executed from the main thread because pymxs can't be used
            # from a background thread.
            self._max_version = self.execute_in_main_thread(
                lambda: pymxs.runtime.maxVersion()
            )
        # 3dsMax Version returns a number which contains max version, sdk version, etc...
        return self._max_version
