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

import Materials
from MaterialDB.Database.DatabaseMySQLCreate import DatabaseMySQLCreate
from MaterialDB.Database.Exceptions import DatabaseConnectionError
from MaterialDB.Configuration import getPreferencesLocation

class DatabaseMySQLTest(DatabaseMySQLCreate):

    def __init__(self):
        super().__init__()

    def _connect(self, noDatabase=False):
        if self._connection is None:
            self._connectODBCTest()

    def _connectODBCTest(self):
        """ Testing requires a DSN called material-test be defined with all the necessary connection paramters """
        try:
            connectString = 'DSN=material-test;charset=utf8mb4'
            print(connectString)

            self._connection = pyodbc.connect(connectString)
            self._connection.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
            self._connection.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
            self._connection.setencoding(encoding='utf-8')
        except Exception as ex:
            print("Unable to create connection:", ex)
            self._connection = None
            raise DatabaseConnectionError(ex)
