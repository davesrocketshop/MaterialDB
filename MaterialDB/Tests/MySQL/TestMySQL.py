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

import unittest

from MaterialDB.Database.DatabaseMySQLTest import DatabaseMySQLTest
from MaterialDB.util.UIPath import getUIPath

class MySQLTests(unittest.TestCase):

    def setUp(self):
        self._db = DatabaseMySQLTest()
        self._db.createTables()
        self._db.createFunctions()

    def tearDown(self):
        self._db.dropTables()
        self._db.dropFunctions()
        pass

    def testConnection(self):
        # self.assertIsNone(self._db._connection)
        self._db._connect()
        self.assertIsNotNone(self._db._connection)

    def testGetIcon(self):
        icon = self._db._getIcon(bytearray(), "")
        self.assertIsNone(icon)
        icon = self._db._getIcon(bytearray(), None)
        self.assertIsNone(icon)
        icon = self._db._getIcon(None, "")
        self.assertIsNone(icon)
        icon = self._db._getIcon(None, None)
        self.assertIsNone(icon)

    def getFolderFunction(self, folderId):
        cursor = self._db._cursor()

        cursor.execute("SELECT GetFolder(?) as folder_name", folderId)
        row = cursor.fetchone()
        if row:
            return row.folder_name

        return None

    def testPaths(self):
        self._db.createLibrary("TestPaths", None, "", False)
        libraryId = self._db._findLibrary("TestPaths")
        self.assertNotEqual(libraryId, 0)

        # Create some paths
        id1 = self._db._createPath(libraryId, "System/Resource/Tests")
        id2 = self._db._createPath(libraryId, "System/Resource/Tests/Test1")
        id3 = self._db._createPath(libraryId, "System/Resource/Tests/Test2")
        id4 = self._db._createPath(libraryId, "System/Resource/Tests/Test3")
        id5 = self._db._createPath(libraryId, "/User")
        id6 = self._db._createPath(libraryId, "User/Henry")
        id7 = self._db._createPath(libraryId, "/")
        id8 = self._db._createPath(libraryId, "")
        self.assertNotEqual(id1, 0)
        self.assertNotEqual(id2, 0)
        self.assertNotEqual(id3, 0)
        self.assertNotEqual(id4, 0)
        self.assertNotEqual(id5, 0)
        self.assertNotEqual(id6, 0)
        self.assertNotEqual(id7, 0)
        self.assertNotEqual(id8, 0)

        # Check the paths
        self.assertEqual(self._db._getPath(id1), "System/Resource/Tests")
        self.assertEqual(self._db._getPath(id2), "System/Resource/Tests/Test1")
        self.assertEqual(self._db._getPath(id3), "System/Resource/Tests/Test2")
        self.assertEqual(self._db._getPath(id4), "System/Resource/Tests/Test3")
        self.assertEqual(self._db._getPath(id5), "User")
        self.assertEqual(self._db._getPath(id6), "User/Henry")
        self.assertEqual(self._db._getPath(id7), "")
        self.assertEqual(self._db._getPath(id8), "")

        self.assertEqual(self.getFolderFunction(id1), "System/Resource/Tests")
        self.assertEqual(self.getFolderFunction(id2), "System/Resource/Tests/Test1")
        self.assertEqual(self.getFolderFunction(id3), "System/Resource/Tests/Test2")
        self.assertEqual(self.getFolderFunction(id4), "System/Resource/Tests/Test3")
        self.assertEqual(self.getFolderFunction(id5), "User")
        self.assertEqual(self.getFolderFunction(id6), "User/Henry")
        self.assertEqual(self.getFolderFunction(id7), "")
        self.assertEqual(self.getFolderFunction(id8), "")

        folders = self._db.libraryFolders("TestPaths")
        self.assertEqual(len(folders), 9)
        # self.assertEqual(folders[0], "System")
        self.assertTrue("/System" in folders)
        self.assertTrue("/System/Resource" in folders)
        self.assertTrue("/System/Resource/Tests" in folders)
        self.assertTrue("/System/Resource/Tests/Test1" in folders)
        self.assertTrue("/System/Resource/Tests/Test2" in folders)
        self.assertTrue("/System/Resource/Tests/Test3" in folders)
        self.assertTrue("/User" in folders)
        self.assertTrue("/User/Henry" in folders)
        self.assertTrue("/" in folders)
