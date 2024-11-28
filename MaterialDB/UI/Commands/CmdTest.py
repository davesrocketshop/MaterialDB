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

from DraftTools import translate

# from MaterialDB.manager.MaterialDBManager import MaterialsDBManager
# import mysql.connector
# import pyodbc

class CmdTest:
    def Activated(self):
        # obj = MaterialsDBManager()
        print("Test")

    def IsActive(self):
        return True

    def GetResources(self):
        return {'MenuText': translate("Rocket", 'Test'),
                'ToolTip': translate("Rocket", 'Test'),
                'Pixmap': FreeCAD.getUserAppDataDir() + "Mod/MaterialDB/Resources/icons/MaterialDBWorkbench.svg"}