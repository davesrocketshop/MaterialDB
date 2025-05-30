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

from PySide.QtCore import QByteArray, QBuffer, QIODevice
from PySide.QtGui import QImage

import Materials
from MaterialAPI.MaterialManagerExternal import MaterialLibraryType, MaterialLibraryObjectType, \
    ModelObjectType, MaterialObjectType
from MaterialDB.Database.Database import Database
from MaterialDB.Database.Exceptions import DatabaseLibraryCreationError, \
    DatabaseIconError, DatabaseLibraryNotFound, DatabaseLibraryReadOnlyError, \
    DatabaseFolderCreationError, \
    DatabaseModelCreationError, DatabaseMaterialCreationError, \
    DatabaseModelUpdateError, \
    DatabaseModelExistsError, DatabaseMaterialExistsError, \
    DatabaseModelNotFound, DatabaseMaterialNotFound, \
    DatabaseRenameError, DatabaseDeleteError

class DatabaseMySQL(Database):

    def __init__(self):
        super().__init__()

    #
    # Library methods
    #

    def getLibraries(self) -> list[MaterialLibraryType]:
        libraries = []
        cursor = self._cursor()
        cursor.execute("SELECT library_name, library_icon, library_read_only FROM "
                                    "library")
        rows = cursor.fetchall()
        for row in rows:
            libraries.append(MaterialLibraryType(row.library_name, row.library_icon, row.library_read_only))

        return libraries

    def getModelLibraries(self) -> list[MaterialLibraryType]:
        libraries = []
        cursor = self._cursor()
        cursor.execute("SELECT DISTINCT l.library_name, l.library_icon, l.library_read_only"
                       " FROM library l, model m WHERE l.library_id = m.library_id")
        rows = cursor.fetchall()
        for row in rows:
            libraries.append(MaterialLibraryType(row.library_name, row.library_icon, row.library_read_only))

        return libraries

    def getMaterialLibraries(self) -> list[MaterialLibraryType]:
        libraries = []
        cursor = self._cursor()
        cursor.execute("SELECT DISTINCT l.library_name, l.library_icon, l.library_read_only"
                       " FROM library l, material m WHERE l.library_id = m.library_id")
        rows = cursor.fetchall()
        for row in rows:
            libraries.append(MaterialLibraryType(row.library_name, row.library_icon, row.library_read_only))

        return libraries

    def getLibrary(self, libraryName: str) -> MaterialLibraryType:
        cursor = self._cursor()
        cursor.execute("SELECT library_name, library_icon, library_read_only"
                       " FROM library WHERE library_name = ?", libraryName)

        row = cursor.fetchone()
        if row:
            return MaterialLibraryType(row.library_name, row.library_icon, row.library_read_only)
        return None

    def createLibrary(self, libraryName: str, icon: bytes, readOnly: bool) -> None:
        try:
            cursor = self._cursor()

            cursor.execute("SELECT library_id, library_icon, library_read_only FROM library WHERE library_name = ?", libraryName)
            row = cursor.fetchone()
            if not row:
                if icon is None or len(icon) == 0:
                    cursor.execute("INSERT INTO library (library_name, library_read_only) "
                                        "VALUES (?, ?)", libraryName, readOnly)
                else:
                    cursor.execute("INSERT INTO library (library_name, library_icon, library_read_only) "
                            "VALUES (?, ?, ?)", libraryName, icon, readOnly)
                self._connection.commit()
            else:
                # Check that everthing matches
                if icon is None:
                    if readOnly == row.library_read_only and (row.library_icon is None or len(row.library_icon) == 0):
                        return
                else:
                    # if readOnly == row.library_read_only and icon == row.library_icon.decode('UTF-8'):
                    #     return
                    if readOnly == row.library_read_only and icon == row.library_icon:
                        return
                raise DatabaseLibraryCreationError("Library already exists")
        except Exception as ex:
            print("Unable to create library '{}':".format(libraryName), ex)
            raise DatabaseLibraryCreationError(ex)

    def renameLibrary(self, oldName: str, newName: str) -> None:
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
            print("Unable to rename library:", ex)
            raise DatabaseRenameError(ex)

    def changeIcon(self, libraryName: str, icon: bytes) -> None:
        try:
            cursor = self._cursor()

            cursor.execute("UPDATE library SET library_icon = ? "
                                "WHERE library_name = ?", icon, libraryName)

            self._connection.commit()
        except Exception as ex:
            print("Unable to change icon:", ex)
            raise DatabaseIconError(ex)

    def removeLibrary(self, libraryName: str) -> None:
        try:
            cursor = self._cursor()

            cursor.execute("DELETE FROM library WHERE library_name = ?", libraryName)

            self._connection.commit()
        except Exception as ex:
            print("Unable to remove library:", ex)
            raise DatabaseDeleteError(ex)

    def libraryModels(self, libraryName: str) -> list[MaterialLibraryObjectType]:
        try:
            models = []
            cursor = self._cursor()

            cursor.execute("SELECT library_id FROM library WHERE library_name = ?", libraryName)
            row = cursor.fetchone()
            if not row:
                raise DatabaseLibraryNotFound()

            cursor.execute("SELECT m.model_id, GetFolder(m.folder_id) as folder_name, m.model_name"
                           " FROM model m, library l"
                           " WHERE m.library_id = l.library_id AND l.library_name = ?", libraryName)
            rows = cursor.fetchall()
            for row in rows:
                # Convert the folder_id to a path
                models.append(MaterialLibraryObjectType(row.model_id, row.folder_name, row.model_name))

            return models
        except Exception as ex:
            print("Unable to get library models:", ex)
            raise DatabaseModelNotFound(ex)

    def libraryMaterials(self, libraryName: str,
                         filter: Materials.MaterialFilter = None,
                         options: Materials.MaterialFilterOptions = None) -> list[MaterialLibraryObjectType]:
        try:
            materials = []
            cursor = self._cursor()

            cursor.execute("SELECT library_id FROM library WHERE library_name = ?", libraryName)
            row = cursor.fetchone()
            if not row:
                raise DatabaseLibraryNotFound()

            cursor.execute("SELECT m.material_id, GetFolder(m.folder_id) as folder_name, m.material_name"
                           " FROM material m, library l"
                           " WHERE m.library_id = l.library_id AND l.library_name = ?", libraryName)
            rows = cursor.fetchall()
            for row in rows:
                materials.append(MaterialLibraryObjectType(row.material_id, row.folder_name, row.material_name))

            return materials
        except Exception as ex:
            print("Unable to get library materials:", ex)
            raise DatabaseMaterialNotFound(ex)

    def libraryFolders(self, libraryName: str) -> list[str]:
        try:
            cursor = self._cursor()

            cursor.execute("SELECT library_id FROM library WHERE library_name = ?", libraryName)
            row = cursor.fetchone()
            if not row:
                raise DatabaseLibraryNotFound()

            cursor.execute("SELECT f.folder_id, f.folder_name, f.library_id, f.parent_id"
                           " FROM folder f, library l"
                           " WHERE f.library_id = l.library_id AND l.library_name = ?"
                           " ORDER BY f.parent_id", libraryName)
            rows = cursor.fetchall()
            folderTree = {}
            for row in rows:
                # folders.append(MaterialLibraryObjectType(row.material_id, row.folder_name, row.material_name))
                if row.parent_id is None:
                    folderTree[row.folder_id] = "/" + row.folder_name
                else:
                    folderTree[row.folder_id] = folderTree[row.parent_id] + "/" + row.folder_name

            return list(folderTree.values())
        except Exception as ex:
            print("Unable to get library folders:", ex)
            raise DatabaseMaterialNotFound(ex)


    def _findLibrary(self, name):
        cursor = self._cursor()

        cursor.execute("SELECT library_id FROM library WHERE library_name = ?", name)
        row = cursor.fetchone()
        if row:
            return row.library_id
        return 0
    
    def _findWriteableLibrary(self, name):
        """ Finds the name library and ensures it's not read only """
        libraryIndex = self._findLibrary(name)
        if libraryIndex > 0:
            if self._isReadOnly(libraryIndex):
                raise DatabaseLibraryReadOnlyError()
        else:
            raise DatabaseLibraryNotFound()

    def _getIcon(self, icon, iconPath):
        if icon is None or len(icon) == 0:
            if iconPath is None or len(iconPath) == 0:
                return None
            iconImage = QImage(iconPath)
            ba = QByteArray()
            buffer = QBuffer(ba)
            buffer.open(QIODevice.WriteOnly)
            iconImage.save(buffer, "PNG") # writes image into ba in PNG format
            # iconImage.save(buffer) # writes image into ba in PNG format
            return bytes(ba.data())
        return icon

    def _getLibrary(self, libraryId):
        cursor = self._cursor()
        cursor.execute("SELECT library_name, library_icon, library_read_only "
                                    "FROM library WHERE library_id = ?",
                       libraryId)
        row = cursor.fetchone()
        if row:
            return MaterialLibraryType(row.library_name, row.library_icon, row.library_read_only)
        return None

    def _isReadOnly(self, libraryId):
        cursor = self._cursor()
        cursor.execute("SELECT library_read_only FROM library WHERE library_id = ?",
                       libraryId)
        row = cursor.fetchone()
        if row:
            return (row.library_read_only == True)
        else:
            raise DatabaseLibraryNotFound()

    #
    # Folder methods
    #

    def createFolder(self, libraryName: str, path: str) -> None:
        try:
            libraryIndex = self._findWriteableLibrary(libraryName)
            self._createPath(libraryIndex, path)
        except Exception as ex:
            print("Unable to create folder:", ex)
            raise DatabaseFolderCreationError(ex)

    def renameFolder(self, libraryName: str, oldPath: str, newPath: str) -> None:
        try:
            libraryIndex = self._findWriteableLibrary(libraryName)

            # Check the folders have the same parent path
            oldPathList = self._pathList(oldPath)
            newPathList = self._pathList(newPath)
            if len(oldPathList) != len(newPathList):
                raise DatabaseRenameError("Path lengths don't match")

            parentIndex = 0 # start at the root
            cursor = self._cursor()
            if len(newPathList) > 0:
                for index in range(0, len(newPathList) - 1):
                    if oldPathList[index] != newPathList[index]:
                        raise DatabaseRenameError("Path tree doesn't match")
                    if parentIndex == 0:
                        cursor.execute("SELECT folder_id FROM folder WHERE folder_name = ? AND library_id = ?"
                            " AND parent_id IS NULL", oldPathList[index], libraryIndex)
                    else:
                        cursor.execute("SELECT folder_id FROM folder WHERE folder_name = ? AND library_id = ?"
                            " AND parent_id IS ?", oldPathList[index], libraryIndex, parentIndex)
                    row = cursor.fetchone()
                    if row:
                        parentIndex = row.folder_id
                    else:
                        raise DatabaseRenameError("Folder path doesn't exist")
                if parentIndex == 0:
                    cursor.execute("UPDATE folder "
                                "SET folder_name = ? "
                                "WHERE parent_id IS NULL AND folder_name = ?", newPathList[-1], oldPathList[-1])
                else:
                    cursor.execute("UPDATE folder "
                                "SET folder_name = ? "
                                "WHERE parent_id = ? AND folder_name = ?", newPathList[-1], parentIndex, oldPathList[-1])
                if cursor.rowcount < 1:
                    raise DatabaseRenameError("Unable to update folder path")

        except Exception as ex:
            raise ex

    def deleteRecursive(self, libraryName: str, path: str) -> None:
        try:
            libraryIndex = self._findWriteableLibrary(libraryName)

            pathList = self._pathList(path)
            parentIndex = 0 # start at the root
            cursor = self._cursor()
            if len(pathList) > 0:
                for index in range(0, len(pathList) - 1):
                    if parentIndex == 0:
                        cursor.execute("SELECT folder_id FROM folder WHERE folder_name = ? AND library_id = ?"
                            " AND parent_id IS NULL", pathList[index], libraryIndex)
                    else:
                        cursor.execute("SELECT folder_id FROM folder WHERE folder_name = ? AND library_id = ?"
                            " AND parent_id IS ?", pathList[index], libraryIndex, parentIndex)
                    row = cursor.fetchone()
                    if row:
                        parentIndex = row.folder_id
                    else:
                        raise DatabaseDeleteError("Folder path doesn't exist")
                if parentIndex == 0:
                    cursor.execute("DELETE from folder "
                                "WHERE parent_id IS NULL AND folder_name = ?", pathList[-1])
                else:
                    cursor.execute("DELETE from folder "
                                "WHERE parent_id = ? AND folder_name = ?", parentIndex, pathList[-1])
                if cursor.rowcount < 1:
                    raise DatabaseDeleteError("Unable to delete folder")

        except Exception as ex:
            raise ex

    def _pathList(self, path):
        # Strip any leading "/"
        if len(path) > 0 and path[0] == '/':
            path = path[1:]
            print(path)

        return path.split('/')

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
        index = pathIndex + 1
        if index >= len(pathList):
            return newId
        return self._createPathRecursive(libraryIndex, newId, index, pathList)

    def _createPath(self, libraryIndex, path):
        newId = 0

        pathList = self._pathList(path)
        if len(pathList) > 0:
            return self._createPathRecursive(libraryIndex, 0, 0, pathList)
        return newId

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

    #
    # Model methods
    #

    def getModel(self, uuid: str) -> ModelObjectType:
        try:
            cursor = self._cursor()
            cursor.execute("SELECT library_id, GetFolder(folder_id) as folder_name, model_type, "
                "model_name, model_url, model_description, model_doi FROM model WHERE model_id = ?",
                        uuid)

            row = cursor.fetchone()
            if not row:
                raise DatabaseModelNotFound()

            model = Materials.Model()
            # model.UUID = uuid
            model.Type = row.model_type
            model.Name = row.model_name
            model.Directory = row.folder_name
            model.URL = row.model_url
            model.Description = row.model_description
            model.DOI = row.model_doi

            # model.Library = self._getLibrary(row.library_id)
            library = self._getLibrary(row.library_id)

            inherits = self._getInherits(uuid)
            for inherit in inherits:
                model.addInheritance(inherit)

            properties = self._getModelProperties(uuid)
            for property in properties:
                model.addProperty(property)

            return ModelObjectType(library.name, model)

        except DatabaseModelNotFound as notFound:
            # Rethrow
            raise notFound
        except Exception as ex:
            print("Unable to get model:", ex)
            raise DatabaseModelNotFound(ex)

    def createModel(self, libraryName: str, path: str, model: Materials.Model) -> None:
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

    def updateModel(self, libraryName: str, path: str, model: Materials.Model) -> None:
        try:
            libraryIndex = self._findWriteableLibrary(libraryName)
            self._updateModel(libraryIndex, path, model)
        except DatabaseModelNotFound as exists:
            # Rethrow
            raise exists
        except DatabaseLibraryReadOnlyError as ro:
            raise ro
        except Exception as ex:
            print("Unable to update model:", ex)
            raise DatabaseModelUpdateError(ex)
        
    def setModelPath(self, libraryName: str, path: str, uuid: str) -> None:
        try:
            libraryIndex = self._findWriteableLibrary(libraryName)
            self._updateModelPath(libraryIndex, path, uuid)
        except DatabaseModelNotFound as exists:
            # Rethrow
            raise exists
        except DatabaseLibraryReadOnlyError as ro:
            raise ro
        except Exception as ex:
            print("Unable to update model:", ex)
            raise DatabaseModelUpdateError(ex)

    def renameModel(self, libraryName: str, name: str, uuid: str) -> None:
        try:
            libraryIndex = self._findWriteableLibrary(libraryName)
            self._updateModelName(libraryIndex, name, uuid)
        except DatabaseModelNotFound as exists:
            # Rethrow
            raise exists
        except DatabaseLibraryReadOnlyError as ro:
            raise ro
        except Exception as ex:
            print("Unable to update model:", ex)
            raise DatabaseModelUpdateError(ex)

    def moveModel(self, libraryName: str, path: str, uuid: str) -> None:
        try:
            libraryIndex = self._findWriteableLibrary(libraryName)
            self._moveModel(libraryIndex, path, uuid)
        except DatabaseModelNotFound as exists:
            # Rethrow
            raise exists
        except DatabaseLibraryReadOnlyError as ro:
            raise ro
        except Exception as ex:
            print("Unable to update model:", ex)
            raise DatabaseModelUpdateError(ex)

    def removeModel(self, uuid: str) -> None:
        cursor = self._cursor()
        cursor.execute("SELECT library_id FROM model WHERE model_id = ?", uuid)
        row = cursor.fetchone()
        if not row:
            raise DatabaseLibraryNotFound()
        else:
            oldLibraryIndex = row.library_id

            # Is the library read only?
            if oldLibraryIndex > 0:
                if self._isReadOnly(oldLibraryIndex):
                    raise DatabaseLibraryReadOnlyError()
            else:
                raise DatabaseLibraryNotFound()
            
            cursor.execute("DELETE FROM model WHERE model_id = ?", uuid)
            if cursor.rowcount < 0:
                raise DatabaseDeleteError()

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
                self._createModelPropertyColumn(propertyId, column, libraryIndex)
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
                self._createModelPropertyColumn(propertyId, column, libraryIndex)
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
                self._createInheritance(model.UUID, inherit, libraryIndex)

            for property in model.Properties.values():
                self._createModelProperty(model.UUID, property, libraryIndex)
        self._connection.commit()

    def _updateModelPath(self, libraryIndex, path, uuid):
        cursor = self._cursor()
        pathIndex = self._createPath(libraryIndex, path)
        cursor.execute("SELECT model_id FROM model WHERE library_id = ? AND model_id = ?", libraryIndex, uuid)
        row = cursor.fetchone()
        if not row:
            raise DatabaseModelNotFound()
        else:
            cursor.execute("UPDATE model SET "
                           "  folder_id = ?"
                           " WHERE model_id = ?",
                        (None if pathIndex == 0 else pathIndex),
                        uuid
                        )
        self._connection.commit()

    def _updateModelName(self, libraryIndex, name, uuid):
        cursor = self._cursor()
        cursor.execute("SELECT model_id FROM model WHERE library_id = ? AND model_id = ?", libraryIndex, uuid)
        row = cursor.fetchone()
        if not row:
            raise DatabaseModelNotFound()
        else:
            cursor.execute("UPDATE model SET "
                           "  model_name = ?"
                           " WHERE model_id = ?",
                        name,
                        uuid
                        )
        self._connection.commit()

    def _moveModel(self, libraryIndex, path, uuid):
        cursor = self._cursor()
        pathIndex = self._createPath(libraryIndex, path)
        cursor.execute("SELECT library_id, folder_id FROM model WHERE model_id = ?", uuid)
        row = cursor.fetchone()
        if not row:
            raise DatabaseModelNotFound()
        else:
            oldLibraryIndex = row.library_id
            oldPathIndex = row.folder_id

            # We already know the new library is writeable, but what about the old library?
            if oldLibraryIndex > 0:
                if self._isReadOnly(oldLibraryIndex):
                    raise DatabaseLibraryReadOnlyError()
            else:
                raise DatabaseLibraryNotFound()
            
            if oldLibraryIndex != libraryIndex or oldPathIndex != pathIndex:
                cursor.execute("UPDATE model SET "
                            "  library_id = ?,"
                            "  folder_id = ?"
                            " WHERE model_id = ?",
                            libraryIndex,
                            pathIndex,
                            uuid
                            )
        self._connection.commit()

    def _updateModel(self, libraryIndex, path, model):
        cursor = self._cursor()
        pathIndex = self._createPath(libraryIndex, path)
        cursor.execute("SELECT model_id FROM model WHERE library_id = ? AND model_id = ?", libraryIndex, model.UUID)
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
                self._createInheritance(model.UUID, inherit, libraryIndex)

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
                self._updateModelProperty(model.UUID, property, libraryIndex)
        self._connection.commit()

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
        self._connection.commit()

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

    #
    # Material methods
    #

    def getMaterial(self, uuid: str) -> MaterialObjectType:
        try:
            cursor = self._cursor()
            cursor.execute("SELECT library_id, GetFolder(folder_id) as folder_name, material_name, "
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
            material.Directory = row.folder_name
            material.Author = row.material_author
            material.License = row.material_license
            material.Parent = row.material_parent_uuid
            material.Description = row.material_description
            material.URL = row.material_url
            material.Reference = row.material_reference

            library = self._getLibrary(row.library_id)

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

            return MaterialObjectType(library.name, material)

        except DatabaseMaterialNotFound as notFound:
            # Rethrow
            raise notFound
        except Exception as ex:
            print("Unable to get material:", ex)
            raise DatabaseMaterialNotFound(ex)

    def createMaterial(self, libraryName: str, path: str, material: Materials.Material) -> None:
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
        
    def updateMaterial(self, libraryName: str, path: str, material: Materials.Material) -> None:
        pass

    def setMaterialPath(self, libraryName: str, path: str, uuid: str) -> None:
        pass

    def renameMaterial(self, libraryName: str, name: str, uuid: str) -> None:
        pass

    def moveMaterial(self, libraryName: str, path: str, uuid: str) -> None:
        pass

    def removeMaterial(self, uuid: str) -> None:
        pass

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

        cursor.execute("SELECT material_id, material_tag_id FROM material_tag_mapping "
                                "WHERE material_id = ? AND material_tag_id = ?", materialUUID, tagId)
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO material_tag_mapping (material_id, material_tag_id) "
                          "VALUES (?, ?)", materialUUID, tagId)
        self._connection.commit()

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

    def _createMaterialModel(self, materialUUID, modelUUID, libraryIndex):
        cursor = self._cursor()
        cursor.execute("SELECT material_id FROM material_models WHERE material_id = ? AND model_id = ?",
                       materialUUID, modelUUID)
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO material_models (material_id, model_id) "
                                    "VALUES (?, ?)", materialUUID, modelUUID)
        self._connection.commit()

    def _createMaterialPropertyValue(self, materialUUID, name, type, libraryIndex):
        cursor = self._cursor()
        cursor.execute("INSERT INTO material_property_value (material_id, material_property_name, material_property_type) "
                    "VALUES (?, ?, ?)",
                    materialUUID, name, type)

        return self._lastId(cursor)

    def _createStringValue(self, materialUUID, name, type, value, libraryIndex):
        if value is not None:
            value_id = self._createMaterialPropertyValue(materialUUID, name, type, libraryIndex)
            cursor = self._cursor()

            cursor.execute("INSERT INTO material_property_string_value "
                        " (material_property_value_id, material_property_value)"
                        " VALUES (?, ?)",
                        value_id, value)
            self._connection.commit()

    def _createLongStringValue(self, materialUUID, name, type, value, libraryIndex):
        if value is not None:
            value_id = self._createMaterialPropertyValue(materialUUID, name, type, libraryIndex)
            cursor = self._cursor()

            cursor.execute("INSERT INTO material_property_long_string_value "
                        " (material_property_value_id, material_property_value)"
                        " VALUES (?, ?)",
                        value_id, value)
            self._connection.commit()

    def _createListValue(self, materialUUID, name, type, list, libraryIndex):
        if list is not None:
            value_id = self._createMaterialPropertyValue(materialUUID, name, type, libraryIndex)
            cursor = self._cursor()

            for entry in list:
                cursor.execute("INSERT INTO material_property_string_value "
                            " (material_property_value_id, material_property_value)"
                            " VALUES (?, ?)",
                            value_id, entry)

            self._connection.commit()

    def _createLongListValue(self, materialUUID, name, type, list, libraryIndex):
        if list is not None:
            value_id = self._createMaterialPropertyValue(materialUUID, name, type, libraryIndex)
            cursor = self._cursor()

            for entry in list:
                cursor.execute("INSERT INTO material_property_long_string_value "
                            " (material_property_value_id, material_property_value)"
                            " VALUES (?, ?)",
                            value_id, entry)

            self._connection.commit()

    def _createArrayValue3D(self, materialUUID, name, propertyType, array, libraryIndex):
        if array is not None:
            value_id = self._createMaterialPropertyValue(materialUUID, name, propertyType, libraryIndex)
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

            self._connection.commit()

    def _createArrayValue2D(self, materialUUID, name, propertyType, array, libraryIndex):
        if array is not None:
            value_id = self._createMaterialPropertyValue(materialUUID, name, propertyType, libraryIndex)
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

            self._connection.commit()

    def _createMaterialProperty(self, materialUUID, material, property, libraryIndex):
        if property.Type == "2DArray" or \
           property.Type == "3DArray":
            if material.hasPhysicalProperty(property.Name):
                array = material.getPhysicalValue(property.Name)
            else:
                array = material.getAppearanceValue(property.Name)
            if array.Dimensions == 2:
                self._createArrayValue2D(materialUUID, property.Name, property.Type, array, libraryIndex)
            else:
                self._createArrayValue3D(materialUUID, property.Name, property.Type, array, libraryIndex)
        elif property.Type == "List" or \
           property.Type == "FileList":
            self._createListValue(materialUUID, property.Name, property.Type, property.Value, libraryIndex)
        elif property.Type == "ImageList":
            self._createLongListValue(materialUUID, property.Name, property.Type, property.Value, libraryIndex)
        elif property.Type == "Quantity":
            if property.Empty:
                return
            self._createStringValue(materialUUID, property.Name, property.Type, property.Value.UserString, libraryIndex)
        elif property.Type == "SVG" or \
            property.Type == "Image":
            self._createLongStringValue(materialUUID, property.Name, property.Type, property.Value, libraryIndex)
        else:
            self._createStringValue(materialUUID, property.Name, property.Type, property.Value, libraryIndex)

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
                self._createTag(material.UUID, tag, libraryIndex)

            # print("{} Physical models".format(len(material.PhysicalModels)))
            for model in material.PhysicalModels:
                self._createMaterialModel(material.UUID, model, libraryIndex)

            # print("{} Appearance models".format(len(material.AppearanceModels)))
            for model in material.AppearanceModels:
                self._createMaterialModel(material.UUID, model, libraryIndex)

            # print("{} Properties".format(len(material.PropertyObjects)))
            for property in material.PropertyObjects.values():
                self._createMaterialProperty(material.UUID, material, property, libraryIndex)

        self._connection.commit()

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

    #
    # Support methods
    #

    def _foreignKeysIgnore(self, cursor):
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")

    def _foreignKeysRestore(self, cursor):
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")
