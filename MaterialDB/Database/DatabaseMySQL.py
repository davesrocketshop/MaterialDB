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

from functools import cache

import Materials
from MaterialDB.Database.Database import Database
from MaterialDB.Database.Exceptions import DatabaseLibraryCreationError, \
    DatabaseIconError, DatabaseLibraryNotFound, \
    DatabaseModelCreationError, DatabaseMaterialCreationError, \
    DatabaseModelUpdateError, \
    DatabaseModelExistsError, DatabaseMaterialExistsError, \
    DatabaseModelNotFound, DatabaseMaterialNotFound, \
    DatabaseRenameError, DatabaseDeleteError

class DatabaseMySQL(Database):

    def __init__(self):
        super().__init__()

    def _updateTimestamp(self, cursor, libraryIndex):
        cursor.execute("UPDATE library SET library_modified = NOW() WHERE library_id = ?", libraryIndex)

    def _findLibrary(self, name):
        cursor = self._cursor()

        cursor.execute("SELECT library_id FROM library WHERE library_name = ?", name)
        row = cursor.fetchone()
        if row:
            return row.library_id
        return 0

    def createLibrary(self, name, icon, readOnly):
        try:
            cursor = self._cursor()

            cursor.execute("SELECT library_id FROM library WHERE library_name = ?", name)
            row = cursor.fetchone()
            if not row:
                if icon is None:
                    cursor.execute("INSERT INTO library (library_name, library_read_only) "
                                        "VALUES (?, ?)", name, readOnly)
                else:
                    cursor.execute("INSERT INTO library (library_name, library_icon, library_read_only) "
                            "VALUES (?, ?, ?)", name, icon, readOnly)
                self._connection.commit()
            else:
                raise DatabaseLibraryCreationError("Library already exists")
        except Exception as ex:
            print("Unable to create library:", ex)
            raise DatabaseLibraryCreationError(ex)

    def renameLibrary(self, oldName, newName):
        try:
            cursor = self._cursor()

            cursor.execute("SELECT library_id FROM library WHERE library_name = ?", newName)
            row = cursor.fetchone()
            if row:
                raise DatabaseRenameError(msg="Destination library name already exists")

            cursor.execute("UPDATE library SET library_name = ? "
                                "WHERE library_name = ?", newName, oldName)

            self._connection.commit()
        except Exception as ex:
            print("Unable to create library:", ex)
            raise DatabaseRenameError(ex)

    def changeIcon(self, name, icon):
        try:
            cursor = self._cursor()

            cursor.execute("UPDATE library SET library_icon = ? "
                                "WHERE library_name = ?", icon, name)

            self._connection.commit()
        except Exception as ex:
            print("Unable to change icon:", ex)
            raise DatabaseIconError(ex)

    def removeLibrary(self, library):
        try:
            cursor = self._cursor()

            cursor.execute("DELETE FROM library WHERE library_name = ?", library)

            self._connection.commit()
        except Exception as ex:
            print("Unable to remove library:", ex)
            raise DatabaseDeleteError(ex)

    def libraryModels(self, library):
        try:
            models = []
            cursor = self._cursor()

            cursor.execute("SELECT library_id FROM library WHERE library_name = ?", library)
            row = cursor.fetchone()
            if not row:
                raise DatabaseLibraryNotFound()

            cursor.execute("SELECT m.model_id, m.folder_id, m.model_name"
                           " FROM model m, library l"
                           " WHERE m.library_id = l.library_id AND l.library_name = ?", library)
            rows = cursor.fetchall()
            for row in rows:
                models.append((row.model_id, row.folder_id, row.model_name))

            pathModels = []
            for model in models:
                # Convert the folder_id to a path
                pathModels.append((model[0], self._getPath(model[1]), model[2]))

            return pathModels
        except Exception as ex:
            print("Unable to get library models:", ex)
            raise DatabaseModelNotFound(ex)

    # @cache
    def libraryMaterials(self, library):
        try:
            materials = []
            cursor = self._cursor()

            cursor.execute("SELECT library_id FROM library WHERE library_name = ?", library)
            row = cursor.fetchone()
            if not row:
                raise DatabaseLibraryNotFound()

            cursor.execute("SELECT m.material_id, GetFolder(m.folder_id) as folder_name, m.material_name"
                           " FROM material m, library l"
                           " WHERE m.library_id = l.library_id AND l.library_name = ?", library)
            rows = cursor.fetchall()
            for row in rows:
                materials.append((row.material_id, row.folder_name, row.material_name))

            return materials
        except Exception as ex:
            print("Unable to get library materials:", ex)
            raise DatabaseMaterialNotFound(ex)

    def _createPathRecursive(self, libraryIndex, parentIndex, pathIndex, pathList):
        newId = 0
        cursor = self._cursor()

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
                newId = self._lastId(cursor)
                self._updateTimestamp(cursor, libraryIndex)
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
                newId = self._lastId(cursor)
                self._updateTimestamp(cursor, libraryIndex)

        self._connection.commit()
        index = pathIndex + 1
        if index >= len(pathList):
            return newId
        return self._createPathRecursive(libraryIndex, newId, index, pathList)

    def _createPath(self, libraryIndex, path):
        newId = 0
        pathList = path.split('/')
        if len(pathList) > 0:
            return self._createPathRecursive(libraryIndex, 0, 0, pathList)
        return newId

    def _foreignKeysIgnore(self, cursor):
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")

    def _foreignKeysRestore(self, cursor):
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")

    def _createInheritance(self, modelUUID, inheritUUID, libraryIndex):
        cursor = self._cursor()
        cursor.execute("SELECT model_inheritance_id FROM model_inheritance WHERE model_id "
                                "= ? AND inherits_id = ?", modelUUID, inheritUUID)
        row = cursor.fetchone()
        if not row:
            # Mass updates may insert models out of sequence creating a foreign key violation
            self._foreignKeysIgnore(cursor)
            cursor.execute("INSERT INTO model_inheritance (model_id, inherits_id) "
                                    "VALUES (?, ?)", modelUUID, inheritUUID)
            self._foreignKeysRestore(cursor)
            self._updateTimestamp(cursor, libraryIndex)
        self._connection.commit()

    def _createModelPropertyColumn(self, propertyId, property, libraryIndex):
        cursor = self._cursor()
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
                property.Type,
                property.Units,
                property.URL,
                property.Description
                )
            self._updateTimestamp(cursor, libraryIndex)
        self._connection.commit()

    def _createModelProperty(self, modelUUID, property, libraryIndex):
        if property.Inherited:
            return

        cursor = self._cursor()
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
                property.Type,
                property.Units,
                property.URL,
                property.Description
                )
            propertyId = self._lastId(cursor)
            for column in property.Columns:
                self._createModelPropertyColumn(propertyId, column)
            self._updateTimestamp(cursor, libraryIndex)
        self._connection.commit()

    def _updateModelProperty(self, modelUUID, property, libraryIndex):
        if property.Inherited:
            return

        cursor = self._cursor()
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
                property.Type,
                property.Units,
                property.URL,
                property.Description
                )
            propertyId = self._lastId(cursor)
            for column in property.Columns:
                self._createModelPropertyColumn(propertyId, column)
            self._updateTimestamp(cursor, libraryIndex)
        self._connection.commit()

    def _createModel(self, libraryIndex, path, model):
        cursor = self._cursor()
        pathIndex = self._createPath(libraryIndex, path)
        cursor.execute("SELECT model_id FROM model WHERE model_id = ?", model.UUID)
        row = cursor.fetchone()
        if row:
            raise DatabaseModelExistsError()
        else:
            cursor.execute("INSERT INTO model (model_id, library_id, folder_id, "
                        "model_name, model_type, model_url, model_description, model_doi) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        model.UUID,
                        libraryIndex,
                        (None if pathIndex == 0 else pathIndex),
                        model.Name,
                        model.Type,
                        model.URL,
                        model.Description,
                        model.DOI,
                        )

            for inherit in model.Inherited:
                self._createInheritance(model.UUID, inherit)

            for property in model.Properties.values():
                self._createModelProperty(model.UUID, property)
            self._updateTimestamp(cursor, libraryIndex)
        self._connection.commit()

    def createModel(self, libraryName, path, model):
        try:
            libraryIndex = self._findLibrary(libraryName)
            if libraryIndex > 0:
                self._createModel(libraryIndex, path, model)
        except DatabaseModelExistsError as exists:
            # Rethrow
            raise exists
        except Exception as ex:
            # print("Exception '{}'".format(type(ex).__name__))
            print("Unable to create model:", ex)
            raise DatabaseModelCreationError(ex)

    def _updateModel(self, libraryIndex, path, model):
        cursor = self._cursor()
        pathIndex = self._createPath(libraryIndex, path)
        cursor.execute("SELECT model_id FROM model WHERE model_id = ?", model.UUID)
        row = cursor.fetchone()
        if not row:
            raise DatabaseModelNotFound()
        else:
            cursor.execute("UPDATE model SET "
                           "  folder_id = ?,"
                           "  model_name = ?,"
                           "  model_type = ?,"
                           "  model_url = ?,"
                           "  model_description = ?,"
                           "  model_doi = ?"
                           " WHERE model_id = ?",
                        (None if pathIndex == 0 else pathIndex),
                        model.Name,
                        model.Type,
                        model.URL,
                        model.Description,
                        model.DOI,
                        model.UUID
                        )

            # Do these deletes need to be smarter due to foreing key constraints?
            cursor.execute("DELETE FROM model_inheritance WHERE model_id = ?", model.UUID)
            for inherit in model.Inherited:
                self._createInheritance(model.UUID, inherit)

            cursor.execute("SELECT model_property_id, model_property_name FROM model_property WHERE model_id = ?", model.UUID)
            rows = cursor.fetchall()
            property_ids = []
            for row in rows:
                if not row.model_property_name in model.Properties.keys():
                    # Remove the property
                    property_ids.append(row.model_property_id)
            for property_id in property_ids:
                cursor.execute("DELETE FROM model_property WHERE model_property_id = ?", property_id)

            for property in model.Properties.values():
                self._updateModelProperty(model.UUID, property)
            self._updateTimestamp(cursor, libraryIndex)
        self._connection.commit()

    def updateModel(self, libraryName, path, model):
        try:
            libraryIndex = self._findLibrary(libraryName)
            if libraryIndex > 0:
                self._updateModel(libraryIndex, path, model)
        except DatabaseModelNotFound as exists:
            # Rethrow
            raise exists
        except Exception as ex:
            print("Unable to update model:", ex)
            raise DatabaseModelUpdateError(ex)

    def _createTag(self, materialUUID, tag, libraryIndex):
        tagId = 0
        cursor = self._cursor()
        cursor.execute("SELECT material_tag_id FROM material_tag WHERE material_tag_name = ?", tag)
        row = cursor.fetchone()
        if row:
            tagId = row.material_tag_id
        else:
            cursor.execute("INSERT INTO material_tag (material_tag_name) "
                                    "VALUES (?)", tag)
            tagId = self._lastId(cursor)
            self._updateTimestamp(cursor, libraryIndex)

        cursor.execute("SELECT material_id, material_tag_id FROM material_tag_mapping "
                                "WHERE material_id = ? AND material_tag_id = ?", materialUUID, tagId)
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO material_tag_mapping (material_id, material_tag_id) "
                          "VALUES (?, ?)", materialUUID, tagId)
            self._updateTimestamp(cursor, libraryIndex)
        self._connection.commit()

    def _createMaterialModel(self, materialUUID, modelUUID, libraryIndex):
        cursor = self._cursor()
        cursor.execute("SELECT material_id FROM material_models WHERE material_id = ? AND model_id = ?",
                       materialUUID, modelUUID)
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO material_models (material_id, model_id) "
                                    "VALUES (?, ?)", materialUUID, modelUUID)
            self._updateTimestamp(cursor, libraryIndex)
        self._connection.commit()

    def _createMaterialPropertyValue(self, materialUUID, name, type, libraryIndex):
        cursor = self._cursor()
        cursor.execute("INSERT INTO material_property_value (material_id, material_property_name, material_property_type) "
                    "VALUES (?, ?, ?)",
                    materialUUID, name, type)
        self._updateTimestamp(cursor, libraryIndex)

        return self._lastId(cursor)

    def _createStringValue(self, materialUUID, name, type, value, libraryIndex):
        if value is not None:
            value_id = self._createMaterialPropertyValue(materialUUID, name, type)
            cursor = self._cursor()

            cursor.execute("INSERT INTO material_property_string_value "
                        " (material_property_value_id, material_property_value)"
                        " VALUES (?, ?)",
                        value_id, value)
            self._updateTimestamp(cursor, libraryIndex)
            self._connection.commit()

    def _createLongStringValue(self, materialUUID, name, type, value, libraryIndex):
        if value is not None:
            value_id = self._createMaterialPropertyValue(materialUUID, name, type)
            cursor = self._cursor()

            cursor.execute("INSERT INTO material_property_long_string_value "
                        " (material_property_value_id, material_property_value)"
                        " VALUES (?, ?)",
                        value_id, value)
            self._updateTimestamp(cursor, libraryIndex)
            self._connection.commit()

    def _createListValue(self, materialUUID, name, type, list, libraryIndex):
        if list is not None:
            value_id = self._createMaterialPropertyValue(materialUUID, name, type)
            cursor = self._cursor()

            for entry in list:
                cursor.execute("INSERT INTO material_property_string_value "
                            " (material_property_value_id, material_property_value)"
                            " VALUES (?, ?)",
                            value_id, entry)

            self._updateTimestamp(cursor, libraryIndex)
            self._connection.commit()

    def _createLongListValue(self, materialUUID, name, type, list, libraryIndex):
        if list is not None:
            value_id = self._createMaterialPropertyValue(materialUUID, name, type)
            cursor = self._cursor()

            for entry in list:
                cursor.execute("INSERT INTO material_property_long_string_value "
                            " (material_property_value_id, material_property_value)"
                            " VALUES (?, ?)",
                            value_id, entry)

            self._updateTimestamp(cursor, libraryIndex)
            self._connection.commit()

    def _createArrayValue3D(self, materialUUID, name, propertyType, array, libraryIndex):
        if array is not None:
            value_id = self._createMaterialPropertyValue(materialUUID, name, propertyType)
            cursor = self._cursor()

            rows = 0
            for depth in range(array.Depth):
                rows = max(rows, array.getRows(depth))
            cursor.execute("INSERT INTO material_property_array_description "
                        " (material_property_value_id, material_property_array_rows, "
                        "  material_property_array_columns, material_property_array_depth)"
                        " VALUES (?, ?, ?, ?)",
                        value_id, rows, array.Columns, array.Depth)

            arrayData = array.Array
            for depth, depthValue in enumerate(arrayData):
                cursor.execute("INSERT INTO material_property_string_value "
                        " (material_property_value_id, material_property_value)"
                        " VALUES (?, ?)",
                        value_id, array.getDepthValue(depth).UserString)
            for depth, depthValue in enumerate(arrayData):
                for row, rowValue in enumerate(depthValue):
                    for column, columnValue in enumerate(rowValue):
                        value = columnValue.UserString
                        cursor.execute("INSERT INTO material_property_array_value "
                                    " (material_property_value_id, material_property_value_row, "
                                    "  material_property_value_column, material_property_value_depth, "
                                    "  material_property_value_depth_rows, material_property_value)"
                                    " VALUES (?, ?, ?, ?, ?, ?)",
                                    value_id, row, column, depth, array.getRows(depth), value)

            self._updateTimestamp(cursor, libraryIndex)
            self._connection.commit()

    def _createArrayValue2D(self, materialUUID, name, propertyType, array, libraryIndex):
        if array is not None:
            value_id = self._createMaterialPropertyValue(materialUUID, name, propertyType)
            cursor = self._cursor()

            cursor.execute("INSERT INTO material_property_array_description "
                        " (material_property_value_id, material_property_array_rows, "
                        "  material_property_array_columns)"
                        " VALUES (?, ?, ?)",
                        value_id, array.Rows, array.Columns)
            arrayData = array.Array
            for row, rowValue in enumerate(arrayData):
                for column, columnValue in enumerate(rowValue):
                    if hasattr(columnValue, "UserString"):
                        value = columnValue.UserString
                    else:
                        value = columnValue
                    cursor.execute("INSERT INTO material_property_array_value "
                                " (material_property_value_id, material_property_value_row, "
                                "  material_property_value_column, material_property_value)"
                                " VALUES (?, ?, ?, ?)",
                                value_id, row, column, value)

            self._updateTimestamp(cursor, libraryIndex)
            self._connection.commit()

    def _createMaterialProperty(self, materialUUID, material, property):
        if property.Type == "2DArray" or \
           property.Type == "3DArray":
            if material.hasPhysicalProperty(property.Name):
                array = material.getPhysicalValue(property.Name)
            else:
                array = material.getAppearanceValue(property.Name)
            if array.Dimensions == 2:
                self._createArrayValue2D(materialUUID, property.Name, property.Type, array)
            else:
                self._createArrayValue3D(materialUUID, property.Name, property.Type, array)
        elif property.Type == "List" or \
           property.Type == "FileList":
            self._createListValue(materialUUID, property.Name, property.Type, property.Value)
        elif property.Type == "ImageList":
            self._createLongListValue(materialUUID, property.Name, property.Type, property.Value)
        elif property.Type == "Quantity":
            if property.Empty:
                return
            self._createStringValue(materialUUID, property.Name, property.Type, property.Value.UserString)
        elif property.Type == "SVG" or \
            property.Type == "Image":
            self._createLongStringValue(materialUUID, property.Name, property.Type, property.Value)
        else:
            self._createStringValue(materialUUID, property.Name, property.Type, property.Value)

    def _createMaterial(self, libraryIndex, path, material):
        pathIndex = self._createPath(libraryIndex, path)

        cursor = self._cursor()
        cursor.execute("SELECT material_id FROM material WHERE material_id = ?",
                       material.UUID)
        row = cursor.fetchone()
        if row:
            raise DatabaseMaterialExistsError()
        else:
            # Mass updates may insert models out of sequence creating a foreign key
            # violation
            self._foreignKeysIgnore(cursor)

            cursor.execute("INSERT INTO material (material_id, library_id, folder_id, "
                            "material_name, material_author, material_license, "
                            "material_parent_uuid, material_description, material_url, "
                            "material_reference) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            material.UUID,
                            libraryIndex,
                            (None if pathIndex == 0 else pathIndex),
                            material.Name,
                            material.Author,
                            material.License,
                            material.Parent,
                            material.Description,
                            material.URL,
                            material.Reference,
                            )

            for tag in material.Tags:
                self._createTag(material.UUID, tag)

            # print("{} Physical models".format(len(material.PhysicalModels)))
            for model in material.PhysicalModels:
                self._createMaterialModel(material.UUID, model)

            # print("{} Appearance models".format(len(material.AppearanceModels)))
            for model in material.AppearanceModels:
                self._createMaterialModel(material.UUID, model)

            # print("{} Properties".format(len(material.PropertyObjects)))
            for property in material.PropertyObjects.values():
                self._createMaterialProperty(material.UUID, material, property)
            self._updateTimestamp(cursor, libraryIndex)

        self._connection.commit()

    def createMaterial(self, libraryName, path, material):
        try:
            libraryIndex = self._findLibrary(libraryName)
            if libraryIndex > 0:
                self._createMaterial(libraryIndex, path, material)
        except DatabaseMaterialExistsError as exists:
            # Rethrow
            raise exists
        except Exception as ex:
            print("Unable to create material:", ex)
            raise DatabaseMaterialCreationError(ex)

    def getLibraries(self):
        libraries = []
        cursor = self._cursor()
        cursor.execute("SELECT library_name, library_icon, library_read_only, library_modified FROM "
                                    "library")
        rows = cursor.fetchall()
        for row in rows:
            libraries.append((row.library_name, row.library_icon.decode('UTF-8'), row.library_read_only,
                              row.library_modified))

        return libraries

    def getModelLibraries(self):
        libraries = []
        cursor = self._cursor()
        cursor.execute("SELECT DISTINCT l.library_name, l.library_icon, l.library_read_only, l.library_modified"
                       " FROM library l, model m WHERE l.library_id = m.library_id")
        rows = cursor.fetchall()
        for row in rows:
            libraries.append((row.library_name, row.library_icon.decode('UTF-8'), row.library_read_only,
                              row.library_modified))

        return libraries

    def getMaterialLibraries(self):
        libraries = []
        cursor = self._cursor()
        cursor.execute("SELECT DISTINCT l.library_name, l.library_icon, l.library_read_only, l.library_modified"
                       " FROM library l, material m WHERE l.library_id = m.library_id")
        rows = cursor.fetchall()
        for row in rows:
            libraries.append((row.library_name, row.library_icon.decode('UTF-8'), row.library_read_only,
                              row.library_modified))

        return libraries

    def _getLibrary(self, libraryId):
        cursor = self._cursor()
        cursor.execute("SELECT library_name, library_icon, library_read_only FROM "
                                    "library WHERE library_id = ?",
                       libraryId)
        row = cursor.fetchone()
        if row:
            return (row.library_name, row.library_icon.decode('UTF-8'), row.library_read_only)
        return None

    def _getPath(self, folderId):
        path = ""
        cursor = self._cursor()
        cursor.execute("""WITH RECURSIVE subordinate AS (
                        SELECT
                            folder_id,
                            folder_name,
                            parent_id
                        FROM folder
                        WHERE folder_id = ?

                        UNION ALL

                        SELECT
                            e.folder_id,
                            e.folder_name,
                            e.parent_id
                        FROM folder e
                        JOIN subordinate s
                        ON e.folder_id = s.parent_id
                        )
                        SELECT
                            folder_name
                        FROM subordinate
                        ORDER BY folder_id ASC;""",
                       folderId)
        rows = cursor.fetchall()
        first = True
        for row in rows:
            if first:
                path = row.folder_name
                first = False
            else:
                path += "/" + row.folder_name
        return path

    def _getInherits(self, uuid):
        inherits = []
        cursor = self._cursor()
        cursor.execute("SELECT inherits_id FROM model_inheritance "
                                    "WHERE model_id = ?",
                       uuid)
        rows = cursor.fetchall()
        for row in rows:
            inherits.append(row.inherits_id)

        return inherits

    def _getModelColumns(self, uuid, propertyName):
        columns = []
        cursor = self._cursor()
        cursor.execute("SELECT model_property_id FROM model_property "
                                    "WHERE model_id = ? AND model_property_name = ?",
                       uuid, propertyName)
        propertyId = 0
        row = cursor.fetchone()
        if row:
            propertyId = row.model_property_id
            cursor.execute("SELECT model_property_name, "
                                    "model_property_display_name, model_property_type, "
                                    "model_property_units, model_property_url, "
                                    "model_property_description FROM model_property_column "
                                    "WHERE model_property_id = ?",
                        propertyId)

            rows = cursor.fetchall()
            for row in rows:
                prop = Materials.ModelProperty()
                prop.Name = row.model_property_name
                prop.DisplayName = row.model_property_display_name
                prop.Type = row.model_property_type
                prop.Units = row.model_property_units
                prop.URL = row.model_property_url
                prop.Description = row.model_property_description

                columns.append(prop)

        return columns

    def _getModelProperties(self, uuid):
        properties = []
        cursor = self._cursor()
        cursor.execute("SELECT model_property_name, "
                                    "model_property_display_name, model_property_type, "
                                    "model_property_units, model_property_url, "
                                    "model_property_description FROM model_property "
                                    "WHERE model_id = ?",
                       uuid)

        rows = cursor.fetchall()
        for row in rows:
            prop = Materials.ModelProperty()
            prop.Name = row.model_property_name
            prop.DisplayName = row.model_property_display_name
            prop.Type = row.model_property_type
            prop.Units = row.model_property_units
            prop.URL = row.model_property_url
            prop.Description = row.model_property_description

            properties.append(prop)

        # This has to happen after the properties are retrieved to prevent nested queries
        for property in properties:
            columns = self._getModelColumns(uuid, property.Name)
            for column in columns:
                property.addColumn(column)

        return properties

    def getModel(self, uuid):
        try:
            cursor = self._cursor()
            cursor.execute("SELECT library_id, folder_id, model_type, "
                "model_name, model_url, model_description, model_doi FROM model WHERE model_id = ?",
                        uuid)

            row = cursor.fetchone()
            if not row:
                raise DatabaseModelNotFound()

            model = Materials.Model()
            # model.UUID = uuid
            model.Type = row.model_type
            model.Name = row.model_name
            model.URL = row.model_url
            model.Description = row.model_description
            model.DOI = row.model_doi

            # model.Library = self._getLibrary(row.library_id)
            library = self._getLibrary(row.library_id)

            path = self._getPath(row.folder_id) #+ "/" + row.model_name
            model.Directory = path

            inherits = self._getInherits(uuid)
            for inherit in inherits:
                model.addInheritance(inherit)

            properties = self._getModelProperties(uuid)
            for property in properties:
                model.addProperty(property)

            return (uuid, library, model)

        except DatabaseModelNotFound as notFound:
            # Rethrow
            raise notFound
        except Exception as ex:
            print("Unable to get model:", ex)
            raise DatabaseModelNotFound(ex)

    def _getTags(self, uuid):
        tags = []
        cursor = self._cursor()
        cursor.execute("SELECT t.material_tag_name FROM material_tag t, material_tag_mapping m "
                          "WHERE m.material_id = ? AND m.material_tag_id = t.material_tag_id",
                       uuid)

        rows = cursor.fetchall()
        for row in rows:
            tags.append(row.material_tag_name)

        return tags

    def _getMaterialModels(self, uuid, isPhysical):
        models = []
        cursor = self._cursor()
        cursor.execute("SELECT m1.model_id FROM material_models m1, model m2 "
            "WHERE m1.material_id = ? AND m1.model_id = m2.model_id AND m2.model_type = ?",
                       uuid,
                       ("Physical" if isPhysical else "Appearance"))

        rows = cursor.fetchall()
        for row in rows:
            models.append(row.model_id)

        return models

    def _getMaterialPropertyStringValue(self, materialPropertyValueId):
        cursor = self._cursor()
        cursor.execute("SELECT material_property_value "
                        "FROM material_property_string_value "
                        "WHERE material_property_value_id = ?",
                       materialPropertyValueId)
        row = cursor.fetchone()
        if not row:
            return None

        return row.material_property_value

    def _getMaterialPropertyLongStringValue(self, materialPropertyValueId):
        cursor = self._cursor()
        cursor.execute("SELECT material_property_value "
                        "FROM material_property_long_string_value "
                        "WHERE material_property_value_id = ?",
                       materialPropertyValueId)
        row = cursor.fetchone()
        if not row:
            return None

        return row.material_property_value

    def _getMaterialPropertyListValue(self, materialPropertyValueId):
        cursor = self._cursor()
        cursor.execute("SELECT material_property_value "
                        "FROM material_property_string_value "
                        "WHERE material_property_value_id = ? "
                        "ORDER BY material_property_value_id ASC",
                       materialPropertyValueId)
        rows = cursor.fetchall()
        list = []
        for row in rows:
            list.append(row.material_property_value)

        return list

    def _getMaterialPropertyLongListValue(self, materialPropertyValueId):
        cursor = self._cursor()
        cursor.execute("SELECT material_property_value "
                        "FROM material_property_long_string_value "
                        "WHERE material_property_value_id = ? "
                        "ORDER BY material_property_value_id ASC",
                       materialPropertyValueId)
        rows = cursor.fetchall()
        list = []
        for row in rows:
            list.append(row.material_property_value)

        return list

    def _getMaterialPropertyArray2D(self, materialPropertyValueId):
        cursor = self._cursor()
        array=Materials.Array2D()

        cursor.execute("SELECT material_property_array_rows, material_property_array_columns "
                        "FROM material_property_array_description "
                        "WHERE material_property_value_id = ?",
                       materialPropertyValueId)
        row = cursor.fetchone()
        if not row:
            return None
        # Columns must be set first so rows can be created
        # print("rows {}, columns {}".format(row.material_property_array_rows, row.material_property_array_columns))
        array.Columns = row.material_property_array_columns
        array.Rows = row.material_property_array_rows

        cursor.execute("SELECT material_property_value_row, material_property_value_column,"
                        " material_property_value_depth, material_property_value "
                        "FROM material_property_array_value "
                        "WHERE material_property_value_id = ? "
                        "ORDER BY material_property_value_id ASC",
                       materialPropertyValueId)
        rows = cursor.fetchall()
        for row in rows:
            array.setValue(row.material_property_value_row,
                            row.material_property_value_column,
                            row.material_property_value)

        return array

    def _getMaterialPropertyArray3D(self, materialPropertyValueId):
        cursor = self._cursor()
        array=Materials.Array3D()

        cursor.execute("SELECT material_property_array_depth, material_property_array_columns "
                        "FROM material_property_array_description "
                        "WHERE material_property_value_id = ?",
                       materialPropertyValueId)
        row = cursor.fetchone()
        if not row:
            return None
        # Columns must be set first so depth can be created
        array.Columns = row.material_property_array_columns
        array.Depth = row.material_property_array_depth

        cursor.execute("SELECT material_property_value "
                        "FROM material_property_string_value "
                        "WHERE material_property_value_id = ?",
                       materialPropertyValueId)
        rows = cursor.fetchall()
        for depth, row in enumerate(rows):
            array.setDepthValue(depth, row.material_property_value)

        cursor.execute("SELECT material_property_value_row, material_property_value_column,"
                        " material_property_value_depth, material_property_value_depth_rows,"
                        " material_property_value "
                        "FROM material_property_array_value "
                        "WHERE material_property_value_id = ? "
                        "ORDER BY material_property_value_id ASC",
                       materialPropertyValueId)
        rows = cursor.fetchall()

        for row in rows:
            array.setRows(row.material_property_value_depth, row.material_property_value_depth_rows)
            array.setValue(row.material_property_value_depth,
                            row.material_property_value_row,
                            row.material_property_value_column,
                            row.material_property_value)

        return array

    def _getMaterialPropertyValue(self, materialPropertyValueId, type):
        if type == "2DArray":
            return self._getMaterialPropertyArray2D(materialPropertyValueId)
        elif type == "3DArray":
            return self._getMaterialPropertyArray3D(materialPropertyValueId)
        elif type == "SVG" or \
           type == "Image":
            return self._getMaterialPropertyLongStringValue(materialPropertyValueId)
        elif type == "List" or \
           type == "FileList":
            return self._getMaterialPropertyListValue(materialPropertyValueId)
        elif type == "ImageList":
            return self._getMaterialPropertyLongListValue(materialPropertyValueId)

        return self._getMaterialPropertyStringValue(materialPropertyValueId)

    def _getMaterialProperties(self, uuid):
        cursor = self._cursor()
        cursor.execute("SELECT material_property_value_id, material_property_name, material_property_type "
                        "FROM material_property_value "
                        "WHERE material_id = ?",
                       uuid)

        propertyKeys = {}
        rows = cursor.fetchall()
        for row in rows:
            propertyKeys[row.material_property_name] = (row.material_property_value_id, row.material_property_type)

        properties = {}
        for key, value in propertyKeys.items():
            properties[key] = self._getMaterialPropertyValue(value[0], value[1])

        return properties

    def getMaterial(self, uuid):
        try:
            cursor = self._cursor()
            cursor.execute("SELECT library_id, folder_id, material_name, "
                                "material_author, material_license, material_parent_uuid, "
                                "material_description, material_url, material_reference FROM "
                                "material WHERE material_id = ?",
                        uuid)

            row = cursor.fetchone()
            if not row:
                raise DatabaseMaterialNotFound()
            material = Materials.Material()
            # material.UUID = uuid
            material.Name = row.material_name
            material.Author = row.material_author
            material.License = row.material_license
            material.Parent = row.material_parent_uuid
            material.Description = row.material_description
            material.URL = row.material_url
            material.Reference = row.material_reference

            library = self._getLibrary(row.library_id)

            path = self._getPath(row.folder_id) #+ "/" + row.material_name
            material.Directory = path

            tags = self._getTags(uuid)
            for tag in tags:
                material.addTag(tag)

            for model in self._getMaterialModels(uuid, True):
                material.addPhysicalModel(model)

            for model in self._getMaterialModels(uuid, False):
                material.addAppearanceModel(model)

            # self.addModelProperties(material)

            # The actual properties are set by the model. We just need to load the values
            properties = self._getMaterialProperties(uuid)
            for name, value in properties.items():
                material.setValue(name, value)

            return (uuid, library, material)

        except DatabaseMaterialNotFound as notFound:
            # Rethrow
            raise notFound
        except Exception as ex:
            print("Unable to get material:", ex)
            raise DatabaseMaterialNotFound(ex)

    # def addModelProperties(self, material):
    #     print("addModelProperties()")
    #     print("{} Physical models".format(len(material.PhysicalModels)))
    #     print("{} Appearance models".format(len(material.AppearanceModels)))
    #     print("{} Properties".format(len(material.PropertyObjects)))
