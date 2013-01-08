"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

Menu handling for Nuke

"""

import tank
import sys
import os
import unicodedata

class BaseMenuAdapter(object):
    """
    Abstract Base class which represents menu functionality
    """
    
    def __init__(self):
        self.__root = None
    
    def create_tank_menu(self):
        """
        Create and return the root tank menu handle
        """
        self.__root = MenuItem(MenuItem.MENU, "Tank")
        return self.__root 
    
    def create_item(self, menu_obj, name, callback, icon=None):
        """
        Create a new menu item and return it
        """
        obj = MenuItem(MenuItem.ACTION, name)
        menu_obj.add_child(obj)
        return obj
        
    def create_submenu(self, menu_obj, name):
        """
        Create a new submenu and return it
        """
        obj = MenuItem(MenuItem.MENU, name)
        menu_obj.add_child(obj)
        return obj
        
    def create_divider(self, menu_obj):
        """
        Create a new separator and return it
        """
        obj = MenuItem(MenuItem.DIVIDER, None)
        menu_obj.add_child(obj)
        return obj
        
    def create_other(self, type, name, callback, properties):
        """
        Create an alternative item. This is engine specific,
        and may be a node menu, a context menu etc.
        """
        return
        
    def render_menu(self):
        """
        Does the actual menu creation. Implemented by the deriving class.
        """
        raise Exception("This method needs to be implemented by a deriving class!")
        
    def launch_web_browser(self, url):
        """
        Launches a url. Defaults to a std pyside implementation
        that can be overridden by deriving classes
        """
        from PySide import QtCore, QtGui
        # deal with fucked up nuke unicode handling
        if url.__class__ == unicode:
            url = unicodedata.normalize('NFKD', url).encode('ascii', 'ignore')
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
                
    ###############################################################################################
    #
    # Protected Stuff
    #
    def _get_menu_root(self):
        """
        returns the main Tank menu handle 
        """
        return self.__root
    
    
class MenuItem(object):
    """
    Represents a menu item. 
    """
    
    ACTION, MENU, DIVIDER = range(3)
    
    def __init__(self, type, name):
        """
        Constructor
        """
        self._name = name
        self._type = type
        self._items = []

    def __repr__(self):
        
        if self._type == MenuItem.ACTION:
            return "[Menu Action:%s]" % self._name
        elif self._type == MenuItem.DIVIDER:
            return "[Menu Divider]"
        elif self._type == MenuItem.MENU:
            return "[Menu Menu:%s]" % self._name
        else:
            return "[Menu Unknown:%s]" % self._name

    def add_child(self, menu_obj):
        """
        Adds a sub item
        """
        self._items.append(menu_obj)
        
    def get_type(self):
        return self._type
        
    def get_name(self):
        return self._name

    def get_children(self):
        return self._items


