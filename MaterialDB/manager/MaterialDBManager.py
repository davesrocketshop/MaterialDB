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
from MaterialDB.Configuration import getInstances, DEFAULT_INSTANCE

class MaterialsDBManager(MaterialManagerExternal):

    def __init__(self):
        self._db = {}

    def getDB(self, instance : str = DEFAULT_INSTANCE) -> DatabaseMySQL:
        if instance not in self._db or not self._db[instance]:
            self._db[instance] = DatabaseMySQL(instance)
        return self._db[instance]

    def instances(self) -> list[str]:
        return getInstances()

    def libraries(self, instance : str = DEFAULT_INSTANCE) -> list[MaterialLibraryType]:
        # print("libraries()")
        return self.getDB(instance).getLibraries()

    def modelLibraries(self, instance : str = DEFAULT_INSTANCE) -> list[MaterialLibraryType]:
        # print("modelLibraries()")
        return self.getDB(instance).getModelLibraries()

    def materialLibraries(self, instance : str = DEFAULT_INSTANCE) -> list[MaterialLibraryType]:
        # print("materialLibraries()")
        return self.getDB(instance).getMaterialLibraries()

    def getLibrary(self, libraryName: str, instance : str = DEFAULT_INSTANCE) -> MaterialLibraryType:
        # print("getLibrary('{}')".format(libraryName))
        return self.getDB(instance).getLibrary(libraryName)

    def createLibrary(self, libraryName: str, icon: bytes, readOnly: bool, instance : str = DEFAULT_INSTANCE) -> None:
        # print("createLibrary('{}', '{}', '{}')".format(libraryName, icon, readOnly))
        self.getDB(instance).createLibrary(libraryName, icon, readOnly)

    def renameLibrary(self, oldName: str, newName: str, instance : str = DEFAULT_INSTANCE) -> None:
        # print("renameLibrary('{}', '{}')".format(oldName, newName))
        self.getDB(instance).renameLibrary(oldName, newName)

    def changeIcon(self, libraryName: str, icon: bytes, instance : str = DEFAULT_INSTANCE) -> None:
        # print("changeIcon('{}', '{}')".format(libraryName, icon))
        self.getDB(instance).changeIcon(libraryName, icon)

    def removeLibrary(self, libraryName: str, instance : str = DEFAULT_INSTANCE) -> None:
        # print("removeLibrary('{}')".format(libraryName))
        self.getDB(instance).removeLibrary(libraryName)

    def libraryModels(self, libraryName: str, instance : str = DEFAULT_INSTANCE) -> list[MaterialLibraryObjectType]:
        # print("libraryModels('{}')".format(libraryName))
        return self.getDB(instance).libraryModels(libraryName)

    def libraryMaterials(self, libraryName: str,
                         filter: Materials.MaterialFilter = None,
                         options: Materials.MaterialFilterOptions = None,
                         instance : str = DEFAULT_INSTANCE) -> list[MaterialLibraryObjectType]:
        # print("libraryMaterials('{}')".format(libraryName))
        return self.getDB(instance).libraryMaterials(libraryName)

    def libraryFolders(self, libraryName: str, instance : str = DEFAULT_INSTANCE) -> list[str]:
        print("libraryFolders('{}')".format(libraryName))
        return self.getDB(instance).libraryFolders(libraryName)

    #
    # Folder methods
    #

    def createFolder(self, libraryName: str, path: str, instance : str = DEFAULT_INSTANCE) -> None:
        print("createFolder('{0}', '{1}')".format(libraryName, path))
        self.getDB(instance).createFolder(libraryName, path)

    def renameFolder(self, libraryName: str, oldPath: str, newPath: str, instance : str = DEFAULT_INSTANCE) -> None:
        print("renameFolder('{0}', '{1}', '{2}')".format(libraryName, oldPath, newPath))
        self.getDB(instance).renameFolder(libraryName, oldPath, newPath)

    def deleteRecursive(self, libraryName: str, path: str, instance : str = DEFAULT_INSTANCE) -> None:
        print("deleteRecursive('{0}', '{1}')".format(libraryName, path))
        self.getDB(instance).deleteRecursive(libraryName, path)

    #
    # Model methods
    #

    def getModel(self, uuid: str, instance : str = DEFAULT_INSTANCE) -> ModelObjectType:
        # print("getModel('{}')".format(uuid))
        return self.getDB(instance).getModel(uuid)

    def addModel(self, libraryName: str, path: str, model: Materials.Model, instance : str = DEFAULT_INSTANCE) -> None:
        # print("addModel('{}', '{}', '{}')".format(libraryName, path, model.Name))
        self.getDB(instance).createModel(libraryName, path, model)

    def migrateModel(self, libraryName: str, path: str, model: Materials.Model, instance : str = DEFAULT_INSTANCE) -> None:
        # print("migrateModel('{}', '{}', '{}')".format(libraryName, path, model.Name))
        try:
            self.getDB(instance).createModel(libraryName, path, model)
        except DatabaseModelExistsError:
            # If it exists we just ignore
            pass

    def updateModel(self, libraryName: str, path: str, model: Materials.Model, instance : str = DEFAULT_INSTANCE) -> None:
        # print("updateModel('{}', '{}', '{}')".format(libraryName, path, model.Name))
        self.getDB(instance).updateModel(libraryName, path, model)

    def setModelPath(self, libraryName: str, path: str, uuid: str, instance : str = DEFAULT_INSTANCE) -> None:
        # print("setModelPath('{}', '{}', '{}')".format(libraryName, path, uuid))
        self.getDB(instance).setModelPath(libraryName, path, uuid)

    def renameModel(self, libraryName: str, name: str, uuid: str, instance : str = DEFAULT_INSTANCE) -> None:
        # print("renameModel('{}', '{}', '{}')".format(libraryName, name, uuid))
        self.getDB(instance).renameModel(libraryName, name, uuid)

    def moveModel(self, libraryName: str, path: str, uuid: str, instance : str = DEFAULT_INSTANCE) -> None:
        # print("moveModel('{}', '{}', '{}')".format(libraryName, path, uuid))
        self.getDB(instance).moveModel(libraryName, path, uuid)

    def removeModel(self, uuid: str, instance : str = DEFAULT_INSTANCE) -> None:
        # print("removeModel('{}')".format(uuid))
        self.removeModel(uuid)

    #
    # Material methods
    #

    def getMaterial(self, uuid: str, instance : str = DEFAULT_INSTANCE) -> MaterialObjectType:
        # print("getMaterial('{}')".format(uuid))
        return self.getDB(instance).getMaterial(uuid)

    def addMaterial(self, libraryName: str, path: str, material: Materials.Material, instance : str = DEFAULT_INSTANCE) -> None:
        # print("addMaterial('{}', '{}', '{}')".format(libraryName, path, material.Name))
        self.getDB(instance).createMaterial(libraryName, path, material)

    def migrateMaterial(self, libraryName: str, path: str, material: Materials.Material, instance : str = DEFAULT_INSTANCE) -> None:
        # print("migrateMaterial('{}', '{}', '{}')".format(libraryName, path, material.Name))
        try:
            self.getDB(instance).createMaterial(libraryName, path, material)
        except DatabaseMaterialExistsError:
            # If it exists we just ignore
            print("Ignore DatabaseModelExistsError error")
            pass

    def updateMaterial(self, libraryName: str, path: str, material: Materials.Material, instance : str = DEFAULT_INSTANCE) -> None:
        print("updateMaterial('{}', '{}', '{}')".format(libraryName, path, material.Name))
        self.getDB(instance).updateMaterial(libraryName, path, material)

    def setMaterialPath(self, libraryName: str, path: str, uuid: str, instance : str = DEFAULT_INSTANCE) -> None:
        print("setMaterialPath('{}', '{}', '{}')".format(libraryName, path, uuid))
        self.getDB(instance).setMaterialPath(libraryName, path, uuid)

    def renameMaterial(self, libraryName: str, name: str, uuid: str, instance : str = DEFAULT_INSTANCE) -> None:
        print("renameMaterial('{}', '{}', '{}')".format(libraryName, name, uuid))
        self.getDB(instance).renameMaterial(libraryName, name, uuid)

    def moveMaterial(self, libraryName: str, path: str, uuid: str, instance : str = DEFAULT_INSTANCE) -> None:
        print("moveMaterial('{}', '{}', '{}')".format(libraryName, path, uuid))
        self.getDB(instance).moveMaterial(libraryName, path, uuid)

    def removeMaterial(self, uuid: str, instance : str = DEFAULT_INSTANCE) -> None:
        print("removeMaterial('{}')".format(uuid))
        self.getDB(instance).removeMaterial(uuid)
