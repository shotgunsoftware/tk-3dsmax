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
A 3ds Max engine for Tank.

"""

import os
import sys
import time
import tank
import sgtk

try:
    from Py3dsMax import mxs
    import blurdev
except:
    raise Exception("Shotgun: Could not import Py3dsMax - in order to run this engine, "
                    "you need to have the blur python extensions installed. "
                    "For more information, see http://code.google.com/p/blur-dev/wiki/Py3dsMax")

# global constant keeping the time when the engine was init-ed
g_engine_start_time = time.time()


class MaxEngine(tank.platform.Engine):
    """
    The main Toolkit engine for 3ds Max
    """
                
    def pre_app_init(self):
        """
        Do any additional initialization before the apps are loaded. 
        """
        self.log_debug("%s: Initializing..." % self)         
        
        # check max version
        max_major_version = mxs.maxVersion()[0]
        # 13000 means 2011, 14000 means 2012, etc. 
        if max_major_version not in (13000, 14000, 15000, 16000):
            raise tank.TankError("Unsupported version of 3ds Max! The engine only works with "
                                 "versions 2011, 2012, 2013* & 2014. (* Please see the engine "
                                 "documentation for more details regarding 2013)")
        elif max_major_version == 15000:
            # specifically for 2013 which is not officially supported but may work, output a warning:
            self.log_warning("This version of 3ds Max is not officially supported by Toolkit and you may "
                             "experience instability.  Please contact toolkitsupport@shotgunsoftware.com "
                             "if you do have any issues.")        
        
        # set up a qt style sheet
        # note! - try to be smart about this and only run
        # the style setup once per session - it looks like
        # 3dsmax slows down if this is executed every engine restart. 
        qt_app_obj = tank.platform.qt.QtCore.QCoreApplication.instance()
        curr_stylesheet = qt_app_obj.styleSheet()
        
        if "toolkit 3dsmax style extension" not in curr_stylesheet:

            self._initialize_dark_look_and_feel()
            
            # note! For some reason it looks like the widget background color isn't being set correctly
            # on 3dsmax top level items. In order to mitigate this, apply a style to set the background
            # color on the main app window area. The main app window area is typically a QWidget which 
            # is a child of a QDialog (created by tk-core) with the name TankDialog. Based on this, 
            # we can construct a style directive QDialog#TankDialog > QWidget which applies to the 
            # immediate QWidget children only.
            curr_stylesheet += "\n\n /* toolkit 3dsmax style extension */ \n\n"
            curr_stylesheet += "\n\n QDialog#TankDialog > QWidget { background-color: #343434; }\n\n"        
            qt_app_obj.setStyleSheet(curr_stylesheet)        
                
        self._safe_dialogs = []

        engine = self
        class DialogEvents(tank.platform.qt.QtCore.QObject):
            def eventFilter(self, obj, event):
                # Remove from tracked dialogs
                if event.type() == tank.platform.qt.QtCore.QEvent.Close:
                    if obj in engine._safe_dialogs: 
                        engine._safe_dialogs.remove(obj)

                return False;

        self.dialogEvents = DialogEvents()
                
    def post_app_init(self):
        """
        Called when all apps have initialized
        """
        # set TANK_MENU_BG_LOCATION needed by the maxscript.  The gamma correction applied to the
        # background images seems to have changed for 2012 & 2013 and then reverted back for 2014
        # which is why there are two versions!
        max_major_version = mxs.maxVersion()[0]
        menu_bg_name = "menu_bg_light.png" if max_major_version in [14000, 15000] else "menu_bg.png"
        os.environ["TANK_MENU_BG_LOCATION"] = os.path.join(self.disk_location, "resources", menu_bg_name)
        
        # now execute the max script to create a menu bar
        menu_script = os.path.join(self.disk_location, "resources", "menu_bar.ms")
        mxs.fileIn(menu_script)
        
        # set up menu handler
        tk_3dsmax = self.import_module("tk_3dsmax")
        self._menu_generator = tk_3dsmax.MenuGenerator(self)

    def destroy_engine(self):
        """
        Called when the engine is shutting down
        """
        self.log_debug('%s: Destroying...' % self)
        
        # remove menu bar
        menu_script = os.path.join(self.disk_location, "resources", "destroy_menu_bar.ms")
        mxs.fileIn(menu_script)
        
    def max_callback_work_area_menu(self, pos):
        """
        Callback called from the maxscript when the work area button is pressed
        """
        # get the coords for the whole widget        
        pos_str = str(pos)
        # '[12344,344233]'
        left_str, top_str = pos_str[1:-1].split(",")
        left = int(left_str)
        top = int(top_str)
        
        # now the center of our button is located 91 pixels from the left hand side
        button_center_from_left = left + 91
        button_center_from_top = top + 16
        
        # call out to render the menu bar
        self._menu_generator.render_work_area_menu(button_center_from_left, button_center_from_top)
        
        
    def max_callback_apps_menu(self, pos):
        """
        Callback called from the maxscript when the apps button is pressed
        """
        # get the coords for the whole widget        
        pos_str = str(pos)
        # '[12344,344233]'
        left_str, top_str = pos_str[1:-1].split(",")
        left = int(left_str)
        top = int(top_str)
        
        # now the center of our button is located 197 pixels from the left hand side
        button_center_from_left = left + 197
        button_center_from_top = top + 16

        # call out to render the menu bar
        self._menu_generator.render_apps_menu(button_center_from_left, button_center_from_top)

    def _define_qt_base(self):
        """
        Re-implemented in order to force tank to use PyQt rather than PySide.
        """
        self.log_debug("Hooking up QT classes...")
        
        base = {}

        # import QT
        from PyQt4 import QtCore, QtGui
        from blurdev.gui import Dialog
        # hot patch the library to make it work with pyside code
        QtCore.Signal = QtCore.pyqtSignal
        QtCore.Slot = QtCore.pyqtSlot
        QtCore.Property = QtCore.pyqtProperty
        base["qt_core"] = QtCore
        base["qt_gui"] = QtGui
        # dialog wrapper needs to be the blurdev dialog 
        base["dialog_base"] = Dialog
        
        return base

    def __launch_blur_dialog(self, title, bundle, widget_class, is_modal, *args, **kwargs):
        """
        Handle launching a TankQDialog using the blur library
        """
        if not self.has_ui:
            self.log_error("Sorry, this environment does not support UI display! Cannot show "
                           "the requested window '%s'." % title)
            return        
        
        from tank.platform.qt import tankqdialog 
        
        # first construct the widget object
        widget = self._create_widget(widget_class, *args, **kwargs)
        
        # temporary factory method which returns a dialog class instance
        # this is what the blur library needs to construct the classes
        def dialog_factory(parent):
            dlg = self._create_dialog(title, bundle, widget, parent)
            return dlg

        blur_result = blurdev.launch(dialog_factory, modal=is_modal) 

        # get the dialog result from the returned blur result:
        dlg_res = None
        
        from tank.platform.qt import QtGui
        if isinstance(blur_result, QtGui.QDialog):
            # As of Blur 13312, the result returned from launching a dialog
            # using Blur seems to be the dialog iteslf rather than the dialog
            # code as was previously returned!
            dlg_res = blur_result.result()
        elif isinstance(blur_result, int):
            # the result is the dialog return code
            dlg_res = blur_result
        else:
            raise TankError("Blur returned an unexpected result when launching a dialog: %s" % blur_result)
        
        return (dlg_res, widget)
        
    ##########################################################################################
    # Engine
    def _create_dialog(self, title, bundle, widget, parent):
        """
        Install event filtering in order to allow tracking dialogs
        """
        dialog = sgtk.platform.Engine._create_dialog(self, title, bundle, widget, parent)
        dialog.installEventFilter(self.dialogEvents)

        # Add to tracked dialogs (will be removed in eventFilter)
        self._safe_dialogs.append(dialog)

        return dialog

    def show_dialog(self, title, bundle, widget_class, *args, **kwargs):
        """
        Shows a non-modal dialog window in a way suitable for this engine. 
        The engine will attempt to parent the dialog nicely to the host application.
        
        :param title: The title of the window
        :param bundle: The app, engine or framework object that is associated with this window
        :param widget_class: The class of the UI to be constructed. This must derive from QWidget.
        
        Additional parameters specified will be passed through to the widget_class constructor.
        
        :returns: the created widget_class instance
        """
        res = self.__launch_blur_dialog(title, bundle, widget_class, False, *args, **kwargs)
        if not res:
            return
        status, widget = res
        return widget
    
    def show_modal(self, title, bundle, widget_class, *args, **kwargs):
        """
        Shows a modal dialog window in a way suitable for this engine. The engine will attempt to
        integrate it as seamlessly as possible into the host application. This call is blocking 
        until the user closes the dialog.
        
        :param title: The title of the window
        :param bundle: The app, engine or framework object that is associated with this window
        :param widget_class: The class of the UI to be constructed. This must derive from QWidget.
        
        Additional parameters specified will be passed through to the widget_class constructor.

        :returns: (a standard QT dialog status return code, the created widget_class instance)
        """
        return self.__launch_blur_dialog(title, bundle, widget_class, True, *args, **kwargs)

    def log_debug(self, msg):
        if not hasattr(self, "_debug_logging"):
            self._debug_logging = self.get_setting("debug_logging", False)
            
        if self._debug_logging:
            global g_engine_start_time
            td = time.time() - g_engine_start_time
            sys.stdout.write("%04fs Shotgun Debug: %s\n" % (td, msg))

    def log_info(self, msg):
        global g_engine_start_time
        td = time.time() - g_engine_start_time
        sys.stdout.write("%04fs Shotgun: %s\n" % (td, msg))

    def log_error(self, msg):
        global g_engine_start_time
        td = time.time() - g_engine_start_time
        sys.stdout.write("%04fs Shotgun Error: %s\n" % (td, msg))
        
    def log_warning(self, msg):
        global g_engine_start_time
        td = time.time() - g_engine_start_time
        sys.stdout.write("%04fs Shotgun Warning: %s\n" % (td, msg))

    def set_safe_modal_dialog(self, dialog):
        """
        Sets the dialog to be used by safe_modal_maxscript_eval
        :param dialog: Dialog to preserve
        """
        self._safe_dialogs = dialog

    def safe_dialog_exec(self, func):
        """
        If running a command from a dialog also creates a 3ds max window, this function tries to
        ensure that the dialog will stay alive and that the max modal window becomes visible
        and unobstructed.

        :param script: Function to execute (partial/lambda)
        """

        # Merge operation can cause max dialogs to pop up, and closing the window results in a crash.
        # So keep alive and hide all of our qt windows while this type of operations are occuring.
        # Note: With Blur's Py3dsMax, hiding a window or changing its windowFlags to disable
        #       closing the window actually causes the window to be destroyed. So the next best thing
        #       is to at least not allow the user to interct with the dialog while a max modal is present.
        for dialog in self._safe_dialogs:
            dialog.setEnabled(False)

            func()

            # Restore the window after the operation is completed
        for dialog in self._safe_dialogs:
            dialog.setEnabled(True)
