# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'app_menu.ui'
#
# Created: Thu Jan 10 16:43:31 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_AppMenu(object):
    def setupUi(self, AppMenu):
        AppMenu.setObjectName("AppMenu")
        AppMenu.resize(268, 293)
        self.verticalLayout = QtGui.QVBoxLayout(AppMenu)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.browser_header = QtGui.QGroupBox(AppMenu)
        self.browser_header.setMinimumSize(QtCore.QSize(0, 44))
        self.browser_header.setMaximumSize(QtCore.QSize(16777215, 44))
        self.browser_header.setStyleSheet("#browser_header {\n"
"border: none;\n"
"background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(97, 97, 97, 255), stop:1 rgba(49, 49, 49, 255))\n"
"}")
        self.browser_header.setTitle("")
        self.browser_header.setObjectName("browser_header")
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.browser_header)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtGui.QLabel(self.browser_header)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.verticalLayout.addWidget(self.browser_header)
        self.scroll_area = QtGui.QScrollArea(AppMenu)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("scroll_area")
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 262, 244))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setContentsMargins(4, 4, 4, 4)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.scroll_area_layout = QtGui.QVBoxLayout()
        self.scroll_area_layout.setSpacing(0)
        self.scroll_area_layout.setObjectName("scroll_area_layout")
        self.verticalLayout_4.addLayout(self.scroll_area_layout)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem)
        self.scroll_area.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scroll_area)

        self.retranslateUi(AppMenu)
        QtCore.QMetaObject.connectSlotsByName(AppMenu)

    def retranslateUi(self, AppMenu):
        AppMenu.setWindowTitle(QtGui.QApplication.translate("AppMenu", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("AppMenu", "Browser Title", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
