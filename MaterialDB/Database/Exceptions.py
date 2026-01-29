# ***************************************************************************
# *   Copyright (c) 2021-2024 David Carter <dcarter@davidcarter.ca>         *
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
"""Class for database exceptions"""

__author__ = "David Carter"
__url__ = "https://www.davesrocketshop.com"

class DatabaseBaseError(Exception):

    def __init__(self, message, error):
        self._error = error
        self._message = message

    def __str__(self):
        if self._error is not None:
            return repr(self._error)
        return repr(self._message)

class DatabaseCreationError(DatabaseBaseError):

    def __init__(self, message="Unable to create database", error=None):
        super().__init__(message, error)

class DatabaseTableCreationError(DatabaseBaseError):

    def __init__(self, message="Unable to create tables", error=None):
        super().__init__(message, error)

class DatabaseConnectionError(DatabaseBaseError):

    def __init__(self, message="Unable to connect", error=None):
        super().__init__(message, error)

#---
#
# Library errors
#
#---

class DatabaseLibraryCreationError(DatabaseBaseError):

    def __init__(self, message="Unable to create library", error=None):
        super().__init__(message, error)

class DatabaseIconError(DatabaseBaseError):

    def __init__(self, message="Unable to set icon", error=None):
        super().__init__(message, error)


class DatabaseLibraryNotFound(DatabaseBaseError):

    def __init__(self, message="Library not found", error=None):
        super().__init__(message, error)

class DatabaseLibraryReadOnlyError(DatabaseBaseError):

    def __init__(self, message="Library is read only", error=None):
        super().__init__(message, error)

#---
#
# Folder errors
#
#---

class DatabaseFolderCreationError(DatabaseBaseError):

    def __init__(self, message = "Unable to create folder", error=None):
        super().__init__(message, error)

#---
#
# Model errors
#
#---

class DatabaseModelCreationError(DatabaseBaseError):

    def __init__(self, message = "Unable to create model", error=None):
        super().__init__(message, error)

class DatabaseModelUpdateError(DatabaseBaseError):

    def __init__(self, message = "Unable to update model", error=None):
        super().__init__(message, error)

class DatabaseModelExistsError(DatabaseBaseError):

    def __init__(self, message = "Model already exists", error=None):
        super().__init__(message, error)

class DatabaseModelNotFound(DatabaseBaseError):

    def __init__(self, message = "Model not found", error=None):
        super().__init__(message, error)

#---
#
# Material errors
#
#---

class DatabaseMaterialCreationError(DatabaseBaseError):

    def __init__(self, message = "Unable to create Material", error=None):
        super().__init__(message, error)

class DatabaseMaterialUpdateError(DatabaseBaseError):

    def __init__(self, message = "Unable to update Material", error=None):
        super().__init__(message, error)

class DatabaseMaterialExistsError(DatabaseBaseError):

    def __init__(self, message = "Material already exists", error=None):
        super().__init__(message, error)

class DatabaseMaterialNotFound(DatabaseBaseError):

    def __init__(self, message = "Material not found", error=None):
        super().__init__(message, error)

#---
#
# Generic errors
#
#---

class DatabaseRenameError(DatabaseBaseError):

    def __init__(self, message="Unable to rename object", error=None):
        super().__init__(message, error)

class DatabaseDeleteError(DatabaseBaseError):

    def __init__(self, message="Unable to remove object", error=None):
        super().__init__(message, error)
