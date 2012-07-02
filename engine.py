"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

A 3ds Max engine for Tank.

"""

# std libs
import sys

# tank libs
import tank

# application libs
from Py3dsMax import mxs


CONSOLE_OUTPUT_WIDTH = 120

class MaxEngine(tank.platform.Engine):
    def init_engine(self):
        self.log_debug("%s: Initializing..." % self)
        
        # now check that there is a location on disk which corresponds to the context
        # for the 3ds Max engine (because it for example sets the 3ds Max project)
        if len(self.context.entity_locations) == 0:
            raise tank.TankError("No folders on disk are associated with the current context. The 3ds Max "
                "engine requires a context which exists on disk in order to run correctly.")

    def destroy_engine(self):
        self.log_debug('%s: Destroying...' % self)

    def log_debug(self, msg):
        sys.stdout.write(str(msg)+'\n')

    def log_info(self, msg):
        sys.stdout.write(str(msg)+'\n')

    def log_error(self, msg):
        mxs.messageBox(str(msg))
        
    def log_warning(self, msg):
        sys.stdout.write(str(msg)+'\n')
