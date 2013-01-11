"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

Default implementation for the Tank Dialog

"""

from PyQt4 import QtCore, QtGui
import blurdev
from blurdev.gui import Dialog

class TankQDialog(Dialog):
    """
    Overridden class which replaces the standard implementation of TankQDialog
    In 3dsmax we derive dialog classes from the blur base class.
    """
        
def create_dialog(dialog_class):
    """
    Creates a dialog instance for a given dialog class.
    This replaces the standard method with the blur python equivalent.
    """
    return blurdev.launch(dialog_class)
