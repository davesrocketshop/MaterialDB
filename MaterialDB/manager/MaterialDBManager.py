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

import Materials

from MaterialAPI.MaterialManagerExternal import MaterialManagerExternal, \
    MaterialLibraryType, MaterialLibraryObjectType, ModelObjectType, \
    MaterialObjectType

from MaterialDB.Database.DatabaseMySQL import DatabaseMySQL
from MaterialDB.Database.Exceptions import DatabaseLibraryCreationError, \
    DatabaseModelCreationError, DatabaseMaterialCreationError, \
    DatabaseModelExistsError, DatabaseMaterialExistsError, \
    DatabaseModelNotFound, DatabaseMaterialNotFound

class MaterialsDBManager(MaterialManagerExternal):

    def __init__(self):
        self._db = DatabaseMySQL()

    def libraries(self) -> list[MaterialLibraryType]:
        # print("libraries()")
        return self._db.getLibraries()

    def modelLibraries(self) -> list[MaterialLibraryType]:
        # print("modelLibraries()")
        return self._db.getModelLibraries()

    def materialLibraries(self) -> list[MaterialLibraryType]:
        # print("materialLibraries()")
        return self._db.getMaterialLibraries()

    def getLibrary(self, libraryName: str) -> MaterialLibraryType:
        # print("getLibrary('{}')".format(libraryName))
        return self._db.getLibrary(libraryName)

    def createLibrary(self, libraryName: str, icon: bytes, readOnly: bool) -> None:
        # print("createLibrary('{}', '{}', '{}')".format(libraryName, icon, readOnly))
        self._db.createLibrary(libraryName, icon, readOnly)

    def renameLibrary(self, oldName: str, newName: str) -> None:
        # print("renameLibrary('{}', '{}')".format(oldName, newName))
        self._db.renameLibrary(oldName, newName)

    def changeIcon(self, libraryName: str, icon: bytes) -> None:
        # print("changeIcon('{}', '{}')".format(libraryName, icon))
        self._db.changeIcon(libraryName, icon)

    def removeLibrary(self, libraryName: str) -> None:
        # print("removeLibrary('{}')".format(libraryName))
        self._db.removeLibrary(libraryName)

    def libraryModels(self, libraryName: str) -> list[MaterialLibraryObjectType]:
        # print("libraryModels('{}')".format(libraryName))
        return self._db.libraryModels(libraryName)

    def libraryMaterials(self, libraryName: str,
                         filter: Materials.MaterialFilter = None,
                         options: Materials.MaterialFilterOptions = None) -> list[MaterialLibraryObjectType]:
        # print("libraryMaterials('{}')".format(libraryName))
        return self._db.libraryMaterials(libraryName)

    def libraryFolders(self, libraryName: str) -> list[str]:
        print("libraryFolders('{}')".format(libraryName))
        return self._db.libraryFolders(libraryName)

    #
    # Folder methods
    #

    def createFolder(self, libraryName: str, path: str) -> None:
        print("createFolder('{0}', '{1}')".format(libraryName, path))
        self._db.createFolder(libraryName, path)

    def renameFolder(self, libraryName: str, oldPath: str, newPath: str) -> None:
        print("renameFolder('{0}', '{1}', '{2}')".format(libraryName, oldPath, newPath))
        self._db.renameFolder(libraryName, oldPath, newPath)

    def deleteRecursive(self, libraryName: str, path: str) -> None:
        print("deleteRecursive('{0}', '{1}')".format(libraryName, path))
        self._db.deleteRecursive(libraryName, path)

    #
    # Model methods
    #

    def getModel(self, uuid: str) -> ModelObjectType:
        # print("getModel('{}')".format(uuid))
        return self._db.getModel(uuid)

    def addModel(self, libraryName: str, path: str, model: Materials.Model) -> None:
        # print("addModel('{}', '{}', '{}')".format(libraryName, path, model.Name))
        self._db.createModel(libraryName, path, model)

    def migrateModel(self, libraryName: str, path: str, model: Materials.Model) -> None:
        # print("migrateModel('{}', '{}', '{}')".format(libraryName, path, model.Name))
        try:
            self._db.createModel(libraryName, path, model)
        except DatabaseModelExistsError:
            # If it exists we just ignore
            pass

    def updateModel(self, libraryName: str, path: str, model: Materials.Model) -> None:
        # print("updateModel('{}', '{}', '{}')".format(libraryName, path, model.Name))
        self._db.updateModel(libraryName, path, model)

    def setModelPath(self, libraryName: str, path: str, uuid: str) -> None:
        # print("setModelPath('{}', '{}', '{}')".format(libraryName, path, uuid))
        self._db.setModelPath(libraryName, path, uuid)

    def renameModel(self, libraryName: str, name: str, uuid: str) -> None:
        # print("renameModel('{}', '{}', '{}')".format(libraryName, name, uuid))
        self._db.renameModel(libraryName, name, uuid)

    def moveModel(self, libraryName: str, path: str, uuid: str) -> None:
        # print("moveModel('{}', '{}', '{}')".format(libraryName, path, uuid))
        self._db.moveModel(libraryName, path, uuid)

    def removeModel(self, uuid: str) -> None:
        # print("removeModel('{}')".format(uuid))
        self.removeModel(uuid)

    #
    # Material methods
    #

    def getMaterial(self, uuid: str) -> MaterialObjectType:
        # print("getMaterial('{}')".format(uuid))
        return self._db.getMaterial(uuid)

    def addMaterial(self, libraryName: str, path: str, material: Materials.Material) -> None:
        # print("addMaterial('{}', '{}', '{}')".format(libraryName, path, material.Name))
        self._db.createMaterial(libraryName, path, material)

    def migrateMaterial(self, libraryName: str, path: str, material: Materials.Material) -> None:
        # print("migrateMaterial('{}', '{}', '{}')".format(libraryName, path, material.Name))
        try:
            self._db.createMaterial(libraryName, path, material)
        except DatabaseMaterialExistsError:
            # If it exists we just ignore
            print("Ignore DatabaseModelExistsError error")
            pass

    def updateMaterial(self, libraryName: str, path: str, material: Materials.Material) -> None:
        print("updateMaterial('{}', '{}', '{}')".format(libraryName, path, material.Name))
        self._db.updateMaterial(libraryName, path, material)

    def setMaterialPath(self, libraryName: str, path: str, uuid: str) -> None:
        print("setMaterialPath('{}', '{}', '{}')".format(libraryName, path, uuid))
        self._db.setMaterialPath(libraryName, path, uuid)

    def renameMaterial(self, libraryName: str, name: str, uuid: str) -> None:
        print("renameMaterial('{}', '{}', '{}')".format(libraryName, name, uuid))
        self._db.renameMaterial(libraryName, name, uuid)

    def moveMaterial(self, libraryName: str, path: str, uuid: str) -> None:
        print("moveMaterial('{}', '{}', '{}')".format(libraryName, path, uuid))
        self._db.moveMaterial(libraryName, path, uuid)

    def removeMaterial(self, uuid: str) -> None:
        print("removeMaterial('{}')".format(uuid))
        self._db.removeMaterial(uuid)
