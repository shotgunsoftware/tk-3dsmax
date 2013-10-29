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

try:
    from Py3dsMax import mxs
    import blurdev
except:
    raise Exception("Could not import Py3dsMax - in order to run this engine, "
                    "you need to have the blur python extensions installed. "
                    "For more information, see http://code.google.com/p/blur-dev/wiki/Py3dsMax")

# global constant keeping the time when the engine was init-ed
g_engine_start_time = time.time()


class MaxEngine(tank.platform.Engine):
        
    def init_engine(self):
        """
        constructor
        """
        self.log_debug("%s: Initializing..." % self)         
        
        # check max version
        max_major_version = mxs.maxVersion()[0]
        # 14000 means 2012, 13000 means 2011 
        if max_major_version not in (15000, 14000, 13000):
            raise tank.TankError("Unsupported version of 3ds Max! The engine only works with "
                                 "versions 2011, 2012 & 2013.")
                
    def post_app_init(self):
        """
        Called when all apps have initialized
        """
        
        # set TANK_MENU_BG_LOCATION needed by the maxscript
        os.environ["TANK_MENU_BG_LOCATION"] = os.path.join(self.disk_location, "resources", "menu_bg.png")
        
        # now execute the max script to create a menu bar
        menu_script = os.path.join(self.disk_location, "resources", "menu_bar.ms")
        mxs.fileIn(menu_script)
        
        # set up menu handler
        tk_3dsmax = self.import_module("tk_3dsmax")
        self._menu_generator = tk_3dsmax.MenuGenerator(self)

        # set up a qt style sheet
        try:
            qt_app_obj = tank.platform.qt.QtCore.QCoreApplication.instance()
            qt_app_obj.setStyleSheet( self._get_standard_qt_stylesheet() )        
        except Exception, e:
            self.log_warning("Could not set QT style sheet: %s" % e )
                

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
