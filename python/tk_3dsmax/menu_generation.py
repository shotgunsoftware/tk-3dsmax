"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

Menu handling for Nuke

"""

import tank
import sys
import os
import unicodedata


class MenuGenerator(object):
    """
    Menu generation functionality for 3dsmax
    """

    def __init__(self, engine):
        self._engine = engine

    ##########################################################################################
    # public methods

    def render_work_area_menu(self, button_center_from_left, button_center_from_top):
        """
        Create a QT window and display
        """
        
        from . import menu_ui
        
        height = 300
        width = 150
        
        dialog_x = button_center_from_left - (width/2)
        dialog_y = button_center_from_top - height + 10
        
        dialog = tank.platform.qt.create_dialog(menu_ui.WorkAreaMenu)
        dialog.move(dialog_x, dialog_y)
        dialog.resize(width, height)
        
        
        # make the context name
        ctx = self._engine.context
        
        if ctx.entity is None:
            # project-only!
            ctx_name = "%s" % ctx.project["name"]
        
        elif ctx.step is None and ctx.task is None:
            # entity only
            # e.g. [Shot ABC_123]
            ctx_name = "%s %s" % (ctx.entity["type"], ctx.entity["name"])

        else:
            # we have either step or task
            task_step = None
            if ctx.step:
                task_step = ctx.step.get("name")
            if ctx.task:
                task_step = ctx.task.get("name")
            
            # e.g. [Lighting, Shot ABC_123]
            ctx_name = "%s, %s %s" % (task_step, ctx.entity["type"], ctx.entity["name"])
        
        dialog.set_work_area_text(ctx_name)
        
        # link to UI
        dialog.add_item("Jump to Shotgun", self._jump_to_sg)
        dialog.add_item("Jump to File System", self._jump_to_fs)

        # add context apps
        for (cmd_name, cmd_details) in self._engine.commands.items():
            properties = cmd_details["properties"]
            callback = cmd_details["callback"]
            if properties.get("type", "default") == "context_menu":
                dialog.add_item(cmd_name, callback)

        
        
        
        
    def render_apps_menu(self, button_center_from_left, button_center_from_top):
        
        from . import menu_ui
        
        height = 300
        width = 150
        
        dialog_x = button_center_from_left - (width/2)
        dialog_y = button_center_from_top - height + 10
        
        dialog = tank.platform.qt.create_dialog(menu_ui.AppsMenu)
        dialog.move(dialog_x, dialog_y)
        
        dialog.resize(width, height)

        for (cmd_name, cmd_details) in self._engine.commands.items():
            properties = cmd_details["properties"]
            callback = cmd_details["callback"]
            if properties.get("type", "default") == "default":
                dialog.add_item(cmd_name, callback)





    def _jump_to_sg(self):
        from tank.platform.qt import QtCore, QtGui
        
        if self._engine.context.entity is None:
            # project-only!
            url = "%s/detail/%s/%d" % (self._engine.shotgun.base_url, 
                                       "Project", 
                                       self._engine.context.project["id"])
        else:
            # entity-based
            url = "%s/detail/%s/%d" % (self._engine.shotgun.base_url, 
                                       self._engine.context.entity["type"], 
                                       self._engine.context.entity["id"])
        
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        
        
    def _jump_to_fs(self):
        
        """
        Jump from context to FS
        """
        
        if self._engine.context.entity:
            paths = self._engine.tank.paths_from_entity(self._engine.context.entity["type"], 
                                                     self._engine.context.entity["id"])
        else:
            paths = self._engine.tank.paths_from_entity(self._engine.context.project["type"], 
                                                     self._engine.context.project["id"])
        
        # launch one window for each location on disk
        # todo: can we do this in a more elegant way?
        for disk_location in paths:                
            cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            exit_code = os.system(cmd)
            if exit_code != 0:
                self._engine.log_error("Failed to launch '%s'!" % cmd)
        