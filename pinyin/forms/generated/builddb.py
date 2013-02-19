# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/builddb.ui'
#
# Created: Tue Feb 19 19:36:49 2013
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_BuildDB(object):
    def setupUi(self, BuildDB):
        BuildDB.setObjectName(_fromUtf8("BuildDB"))
        BuildDB.resize(400, 260)
        self.verticalLayout_2 = QtGui.QVBoxLayout(BuildDB)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.explanationLabel = QtGui.QLabel(BuildDB)
        self.explanationLabel.setWordWrap(True)
        self.explanationLabel.setOpenExternalLinks(True)
        self.explanationLabel.setObjectName(_fromUtf8("explanationLabel"))
        self.verticalLayout_2.addWidget(self.explanationLabel)
        self.progressBar = QtGui.QProgressBar(BuildDB)
        self.progressBar.setMaximum(0)
        self.progressBar.setProperty("value", -1)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.verticalLayout_2.addWidget(self.progressBar)
        self.cancelButtonBox = QtGui.QDialogButtonBox(BuildDB)
        self.cancelButtonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel)
        self.cancelButtonBox.setObjectName(_fromUtf8("cancelButtonBox"))
        self.verticalLayout_2.addWidget(self.cancelButtonBox)

        self.retranslateUi(BuildDB)
        QtCore.QMetaObject.connectSlotsByName(BuildDB)

    def retranslateUi(self, BuildDB):
        BuildDB.setWindowTitle(QtGui.QApplication.translate("BuildDB", "Build Pinyin Toolkit Database", None, QtGui.QApplication.UnicodeUTF8))

