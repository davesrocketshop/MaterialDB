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

import traceback
from typing import Any
from pyodbc import Cursor

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

    def createLibrary(self, libraryName: str, icon: bytes | None, readOnly: bool) -> None:
        cursor = self._cursor()
        try:

            cursor.execute("SELECT library_id, library_icon, library_read_only FROM library WHERE library_name = ?", libraryName)
            row = cursor.fetchone()
            if not row:
                if icon is None or len(icon) == 0:
                    cursor.execute("INSERT INTO library (library_name, library_read_only) "
                                        "VALUES (?, ?)", libraryName, readOnly)
                else:
                    cursor.execute("INSERT INTO library (library_name, library_icon, library_read_only) "
                            "VALUES (?, ?, ?)", libraryName, icon, readOnly)
                cursor.commit()
            else:
                # Check that everything matches
                if icon is None:
                    if readOnly == row.library_read_only and (row.library_icon is None or len(row.library_icon) == 0):
                        return
                else:
                    # if readOnly == row.library_read_only and icon == row.library_icon.decode('UTF-8'):
                    #     return
                    if readOnly == row.library_read_only and icon == row.library_icon:
                        return
                    
                raise DatabaseLibraryCreationError("Library already exists")
        except DatabaseLibraryCreationError as createError:
            cursor.rollback()
            raise createError
        except Exception as ex:
            cursor.rollback()
            print("Unable to create library '{}':".format(libraryName), ex)
            raise DatabaseLibraryCreationError(error=ex)

    def renameLibrary(self, oldName: str, newName: str) -> None:
        cursor = self._cursor()
        try:
            cursor.execute("SELECT library_id FROM library WHERE library_name = ?", newName)
            row = cursor.fetchone()
            if row:
                raise DatabaseRenameError(message="Destination library name already exists")

            cursor.execute("UPDATE library SET library_name = ? "
                                "WHERE library_name = ?", newName, oldName)

            cursor.commit()
        except DatabaseRenameError as renameError:
            cursor.rollback()
            raise renameError
        except Exception as ex:
            cursor.rollback()
            print("Unable to rename library:", ex)
            raise DatabaseRenameError(error=ex)

    def changeIcon(self, libraryName: str, icon: bytes) -> None:
        cursor = self._cursor()
        try:
            cursor.execute("UPDATE library SET library_icon = ? "
                                "WHERE library_name = ?", icon, libraryName)

            cursor.commit()
        except Exception as ex:
            cursor.rollback()
            print("Unable to change icon:", ex)
            raise DatabaseIconError(error=ex)

    def removeLibrary(self, libraryName: str) -> None:
        cursor = self._cursor()
        try:
            cursor.execute("DELETE FROM library WHERE library_name = ?", libraryName)

            cursor.commit()
        except Exception as ex:
            cursor.rollback()
            print("Unable to remove library:", ex)
            raise DatabaseDeleteError(error=ex)

    def libraryModels(self, libraryName: str) -> list[MaterialLibraryObjectType]:
        cursor = self._cursor()
        try:
            models = []

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
        except DatabaseLibraryNotFound as notFound:
            cursor.rollback()
            # Rethrow
            raise notFound
        except Exception as ex:
            cursor.rollback()
            print("Unable to get library models:", ex)
            raise DatabaseLibraryNotFound(error=ex)

    def libraryMaterials(self, libraryName: str,
                         filter: Materials.MaterialFilter = None,
                         options: Materials.MaterialFilterOptions = None) -> list[MaterialLibraryObjectType]:
        cursor = self._cursor()
        try:
            materials = []

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
        except DatabaseLibraryNotFound as notFound:
            cursor.rollback()
            raise notFound # Rethrow
        except Exception as ex:
            cursor.rollback()
            print("Unable to get library materials:", ex)
            raise DatabaseMaterialNotFound(error=ex)

    def libraryFolders(self, libraryName: str) -> list[str]:
        cursor = self._cursor()
        try:
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
        except DatabaseLibraryNotFound as notFound:
            cursor.rollback()
            raise notFound # Rethrow
        except Exception as ex:
            cursor.rollback()
            print("Unable to get library folders:", ex)
            raise DatabaseMaterialNotFound(error=ex)

    def librarySubFolders(self, libraryName: str, path: str) -> list[str]:
        cursor = self._cursor()
        try:
            libraryIndex = self._findLibrary(cursor, libraryName)
            if libraryIndex == 0:
                raise DatabaseLibraryNotFound()

            pathList = self._pathList(path)
            parentIndex = 0 # start at the root
            for index in range(0, len(pathList)):
                if parentIndex == 0:
                    cursor.execute("SELECT folder_id FROM folder WHERE folder_name = ? AND library_id = ?"
                        " AND parent_id IS NULL", pathList[index], libraryIndex)
                else:
                    cursor.execute("SELECT folder_id FROM folder WHERE folder_name = ? AND library_id = ?"
                        " AND parent_id = ?", pathList[index], libraryIndex, parentIndex)
                row = cursor.fetchone()
                if row:
                    parentIndex = row.folder_id
                else:
                    raise DatabaseLibraryNotFound()

            cursor.execute("SELECT folder_name FROM folder "
                           "WHERE library_id = ? AND parent_id = ?", libraryIndex, parentIndex)
            rows = cursor.fetchall()
            folders = []
            for row in rows:
                folders.append(row.folder_name)

            return folders
        except DatabaseLibraryNotFound as notFound:
            cursor.rollback()
            raise notFound # Rethrow
        except Exception as ex:
            cursor.rollback()
            print("Unable to get library subfolders:", ex)
            # print(type(ex))
            # traceback.print_exc() 
            raise DatabaseMaterialNotFound(error=ex)

    def _findLibrary(self, cursor : Cursor, name : str) -> int:
        cursor.execute("SELECT library_id FROM library WHERE library_name = ?", name)
        row = cursor.fetchone()
        if row:
            return row.library_id
        return 0
    
    def _findWriteableLibrary(self, cursor : Cursor, name : str) -> int:
        """ Finds the name library and ensures it's not read only """
        libraryIndex = self._findLibrary(cursor, name)
        if libraryIndex > 0:
            if self._isReadOnly(cursor, libraryIndex):
                raise DatabaseLibraryReadOnlyError()
        else:
            raise DatabaseLibraryNotFound()
        return libraryIndex

    def _getLibrary(self, cursor : Cursor, libraryId : int) -> MaterialLibraryType:
        cursor.execute("SELECT library_name, library_icon, library_read_only "
                                    "FROM library WHERE library_id = ?",
                       libraryId)
        row = cursor.fetchone()
        if row:
            return MaterialLibraryType(row.library_name, row.library_icon, row.library_read_only)
        return None

    def _isReadOnly(self, cursor : Cursor, libraryId : int) -> bool:
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
        cursor = self._cursor()
        try:
            libraryIndex = self._findWriteableLibrary(cursor, libraryName)
            self._createPath(cursor, libraryIndex, path)
            cursor.commit()
        except Exception as ex:
            cursor.rollback()
            print("Unable to create folder:", ex)
            raise DatabaseFolderCreationError(error=ex)

    def renameFolder(self, libraryName: str, oldPath: str, newPath: str) -> None:
        cursor = self._cursor()
        try:
            libraryIndex = self._findWriteableLibrary(cursor, libraryName)

            # Check the folders have the same parent path
            oldPathList = self._pathList(oldPath)
            newPathList = self._pathList(newPath)
            if len(oldPathList) != len(newPathList):
                raise DatabaseRenameError("Path lengths don't match")

            parentIndex = 0 # start at the root
            if len(newPathList) > 0:
                for index in range(0, len(newPathList) - 1):
                    if oldPathList[index] != newPathList[index]:
                        raise DatabaseRenameError("Path tree doesn't match")
                    if parentIndex == 0:
                        cursor.execute("SELECT folder_id FROM folder WHERE folder_name = ? AND library_id = ?"
                            " AND parent_id IS NULL", oldPathList[index], libraryIndex)
                    else:
                        cursor.execute("SELECT folder_id FROM folder WHERE folder_name = ? AND library_id = ?"
                            " AND parent_id = ?", oldPathList[index], libraryIndex, parentIndex)
                    row = cursor.fetchone()
                    if row:
                        parentIndex = row.folder_id
                    else:
                        raise DatabaseRenameError("Folder path doesn't exist")
                if parentIndex == 0:
                    cursor.execute("UPDATE folder "
                                "SET folder_name = ? "
                                "WHERE parent_id IS NULL AND folder_name = ? AND library_id = ?", newPathList[-1], oldPathList[-1], libraryIndex)
                else:
                    cursor.execute("UPDATE folder "
                                "SET folder_name = ? "
                                "WHERE parent_id = ? AND folder_name = ? AND library_id = ?", newPathList[-1], parentIndex, oldPathList[-1], libraryIndex)
                if cursor.rowcount < 1:
                    raise DatabaseRenameError("Unable to update folder path")
            cursor.commit()

        except DatabaseRenameError as renameError:
            cursor.rollback()
            raise renameError # Re-raise
        except Exception as ex:
            cursor.rollback
            raise DatabaseRenameError(error=ex)

    def deleteRecursive(self, libraryName: str, path: str) -> None:
        cursor = self._cursor()
        try:
            libraryIndex = self._findWriteableLibrary(cursor, libraryName)

            pathList = self._pathList(path)
            parentIndex = 0 # start at the root
            if len(pathList) > 0:
                for index in range(0, len(pathList) - 1):
                    if parentIndex == 0:
                        cursor.execute("SELECT folder_id FROM folder WHERE folder_name = ? AND library_id = ?"
                            " AND parent_id IS NULL", pathList[index], libraryIndex)
                    else:
                        cursor.execute("SELECT folder_id FROM folder WHERE folder_name = ? AND library_id = ?"
                            " AND parent_id = ?", pathList[index], libraryIndex, parentIndex)
                    row = cursor.fetchone()
                    if row:
                        parentIndex = row.folder_id
                    else:
                        raise DatabaseDeleteError("Folder path doesn't exist")
                if parentIndex == 0:
                    cursor.execute("DELETE from folder "
                                "WHERE parent_id IS NULL AND folder_name = ? AND library_id = ?", pathList[-1], libraryIndex)
                else:
                    cursor.execute("DELETE from folder "
                                "WHERE parent_id = ? AND folder_name = ? AND library_id = ?", parentIndex, pathList[-1], libraryIndex)
                if cursor.rowcount < 1:
                    raise DatabaseDeleteError("Unable to delete folder")
            cursor.commit()
        except DatabaseDeleteError as deleteError:
            cursor.rollback()
            raise deleteError
        except Exception as ex:
            cursor.rollback()
            raise DatabaseDeleteError(error=ex)
        
    def folderMaterials(self, libraryName: str, path: str) -> list[MaterialLibraryObjectType]:
        cursor = self._cursor()
        try:
            materials = []
            libraryIndex = self._findLibrary(cursor, libraryName)

            pathList = self._pathList(path)
            parentIndex = 0 # start at the root
            if len(pathList) > 0:
                for index in range(0, len(pathList) - 1):
                    if parentIndex == 0:
                        cursor.execute("SELECT folder_id FROM folder WHERE folder_name = ? AND library_id = ?"
                            " AND parent_id IS NULL", pathList[index], libraryIndex)
                    else:
                        cursor.execute("SELECT folder_id FROM folder WHERE folder_name = ? AND library_id = ?"
                            " AND parent_id = ?", pathList[index], libraryIndex, parentIndex)
                    row = cursor.fetchone()
                    if row:
                        parentIndex = row.folder_id
                    else:
                        raise DatabaseMaterialNotFound("Folder path doesn't exist")
                cursor.execute("SELECT material_id, GetFolder(folder_id) as folder_name, material_name"
                            " FROM material"
                            " WHERE folder_id = ? AND library_id = ?", parentIndex, libraryIndex)
                # if parentIndex == 0:
                #     cursor.execute("SELECT material_id FROM material WHERE folder_id IS NULL AND library_id = ?", libraryIndex)
                # else:
                #     cursor.execute("SELECT material_id FROM material WHERE folder_id = ? AND library_id = ?", parentIndex, libraryIndex)
                rows = cursor.fetchall()
                for row in rows:
                    materials.append(MaterialLibraryObjectType(row.material_id, row.folder_name, row.material_name))
            return materials
        except DatabaseMaterialNotFound as folderMaterialsError:
            raise folderMaterialsError
        except Exception as ex:
            print("Unable to get folder materials:", ex)
            raise DatabaseMaterialNotFound(error=ex)

    def _pathList(self, path : str) -> list[str]:
        # Strip any leading "/"
        if len(path) > 0 and path[0] == '/':
            path = path[1:]

        return path.split('/')

    def _createPathRecursive(self, cursor : Cursor, libraryIndex : int, parentIndex : int, pathIndex : int, pathList : list[str]) -> int:
        newId = 0

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

        index = pathIndex + 1
        if index >= len(pathList):
            return newId
        return self._createPathRecursive(cursor, libraryIndex, newId, index, pathList)

    def _createPath(self, cursor : Cursor, libraryIndex : int, path : str) -> int:
        newId = 0

        pathList = self._pathList(path)
        if len(pathList) > 0:
            return self._createPathRecursive(cursor, libraryIndex, 0, 0, pathList)
        return newId

    def _getPath(self, cursor : Cursor, folderId : int) -> str:
        path = ""
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
        cursor = self._cursor()
        try:
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
            library = self._getLibrary(cursor, row.library_id)

            inherits = self._getInherits(cursor, uuid)
            for inherit in inherits:
                model.addInheritance(inherit)

            properties = self._getModelProperties(cursor, uuid)
            for property in properties:
                model.addProperty(property)

            cursor.commit()
            return ModelObjectType(library.name, model)

        except DatabaseModelNotFound as notFound:
            cursor.rollback()
            # Rethrow
            raise notFound
        except Exception as ex:
            cursor.rollback()
            print("Unable to get model:", ex)
            raise DatabaseModelNotFound(error=ex)

    def createModel(self, libraryName: str, path: str, model: Materials.Model) -> None:
        cursor = self._cursor()
        try:
            libraryIndex = self._findLibrary(cursor, libraryName)
            if libraryIndex > 0:
                self._createModel(cursor, libraryIndex, path, model)
            cursor.commit()
        except DatabaseModelExistsError as exists:
            cursor.rollback()
            # Rethrow
            raise exists
        except Exception as ex:
            cursor.rollback()
            # print("Exception '{}'".format(type(ex).__name__))
            print("Unable to create model:", ex)
            raise DatabaseModelCreationError(error=ex)

    def updateModel(self, libraryName: str, path: str, model: Materials.Model) -> None:
        cursor = self._cursor()
        try:
            libraryIndex = self._findWriteableLibrary(cursor, libraryName)
            self._updateModel(cursor, libraryIndex, path, model)
            cursor.commit()
        except DatabaseModelNotFound as exists:
            cursor.rollback()
            # Rethrow
            raise exists
        except DatabaseLibraryReadOnlyError as ro:
            cursor.rollback()
            raise ro
        except Exception as ex:
            cursor.rollback()
            print("Unable to update model:", ex)
            raise DatabaseModelUpdateError(error=ex)
        
    def setModelPath(self, libraryName: str, path: str, uuid: str) -> None:
        cursor = self._cursor()
        try:
            libraryIndex = self._findWriteableLibrary(cursor, libraryName)
            self._updateModelPath(cursor, libraryIndex, path, uuid)
            cursor.commit()
        except DatabaseModelNotFound as exists:
            cursor.rollback()
            # Rethrow
            raise exists
        except DatabaseLibraryReadOnlyError as ro:
            cursor.rollback()
            raise ro
        except Exception as ex:
            cursor.rollback()
            print("Unable to update model:", ex)
            raise DatabaseModelUpdateError(error=ex)

    def renameModel(self, libraryName: str, name: str, uuid: str) -> None:
        cursor = self._cursor()
        try:
            libraryIndex = self._findWriteableLibrary(cursor, libraryName)
            self._updateModelName(cursor, libraryIndex, name, uuid)
            cursor.commit()
        except DatabaseModelNotFound as exists:
            cursor.rollback()
            # Rethrow
            raise exists
        except DatabaseLibraryReadOnlyError as ro:
            cursor.rollback()
            raise ro
        except Exception as ex:
            cursor.rollback()
            print("Unable to update model:", ex)
            raise DatabaseModelUpdateError(error=ex)

    def moveModel(self, libraryName: str, path: str, uuid: str) -> None:
        cursor = self._cursor()
        try:
            libraryIndex = self._findWriteableLibrary(cursor, libraryName)
            self._moveModel(cursor, libraryIndex, path, uuid)
            cursor.commit()
        except DatabaseModelNotFound as exists:
            cursor.rollback()
            # Rethrow
            raise exists
        except DatabaseLibraryReadOnlyError as ro:
            cursor.rollback()
            raise ro
        except Exception as ex:
            cursor.rollback()
            print("Unable to update model:", ex)
            raise DatabaseModelUpdateError(error=ex)

    def removeModel(self, uuid: str) -> None:
        cursor = self._cursor()
        try:
            cursor.execute("SELECT library_id FROM model WHERE model_id = ?", uuid)
            row = cursor.fetchone()
            if not row:
                raise DatabaseLibraryNotFound()
            else:
                oldLibraryIndex = row.library_id

                # Is the library read only?
                if oldLibraryIndex > 0:
                    if self._isReadOnly(cursor, oldLibraryIndex):
                        raise DatabaseLibraryReadOnlyError()
                else:
                    raise DatabaseLibraryNotFound()
                
                cursor.execute("DELETE FROM model WHERE model_id = ?", uuid)
                if cursor.rowcount < 0:
                    raise DatabaseDeleteError()
            cursor.commit()
        except DatabaseLibraryNotFound as noLibrary:
            cursor.rollback()
            raise noLibrary
        except DatabaseDeleteError as delError:
            cursor.rollback()
            raise delError
        except Exception as ex:
            cursor.rollback()
            print(f"Unable to remove model: {ex}")
            raise DatabaseDeleteError(error=ex)

    def _createModelPropertyColumn(self, cursor : Cursor, propertyId : int, property : Materials.ModelProperty, libraryIndex : int) -> None:
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

    def _createModelProperty(self, cursor : Cursor, modelUUID : str, property : Materials.ModelProperty, libraryIndex : int) -> None:
        if property.Inherited:
            return

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
                self._createModelPropertyColumn(cursor, propertyId, column, libraryIndex)

    def _updateModelProperty(self,cursor : Cursor,  modelUUID : str, property : Materials.ModelProperty, libraryIndex : int) -> None:
        if property.Inherited:
            return

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
                self._createModelPropertyColumn(cursor, propertyId, column, libraryIndex)

    def _createModel(self, cursor : Cursor, libraryIndex : int, path : str, model : Materials.Model) -> None:
        pathIndex = self._createPath(cursor, libraryIndex, path)
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
                self._createInheritance(cursor, model.UUID, inherit, libraryIndex)

            for property in model.Properties.values():
                self._createModelProperty(cursor, model.UUID, property, libraryIndex)

    def _updateModelPath(self, cursor : Cursor, libraryIndex : int, path : str, uuid : str) -> None:
        pathIndex = self._createPath(cursor, libraryIndex, path)
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

    def _updateModelName(self, cursor : Cursor, libraryIndex : int, name : str, uuid : str) -> None:
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

    def _moveModel(self, cursor : Cursor, libraryIndex : int, path : str, uuid : str) -> None:
        pathIndex = self._createPath(cursor, libraryIndex, path)
        cursor.execute("SELECT library_id, folder_id FROM model WHERE model_id = ?", uuid)
        row = cursor.fetchone()
        if not row:
            raise DatabaseModelNotFound()
        else:
            oldLibraryIndex = row.library_id
            oldPathIndex = row.folder_id

            # We already know the new library is writeable, but what about the old library?
            if oldLibraryIndex > 0:
                if self._isReadOnly(cursor, oldLibraryIndex):
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

    def _updateModel(self, cursor : Cursor, libraryIndex : int, path : str, model : Materials.Model) -> None:
        pathIndex = self._createPath(cursor, libraryIndex, path)
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
                self._createInheritance(cursor, model.UUID, inherit, libraryIndex)

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
                self._updateModelProperty(cursor, model.UUID, property, libraryIndex)

    def _createInheritance(self, cursor : Cursor, modelUUID : str, inheritUUID : str, libraryIndex : int) -> None:
        cursor.execute("SELECT model_inheritance_id FROM model_inheritance WHERE model_id "
                                "= ? AND inherits_id = ?", modelUUID, inheritUUID)
        row = cursor.fetchone()
        if not row:
            # Mass updates may insert models out of sequence creating a foreign key violation
            self._foreignKeysIgnore(cursor)
            cursor.execute("INSERT INTO model_inheritance (model_id, inherits_id) "
                                    "VALUES (?, ?)", modelUUID, inheritUUID)
            self._foreignKeysRestore(cursor)

    def _getInherits(self, cursor : Cursor, uuid : str) -> list[str]:
        inherits = []
        cursor.execute("SELECT inherits_id FROM model_inheritance "
                                    "WHERE model_id = ?",
                       uuid)
        rows = cursor.fetchall()
        for row in rows:
            inherits.append(row.inherits_id)

        return inherits

    def _getModelColumns(self, cursor : Cursor, uuid : str, propertyName : str) -> list[Materials.ModelProperty]:
        columns = []
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

    def _getModelProperties(self, cursor : Cursor, uuid : str) -> list[Materials.ModelProperty]:
        properties = []
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
            columns = self._getModelColumns(cursor, uuid, property.Name)
            for column in columns:
                property.addColumn(column)

        return properties

    #
    # Material methods
    #

    def getMaterial(self, uuid: str) -> MaterialObjectType:
        cursor = self._cursor()
        try:
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

            library = self._getLibrary(cursor, row.library_id)

            tags = self._getTags(cursor, uuid)
            for tag in tags:
                material.addTag(tag)

            for model in self._getMaterialModels(cursor, uuid, True):
                material.addPhysicalModel(model)

            for model in self._getMaterialModels(cursor, uuid, False):
                material.addAppearanceModel(model)

            # self.addModelProperties(material)

            # The actual properties are set by the model. We just need to load the values
            properties = self._getMaterialProperties(cursor, uuid)
            for name, value in properties.items():
                material.setValue(name, value)

            return MaterialObjectType(library.name, material)

        except DatabaseMaterialNotFound as notFound:
            cursor.rollback()
            # Rethrow
            raise notFound
        except Exception as ex:
            cursor.rollback()
            print("Unable to get material:", ex)
            raise DatabaseMaterialNotFound(error=ex)

    def createMaterial(self, libraryName: str, path: str, material: Materials.Material) -> None:
        cursor = self._cursor()
        try:
            libraryIndex = self._findLibrary(cursor, libraryName)
            if libraryIndex > 0:
                self._createMaterial(cursor, libraryIndex, path, material)
            cursor.commit()
        except DatabaseMaterialExistsError as exists:
            cursor.rollback()
            # Rethrow
            raise exists
        except Exception as ex:
            cursor.rollback()
            print("Unable to create material:", ex)
            raise DatabaseMaterialCreationError(error=ex)
        
    def updateMaterial(self, libraryName: str, path: str, material: Materials.Material) -> None:
        cursor = self._cursor()
        try:
            libraryIndex = self._findLibrary(cursor, libraryName)
            if libraryIndex > 0:
                self._updateMaterial(cursor, libraryIndex, path, material)
            cursor.commit()
        except DatabaseMaterialNotFound as notFound:
            cursor.rollback()
            # Rethrow
            raise notFound
        except Exception as ex:
            cursor.rollback()
            print("Unable to update material:", ex)
            raise DatabaseMaterialCreationError(error=ex)

    def setMaterialPath(self, libraryName: str, path: str, uuid: str) -> None:
        pass

    def renameMaterial(self, libraryName: str, name: str, uuid: str) -> None:
        pass

    def moveMaterial(self, libraryName: str, path: str, uuid: str) -> None:
        pass

    def removeMaterial(self, uuid: str) -> None:
        pass

    def materialExists(self, libraryName : str, uuid: str) -> bool:
        cursor = self._cursor()
        try:
            if not libraryName:
                cursor.execute("SELECT COUNT(*) FROM material WHERE material_id = ?",
                            uuid)
            else:
                cursor.execute("SELECT COUNT(*) FROM material m, library l "
                                "WHERE l.library_name = ? AND m.material_id = ? AND l.library_id = m.library_id",
                            libraryName, uuid)

            rows = cursor.fetchone()
            if rows:
                return (rows[0] > 0)
        except Exception as ex:
            pass
        return False

    def _createTag(self, cursor : Cursor, materialUUID : str, tag : str, libraryIndex : int) -> None:
        tagId = 0
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

    def _updateTags(self, cursor : Cursor, materialUUID : str, tags : list[str], libraryIndex : int) -> None:
        currentTags = self._getTags(cursor, materialUUID)
        deleteTags = []
        for tag in currentTags:
            if tag not in tags:
                deleteTags.append(tag)

        # Remove deleted tags
        for tag in deleteTags:
            tagId = 0
            cursor.execute("SELECT material_tag_id FROM material_tag WHERE material_tag_name = ?", tag)
            row = cursor.fetchone()
            if row:
                tagId = row.material_tag_id

                cursor.execute("DELETE FROM material_tag_mapping "
                                        "WHERE material_id = ? AND material_tag_id = ?", materialUUID, tagId)

        # add new tags
        for tag in tags:
            if tag not in currentTags:
                self._createTag(cursor, materialUUID, tag, libraryIndex)

    def _getTags(self, cursor : Cursor, uuid : str) -> list[str]:
        tags = []
        cursor.execute("SELECT t.material_tag_name FROM material_tag t, material_tag_mapping m "
                          "WHERE m.material_id = ? AND m.material_tag_id = t.material_tag_id",
                       uuid)

        rows = cursor.fetchall()
        for row in rows:
            tags.append(row.material_tag_name)

        return tags

    def _createMaterialModel(self, cursor : Cursor, materialUUID : str, modelUUID : str, libraryIndex : int) -> None:
        cursor.execute("INSERT IGNORE INTO material_models (material_id, model_id) "
                                "VALUES (?, ?)", materialUUID, modelUUID)

    def _updateMaterialModels(self, cursor : Cursor, materialUUID : str, physicalUUIDs : list[str], appearanceUUIDs : list[str], libraryIndex : int) -> None:
        deleteModels = []
        physical = self._getMaterialModels(cursor, materialUUID, True)
        for model in physical:
            if not model in physicalUUIDs:
                deleteModels.append(model)
        appearance = self._getMaterialModels(cursor, materialUUID, False)
        for model in appearance:
            if not model in appearanceUUIDs:
                deleteModels.append(model)

        # Delete removed models
        for model in deleteModels:
            cursor.execute("DELETE FROM material_models "
                    "WHERE material_id = ? AND model_id = ?", materialUUID, model)

        # Add new models
        for model in physicalUUIDs:
            if model not in physical:
                self._createMaterialModel(cursor, materialUUID, model, libraryIndex)
        for model in appearanceUUIDs:
            if model not in appearance:
                self._createMaterialModel(cursor, materialUUID, model, libraryIndex)

    def _createMaterialPropertyValue(self, cursor : Cursor, materialUUID : str, name : str, type : str) -> int:
        cursor.execute("INSERT INTO material_property_value (material_id, material_property_name, material_property_type) "
                    "VALUES (?, ?, ?)",
                    materialUUID, name, type)

        return self._lastId(cursor)

    def _updateMaterialPropertyValue(self, cursor : Cursor, materialUUID : str, name : str, type : str) -> int:
        cursor.execute("SELECT material_property_value_id FROM material_property_value "
                          "WHERE material_id = ? AND material_property_name= ?",
                       materialUUID, name)

        row = cursor.fetchone()
        if row:
            value_id = row.material_property_value_id
        else:
            value_id = self._createMaterialPropertyValue(cursor, materialUUID, name, type)
        return value_id

    def _deleteMaterialPropertyValue(self, cursor : Cursor, materialUUID : str, name : str) -> None:
        cursor.execute("DELETE FROM material_property_value "
                          "WHERE material_id = ? AND material_property_name= ?",
                       materialUUID, name)

    def _createStringValue(self, cursor : Cursor, materialUUID : str, name : str, type : str, value : str) -> None:
        if value is not None:
            value_id = self._createMaterialPropertyValue(cursor, materialUUID, name, type)
            cursor.execute("INSERT INTO material_property_string_value "
                        " (material_property_value_id, material_property_value)"
                        " VALUES (?, ?)",
                        value_id, value)

    def _updateStringValue(self, cursor : Cursor, materialUUID : str, name : str, type : str, value : str) -> None:
        if value is not None:
            value_id = self._updateMaterialPropertyValue(cursor, materialUUID, name, type)
            cursor.execute("SELECT material_property_string_value_id FROM material_property_string_value "
                            "WHERE material_property_value_id = ?",
                        value_id)

            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE material_property_string_value "
                            " SET material_property_value = ?"
                            " WHERE material_property_value_id = ?",
                            value, value_id)
            else:
                cursor.execute("INSERT INTO material_property_string_value "
                            " (material_property_value_id, material_property_value)"
                            " VALUES (?, ?)",
                            value_id, value)
        else:
            self._deleteMaterialPropertyValue(cursor, materialUUID, name)

    def _createLongStringValue(self, cursor : Cursor, materialUUID : str, name : str, type : str, value : str) -> None:
        if value is not None:
            value_id = self._createMaterialPropertyValue(cursor, materialUUID, name, type)
            cursor.execute("INSERT INTO material_property_long_string_value "
                        " (material_property_value_id, material_property_value)"
                        " VALUES (?, ?)",
                        value_id, value)

    def _updateLongStringValue(self, cursor : Cursor, materialUUID : str, name : str, type : str, value : str) -> None:
        if value is not None:
            value_id = self._updateMaterialPropertyValue(cursor, materialUUID, name, type)
            cursor.execute("SELECT material_property_long_string_value_id FROM material_property_long_string_value "
                            "WHERE material_property_value_id = ?",
                        value_id)

            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE material_property_long_string_value "
                            " SET material_property_value = ?"
                            " WHERE material_property_value_id = ?",
                            value, value_id)
            else:
                cursor.execute("INSERT INTO material_property_long_string_value "
                            " (material_property_value_id, material_property_value)"
                            " VALUES (?, ?)",
                            value_id, value)
        else:
            self._deleteMaterialPropertyValue(cursor, materialUUID, name)

    def _createListValue(self, cursor : Cursor, materialUUID : str, name : str, type : str, list : list[str]) -> None:
        if list is not None:
            value_id = self._createMaterialPropertyValue(cursor, materialUUID, name, type)

            for entry in list:
                cursor.execute("INSERT INTO material_property_string_value "
                            " (material_property_value_id, material_property_value)"
                            " VALUES (?, ?)",
                            value_id, entry)


    def _updateListValue(self, cursor : Cursor, materialUUID : str, name : str, type : str, list : list[str]) -> None:
        value_id = self._updateMaterialPropertyValue(cursor, materialUUID, name, type)

        # Remove and re-add any list entries
        cursor.execute("DELETE FROM material_property_string_value "
                        "WHERE material_property_value_id = ?",
                        value_id)
        for entry in list:
            cursor.execute("INSERT INTO material_property_string_value "
                        " (material_property_value_id, material_property_value)"
                        " VALUES (?, ?)",
                        value_id, entry)


    def _createLongListValue(self, cursor : Cursor, materialUUID : str, name : str, type : str, list : list[str]) -> None:
        if list is not None:
            value_id = self._createMaterialPropertyValue(cursor, materialUUID, name, type)

            for entry in list:
                cursor.execute("INSERT INTO material_property_long_string_value "
                            " (material_property_value_id, material_property_value)"
                            " VALUES (?, ?)",
                            value_id, entry)

    def _updateLongListValue(self, cursor : Cursor, materialUUID : str, name : str, type : str, list : list[str]) -> None:
        value_id = self._updateMaterialPropertyValue(cursor, materialUUID, name, type)

        # Remove and re-add any list entries
        cursor.execute("DELETE FROM material_property_long_string_value "
                        "WHERE material_property_value_id = ?",
                        value_id)
        for entry in list:
            cursor.execute("INSERT INTO material_property_long_string_value "
                        " (material_property_value_id, material_property_value)"
                        " VALUES (?, ?)",
                        value_id, entry)

    def _createArrayValue3D(self, cursor : Cursor, materialUUID : str, name : str, propertyType : str, array : Materials.Array3D) -> None:
        if array is not None:
            value_id = self._createMaterialPropertyValue(cursor, materialUUID, name, propertyType)

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
                        if columnValue is None:
                            value = None
                        else:
                            value = columnValue.UserString
                        cursor.execute("INSERT INTO material_property_array_value "
                                    " (material_property_value_id, material_property_value_row, "
                                    "  material_property_value_column, material_property_value_depth, "
                                    "  material_property_value_depth_rows, material_property_value)"
                                    " VALUES (?, ?, ?, ?, ?, ?)",
                                    value_id, row, column, depth, array.getRows(depth), value)

    def _createArrayValue2D(self, cursor : Cursor, materialUUID : str, name : str, propertyType : str, array : Materials.Array2D) -> None:
        if array is not None:
            value_id = self._createMaterialPropertyValue(cursor, materialUUID, name, propertyType)

            cursor.execute("INSERT INTO material_property_array_description "
                        " (material_property_value_id, material_property_array_rows, "
                        "  material_property_array_columns)"
                        " VALUES (?, ?, ?)",
                        value_id, array.Rows, array.Columns)
            arrayData = array.Array
            for row, rowValue in enumerate(arrayData):
                for column, columnValue in enumerate(rowValue):
                    if columnValue is None:
                        value = None
                    elif hasattr(columnValue, "UserString"):
                        value = columnValue.UserString
                    else:
                        value = columnValue
                    cursor.execute("INSERT INTO material_property_array_value "
                                " (material_property_value_id, material_property_value_row, "
                                "  material_property_value_column, material_property_value)"
                                " VALUES (?, ?, ?, ?)",
                                value_id, row, column, value)

    def _createMaterialProperty(self, cursor : Cursor, materialUUID : str, material : Materials.Material, property : Materials.MaterialProperty) -> None:
        if property.Type == "2DArray" or \
           property.Type == "3DArray":
            if material.hasPhysicalProperty(property.Name):
                array = material.getPhysicalValue(property.Name)
            else:
                array = material.getAppearanceValue(property.Name)
            if array.Dimensions == 2:
                self._createArrayValue2D(cursor, materialUUID, property.Name, property.Type, array)
            else:
                self._createArrayValue3D(cursor, materialUUID, property.Name, property.Type, array)
        elif property.Type == "List" or \
           property.Type == "FileList":
            self._createListValue(cursor, materialUUID, property.Name, property.Type, property.Value)
        elif property.Type == "ImageList":
            self._createLongListValue(cursor, materialUUID, property.Name, property.Type, property.Value)
        elif property.Type == "Quantity":
            if property.Empty:
                return
            self._createStringValue(cursor, materialUUID, property.Name, property.Type, property.Value.UserString)
        elif property.Type == "SVG" or \
            property.Type == "Image":
            self._createLongStringValue(cursor, materialUUID, property.Name, property.Type, property.Value)
        else:
            self._createStringValue(cursor, materialUUID, property.Name, property.Type, property.Value)

    def _updateMaterialProperty(self, cursor : Cursor, materialUUID : str, material : Materials.Material, property : Materials.MaterialProperty) -> None:
        # if property.Type == "2DArray" or \
        #    property.Type == "3DArray":
        #     if material.hasPhysicalProperty(property.Name):
        #         array = material.getPhysicalValue(property.Name)
        #     else:
        #         array = material.getAppearanceValue(property.Name)
        #     if array.Dimensions == 2:
        #         self._createArrayValue2D(materialUUID, property.Name, property.Type, array, libraryIndex)
        #     else:
        #         self._createArrayValue3D(materialUUID, property.Name, property.Type, array, libraryIndex)
        if property.Type == "List" or \
           property.Type == "FileList":
            self._updateListValue(cursor, materialUUID, property.Name, property.Type, property.Value)
        elif property.Type == "ImageList":
            self._updateLongListValue(cursor, materialUUID, property.Name, property.Type, property.Value)
        elif property.Type == "Quantity":
            if property.Empty:
                return
            self._updateStringValue(cursor, materialUUID, property.Name, property.Type, property.Value.UserString)
        elif property.Type == "SVG" or \
            property.Type == "Image":
            self._updateLongStringValue(cursor, materialUUID, property.Name, property.Type, property.Value)
        else:
            self._updateStringValue(cursor, materialUUID, property.Name, property.Type, property.Value)

    def _updateMaterialProperties(self, cursor : Cursor, materialUUID : str, material : Materials.Material) -> None:
        properties = self._getMaterialProperties(cursor, materialUUID)
        newProperties = material.PropertyObjects
        deleteProperties = []
        for name, value in properties.items():
            if name not in newProperties:
                deleteProperties.append(name)

        for name in deleteProperties:
            cursor.execute("DELETE FROM material_property_value "
                        "WHERE material_id = ? AND material_property_name = ?", materialUUID, name)

        for property in material.PropertyObjects.values():
            self._updateMaterialProperty(cursor, material.UUID, material, property)

    def _createMaterial(self, cursor : Cursor, libraryIndex : int, path : str, material : Materials.Material):
        pathIndex = self._createPath(cursor, libraryIndex, path)

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
                self._createTag(cursor, material.UUID, tag, libraryIndex)

            # print("{} Physical models".format(len(material.PhysicalModels)))
            for model in material.PhysicalModels:
                self._createMaterialModel(cursor, material.UUID, model, libraryIndex)

            # print("{} Appearance models".format(len(material.AppearanceModels)))
            for model in material.AppearanceModels:
                self._createMaterialModel(cursor, material.UUID, model, libraryIndex)

            # print("{} Properties".format(len(material.PropertyObjects)))
            for property in material.PropertyObjects.values():
                self._createMaterialProperty(cursor, material.UUID, material, property)

    def _updateMaterial(self, cursor : Cursor, libraryIndex : int, path : str, material : Materials.Material):
        pathIndex = self._createPath(cursor, libraryIndex, path)

        cursor.execute("SELECT material_id FROM material WHERE material_id = ?",
                       material.UUID)
        row = cursor.fetchone()
        if not row:
            raise DatabaseMaterialNotFound()
        else:
            # Mass updates may insert models out of sequence creating a foreign key
            # violation
            self._foreignKeysIgnore(cursor)

            cursor.execute("UPDATE material SET "
                            "library_id = ?, folder_id = ?, "
                            "material_name = ?, material_author = ?, material_license = ?, "
                            "material_parent_uuid = ?, material_description = ?, material_url = ?, "
                            "material_reference = ? "
                            "WHERE material_id = ?",
                            libraryIndex,
                            (None if pathIndex == 0 else pathIndex),
                            material.Name,
                            material.Author,
                            material.License,
                            material.Parent,
                            material.Description,
                            material.URL,
                            material.Reference,
                            material.UUID,
                            )

            self._updateTags(cursor, material.UUID, material.Tags, libraryIndex)
            self._updateMaterialModels(cursor, material.UUID, material.PhysicalModels, material.AppearanceModels, libraryIndex)
            self._updateMaterialProperties(cursor, material.UUID, material)

    def _getMaterialModels(self, cursor : Cursor, uuid : str, isPhysical : bool) -> list[int]:
        models = []
        cursor.execute("SELECT m1.model_id FROM material_models m1, model m2 "
            "WHERE m1.material_id = ? AND m1.model_id = m2.model_id AND m2.model_type = ?",
                       uuid,
                       ("Physical" if isPhysical else "Appearance"))

        rows = cursor.fetchall()
        for row in rows:
            models.append(row.model_id)

        return models

    def _getMaterialPropertyStringValue(self, cursor : Cursor, materialPropertyValueId : int) -> str | None:
        cursor.execute("SELECT material_property_value "
                        "FROM material_property_string_value "
                        "WHERE material_property_value_id = ?",
                       materialPropertyValueId)
        row = cursor.fetchone()
        if not row:
            return None

        return row.material_property_value

    def _getMaterialPropertyLongStringValue(self, cursor : Cursor, materialPropertyValueId : int) -> str | None:
        cursor.execute("SELECT material_property_value "
                        "FROM material_property_long_string_value "
                        "WHERE material_property_value_id = ?",
                       materialPropertyValueId)
        row = cursor.fetchone()
        if not row:
            return None

        return row.material_property_value

    def _getMaterialPropertyListValue(self, cursor : Cursor, materialPropertyValueId : int) -> list[str]:
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

    def _getMaterialPropertyLongListValue(self, cursor : Cursor, materialPropertyValueId : int) -> list[str]:
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

    def _getMaterialPropertyArray2D(self, cursor : Cursor, materialPropertyValueId : int) -> Materials.Array2D:
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
            # print(f"row: {row.material_property_value_row} column: {row.material_property_value_column} value: {row.material_property_value}")
            array.setValue(row.material_property_value_row,
                            row.material_property_value_column,
                            row.material_property_value)

        return array

    def _getMaterialPropertyArray3D(self, cursor : Cursor, materialPropertyValueId : int) -> Materials.Array3D:
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

    def _getMaterialPropertyValue(self, cursor : Cursor, materialPropertyValueId : int, type : str) -> Any:
        if type == "2DArray":
            return self._getMaterialPropertyArray2D(cursor, materialPropertyValueId)
        elif type == "3DArray":
            return self._getMaterialPropertyArray3D(cursor, materialPropertyValueId)
        elif type == "SVG" or \
           type == "Image":
            return self._getMaterialPropertyLongStringValue(cursor, materialPropertyValueId)
        elif type == "List" or \
           type == "FileList":
            return self._getMaterialPropertyListValue(cursor, materialPropertyValueId)
        elif type == "ImageList":
            return self._getMaterialPropertyLongListValue(cursor, materialPropertyValueId)

        return self._getMaterialPropertyStringValue(cursor, materialPropertyValueId)

    def _getMaterialProperties(self, cursor : Cursor, uuid : str) -> dict[str,str]:
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
            properties[key] = self._getMaterialPropertyValue(cursor, value[0], value[1])

        return properties
    
    def _copyMaterial(self, cursor : Cursor, destinationLibraryIndex : int, path : str, materialUuid : str) -> None:
        material = self.getMaterial(materialUuid)
        self._createMaterial(cursor, destinationLibraryIndex, path, material)

    #
    # Support methods
    #

    def _foreignKeysIgnore(self, cursor : Cursor) -> None:
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")

    def _foreignKeysRestore(self, cursor : Cursor) -> None:
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")
