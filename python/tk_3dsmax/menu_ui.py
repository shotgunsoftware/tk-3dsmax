"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

Menu handling for Nuke

"""

import tank
import sys
import os
import unicodedata

from tank.platform.qt import QtCore, QtGui, TankQDialog

class WorkAreaMenu(TankQDialog):

    def __init__(self, parent=None):
        TankQDialog.__init__(self, parent)
        # no window border pls
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
        
    def mousePressEvent(self, event):
        # if no other widgets accepts it, it means click is outside any button
        # close dialog
        self.accept()




class AppsMenu(TankQDialog):

    def __init__(self, parent=None):
        TankQDialog.__init__(self, parent)
        # no window border pls
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
        
    def mousePressEvent(self, event):
        # if no other widgets accepts it, it means click is outside any button
        # close dialog
        self.accept()
