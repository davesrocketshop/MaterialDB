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

import sqlite3
import Materials

from MaterialDB.Database import Database

class DatabaseSQLite(Database):
    """SQLite specific database interface"""

    def __init__(self, rootFolder):
        self._rootFolder = rootFolder
        # self._manager = Materials.MaterialManager()

    def create(self) -> None:
        """Create a new SQLite database"""
        pass

    def getConnection(self):
        # Check if the file exists
        exists = False

        # Connect
        connection = sqlite3.connect(self._rootFolder + "/Resources/db/Materials.db")

        # if the file didn't exist, create the tables
        if not exists:
            self._createTables(connection)

        return connection

    def _createTables(self, connection):
        cursor = connection.cursor()

        cursor.execute("""CREATE TABLE IF NOT EXISTS library
                       (library_id INTEGER PRIMARY KEY ASC, library_name, library_icon, library_read_only)""")

        # # cursor.execute("DROP TABLE IF EXISTS material")
        # cursor.execute("CREATE TABLE IF NOT EXISTS material (material_index INTEGER PRIMARY KEY ASC, manufacturer, material_name, uuid, type, density, units)")
        # cursor.execute("CREATE INDEX IF NOT EXISTS idx_material ON material(manufacturer, material_name, type)")

        # # cursor.execute("DROP TABLE IF EXISTS component")
        # cursor.execute("CREATE TABLE IF NOT EXISTS component (component_index INTEGER PRIMARY KEY ASC, manufacturer, part_number, description, material_index, mass, mass_units)")
        # cursor.execute("CREATE INDEX IF NOT EXISTS idx_component_manufacturer ON component(manufacturer)")

        # cursor.execute("DROP TABLE IF EXISTS tube_type")
        # cursor.execute("CREATE TABLE IF NOT EXISTS tube_type (tube_type_index INTEGER PRIMARY KEY ASC, type UNIQUE)")
        # cursor.execute("CREATE INDEX IF NOT EXISTS idx_tube_type_type ON tube_type(type)")
        # cursor.execute("""INSERT INTO tube_type(type)
        #                VALUES ('Body Tube'), ('Centering Ring'), ('Tube Coupler'), ('Engine Block'), ('Launch Lug'), ('Bulkhead')
        #                ON CONFLICT(type) DO NOTHING""")

        # # cursor.execute("DROP TABLE IF EXISTS body_tube")
        # cursor.execute("CREATE TABLE IF NOT EXISTS body_tube (body_tube_index INTEGER PRIMARY KEY ASC, component_index, tube_type_index, inner_diameter, inner_diameter_units, outer_diameter, outer_diameter_units, length, length_units)")
        # cursor.execute("CREATE INDEX IF NOT EXISTS idx_body_tube ON body_tube(component_index, tube_type_index)")

        # # cursor.execute("DROP TABLE IF EXISTS nose")
        # cursor.execute("""CREATE TABLE IF NOT EXISTS nose (nose_index INTEGER PRIMARY KEY ASC, component_index, shape, style, diameter, diameter_units,
        #     length, length_units, thickness, thickness_units, shoulder_diameter, shoulder_diameter_units, shoulder_length, shoulder_length_units)""")

        # # cursor.execute("DROP TABLE IF EXISTS transition")
        # cursor.execute("""CREATE TABLE IF NOT EXISTS transition (transition_index INTEGER PRIMARY KEY ASC, component_index, shape, style,
        #     fore_outside_diameter, fore_outside_diameter_units, fore_shoulder_diameter, fore_shoulder_diameter_units, fore_shoulder_length, fore_shoulder_length_units,
        #     aft_outside_diameter, aft_outside_diameter_units, aft_shoulder_diameter, aft_shoulder_diameter_units, aft_shoulder_length, aft_shoulder_length_units,
        #     length, length_units, thickness, thickness_units)""")

        # # cursor.execute("DROP TABLE IF EXISTS rail_button")
        # cursor.execute("""CREATE TABLE IF NOT EXISTS rail_button (rail_button_index INTEGER PRIMARY KEY ASC, component_index, finish, outer_diameter, outer_diameter_units,
        #         inner_diameter, inner_diameter_units, height, height_units, base_height, base_height_units, flange_height, flange_height_units, screw_height, screw_height_units,
        #         drag_coefficient, screw_mass, screw_mass_units, nut_mass, nut_mass_units, screw_diameter, screw_diameter_units, countersink_diameter, countersink_diameter_units, countersink_angle)""")

        # # cursor.execute("DROP TABLE IF EXISTS parachute")
        # cursor.execute("CREATE TABLE IF NOT EXISTS parachute (parachute_index INTEGER PRIMARY KEY ASC, component_index, line_material_index, sides, lines, diameter, diameter_units, line_length, line_length_units)")

        # # cursor.execute("DROP TABLE IF EXISTS streamer")
        # cursor.execute("CREATE TABLE IF NOT EXISTS streamer (streamer_index INTEGER PRIMARY KEY ASC, component_index, length, length_units, width, width_units, thickness, thickness_units)")

        connection.commit()

    def libraries(self) -> list:
        """Returns a list of libraries managed by this interface

        The list contains a series of tuples describing all libraries managed by
        this module. Each tuple containes the library name, and a boolean to indicate
        if it is a read only library."""

        libs = []
        connection = self.getConnection()
        cursor = connection.cursor()

        cursor.execute("""SELECT library_name, library_icon, library_read_only
                        FROM library""")

        rows = cursor.fetchall()
        for row in rows:
            libs.append((row["library_name"], row["library_icon"], row["library_read_only"]))
        return libs

    def createLibrary(self, name: str) -> None:
        """Create a new library

        Create a new library with the given name"""
        pass

    def renameLibrary(self, oldName: str, newName: str) -> None:
        """Rename an existing library

        Change the name of an existing library"""
        pass

    def removeLibrary(self, library: str) -> None:
        """Delete a library and its contents

        Deletes the library and any models or materials it contains"""
        pass
