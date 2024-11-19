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

from API.RemoteMaterials import RemoteMaterials

class MaterialsDBInterface(RemoteMaterials):

    def APIVersion(cls):
        return (1,0,0)

    def libraries(self):
        return []

    def createLibrary(self, name):
        pass

    def renameLibrary(self, oldName, newName):
        pass

    def removeLibrary(self, oldName, newName):
        pass

    def libraryModels(self, library):
        return []

    def libraryMaterials(self, library):
        return []

    def getModel(self, uuid):
        pass

    def addModel(self, library, path, model):
        pass

    def setModelPath(self, library, path, model):
        pass

    def renameModel(self, library, name, model):
        pass

    def removeModel(self, model):
        pass

    def getMaterial(self, uuid):
        pass

    def addMaterial(self, library, path, material):
        pass

    def setMaterialPath(self, library, path, material):
        pass

    def renameMaterial(self, library, name, material):
        pass

    def removeMaterial(self, material):
        pass
