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

import sqlite3
import Materials
import os

from MaterialDB.Database import Database
from MaterialDB.util.UIPath import getUIPath

class DatabaseSQLite(Database):
    """SQLite specific database interface"""

    def __init__(self, path=None):
        if path is None:
            self._database = os.path.join(getUIPath(), 'Resources', 'db', 'Materials.db')
        else:
            self._database = path
        print("database {}".format(self._database))
        self._createTables()

    def databasePath(self):
        return self._database

    def _createTables(self):
        sql_statements = [
            """CREATE TABLE IF NOT EXISTS library
                    (library_id INTEGER PRIMARY KEY ASC,
                    library_name UNIQUE,
                    library_icon,
                    library_read_only
                );""",
            """CREATE TABLE IF NOT EXISTS model
                    (model_id PRIMARY KEY ASC UNIQUE,
                    library_id INTEGER,
                    model_path,
                    model_type,
                    model_name,
                    model_url,
                    model_description,
                    model_doi
                );""",
        ]
        with sqlite3.connect(self._database) as connection:
            try:
                cursor = connection.cursor()

                for statement in sql_statements:
                    cursor.execute(statement)

                connection.commit()
            except sqlite3.OperationalError as e:
                print("Unable to create tables: ", e)

    def _clearTables(self):
        with sqlite3.connect(self._database) as connection:
            cursor = connection.cursor()

            # Retrieve the list of all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            # Drop each table
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table[0]};")

            # Commit changes and close the connection
            connection.commit()

    def libraries(self) -> dict:
        """Returns a list of libraries managed by this interface

        The list contains a series of tuples describing all libraries managed by
        this module. Each tuple containes the library name, and a boolean to indicate
        if it is a read only library."""
        libs = {}
        with sqlite3.connect(self._database) as connection:
            cursor = connection.cursor()

            cursor.execute("""SELECT library_name, library_icon, library_read_only
                            FROM library""")

            rows = cursor.fetchall()
            for row in rows:
                libs[row[0]] = (row[1], row[2])
        return libs

    def _getLibraryId(self, name: str) -> int:
        """Returns the library id for the named library

        Find the id for the given library."""
        library_id = 0
        with sqlite3.connect(self._database) as connection:
            cursor = connection.cursor()

            cursor.execute("""SELECT library_id
                            FROM library
                            WHERE library_name = ?""", (name,))

            rows = cursor.fetchall()
            if len(rows) == 1:
                library_id = rows[0][0]
        return library_id

    def createLibrary(self, name: str, icon: str) -> None:
        """Create a new library

        Create a new library with the given name"""
        with sqlite3.connect(self._database) as connection:
            try:
                cursor = connection.cursor()

                cursor.execute("INSERT INTO library (library_name, library_icon, library_read_only) VALUES (?,?,?)",
                                    (name, icon, False))

                connection.commit()
            except sqlite3.IntegrityError as e:
                print("Unable to create library: ", e)

    def renameLibrary(self, oldName: str, newName: str) -> None:
        """Rename an existing library

        Change the name of an existing library"""
        with sqlite3.connect(self._database) as connection:
            cursor = connection.cursor()

            cursor.execute("UPDATE library SET library_name=? WHERE library_name = ?", (newName, oldName))

            connection.commit()

    def removeLibrary(self, name: str) -> None:
        """Delete a library and its contents

        Deletes the library and any models or materials it contains"""
        with sqlite3.connect(self._database) as connection:
            cursor = connection.cursor()

            cursor.execute("DELETE FROM library WHERE library_name = ?", (name, ))

            connection.commit()

    def libraryModels(self, library: str) -> list:
        """Returns a list of models managed by this interface

        Each list entry is a tuple containing the UUID, path, and name of the model"""
        models = {}
        with sqlite3.connect(self._database) as connection:
            cursor = connection.cursor()

            cursor.execute("""SELECT model_name, model_id, model_path
                            FROM model m, library l
                            WHERE m.library_id = l.library_id AND l.library_name = ?""",
                            (library, ))

            rows = cursor.fetchall()
            for row in rows:
                models[row[0]] = (row[1], row[2])
        return models

    #
    # Model functions
    #
    def getModel(self, uuid: str) -> Materials.Model:
        """Find a model in the database

        Finds the model, constructs the properties, and returns the model to the user"""
        model = Materials.Model(uuid)
        with sqlite3.connect(self._database) as connection:
            cursor = connection.cursor()

            cursor.execute("""SELECT model_path,
                                model_type,
                                model_name,
                                model_url,
                                model_description,
                                model_doi
                           FROM model WHERE model_id = ?""", (uuid, ))

            rows = cursor.fetchall()
            if len(rows) == 0:
                pass # Not found
            elif len(rows) > 1:
                pass # Too many rows found
            else:
                row = rows[0]
                model.Directory = row[0]
                model.TypeId = row[1]
                model.Name = row[2]
                model.URL = row[3]
                model.Description = row[4]
                model.DOI = row[5]

            connection.commit()

        return model

    def addModel(self, library: str, path: str, model: Materials.Model) -> None:
        libraryId = self._getLibraryId(library)

        with sqlite3.connect(self._database) as connection:
            try:
                cursor = connection.cursor()
                cursor.execute("""INSERT INTO model
                                    model_id,
                                    library_id,
                                    model_path,
                                    model_type,
                                    model_name,
                                    model_url,
                                    model_description,
                                    model_doi
                               VALUES (?,?,?,?,?,?,?,?)""",
                            (model.UUID, libraryId, path, model.TypeId, model.Name, model.URL, model.Description, model.DOI))

                connection.commit()
            except sqlite3.IntegrityError as e:
                print("Unable to add model: ", e)

    def setModelPath(self, library: str, path: str, model: Materials.Model) -> None:
        pass

    def renameModel(self, library: str, name: str, model: Materials.Model) -> None:
        pass

    def moveModel(self, library: str, path: str, model: Materials.Model) -> None:
        """Move a model across libraries

        Move the model to the desired path in a different library. This should also
        remove the model from the old library if that library is managed by this
        interface"""
        pass

    def removeModel(self, model: Materials.Model) -> None:
        pass
