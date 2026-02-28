import os
import sqlite3


class QuerySteelDb():
    """
    Database query interface for AISC Steel Section Database (V15).

    This class provides methods to query and retrieve steel section properties from the 
    AISC Steel Section Database (V15). It manages database connections and formats 
    section property data.

    The database contains comprehensive steel section data including geometric and 
    structural properties for various steel shapes (W-shapes, channels, angles, etc.).

    Attributes:
        table (str): Name of the database table containing AISC data ('AISC_SSDB_V15').
        headers (list[str]): Column headers mapping database fields to property names.
        units (list[str]): Units corresponding to each property in headers.
        path (str): File path to the SQLite database (Data.db).
        connection: SQLite database connection object.
        cursor: SQLite database cursor for executing queries.
    """

    def __init__(self):
        """
        Initialize the QuerySteelDb instance.

        Sets up the database table name, property headers, units for each property,
        and constructs the path to the SQLite database file located in the same 
        directory as this module.
        """
        # Database table name containing AISC steel section data
        self.table: str = 'AISC_SSDB_V15'
        # Property names corresponding to each database column (parallel to self.units)
        self.headers: list[str] = [
            'Type', 'EDI_Std_Nomenclature', 'AISC_Manual_Label', 'T_F', 'W', 'A', 'd', 'ddet',
            'Ht', 'h1', 'OD', 'bf', 'bfdet', 'B1', 'b2', 'ID', 'tw', 'twdet', 'twdet_over_2',
            'tf', 'tfdet', 't1', 'tnom', 'tdes', 'kdes', 'kdet', 'k1', 'x', 'y', 'eo', 'xp',
            'yp', 'bf_over_2tf', 'b_over_t', 'b_over_tdes', 'h_over_tw', 'h_over_tdes', 'D_over_t',
            'Ix', 'Zx', 'Sx', 'rx', 'Iy', 'Zy', 'Sy', 'ry', 'Iz', 'rz', 'Sz', 'J', 'Cw', 'C', 'Wno',
            'Sw1', 'Sw2', 'Sw3', 'Qf', 'Qw', 'ro', 'H', 'tana', 'Iw', 'zA', 'zB', 'zC', 'wA', 'wB',
            'wC', 'SwA', 'SwB', 'SwC', 'SzA', 'SzB', 'SzC', 'rts', 'ho', 'PA', 'PA2', 'PB', 'PC',
            'PD', 'T', 'WGi', 'WGo'
        ]
        # Units for each property in self.headers (parallel list - indices must match)
        self.units: list[str] = [
            '[-]', '[-]', '[-]', '[-]', '[lb/ft]', '[in^2]', '[in]', '[in]', '[in]', '[in]', '[in]',
            '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]',
            '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[-]',
            '[-]', '[-]', '[-]', '[-]', '[-]', '[in^4]', '[in^3]', '[in^3]', '[in]', '[in^4]', '[in^3]',
            '[in^3]', '[in]', '[in^4]', '[in]', '[in^3]', '[in^4]', '[in^6]', '[in^3]', '[in^2]',
            '[in^4]', '[in^4]', '[in^4]', '[in^3]', '[in^3]', '[in]', '[-]', '[-]', '[in^4]', '[in]',
            '[in]', '[in]', '[in]', '[in]', '[in]', '[in^3]', '[in^3]', '[in^3]', '[in^3]', '[in^3]',
            '[in^3]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]'
        ]
        # Construct path to SQLite database file in the same directory as this module
        self.path: str = os.path.join(os.path.dirname(__file__), 'Data.db')

    def connect(self) -> None:
        """Establish a connection to the SQLite database.

        Creates a connection object and cursor for executing database queries.
        The database file is located at the path specified by :attr:`self.path`.
        """
        # Establish SQLite connection to the database file
        self.connection = sqlite3.connect(self.path)
        # Create cursor object for executing SQL queries
        self.cursor = self.connection.cursor()

    def disconnect(self) -> None:
        """Commit changes and close the database connection.

        Commits any pending transactions and closes the connection to the database.
        Should be called after all queries are complete.
        """
        # Save any pending database changes
        self.connection.commit()
        # Close the database connection
        self.connection.close()

    def format_records(self, records: list[tuple[str]], query: str) -> dict[str, list[str]]:
        """Format database records into a standardized dictionary structure.

        Converts raw database records into a dictionary mapping property names to 
        `[value, unit]` pairs. Handles special formatting for type and label queries 
        versus detailed property queries.

        Args:
            records (list[tuple[str]]): List of tuples containing database query results.
            query (str): The type of query executed (e.g., ``'get_aisc_manual_labels'``, ``'get_section_properties'``).

        Returns:
            dict[str, list[str]]: Dictionary mapping property names to [value, unit] pairs.
        """        # For label/type queries, return the label/type mapped to itself (no separate unit needed)
        if query in ['get_aisc_manual_labels', 'get_aisc_manual_types']:
            return {record[0]: [record[0], record[0]] for record in records}
        # For property queries, return each property with its corresponding value and unit
        else:
            return {k: [v, u] for k, v, u in zip(self.headers, records[0], self.units)}

    def return_records(self, records: list[tuple[str]] | None, Query: str) -> dict[str, list[str]]:
        """Return formatted records or a placeholder if no records are found.

        Wraps :meth:`format_records` to handle the case when no database records are
        returned. Returns a standardized "No Records Found" response if the query
        yields no results.

        Args:
            records (list[tuple[str]] | None): List of database records or None if no records found.
            Query (str): The type of query executed.

        Returns:
            dict[str, list[str]]: Formatted dictionary with property data or "No Records Found" message.
        """        # Return a placeholder message if no records were found in the database
        if records == None:
            val: str = 'No Records Found'
            return ({val: [val, val]})
        # Otherwise, format and return the retrieved records
        else:
            return (self.format_records(records, Query))

    def get_aisc_manual_types(self) -> dict[str, list[str]]:
        """Retrieve all available steel shape types from the database.

        Queries the database for distinct section types (e.g., W-shapes, Channels,
        Angles, etc.) available in the AISC Steel Section Database.

        Returns:
            dict[str, list[str]]: Dictionary mapping each shape type to itself in
            ``[type, type]`` format.
        """
        self.connect()
        # Query for distinct shape types (no parameters needed)
        query = """SELECT DISTINCT Type FROM {Table}""".format(
            Table=self.table)
        self.cursor.execute(query)
        records = self.cursor.fetchall()
        self.disconnect()
        return self.return_records(records, 'get_aisc_manual_types')

    def get_aisc_manual_labels(self, shape_type: str) -> dict[str, list[str]]:
        """Retrieve all AISC manual labels for a specified shape type.

        Queries the database for all standard AISC manual labels (e.g., W12x22,
        C8x11.5) that belong to the specified shape type.

        Args:
            shape_type (str): The steel shape type (e.g., 'W', 'C', 'L', 'T').

        Returns:
            dict[str, list[str]]: Dictionary mapping each AISC manual label to itself
            in ``[label, label]`` format.
        """
        self.connect()
        # Query for all labels of a specific shape type; (shape_type,) provides parameter binding
        query = """SELECT AISC_Manual_Label FROM {Table} WHERE Type = ?""".format(
            Table=self.table)
        self.cursor.execute(query, (shape_type,))
        records = self.cursor.fetchall()
        self.disconnect()
        return self.return_records(records, 'get_aisc_manual_labels')

    def get_section_properties(self, shape: str) -> dict[str, list[str]]:
        """Retrieve all geometric and structural properties for a specified steel section.

        Queries the database for complete section properties (moment of inertia,
        section modulus, radius of gyration, etc.) of a specific steel shape
        identified by its AISC manual label.

        Args:
            shape (str): The AISC manual label of the steel section (e.g., 'W12x22').

        Returns:
            dict[str, list[str]]: Dictionary mapping property names to [value, unit]
            pairs for the specified shape.
        """
        self.connect()
        # Query for all properties of a specific steel section (returns all columns)
        query = """SELECT * FROM {Table} WHERE AISC_Manual_Label = ?""".format(
            Table=self.table)
        self.cursor.execute(query, (shape,))
        records = self.cursor.fetchall()
        self.disconnect()
        return (self.return_records(records, 'get_section_properties'))

    def get_shapes(self, shape_type: str, shape_substring: str) -> dict[str, list[str]]:
        """Retrieve steel shapes matching a specified type and name pattern.

        Queries the database for AISC manual labels that match both the specified
        shape type and a substring pattern in their label name. Useful for searching
        for shapes with specific naming characteristics.

        Args:
            shape_type (str): The steel shape type (e.g., 'W', 'C', 'L', 'T').
            shape_substring (str): Substring pattern to match in AISC manual label (e.g., '12', 'x22').

        Returns:
            dict[str, list[str]]: Dictionary mapping matching AISC manual labels to
            themselves in ``[label, label]`` format.
        """
        self.connect()
        # Query for shapes matching type and substring pattern;
        # LIKE with % wildcards allows partial string matching (e.g., '%12%' matches any label containing '12')
        query = """SELECT AIC_Manual_Label FROM {Table} WHERE Type = ? AND AISC_Manual_Label LIKE ?""".format(
            Table=self.table)
        self.cursor.execute(query, (shape_type, '%'+shape_substring+'%'))
        records = self.cursor.fetchall()
        self.disconnect()
        return (self.return_records(records, 'get_shapes'))
