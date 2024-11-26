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

import pyodbc

import Materials

from DatabaseMySQL import DatabaseMySQL

class DatabaseMySQLCreate(DatabaseMySQL):

    def __init__(self):
        super().__init__()

        # See Resources/db/create_tables.sql
        self._tables = {
            "library" : """CREATE TABLE library (
                            library_id INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
                            library_name VARCHAR(512) NOT NULL UNIQUE,
                            library_icon BLOB,
                            library_read_only TINYINT(1) NOT NULL DEFAULT 0
                        )""",
            "folder" :  """CREATE TABLE folder (
                            folder_id INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
                            folder_name VARCHAR(512) NOT NULL,
                            library_id INTEGER NOT NULL,
                            parent_id INTEGER,
                            FOREIGN KEY (library_id)
                                REFERENCES library(library_id)
                                ON DELETE CASCADE,
                            FOREIGN KEY (parent_id)
                                REFERENCES folder(folder_id)
                        )""",
            "model" :   """CREATE TABLE model (
                            model_id CHAR(36) NOT NULL PRIMARY KEY,
                            library_id INTEGER NOT NULL,
                            folder_id INTEGER,
                            model_type ENUM('Physical', 'Appearance') NOT NULL,
                            model_name VARCHAR(255) NOT NULL,
                            model_url VARCHAR(255),
                            model_description TEXT,
                            model_doi VARCHAR(255),
                            FOREIGN KEY (library_id)
                                REFERENCES library(library_id)
                                ON DELETE CASCADE,
                            FOREIGN KEY (folder_id)
                                REFERENCES folder(folder_id)
                                ON DELETE CASCADE
                        )""",
            "model_inheritance" : """CREATE TABLE model_inheritance (
                            model_inheritance_id INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
                            model_id CHAR(36) NOT NULL,
                            inherits_id CHAR(36) NOT NULL,
                            FOREIGN KEY (model_id)
                                REFERENCES model(model_id)
                                ON DELETE CASCADE,
                            FOREIGN KEY (inherits_id)
                                REFERENCES model(model_id)
                                ON DELETE RESTRICT
                        )""",
            "model_property" : """CREATE TABLE model_property (
                            model_property_id INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
                            model_id CHAR(36) NOT NULL,
                            model_property_name VARCHAR(255) NOT NULL,
                            model_property_display_name VARCHAR(255) NOT NULL,
                            model_property_type VARCHAR(255) NOT NULL,
                            model_property_units VARCHAR(255) NOT NULL,
                            model_property_url VARCHAR(255) NOT NULL,
                            model_property_description TEXT,
                            FOREIGN KEY (model_id)
                                REFERENCES model(model_id)
                                ON DELETE CASCADE
                        )""",
            "model_property_column" : """CREATE TABLE model_property_column (
                            model_property_column_id INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
                            model_property_id INTEGER NOT NULL,
                            model_property_name VARCHAR(255) NOT NULL,
                            model_property_display_name VARCHAR(255) NOT NULL,
                            model_property_type VARCHAR(255) NOT NULL,
                            model_property_units VARCHAR(255) NOT NULL,
                            model_property_url VARCHAR(255) NOT NULL,
                            model_property_description TEXT,
                            FOREIGN KEY (model_property_id)
                                REFERENCES model_property(model_property_id)
                                ON DELETE CASCADE
                        )""",
            "material" : """CREATE TABLE material (
                            material_id CHAR(36) NOT NULL PRIMARY KEY,
                            library_id INTEGER NOT NULL,
                            folder_id INTEGER,
                            material_name VARCHAR(255) NOT NULL,
                            material_author VARCHAR(255),
                            material_license VARCHAR(255),
                            material_parent_uuid CHAR(36),
                            material_description TEXT,
                            material_url VARCHAR(255),
                            material_reference VARCHAR(255),
                            FOREIGN KEY (library_id)
                                REFERENCES library(library_id)
                                ON DELETE CASCADE,
                            FOREIGN KEY (folder_id)
                                REFERENCES folder(folder_id)
                                ON DELETE CASCADE,
                            FOREIGN KEY (material_parent_uuid)
                                REFERENCES material(material_id)
                                ON DELETE RESTRICT
                        )""",
            "material_tag" : """CREATE TABLE material_tag (
                            material_tag_id INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
                            material_tag_name VARCHAR(255) NOT NULL UNIQUE KEY
                        )""",
            "material_tag_mapping" : """CREATE TABLE material_tag_mapping (
                        material_id CHAR(36) NOT NULL INDEX,
                        material_tag_id INTEGER NOT NULL INDEX,
                        FOREIGN KEY (material_id)
                            REFERENCES material(material_id)
                            ON DELETE CASCADE,
                        FOREIGN KEY (material_tag_id)
                            REFERENCES material_tag(material_tag_id)
                            ON DELETE CASCADE
                    )""",
            "material_models" : """CREATE TABLE material_models (
                        material_id CHAR(36) NOT NULL INDEX,
                        model_id CHAR(36) NOT NULL,
                        FOREIGN KEY (material_id)
                            REFERENCES material(material_id)
                            ON DELETE CASCADE,
                        FOREIGN KEY (model_id)
                            REFERENCES model(model_id)
                            ON DELETE CASCADE
                    )""",
            "material_property_value" : """CREATE TABLE material_property_value (
                        material_property_value_id INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
                        material_id CHAR(36) NOT NULL,
                        material_property_name VARCHAR(255) NOT NULL,
                        material_property_value TEXT NOT NULL,
                        FOREIGN KEY (material_id)
                            REFERENCES material(material_id)
                            ON DELETE CASCADE
                    )"""
        }

    def checkIfExists(self):
        try:
            self._connect()
            cursor = self._connection.cursor()

            cursor.execute("USE {}".format(self._database))
            cursor.commit()
            return True
        except Exception as err:
            print(err)
            print("Database {} does not exist.".format(self._database))
        return False

    def dropTables(self):
        try:
            self._connect()
            cursor = self._connection.cursor()

            # Foreign key checks are turned off to avoid requiring a specific sequence
            cursor.execute("SET FOREIGN_KEY_CHECKS=0")

            for table in self._tables:
                cursor.execute("DROP TABLE IF EXISTS {}".format(table))

            cursor.execute("SET FOREIGN_KEY_CHECKS=1")
            cursor.commit()
        except Exception as err:
            print(err)

    def createTables(self):
        try:
            self._connect()
            cursor = self._connection.cursor()

            for table in self._tables:
                cursor.execute(self._tables[table])
            cursor.commit()
        except Exception as err:
            print(err)

    def createDatabase(self):
        try:
            self._connect()
            cursor = self._connection.cursor()

            cursor.execute(
                "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(self._database))
            cursor.commit()
        except Exception as err:
            print("Failed creating database: {}".format(err))

