#
# Copyright (c) 2012 Shotgun Software, Inc
# ----------------------------------------------------
#
"""
A 3ds Max engine for Tank.

"""

# std libs
import os
import sys
import time

# tank libs
import tank

from Py3dsMax import mxs

# global constant keeping the time when the 
# engine was init-ed
g_engine_start_time = time.time()

class MaxEngine(tank.platform.Engine):
    
    
    def init_engine(self):
        """
        constructor
        """
        global g_engine_start_time
        self.log_debug("%s: Initializing..." % self)
         
        # now check that there is a location on disk which corresponds to the context
        # for the 3ds Max engine (because it for example sets the 3ds Max project)
        if len(self.context.entity_locations) == 0:
            raise tank.TankError("No folders on disk are associated with the current context. The 3ds Max "
                "engine requires a context which exists on disk in order to run correctly.")
                
    def post_app_init(self):
        """
        Called when all apps have initialized
        """
        
        # set TANK_MENU_BG_LOCATION needed by the maxscript
        os.environ["TANK_MENU_BG_LOCATION"] = os.path.join(self.disk_location, "resources", "menu_bg.png")
        
        # now execute the max script
        menu_script = os.path.join(self.disk_location, "resources", "menu_bar.ms")
        mxs.fileIn(menu_script)
        
        
#        # todo: detect if in batch mode
#        # create our menu handler
#        tk_3dsmax = self.import_module("tk_3dsmax")
#        adapter = tk_3dsmax.MenuAdapter3dsmax(self)
#        m = tk_3dsmax.MenuGenerator(self, adapter)
#        m.create_menu()

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
        self.log_debug('%s: Destroying...' % self)
        
        # remove menu bar
        menu_script = os.path.join(self.disk_location, "resources", "destroy_menu_bar.ms")
        mxs.fileIn(menu_script)
        
    def max_callback_work_area_menu(self, pos):
        self.log_debug("CALLBACK! %s" % str(pos))
        
    def max_callback_apps_menu(self, pos):
        self.log_debug("APPS CALLBACK! %s" % str(pos))


    def _define_qt_base(self):
        self.log_debug("Hooking up QT classes...")
        from PyQt4 import QtCore, QtGui
        
        # hot patching 
        QtCore.Signal = QtCore.pyqtSignal
        
        return (QtCore, QtGui)        
    
    def _define_qt_tankdialog(self):
        self.log_debug("Hooking up QT Dialog classes...")
        tk_3dsmax = self.import_module("tk_3dsmax")
        return (tk_3dsmax.tankqdialog.TankQDialog, tk_3dsmax.tankqdialog.create_dialog) 

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
