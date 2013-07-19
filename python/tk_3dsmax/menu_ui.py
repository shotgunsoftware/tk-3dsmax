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
Menu handling
"""

import tank
import sys
import os
import unicodedata

from tank.platform.qt import QtCore, QtGui
from blurdev.gui import Dialog

from .ui.app_menu import Ui_AppMenu
from .ui.context_menu import Ui_ContextMenu

class WorkAreaMenu(Dialog):
    """
    Represents the current work area menu
    """
    def __init__(self, parent=None):
        Dialog.__init__(self, parent)
        self.ui = Ui_ContextMenu() 
        self.ui.setupUi(self)        
        # no window border pls
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
        self._dynamic_widgets = []
        self._ui_visible = True
        
    def accept(self):
        """
        closes the menu object. This may be called several times
        and will do the right thing (e.g. if the actual UI object
        has been destroyed, it will just do nothing
        """
        if self._ui_visible:
            Dialog.accept(self)
            self._ui_visible = False            
        
    def mousePressEvent(self, event):
        # if no other widgets accepts it, it means click is outside any button
        # close dialog
        self.accept()

    def set_work_area_text(self, msg):
        """
        Sets the top text
        """
        self.ui.label.setText(msg)

    def __click_and_close_wrapper(self, callback):
        """
        Closes the dialog, then runs callback
        """
        self.accept()
        callback()

    def add_item(self, label, callback):
        """
        Adds a list item. Returns the created object.
        """
        widget = QtGui.QPushButton(self)
        widget.setText(label)
        self.ui.scroll_area_layout.addWidget(widget)
        self._dynamic_widgets.append(widget)   
        widget.clicked.connect( lambda : self.__click_and_close_wrapper(callback) )   
        return widget  


class AppsMenu(Dialog):
    """
    Represents the current apps menu
    """

    def __init__(self, parent=None):
        Dialog.__init__(self, parent)
        self.ui = Ui_AppMenu() 
        self.ui.setupUi(self)                
        # no window border pls
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
        self.ui.label.setText("Your Current Apps")
        self._dynamic_widgets = []
        self._ui_visible = True
        
    def accept(self):
        """
        closes the menu object. This may be called several times
        and will do the right thing (e.g. if the actual UI object
        has been destroyed, it will just do nothing
        """
        if self._ui_visible:
            Dialog.accept(self)
            self._ui_visible = False
        
    def mousePressEvent(self, event):
        # if no other widgets accepts it, it means click is outside any button
        # close dialog
        self.accept()

    def __click_and_close_wrapper(self, callback):
        """
        Closes the dialog, then runs callback
        """
        self.accept()
        callback()

    def add_item(self, label, callback):
        """
        Adds a list item. Returns the created object.
        """
        widget = QtGui.QPushButton(self)
        widget.setText(label)
        self.ui.scroll_area_layout.addWidget(widget)
        self._dynamic_widgets.append(widget)
        widget.clicked.connect( lambda : self.__click_and_close_wrapper(callback) )   
        return widget  
