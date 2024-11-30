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

import pyodbc

from DraftTools import translate

from PySide import  QtCore, QtGui
# from PySide.QtGui import QMessageBox

from MaterialDB.Configuration import getPreferencesLocation

# from MaterialDB.Database.DatabaseMySQLCreate import DatabaseMySQLCreate
# from MaterialDB.Database.Exceptions import DatabaseCreationError, DatabaseTableCreationError
from MaterialDB.util.UIPath import getUIPath

class DlgSettingsDatabase(QtCore.QObject):

    def __init__(self):
        super().__init__()

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(getUIPath(), 'Resources', 'ui', "DlgSettingsDatabase.ui"))

        self.initialize()

    def initialize(self):
        pass

    def saveSettings(self):
        prefs = getPreferencesLocation()
        FreeCAD.ParamGet(prefs).SetString("Connection", self.form.comboConnectionType.currentText())
        FreeCAD.ParamGet(prefs).SetString("DSN", self.form.comboDSN.currentData())
        FreeCAD.ParamGet(prefs).SetString("Database", self.form.editDatabase.text())
        FreeCAD.ParamGet(prefs).SetString("Hostname", self.form.editHostname.text())
        FreeCAD.ParamGet(prefs).SetString("Port", self.form.editPort.text())
        FreeCAD.ParamGet(prefs).SetString("Username", self.form.editUsername.text())
        FreeCAD.ParamGet(prefs).SetString("Password", self.form.editPassword.text())

        # Get the DSN

    def loadSettings(self):
        prefs = getPreferencesLocation()

        connectionTypes = ["ODBC", "MySQL"]
        self.form.comboConnectionType.addItems(connectionTypes)
        connectionType = FreeCAD.ParamGet(prefs).GetString("Connection", "ODBC")
        self.form.comboConnectionType.setCurrentText(connectionType)

        self.show_odbc_sources()

        dbName = FreeCAD.ParamGet(prefs).GetString("Database", "material")
        self.form.editDatabase.setText(dbName)
        hostname = FreeCAD.ParamGet(prefs).GetString("Hostname", "")
        self.form.editHostname.setText(hostname)
        port = FreeCAD.ParamGet(prefs).GetString("Port", "")
        self.form.editPort.setText(port)
        username = FreeCAD.ParamGet(prefs).GetString("Username", "")
        self.form.editUsername.setText(username)
        password = FreeCAD.ParamGet(prefs).GetString("Password", "")
        self.form.editPassword.setText(password)

    def show_odbc_sources(self):
        sources = pyodbc.dataSources()
        dsns = sources.keys()
        # dsns.sort()
        for dsn in dsns:
            self.form.comboDSN.addItem('%s [%s]' % (dsn, sources[dsn]), dsn)

        prefs = getPreferencesLocation()
        currentDSN = FreeCAD.ParamGet(prefs).GetString("DSN", "")
        if currentDSN in dsns:
            self.form.comboDSN.setCurrentText('%s [%s]' % (currentDSN, sources[currentDSN]))