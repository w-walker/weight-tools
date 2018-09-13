from PySide2 import QtGui, QtCore, QtWidgets
from utils.weight_utils import WeightTools
from shiboken2 import wrapInstance
import ui.main_window as main_window
import maya.OpenMayaUI as omui
reload(main_window)


def getMayaWindow():
    # returns a pointer to the main maya window
    pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(long(pointer), QtWidgets.QWidget)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        self.parent = parent
        super(MainWindow, self).__init__(parent)
        self.ui = main_window.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.weight_export.clicked.connect(self.weight_export)
        self.ui.bind_from_file.clicked.connect(self.bind_to_file)
        self.ui.weight_import.clicked.connect(self.weight_import)

    def show_window(self):
        parent = getMayaWindow()
        window = MainWindow(parent)
        window.show()

    def weight_export(self):
        wt= WeightTools()
        wt.weight_export(path=None, batch=self.ui.batch_mode.isChecked())

    def weight_import(self):
        wt= WeightTools()
        wt.weight_import(path=None, batch=self.ui.batch_mode.isChecked())

    def bind_to_file(self):
        wt= WeightTools()
        wt.bind_from_file(path=None,batch=self.ui.batch_mode.isChecked())


def run():
    mw = MainWindow()
    mw.show_window()
