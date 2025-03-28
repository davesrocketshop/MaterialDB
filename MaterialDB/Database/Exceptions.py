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

class DatabaseCreationError(Exception):

    def __init__(self, error):
        self._error = error

class DatabaseTableCreationError(Exception):

    def __init__(self, error):
        self._error = error

class DatabaseConnectionError(Exception):

    def __init__(self, message="Unable to connect"):
        self._message = message

#---
#
# Library errors
#
#---

class DatabaseLibraryCreationError(Exception):

    def __init__(self, error):
        self._error = error

class DatabaseIconError(Exception):

    def __init__(self, msg="Unable to set icon", error=None):
        self._error = error
        self.msg = msg

    def __str__(self):
        if self._error is not None:
            return repr(self._error)
        return repr(self.msg)


class DatabaseLibraryNotFound(Exception):

    def __init__(self, msg="Library not found", error=None):
        self._error = error
        self.msg = msg

    def __str__(self):
        if self._error is not None:
            return repr(self._error)
        return repr(self.msg)

#---
#
# Model errors
#
#---

class DatabaseModelCreationError(Exception):

    def __init__(self, error):
        self._error = error

class DatabaseModelUpdateError(Exception):

    def __init__(self, error):
        self._error = error

class DatabaseModelExistsError(Exception):

    def __init__(self, error=None):
        self._error = error
        self.msg = "Model already exists"

    def __str__(self):
        if self._error is not None:
            return repr(self._error)
        return repr(self.msg)

class DatabaseModelNotFound(Exception):

    def __init__(self, error=None):
        self._error = error
        self.msg = "Model not found"

    def __str__(self):
        if self._error is not None:
            return repr(self._error)
        return repr(self.msg)

#---
#
# Material errors
#
#---

class DatabaseMaterialCreationError(Exception):

    def __init__(self, error):
        self._error = error

class DatabaseMaterialExistsError(Exception):

    def __init__(self, error=None):
        self._error = error
        self.msg = "Material already exists"

    def __str__(self):
        if self._error is not None:
            return repr(self._error)
        return repr(self.msg)

class DatabaseMaterialNotFound(Exception):

    def __init__(self, error=None):
        self._error = error
        self.msg = "Material not found"

    def __str__(self):
        if self._error is not None:
            return repr(self._error)
        return repr(self.msg)

#---
#
# Generic errors
#
#---

class DatabaseRenameError(Exception):

    def __init__(self, msg="Unable to rename object", error=None):
        self._error = error
        self.msg = msg

    def __str__(self):
        if self._error is not None:
            return repr(self._error)
        return repr(self.msg)

class DatabaseDeleteError(Exception):

    def __init__(self, msg="Unable to remove object", error=None):
        self._error = error
        self.msg = msg

    def __str__(self):
        if self._error is not None:
            return repr(self._error)
        return repr(self.msg)
