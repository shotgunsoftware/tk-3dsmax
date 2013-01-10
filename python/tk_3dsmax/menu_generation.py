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
        
        self._dialog = tank.platform.qt.create_dialog(menu_ui.WorkAreaMenu)
        self._dialog.move(dialog_x, dialog_y)
        self._dialog.resize(width, height)
        
        
        
        
    def render_apps_menu(self, button_center_from_left, button_center_from_top):
        
        from . import menu_ui
        
        height = 300
        width = 150
        
        dialog_x = button_center_from_left - (width/2)
        dialog_y = button_center_from_top - height + 10
        
        self._dialog = tank.platform.qt.create_dialog(menu_ui.AppsMenu)
        self._dialog.move(dialog_x, dialog_y)
        
        self._dialog.resize(width, height)

