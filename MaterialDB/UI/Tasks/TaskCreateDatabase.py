# ***************************************************************************
# *   Copyright (c) 2024 David Carter <dcarter@davidcarter.ca>              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

__author__ = "David Carter"
__url__ = "https://www.davesrocketshop.com"

import FreeCAD
import FreeCADGui
import os
import math

from DraftTools import translate

from PySide import  QtCore, QtGui
from PySide.QtGui import QMessageBox

from MaterialDB.Configuration import getPreferencesLocation

from MaterialDB.Database.DatabaseMySQLCreate import DatabaseMySQLCreate
from MaterialDB.Database.Exceptions import DatabaseCreationError, DatabaseTableCreationError
from MaterialDB.util.UIPath import getUIPath

class TaskPanelCreateDatabase(QtCore.QObject):

    def __init__(self):
        super().__init__()

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(getUIPath(), 'Resources', 'ui', "DlgCreateDatabase.ui"))

        self._db = DatabaseMySQLCreate()
        self.initialize()

    def initialize(self):
        prefs = getPreferencesLocation()
        dbName = FreeCAD.ParamGet(prefs).GetString("Database", "material")
        self.form.editDatabase.setText(dbName)

    def saveSettings(self):
        prefs = getPreferencesLocation()
        FreeCAD.ParamGet(prefs).SetString("Database", self.form.editDatabase.text())

    def getStandardButtons(self):
        return QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Close

    def modifyStandardButtons(self, box):
        createButton = box.button(QtGui.QDialogButtonBox.Ok)
        createButton.setText(translate("MaterialDB", "Create"))

    def accept(self):
        self.saveSettings()

        try:
            self.updateStatus(translate('MaterialDB', "Creating database..."))
            self._db.createDatabase(self.form.editDatabase.text())
            self.updateStatus(translate('MaterialDB', "Creating tables..."))
            self._db.createTables()
            self.updateStatus(translate('MaterialDB', "done"))
        except DatabaseCreationError as dbErr:
            self.reportError(translate('MaterialDB', "Unable to create database."),
                             dbErr._error)
        except DatabaseTableCreationError as tableErr:
            self.reportError(translate('MaterialDB', "Unable to create database tables."),
                             tableErr._error)

        # self.deactivate()
        return False

    def reportError(self, title, error):
        msgBox = QMessageBox()
        msgBox.setText(title)

        msgBox.setInformativeText(str(error))
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.setDefaultButton(QMessageBox.Ok)
        msgBox.exec()

    def updateStatus(self, status):
        print(status)
        self.form.textStatus.append(status)

        # This is required to update in real time
        QtCore.QCoreApplication.processEvents()

    def reject(self):
        self.deactivate()
        return True

    def deactivate(self):
        if FreeCADGui.Control.activeDialog():
            FreeCADGui.Control.closeDialog()
