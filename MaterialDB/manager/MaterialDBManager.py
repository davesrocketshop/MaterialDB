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

from MaterialAPI.MaterialManagerExternal import MaterialManagerExternal

from MaterialDB.Database.DatabaseMySQL import DatabaseMySQL

class MaterialsDBManager(MaterialManagerExternal):

    def __init__(self):
        self._db = DatabaseMySQL()

    def libraries(self) -> list:
        return self._db.getLibraries()

    def createLibrary(self, name: str, icon: str) -> None:
        pass

    def renameLibrary(self, oldName: str, newName: str) -> None:
        pass

    def changeIcon(self, icon: str) -> None:
        pass

    def removeLibrary(self, library: str) -> None:
        pass

    def libraryModels(self, library: str) -> list:
        pass

    def libraryMaterials(self, library: str) -> list:
        pass

    #
    # Model methods
    #

    def getModel(self, uuid: str) -> Materials.Model:
        pass

    def addModel(self, library: str, path: str, model: Materials.Model) -> None:
        pass

    def setModelPath(self, library: str, path: str, model: Materials.Model) -> None:
        pass

    def renameModel(self, library: str, name: str, model: Materials.Model) -> None:
        pass

    def moveModel(self, library: str, path: str, model: Materials.Model) -> None:
        pass

    def removeModel(self, model: Materials.Model) -> None:
        pass

    #
    # Material methods
    #

    def getMaterial(self, uuid: str) -> Materials.Material:
        pass

    def addMaterial(self, library: str, path: str, material: Materials.Material) -> None:
        pass

    def setMaterialPath(self, library: str, path: str, material: Materials.Material) -> None:
        pass

    def renameMaterial(self, library: str, name: str, material: Materials.Material) -> None:
        pass

    def moveMaterial(self, library: str, path: str, material: Materials.Material) -> None:
        pass

    def removeMaterial(self, material: Materials.Material) -> None:
        pass
