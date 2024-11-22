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
import os
import sqlite3

import Materials

from MaterialDB.DatabaseSQLite import DatabaseSQLite
from MaterialDB.util.UIPath import getUIPath

class SQLiteTests(unittest.TestCase):

    def setUp(self):
        testPath = os.path.join(getUIPath(), '..', 'Resources', 'db', 'Materials-test.db')
        self._db = DatabaseSQLite(testPath)

        # This needs to be done due to connection pooling. Trying to delete the file
        # results in Windows locks
        self._db._clearTables()
        self._db._createTables()

    def tearDown(self):
        pass

    def testLibraryCreation(self):
        libraries = self._db.libraries()
        self.assertEqual(len(libraries), 0)
        self._db.createLibrary("Test1", "icon1")
        self._db.createLibrary("Test2", "icon2")
        libraries = self._db.libraries()
        self.assertEqual(len(libraries), 2)
        self.assertIn("Test1", libraries)
        self.assertIn("Test2", libraries)

        # Test duplicate library name
        self._db.createLibrary("Test1", "icon1")
        libraries = self._db.libraries()
        self.assertEqual(len(libraries), 2)
        self.assertIn("Test1", libraries)
        self.assertIn("Test2", libraries)

        # Test no icon
        self._db.createLibrary("Test3", None)
        libraries = self._db.libraries()
        self.assertEqual(len(libraries), 3)
        self.assertIn("Test1", libraries)
        self.assertIn("Test2", libraries)
        self.assertIn("Test3", libraries)

        # Test library removal
        self._db.removeLibrary("Test2")
        libraries = self._db.libraries()
        self.assertEqual(len(libraries), 2)
        self.assertIn("Test1", libraries)
        self.assertIn("Test3", libraries)

        # Test library rename
        self._db.renameLibrary("Test3", "Phantasm")
        libraries = self._db.libraries()
        self.assertEqual(len(libraries), 2)
        self.assertIn("Test1", libraries)
        self.assertIn("Phantasm", libraries)
        self._db.removeLibrary("Phantasm")
        libraries = self._db.libraries()
        self.assertEqual(len(libraries), 1)
        self.assertIn("Test1", libraries)

    def testModelCreation(self):
        libraries = self._db.libraries()
        self.assertEqual(len(libraries), 0)
        self._db.createLibrary("Test1", "icon1")
        self._db.createLibrary("Test2", "icon1")
        libraries = self._db.libraries()
        self.assertEqual(len(libraries), 2)
        self.assertIn("Test1", libraries)
        self.assertIn("Test2", libraries)

        model = Materials.Model()
        model.Name = "Test1 Model"
        self._db.addModel("Test1", "", model)
        models = self._db.libraryModels("Test1")
        self.assertEqual(len(models), 1)
        self.assertIn("Test1 Model", models)
        models = self._db.libraryModels("Test2")
        self.assertEqual(len(models), 0)
