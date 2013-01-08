#
# Copyright (c) 2012 Shotgun Software, Inc
# ----------------------------------------------------
#
"""
A 3ds Max engine for Tank.

"""

# std libs
import sys
import time

# tank libs
import tank

# global constant keeping the time when the 
# engine was init-ed
g_engine_start_time = 0

class MaxEngine(tank.platform.Engine):
    
    
    def init_engine(self):
        """
        constructor
        """
        global g_engine_start_time
        g_engine_start_time = time.time()
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
        # todo: detect if in batch mode
        # create our menu handler
        tk_3dsmax = self.import_module("tk_3dsmax")
        adapter = tk_3dsmax.MenuAdapter3dsmax(self)
        m = tk_3dsmax.MenuGenerator(self, adapter)
        m.create_menu()
                

    def destroy_engine(self):
        self.log_debug('%s: Destroying...' % self)

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
