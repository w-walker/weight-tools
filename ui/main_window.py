# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Z:\wwalker\maya\python\gui\weight_tools\ui\main_window.ui'
#
# Created by: PyQt5 UI code generator 5.7.1
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(168, 228)
        MainWindow.setMinimumSize(QtCore.QSize(168, 228))
        MainWindow.setMaximumSize(QtCore.QSize(168, 228))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.weight_export = QtWidgets.QPushButton(self.centralwidget)
        self.weight_export.setGeometry(QtCore.QRect(10, 10, 151, 61))
        self.weight_export.setObjectName("weight_export")
        self.weight_import = QtWidgets.QPushButton(self.centralwidget)
        self.weight_import.setGeometry(QtCore.QRect(10, 130, 151, 61))
        self.weight_import.setObjectName("weight_import")
        self.batch_mode = QtWidgets.QCheckBox(self.centralwidget)
        self.batch_mode.setGeometry(QtCore.QRect(10, 190, 70, 17))
        self.batch_mode.setObjectName("batch_mode")
        self.bind_from_file = QtWidgets.QPushButton(self.centralwidget)
        self.bind_from_file.setGeometry(QtCore.QRect(10, 70, 151, 61))
        self.bind_from_file.setObjectName("bind_from_file")
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.weight_export.setText(_translate("MainWindow", "Export"))
        self.weight_import.setText(_translate("MainWindow", "Import"))
        self.batch_mode.setText(_translate("MainWindow", "Batch"))
        self.bind_from_file.setText(_translate("MainWindow", "Bind From File"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

