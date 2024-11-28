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

import pyodbc

import FreeCAD

from DraftTools import translate

from MaterialDB.Database.Exceptions import DatabaseConnectionError

class Database:

    def __init__(self):
        self._connection = None

        # self._database = "material" # This needs to be generalized

    def _connect(self):
        if self._connection is None:
            self._connectODBC()

    def _cursor(self):
        for retry in range(3):
            try:
                self._connect()
                cursor = self._connection.cursor()
                return cursor
            except pyodbc.ProgrammingError:
                # Force a reconnection
                FreeCAD.Console.PrintError(translate('MaterialDB', "\nUnable to connect to database. Reconnecting...\n"))
                self._connection = None

        raise DatabaseConnectionError()

    def _connectODBC(self):
        try:
            self._connection = pyodbc.connect('DSN=material;charset=utf8mb4')
            self._connection.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
            self._connection.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
            self._connection.setencoding(encoding='utf-8')
        except Exception as ex:
            print("Unable to create connection:", ex)
            self._connection = None

    def _lastId(self, cursor):
        """Returns the last insertion id"""
        cursor.execute("SELECT @@IDENTITY as id")
        row = cursor.fetchone()
        if row:
            return row.id
        return 0

    def checkCreatePermissions(self):
        return False

    def checkManageUsersPermissions(self):
        return False

    def checkManageLibrariesPermissions(self):
        return False

    def checkCreateLibrariesPermissions(self):
        return False
