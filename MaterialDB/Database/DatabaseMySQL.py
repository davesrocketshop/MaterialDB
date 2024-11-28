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
from MaterialDB.Database.Database import Database

class DatabaseMySQL(Database):

    def __init__(self):
        super().__init__()

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
        except Exception as ex:
            print("Unable to create library:", ex)

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

        self._connection.commit()
        index = parentIndex + 1
        if index >= (len(pathList) - 1):
            return newId
        return self._createPathRecursive(libraryIndex, newId, index, pathList)

    def _createPath(self, libraryIndex, path):
        newId = 0
        pathList = path.split('/')
        if len(pathList) >= 2:
            return self._createPathRecursive(libraryIndex, 0, 0, pathList)
        return newId

    def _foreignKeysIgnore(self, cursor):
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")

    def _foreignKeysRestore(self, cursor):
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")

    def _createInheritance(self, modelUUID, inheritUUID):
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
        self._connection.commit()

    def _createModelPropertyColumn(self, propertyId, property):
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
                property.PropertyType,
                property.Units,
                property.URL,
                property.Description
                )
        self._connection.commit()

    def _createModelProperty(self, modelUUID, property):
        if property.inherited:
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
                property.PropertyType,
                property.Units,
                property.URL,
                property.Description
                )
            propertyId = self._lastId(cursor)
            for column in property.Columns:
                self._createModelPropertyColumn(propertyId, column)
        self._connection.commit()

    def _createModel(self, libraryIndex, path, model):
        cursor = self._cursor()
        pathIndex = self._createPath(libraryIndex, path)
        cursor.execute("SELECT model_id FROM model WHERE model_id = ?", model.UUID)
        row = cursor.fetchone()
        if not row:
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

            for property in model.Properties:
                self._createModelProperty(model.UUID, property)
        self._connection.commit()

    def createModel(self, libraryName, path, model):
        try:
            libraryIndex = self._findLibrary(libraryName)
            if libraryIndex > 0:
                self._createModel(libraryIndex, path, model)
        except Exception as ex:
            print("Unable to create model:", ex)

    def _createTag(self, materialUUID, tag):
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

        cursor.execute("SELECT material_id, material_tag_id FROM material_tag_mapping "
                                "WHERE material_id = ? AND material_tag_id = ?", materialUUID, tagId)
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO material_tag_mapping (material_id, material_tag_id) "
                          "VALUES (?, ?)", materialUUID, tagId)
        self._connection.commit()

    def _createMaterialModel(self, materialUUID, modelUUID):
        cursor = self._cursor()
        cursor.execute("SELECT material_id FROM material_models WHERE material_id = ? AND model_id = ?",
                       materialUUID, modelUUID)
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO material_models (material_id, model_id) "
                                    "VALUES (?, ?)", materialUUID, modelUUID)
        self._connection.commit()

    def _createStringValue(self, materialUUID, name, value):
        cursor = self._cursor()
        cursor.execute("INSERT INTO material_property_value (material_id, material_property_name, "
                      "material_property_value) "
                      "VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE material_property_value = ?",
                       materialUUID, name, value, value)
        self._connection.commit()

    # def _createMaterialProperty(self, materialUUID, property):
    #     if property.Type == "List" or \
    #        property.Type == "Array2D" or \
    #        property.Type == "Array3D" or \
    #        property.Type == "Image" or \
    #        property.Type == "File" or \
    #        property.Type == "FileList" or \
    #        property.Type == "ImageList" or \
    #        property.Type == "SVG":
    #         pass
    #     else:
    #         self._createStringValue(materialUUID, property.Name, property.Value)

    def _createMaterialProperty(self, materialUUID, name, value):
        self._createStringValue(materialUUID, name, value)

    def _createMaterial(self, libraryIndex, path, material):
        pathIndex = self._createPath(libraryIndex, path)

        cursor = self._cursor()
        cursor.execute("SELECT material_id FROM material WHERE material_id = ?",
                       material.UUID)
        row = cursor.fetchone()
        if not row:
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

            for model in material.PhysicalModels:
                self._createMaterialModel(material.UUID, model)

            for model in material.AppearanceModels:
                self._createMaterialModel(material.UUID, model)

            for name, value in material.PhysicalProperties.items():
                self._createMaterialProperty(material.UUID, name, value)

            for name, value in material.AppearanceProperties.items():
                self._createMaterialProperty(material.UUID, name, value)

        self._connection.commit()

    def createMaterial(self, libraryName, path, material):
        try:
            libraryIndex = self._findLibrary(libraryName)
            if libraryIndex > 0:
                self._createMaterial(libraryIndex, path, material)
        except Exception as ex:
            print("Unable to create material:", ex)

    def getLibraries(self):
        libraries = []
        cursor = self._cursor()
        cursor.execute("SELECT library_name, library_icon, library_read_only FROM "
                                    "library")
        rows = cursor.fetchall()
        for row in rows:
            libraries.append((row.library_name, row.library_icon, row.library_read_only))

        return libraries

    def getModelLibraries(self):
        libraries = []
        cursor = self._cursor()
        cursor.execute("SELECT DISTINCT l.library_name, l.library_icon, l.library_read_only"
                       " FROM library l, model m WHERE l.library_id = m.library_id")
        rows = cursor.fetchall()
        for row in rows:
            libraries.append((row.library_name, row.library_icon, row.library_read_only))

        return libraries

    def getMaterialLibraries(self):
        libraries = []
        cursor = self._cursor()
        cursor.execute("SELECT DISTINCT l.library_name, l.library_icon, l.library_read_only"
                       " FROM library l, material m WHERE l.library_id = m.library_id")
        rows = cursor.fetchall()
        for row in rows:
            libraries.append((row.library_name, row.library_icon, row.library_read_only))

        return libraries

    def _getLibrary(self, libraryId):
        cursor = self._cursor()
        cursor.execute("SELECT library_name, library_icon, library_read_only FROM "
                                    "library WHERE library_id = ?",
                       libraryId)
        row = cursor.fetchone()
        if row:
            return (row.library_name, row.library_icon, row.library_read_only)
        return None

    def _getMaterialLibrary(self, libraryId):
        cursor = self._cursor()
        # Need to add logic to ensure there's a material in there?
        cursor.execute("SELECT library_name, library_icon, library_read_only FROM "
                                    "library WHERE library_id = ?",
                       libraryId)
        row = cursor.fetchone()
        if row:
            # This needs to be a library object
            return Materials.MaterialLibrary(row.library_name, row.library_icon, row.library_read_only)
        return None

    def _getPath(self, folderId):
        path = ""
        cursor = self._cursor()
        cursor.execute("SELECT folder_name, parent_id FROM folder WHERE folder_id = ?",
                       folderId)
        row = cursor.fetchone()
        if row:
            if row.parent_id is None:
                path = row.folder_name
            else:
                path = self._getPath(row.parent_id) + '/' + path
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
                prop = Materials.Model.ModelProperty()
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
            prop = Materials.Model.ModelProperty()
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
                property.addColumns(column)

        return properties

    def getModel(self, uuid):
        cursor = self._cursor()
        cursor.execute("SELECT library_id, folder_id, model_type, "
            "model_name, model_url, model_description, model_doi FROM model WHERE model_id = ?",
                       uuid)

        row = cursor.fetchone()
        if row:
            model = Materials.Model()
            model.UUID = uuid
            model.Type = row.model_type
            model.Name = row.model_name
            model.URL = row.model_url
            model.Description = row.model_description
            model.DOI = row.model_doi

            model.Library = self._getLibrary(row.library_id)

            path = self._getPath(row.folder_id) + "/" + row.model_name
            model.Path = path

            inherits = self._getInherits(uuid)
            for inherit in inherits:
                model.addInheritance(inherit)

            properties = self._getModelProperties(uuid)
            for property in properties:
                model.addProperty(inherit)

            return model

        return None

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
                       ("Model" if isPhysical else "AppearanceModel"))

        rows = cursor.fetchall()
        for row in rows:
            models.append(row.model_id)

        return models

    def _getMaterialProperties(self, uuid):
        properties = {}
        cursor = self._cursor()
        cursor.execute("SELECT material_property_name, "
                                    "material_property_value FROM material_property_value "
                                    "WHERE material_id = ?",
                       uuid)

        rows = cursor.fetchall()
        for row in rows:
            properties[row.property_name] = row.property_value

        return properties

    def getMaterial(self, uuid):
        cursor = self._cursor()
        cursor.execute("SELECT library_id, folder_id, material_name, "
                            "material_author, material_license, material_parent_uuid, "
                            "material_description, material_url, material_reference FROM "
                            "material WHERE material_id = ?",
                       uuid)

        row = cursor.fetchone()
        if row:
            material = Materials.Material()
            material.UUID = uuid
            material.Name = row.material_name
            material.Author = row.material_author
            material.License = row.material_license
            material.Parent = row.material_parent_uuid
            material.Description = row.material_description
            material.URL = row.material_url
            material.Reference = row.material_reference

            material.Library = self._getMaterialLibrary(row.library_id)

            path = self._getPath(row.folder_id) + "/" + row.material_name
            material.Directory = path

            tags = self._getTags(uuid)
            for tag in tags:
                material.addTag(tag)

            for model in self._getMaterialModels(uuid, True):
                material.addPhysicalModel(model)

            for model in self._getMaterialModels(uuid, False):
                material.addAppearanceModel(model)

            # The actual properties are set by the model. We just need to load the values
            properties = self._getMaterialProperties(uuid)
            for name, value in properties.items():
                material.setValue(name, value)

            return material

        return None
