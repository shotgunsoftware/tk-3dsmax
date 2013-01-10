"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

Menu handling for Nuke

"""

import tank
import sys
import os
import unicodedata
from Py3dsMax import mxs

from .menu_adapter import BaseMenuAdapter
from .menu_adapter import MenuItem


class MenuAdapter3dsmax(BaseMenuAdapter):
    """
    3dsmax implementation of menu commands
    """
    
    def __init__(self, engine):
        BaseMenuAdapter.__init__(self)
        self._engine = engine
        
    def render_menu(self):
        
        # make main entry
        menu_obj = self._create_main_tank_menu()
        
        # process rest
        self._process_menu_r(menu_obj)
        
    def launch_web_browser(self, url):
        from PyQt4 import QtGui, QtCore
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        
        
    def _process_menu_r(self, menu_obj):
        """
        Create menu structure, recursively
        """
        parent_handle = menu_obj.handle
        
        for item in menu_obj.get_children():
            self._engine.log_debug("Creating menu item: %s" % item)
            
            if item.get_type() == MenuItem.DIVIDER:
                handle = mxs.menuMan.createSeparatorItem()
                parent_handle.addItem(handle, -1)
            
            elif item.get_type() == MenuItem.ACTION:
                handle = mxs.menuMan.createActionItem(item.get_name(), "Tank")
                if handle is None:
                    self._engine.log_warning("Could not register menu item %s!" % item)
                else:
                    handle.setTitle(item.get_name())
                    parent_handle.addItem(handle, -1)
            
            elif item.get_type() == MenuItem.MENU:
                # strange how this needs to be declared twice
                menu_handle = mxs.menuMan.createMenu(item.get_name())
                handle = mxs.menuMan.createSubMenuItem(item.get_name(), menu_handle)
                parent_handle.addItem(handle, -1)
                
                # associate the handle with our internal menu obj
                # then process recursively
                item.handle = menu_handle
                self._process_menu_r(item)
                
            else:
                raise Exception("Unknown menu type!")
 
        
    def _create_main_tank_menu(self):
        """
        Creates a Tank menu and returns a menu handle
        """
        root_obj = self._get_menu_root()
        root_name = root_obj.get_name()
        
        menu_handle = mxs.menuMan.findMenu(root_name)
        
        # create the tank menu
        if menu_handle is None:
            # no tank menu - so create it!
            menu_item = mxs.menuMan.createMenu(root_name)
            sub_menu = mxs.menuMan.createSubMenuItem(root_name, menu_item)
            
            # figure out the menu index - place after MAXScript menu
            main_menu = mxs.menuMan.getMainMenuBar()
            for idx in range(main_menu.numItems()):
                # indices are one based
                menu_idx = idx+1
                if main_menu.getItem(menu_idx).getTitle() == "&MAXScript":
                    tank_menu_index = menu_idx+1
                    break
            
            main_menu.addItem(sub_menu, tank_menu_index)
            mxs.menuMan.updateMenuBar()
            menu_handle = mxs.menuMan.findMenu(root_name)
        
        # attach 3dsmax impl to object
        root_obj.handle = menu_handle
        
        return root_obj
        
        

        

