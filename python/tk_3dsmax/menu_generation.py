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
Menu handling for 3ds Max

"""

import tank
import sys
import os
import unicodedata
import blurdev


class MenuGenerator(object):
    """
    Menu generation functionality for 3dsmax
    """

    def __init__(self, engine):
        self._engine = engine
        
        self._current_work_area_menu = None
        self._current_app_menu = None

    ##########################################################################################
    # public methods

    def render_work_area_menu(self, button_center_from_left, button_center_from_top):
        """
        Create a QT window and display
        """
        
        from . import menu_ui
        
        self._close_existing_menus()
        
        height = 300
        width = 200
        
        dialog_x = button_center_from_left - (width/2)
        dialog_y = button_center_from_top - height + 10
        
        self._current_work_area_menu = blurdev.launch(menu_ui.WorkAreaMenu)
        
        self._current_work_area_menu.move(dialog_x, dialog_y)
        self._current_work_area_menu.resize(width, height)
        
        
        # make the context name
        ctx = self._engine.context
        ctx_name = str(ctx)        
        self._current_work_area_menu.set_work_area_text(ctx_name)
        
        # link to UI
        self._current_work_area_menu.add_item("Jump to Shotgun", self._jump_to_sg)
        self._current_work_area_menu.add_item("Jump to File System", self._jump_to_fs)

        # add context apps
        for (cmd_name, cmd_details) in self._engine.commands.items():
            properties = cmd_details["properties"]
            callback = cmd_details["callback"]
            if properties.get("type", "default") == "context_menu":
                self._current_work_area_menu.add_item(cmd_name, callback)

        
        
        
        
    def render_apps_menu(self, button_center_from_left, button_center_from_top):
        
        from . import menu_ui
        
        self._close_existing_menus()
        
        height = 300
        width = 200
        
        dialog_x = button_center_from_left - (width/2)
        dialog_y = button_center_from_top - height + 10
        
        self._current_app_menu = blurdev.launch(menu_ui.AppsMenu)
        self._current_app_menu.move(dialog_x, dialog_y)
        
        self._current_app_menu.resize(width, height)

        for (cmd_name, cmd_details) in self._engine.commands.items():
            properties = cmd_details["properties"]
            callback = cmd_details["callback"]
            if properties.get("type", "default") == "default":
                self._current_app_menu.add_item(cmd_name, callback)


    ##########################################################################################
    # private methods

    def _close_existing_menus(self):
        """
        Close any open menus
        """
        if self._current_work_area_menu:
            self._current_work_area_menu.accept()
            self._current_work_area_menu = None
        
        if self._current_app_menu:
            self._current_app_menu.accept()
            self._current_app_menu = None

    def _jump_to_sg(self):
        """
        Jump to shotgun, launch web browser
        """
        from tank.platform.qt import QtCore, QtGui        
        url = self._engine.context.shotgun_url
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        
    def _jump_to_fs(self):
        """
        Jump from context to FS
        """
        # launch one window for each location on disk
        paths = self._engine.context.filesystem_locations
        for disk_location in paths:                
            cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            exit_code = os.system(cmd)
            if exit_code != 0:
                self._engine.log_error("Failed to launch '%s'!" % cmd)
        