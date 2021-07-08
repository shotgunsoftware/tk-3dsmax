# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk #@UnresolvedImport
import os
from traceback import format_exc

from .menu_generation import MenuGenerator
from .maxscript import MaxScript
from .warning_dialog import WarningDialog

import MaxPlus, pymxs #@UnresolvedImport

logger = sgtk.LogManager.get_logger(__name__)

g_tank_callbacks_registered = False

def PostOpenProcess(*args, **kwargs):
    """
    Callback that fires every time a script is loaded.
    """
    try:
        logger.debug("SGTK Callback: script loaded")
        # If we have opened a file then we should check if automatic 
        # context switching is enabled and change if possible
        engine = sgtk.platform.current_engine()
        file_name = _session_path()
        logger.debug("Currently running engine: %s" % (engine,))
        logger.debug("File name to load: '%s'" % (file_name,))
        
        #if we already have a context and it matches the path, dont do anything else
        curr_ctx = None
        if engine:
            curr_ctx = engine.context
            new_ctx = engine.sgtk.context_from_path(file_name, curr_ctx)
            if curr_ctx==new_ctx:
                logger.debug("Shotgun reports context is already correct, not attempting to reset")
                return

        if file_name and engine is not None:
            logger.debug("Will attempt to execute tank_from_path('%s')" % (file_name,))
            try:
                # todo: do we need to create a new tk object, instead should we just 
                # check that the context gets created correctly?
                tk = sgtk.sgtk_from_path(file_name)
                logger.debug("Instance '%s'is associated with '%s'" % (tk, file_name))
            except sgtk.TankError as e:
                error=format_exc().replace('\n', '<br />')
                errorMessage="No tk instance associated with '%s':<br /><br /> %s<br /><br />%s" % (file_name, e, error)
                friendlyMessage='<b>Could not determine a Shotgun Entitiy for '+os.path.basename(file_name)+",</b><br />"
                friendlyMessage+='Please ensure you are in a Shotgun-aware instance of 3dsMax with the correct project and try again.'
                logger.debug(errorMessage)
                engine.show_modal('Error Initializing Shotgun', 
										engine,
										WarningDialog,
										message=friendlyMessage,
										details=errorMessage)
                
                #TODO: replace with command that just remove tools requiring specific context (ie Publish)
                #but leave tools that can direct a user back to the correct context (ie Workfiles)
                engine._remove_shotgun_menu()
                return

            # try to get current ctx and inherit its values if possible
            curr_ctx = None
            if sgtk.platform.current_engine():
                curr_ctx = sgtk.platform.current_engine().context

            logger.debug("")
            new_ctx = tk.context_from_path(file_name, curr_ctx)
            logger.debug("Current context: %r" % (curr_ctx,))
            logger.debug("New context: %r" % (new_ctx,))
            # Now switch to the context appropriate for the file
            engine.change_context(new_ctx)

        elif file_name and engine is None:
        
            #NOTE that this is untested, as I was unable to determine when this sitatuation would be true
            
            # we have no engine, this maybe because the integration disabled itself, 
            # due to a non Toolkit file being opened, prior to this new file. We must 
            # create a sgtk instance from the script path.
            logger.debug("3dsmax file is already loaded but no tk engine running.")
            logger.debug("Will attempt to execute tank_from_path('%s')" % (file_name,))
            try:
                tk = sgtk.sgtk_from_path(file_name)
                logger.debug("Instance '%s'is associated with '%s'" % (tk, file_name))
            except sgtk.TankError as e:
                error=format_exc().replace('\n', '<br />')
                errorMessage="No tk instance associated with '%s':<br /><br /> %s<br /><br />%s" % (file_name, e, error)
                friendlyMessage='<b>Could not determine a Shotgun Entitiy for '+os.path.basename(file_name)+",</b><br />"
                friendlyMessage+='Please ensure you are in a Shotgun-aware instance of 3dsMax with the correct project and try again.'
                logger.debug(errorMessage)
                engine.show_modal('Error Initializing Shotgun', 
										engine,
										WarningDialog,
										message=friendlyMessage,
										details=errorMessage)

                engine._remove_shotgun_menu()
                return

            new_ctx = tk.context_from_path(file_name)
            logger.debug("New context: %r" % (new_ctx,))
            # Now switch to the context appropriate for the file
            engine.change_context(new_ctx)

    except Exception:
        error=format_exc()
        logger.exception("An exception was raised during addOnScriptLoad callback.")
        friendlyMessage='An unknown error occured attempting to initialize the Shotgun engine.'
        logger.debug(error)
        engine.show_modal('Error Initializing Shotgun', 
										engine,
										WarningDialog,
										message=friendlyMessage,
										details=error)
        return

def tank_ensure_callbacks_registered(engine=None):
    """
    Make sure that we have callbacks tracking context state changes.
    The OnScriptLoad callback really only comes into play when you're opening a file or creating a new script, when
    there is no current script open in your Nuke session. If there is a script currently open then this will spawn a
    new Nuke instance and the callback won't be called.
    """
    
    global g_tank_callbacks_registered
    
    logger.debug("Setting up 3dsMax Context Switching callbacks")

    # we'll assume context switching is allowed for now
    #if engine.get_setting("automatic_context_switch"):
    if not g_tank_callbacks_registered:
        logger.debug("SGTK Registering onLoad callback")
        MaxPlus.NotificationManager.Register(MaxPlus.NotificationCodes.FilePostOpen, PostOpenProcess)
        g_tank_callbacks_registered = True
    #else:
        # we have an engine but the automatic context switching has been disabled, we should ensure the callbacks
        # are removed.
    #    if g_tank_callbacks_registered:
            #remove here
    #        g_tank_callbacks_registered = False
    
def _session_path():
    """
    Return the path to the current session
    :return:
    """
    if pymxs.runtime.maxFilePath and pymxs.runtime.maxFileName:
        return os.path.join(pymxs.runtime.maxFilePath, pymxs.runtime.maxFileName)
    else:
        return None

def __engine_refresh(new_context):
    """
    Checks if the 3dsmax engine should be created or just have the context changed.
    If an engine is already started then we just need to change context, 
    else we need to start the engine.
    """

    engine_name = 'tk-3dsmax'
    
    curr_engine = sgtk.platform.current_engine()
    if curr_engine:
        # If we already have an engine, we can just tell it to change contexts
        curr_engine.change_context(new_context)
    else:
        # try to create new engine
        try:
            logger.debug(
                "Starting new engine: %s, %s, %s" % (
                    engine_name, 
                    new_context.sgtk, 
                    new_context
                )
            )
            sgtk.platform.start_engine(engine_name, new_context.sgtk, new_context)
            
        except sgtk.TankEngineInitError as e:
            # context was not sufficient! - disable tank!
            logger.exception("Engine could not be started.")
            
            #TODO: replace with command that just remove tools requiring specific context (ie Publish)
            #but leave tools that can direct a user back to the correct context (ie Workfiles)
            
            #engine._remove_shotgun_menu()
            
            
            
            