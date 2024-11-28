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

from PySide.QtGui import QMessageBox

from DraftTools import translate

# from MaterialDB.manager.MaterialDBManager import MaterialsDBManager
from MaterialDB.Database.DatabaseMySQLCreate import DatabaseMySQLCreate

from MaterialDB.UI.Tasks.TaskCreateDatabase import TaskPanelCreateDatabase

def createDatabase():
    db = DatabaseMySQLCreate()
    if db.checkIfExists():
        # DB exists
        msgBox = QMessageBox()
        msgBox.setText(translate('MaterialDB', "The database already exists."))

        msgBox.setInformativeText(translate('MaterialDB', "Continuing will destroy the database and replace it with an empty one. Continue?"))
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msgBox.setDefaultButton(QMessageBox.Ok)
        ret = msgBox.exec()
        if ret != QMessageBox.Ok:
            return

    print(translate('MaterialDB', "Create database"))
    taskd = TaskPanelCreateDatabase()
    FreeCADGui.Control.showDialog(taskd)

class CmdCreate:
    def Activated(self):
        createDatabase()

    def IsActive(self):
        return True

    def GetResources(self):
        return {'MenuText': translate("MaterialDB", 'Create database...'),
                'ToolTip': translate("MaterialDB", 'Create database'),
                'Pixmap': FreeCAD.getUserAppDataDir() + "Mod/MaterialDB/Resources/icons/MaterialDB_Create.svg"}
