"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

Default implementation for the Tank Dialog

"""

from PyQt4 import QtCore, QtGui
from blurdev.gui import Dialog

class TankQDialog(Dialog):
    """
    Overridden class which replaces the standard implementation of TankQDialog
    In 3dsmax we derive dialog classes from the blur base class.
    """
    
    def __init__(self):
        Dialog.__init__(self)
        
