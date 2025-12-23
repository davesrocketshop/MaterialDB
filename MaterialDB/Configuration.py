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

import FreeCAD

DEFAULT_INSTANCE = "Default"

def getPreferencesLocation(instance : str | None = DEFAULT_INSTANCE) -> str:
    # Set parameter location
    if not instance:
        return f"User parameter:BaseApp/Preferences/Mod/MaterialDB/"
    return f"User parameter:BaseApp/Preferences/Mod/MaterialDB/Instance/{instance}"

def getInstancePreferencesLocation() -> str:
    return "User parameter:BaseApp/Preferences/Mod/MaterialDB/Instance"

def getDatabaseName(instance : str = DEFAULT_INSTANCE) -> str:
    prefs = getPreferencesLocation(instance)
    return FreeCAD.ParamGet(prefs).GetString("Database", "material")

def getInstances() -> list[str]:
    instances = []
    prefs = getInstancePreferencesLocation()
    param = FreeCAD.ParamGet(prefs)
    for group in param.GetGroups():
        print(group)
        instances.append(group)

    if DEFAULT_INSTANCE not in instances:
        instances.insert(0, DEFAULT_INSTANCE)
    return instances

def renameInstance(oldInstance : str, newInstance : str) -> None:
    prefs = getInstancePreferencesLocation()
    param = FreeCAD.ParamGet(prefs)
    param.RenameGrp(oldInstance, newInstance)
