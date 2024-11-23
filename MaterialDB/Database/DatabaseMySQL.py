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

from MaterialDB.Database.Database import Database

class DatabaseMySQL(Database):

    def __init__(self):
        self._connection = None

    def _connect(self):
        if self._connection is None:
            self._connection = pyodbc.connect('DSN=material;charset=utf8mb4')
            self._connection.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
            self._connection.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
            self._connection.setencoding(encoding='utf-8')

    def _findLibrary(self, name):
        self._connect()
        cursor = self._connection.cursor()

        cursor.execute("SELECT library_id FROM library WHERE library_name = ?", name)
        row = cursor.fetchone()
        if row:
            return row.library_id
        return 0

    def createLibrary(self, name, icon, readOny):
        self._connect()
        cursor = self._connection.cursor()

        cursor.execute("SELECT library_id FROM library WHERE library_name = ?", name)
        row = cursor.fetchone()
        if row:
            if icon is None:
                cursor.execute("INSERT INTO library (library_name, library_read_only) "
                                      "VALUES (?, ?)", name, readOny)
            else:
                cursor.execute("INSERT INTO library (library_name, library_icon, library_read_only) "
                        "VALUES (?, ?, ?)", name, icon, readOny)
            self._connection.commit()

    def _lastId(self):
        """Returns the last insertion id"""
        cursor = self._connection.cursor()
        cursor.execute("SELECT @@IDENTITY as id")
        row = cursor.fetchone()
        if row:
            return row.id
        return 0

    def _createPath(self, libraryIndex, parentIndex, pathIndex, pathList):
        self._connect()
        newId = 0
        cursor = self._connection.cursor()

        if parentIndex == 0:
            # No parent. This is a root folder
            # First see if the folder exists
            cursor.execute("SELECT folder_id FROM folder WHERE folder_name = ? AND library_id = ?"
                " AND parent_id IS NULL", pathList[pathIndex], libraryIndex)
            row = cursor.fetchone()
            if row:
                newId = row.folder_id
            else:
                cursor.execute("INSERT INTO folder (folder_name, library_id) "
                                            "VALUES (?, ?)", pathList[pathIndex], libraryIndex)
                newId = self._lastId()
        else:
            # First see if the folder exists
            cursor.execute("SELECT folder_id FROM folder WHERE folder_name = ? AND library_id = ?"
                " AND parent_id = ?", pathList[pathIndex], libraryIndex, parentIndex)
            row = cursor.fetchone()
            if row:
                newId = row.folder_id
            else:
                cursor.execute("INSERT INTO folder (folder_name, library_id, parent_id) "
                                            "VALUES (?, ?, ?)", pathList[pathIndex], libraryIndex, parentIndex)
                newId = self._lastId()

        self._connection.commit()
        index = parentIndex + 1
        if index >= (len(pathList) - 1):
            return newId
        return self._createPath(libraryIndex, newId, index, pathList)

    def createPath(self, libraryIndex, path):
        newId = 0
        pathList = path.split('/')
        if len(pathList) >= 2:
            return self._createPath(libraryIndex, 0, 0, pathList)
        return newId

    def _foreignKeysIgnore(self, cursor):
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")

    def _foreignKeysRestore(self, cursor):
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")

    def _createInheritance(self, modelUUID, inheritUUID):
        self._connect()
        cursor = self._connection.cursor()
        cursor.execute("SELECT model_inheritance_id FROM model_inheritance WHERE model_id "
                                "= ? AND inherits_id = ?", modelUUID, inheritUUID)
        row = cursor.fetchone()
        if not row:
            # Mass updates may insert models out of sequence creating a foreign key violation
            self._foreignKeysIgnore(cursor)
            cursor.execute("INSERT INTO model_inheritance (model_id, inherits_id) "
                                    "VALUES (?, ?)", modelUUID, inheritUUID)
            self._foreignKeysRestore(cursor)
        self._connection.commit()

    def _createModelPropertyColumn(self, propertyId, property):
        self._connect()
        cursor = self._connection.cursor()
        cursor.execute("SELECT model_property_column_id FROM model_property_column WHERE model_property_id "
            "= ? AND model_property_name = ?", propertyId, property.Name)
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO model_property_column (model_property_id, model_property_name, "
                "model_property_display_name, model_property_type, "
                "model_property_units, model_property_url, "
                "model_property_description) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                propertyId,
                property.Name,
                property.DisplayName,
                property.PropertyType,
                property.Units,
                property.URL,
                property.Description
                )
        self._connection.commit()

    def _createModelProperty(self, modelUUID, property):
        if property.inherited:
            return

        self._connect()
        cursor = self._connection.cursor()
        cursor.execute("SELECT model_property_id FROM model_property WHERE model_id "
                                "= ? AND model_property_name = ?", modelUUID, property.Name)
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO model_property (model_id, model_property_name, "
                                    "model_property_display_name, model_property_type, "
                                    "model_property_units, model_property_url, "
                                    "model_property_description) "
                                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                modelUUID,
                property.Name,
                property.DisplayName,
                property.PropertyType,
                property.Units,
                property.URL,
                property.Description
                )
            propertyId = self._lastId()
            for column in property.Columns:
                self._createModelPropertyColumn(propertyId, column)
        self._connection.commit()

    def _createModel(self, libraryIndex, path, model):
        self._connect()
        cursor = self._connection.cursor()
        pathIndex = self.createPath(libraryIndex, path)
        cursor.execute("SELECT model_id FROM model WHERE model_id = ?", model.UUID)
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO model (model_id, library_id, folder_id, "
                        "model_name, model_type, model_url, model_description, model_doi) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        model.UUID,
                        libraryIndex,
                        (pathIndex == 0 ? None : pathIndex),
                        model.Name,
                        model.Base,
                        model.URL,
                        model.Description,
                        model.DOI,
                        )

            for inherit in model.Inheritance:
                self._createInheritance(model.UUID, inherit)

            for property in model.Properties:
                self._createModelProperty(model.UUID, property)
        self._connection.commit()

    def _createTag(self, materialUUID, tag):
        tagId = 0
        self._connect()
        cursor = self._connection.cursor()
        cursor.execute("SELECT material_tag_id FROM material_tag WHERE material_tag_name = ?", tag)
        row = cursor.fetchone()
        if row:
            tagId = row.material_tag_id
        else:
            cursor.execute("INSERT INTO material_tag (material_tag_name) "
                                    "VALUES (?)", tag)
            tagId = self._lastId()

        cursor.execute("SELECT material_id, material_tag_id FROM material_tag_mapping "
                                "WHERE material_id = ? AND material_tag_id = ?", materialUUID, tagId)
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO material_tag_mapping (material_id, material_tag_id) "
                          "VALUES (?, ?)", materialUUID, tagId)
        self._connection.commit()
