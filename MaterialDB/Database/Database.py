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
from pyodbc import Cursor, Connection

import FreeCAD

from DraftTools import translate

from MaterialDB.Database.Exceptions import DatabaseConnectionError
from MaterialDB.Configuration import getPreferencesLocation

_connection = None

class Database:

    def __init__(self):
        self._disconnect()

        # self._database = "material" # This needs to be generalized

    def _connect(self, noDatabase : bool = False) -> None:
        global _connection
        if _connection is None:
            self._connectODBC(noDatabase)

    def _disconnect(self) -> None:
        global _connection
        if _connection:
            _connection.close()
        _connection = None

    def _getConnection(self) -> Connection | None:
        global _connection
        return _connection

    def _cursor(self, noDatabase : bool = False) -> Cursor:
        global _connection
        for retry in range(3):
            try:
                self._connect(noDatabase)
                if _connection:
                    cursor = _connection.cursor()
                    return cursor
            except pyodbc.ProgrammingError:
                # Force a reconnection
                FreeCAD.Console.PrintError(translate('MaterialDB', "\nUnable to connect to database. Reconnecting...\n"))
                self._disconnect()

        raise DatabaseConnectionError()

    def _connectODBC(self, noDatabase : bool = False) -> None:
        global _connection
        try:
            prefs = getPreferencesLocation()
            connectString = ""
            currentDriver = FreeCAD.ParamGet(prefs).GetString("Driver", "")
            if currentDriver:
                  connectString = connectString + "Driver={%s}" % (currentDriver)
            currentDSN = FreeCAD.ParamGet(prefs).GetString("DSN", "")
            if currentDSN:
                if connectString:
                    connectString = connectString + ';'
                connectString = connectString + 'DSN={}'.format(currentDSN)
            hostname = FreeCAD.ParamGet(prefs).GetString("Hostname", "")
            if hostname:
                if connectString:
                    connectString = connectString + ';'
                connectString = connectString + "Server={}".format(hostname)
            port = FreeCAD.ParamGet(prefs).GetString("Port", "")
            if port:
                  connectString = connectString + ";Port={}".format(port)
            dbName = FreeCAD.ParamGet(prefs).GetString("Database", "material")
            if dbName and not noDatabase:
                  connectString = connectString + ";Database={}".format(dbName)
            username = FreeCAD.ParamGet(prefs).GetString("Username", "")
            if username:
                  connectString = connectString + ";Uid={}".format(username)
            password = FreeCAD.ParamGet(prefs).GetString("Password", "")
            if password:
                  connectString = connectString + ";Pwd={}".format(password)
            connectString = connectString + ";charset=utf8mb4"
            print(connectString)

            _connection = pyodbc.connect(connectString)
            _connection.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
            _connection.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
            _connection.setencoding(encoding='utf-8')
        except Exception as ex:
            print("Unable to create connection:", ex)
            self._disconnect()
            raise DatabaseConnectionError(error=ex)

    def _lastId(self, cursor : Cursor) -> int:
        """Returns the last insertion id"""
        cursor.execute("SELECT @@IDENTITY as id")
        row = cursor.fetchone()
        if row:
            return row.id
        return 0

    def checkCreatePermissions(self) -> bool:
        return False

    def checkManageUsersPermissions(self) -> bool:
        return False

    def checkManageLibrariesPermissions(self) -> bool:
        return False

    def checkCreateLibrariesPermissions(self) -> bool:
        return False
