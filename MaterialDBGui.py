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

import FreeCADGui

from MaterialDB.UI.Commands.CmdTest import CmdTest
from MaterialDB.UI.Commands.CmdCreate import CmdCreate
from MaterialDB.UI.Commands.CmdManageUsers import CmdManageUsers
from MaterialDB.UI.Commands.CmdMigrate import CmdMigrate

FreeCADGui.addCommand('MaterialDB_Test', CmdTest())
FreeCADGui.addCommand('MaterialDB_CreateDatabase', CmdCreate())
FreeCADGui.addCommand('MaterialDB_Migrate', CmdMigrate())
FreeCADGui.addCommand('MaterialDB_ManageUsers', CmdManageUsers())
