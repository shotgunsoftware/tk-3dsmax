'''

simple dialog to raise warnings to user

'''

from sgtk.platform.qt import QtGui, QtCore #@UnresolvedImport

#if we have an engine, we can simply use this class
class WarningDialog(QtGui.QWidget):
	
	def __init__(self, message, details=None, *args, **kwargs):
		
		super(WarningDialog, self).__init__(*args, **kwargs)
		
		self.setObjectName("SGTK_WARNING_DIALOG")

		self._label = QtGui.QLabel("<h3>"+message+"</h3>")
		self._label.setTextFormat(QtCore.Qt.RichText)
		self._text = QtGui.QTextEdit()
		self._text.setReadOnly(True)
		#self._text.setLineWrapMode(QtGui.QTextEdit.NoWrap)
		self._text.setText(str(details))

		self._layout = QtGui.QVBoxLayout(self)
		self._layout.addWidget(self._label)
		self._layout.addWidget(self._text)
			
#if we don't have an engine, we'll need to do some of the legwork ourselves
def showWarningDialog(message, details=None):
	
	parent=QtGui.QApplication.activeWindow()
