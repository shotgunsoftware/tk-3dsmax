# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from .menu_generation import MenuGenerator
from .maxscript import MaxScript
'''
import MaxPlus #@UnresolvedImport

g_tank_callbacks_registered = False

def PostOpenProcess(*args, **kwargs):
    print "PostOpenProcess executed with "
    print "args: "+str(args)
    print "kwargs: "+str(kwargs)

def tank_ensure_callbacks_registered(engine=None):
    """
    Make sure that we have callbacks tracking context state changes.
    The OnScriptLoad callback really only comes into play when you're opening a file or creating a new script, when
    there is no current script open in your Nuke session. If there is a script currently open then this will spawn a
    new Nuke instance and the callback won't be called.
    """

    # Register only if we're missing an engine (to allow going from disabled to something else)
    # or if the engine specifically requests for it.
    if not engine or engine.get_setting("automatic_context_switch"):
        global g_tank_callbacks_registered
        if not g_tank_callbacks_registered:
            MaxPlus.NotificationManager.Register(MaxPlus.NotificationCodes.FilePostOpen, PostOpenProcess)
            g_tank_callbacks_registered = True
    elif engine and not engine.get_setting("automatic_context_switch"):
        # we have an engine but the automatic context switching has been disabled, we should ensure the callbacks
        # are removed.
        global g_tank_callbacks_registered
        if g_tank_callbacks_registered:
            #remove here
            g_tank_callbacks_registered = False
'''