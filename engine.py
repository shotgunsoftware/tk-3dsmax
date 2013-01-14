#
# Copyright (c) 2012 Shotgun Software, Inc
# ----------------------------------------------------
#
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
        if mxs.maxVersion()[0] != 14000:
            raise tank.TankError("Unsupported version of Max! The tank engine only works with "
                                 "3dsmax version 2012.")
                
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
            css_file = os.path.join(self.disk_location, "resources", "dark.css")
            f = open(css_file)
            css = f.read()
            f.close()
            qt_app_obj.setStyleSheet(css)        
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
        
        # now the center of our button is located 165 pixels to the left
        button_center_from_left = left + 165
        button_center_from_top = top + 28
        
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
        
        # now the center of our button is located 165 pixels to the left
        button_center_from_left = left + 285
        button_center_from_top = top + 28

        # call out to render the menu bar
        self._menu_generator.render_apps_menu(button_center_from_left, button_center_from_top)

    def _define_qt_base(self):
        """
        Re-implemented in order to force tank to use PyQt rather than PySide.
        """
        self.log_debug("Hooking up QT classes...")
        # import QT
        from PyQt4 import QtCore, QtGui
        # hot patch the library to make it work with pyside code
        QtCore.Signal = QtCore.pyqtSignal
        # return QT classes back to the engine base class
        return (QtCore, QtGui)        
    
    def _define_qt_tankdialog(self):
        """
        Re-implemented dialog construction to hook up blur python's
        widget factories to the tank QT window creation functions.
        """
        self.log_debug("Hooking up QT Dialog classes...")
        tk_3dsmax = self.import_module("tk_3dsmax")
        return tk_3dsmax.tankqdialog.TankQDialog 

    def show_dialog(self, dialog_class, *args, **kwargs):
        """
        Shows a dialog window in a way suitable for this engine. The engine will attempt to 
        parent the dialog nicely to the host application.
        
        :param dialog_class: the class to instantiate. This must derive from tank.platform.qt.TankQDialog
        
        Additional parameters specified will be passed through to the dialog_class constructor.
        
        :returns: the created dialog object
        """        
        tk_3dsmax = self.import_module("tk_3dsmax")

        if not issubclass(dialog_class, tk_3dsmax.tankqdialog.TankQDialog):
            raise tank.TankError("Class %s must derive from TankQDialog in order to be displayed." % dialog_class)
        
        # temporary factory method which returns a dialog class instance
        # this is what the blur library needs to construct the classes
        def dialog_factory(parent):
            return dialog_class(*args, **kwargs)
        
        return blurdev.launch(dialog_factory)
        
    
    def show_modal(self, modal_class, *args, **kwargs):
        """
        Shows a modal dialog window in a way suitable for this engine. The engine will attempt to
        integrate it as seamlessly as possible into the host application. This call is blocking 
        until the user closes the dialog.
        
        :param dialog_class: the class to instantiate. This must derive from tank.platform.qt.TankQDialog
        
        Additional parameters specified will be passed through to the dialog_class constructor.

        :returns: (a standard QT dialog status return code, the dialog object)
        """
        tk_3dsmax = self.import_module("tk_3dsmax")

        if not issubclass(modal_class, tk_3dsmax.tankqdialog.TankQDialog):
            raise tank.TankError("Class %s must derive from TankQDialog in order to be displayed." % modal_class)
        
        # temporary factory method which returns a dialog class instance
        # this is what the blur library needs to construct the classes
        self._tmp_modal_dialog_obj = None
        def dialog_factory(parent):
            obj = modal_class(*args, **kwargs)
            self._tmp_modal_dialog_obj = obj
            return obj
        
        status = blurdev.launch(dialog_factory, modal=True)
        return (status, self._tmp_modal_dialog_obj)


    def log_debug(self, msg):
        global g_engine_start_time
        td = time.time() - g_engine_start_time
        sys.stdout.write("%04fs DEBUG: %s\n" % (td, msg))

    def log_info(self, msg):
        global g_engine_start_time
        td = time.time() - g_engine_start_time
        sys.stdout.write("%04fs INFO: %s\n" % (td, msg))

    def log_error(self, msg):
        global g_engine_start_time
        td = time.time() - g_engine_start_time
        sys.stdout.write("%04fs ERROR: %s\n" % (td, msg))
        
    def log_warning(self, msg):
        global g_engine_start_time
        td = time.time() - g_engine_start_time
        sys.stdout.write("%04fs WARNING: %s\n" % (td, msg))
