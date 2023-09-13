import json
import os
from pathlib import Path

import cx_Oracle


class DBConnection:
    """Handler class to easily connect to the DB"""

    def __init__(self, config_file: str = "../db.conf", root_folder: str = None):
        """Load the configuration parameters from the given file.

        Args:
            config_file (str, optional): DB configuration file containing connection parameters.
        """
        self.root_folder =  root_folder
        try:
            if root_folder is None:
                config_path = Path(os.getcwd()) / config_file
            else:
                config_path = Path(root_folder) / config_file
            
            with open(config_path, "r") as f:
                self.config = json.load(f)
                self.connection = None
        except FileNotFoundError:
            with open(config_file ,"r") as f:
                self.config=json.load(f)
                self.connection = None

    def connect(self) -> cx_Oracle.Connection:
        """Connect to the DB, using the parameters specified in the config file.

        Returns:
            cx_Oracle.Connection: Instance of the DB connection.
        """
        dsn = f"""(DESCRIPTION =
            (ADDRESS = (PROTOCOL = TCP)(HOST = {self.config["host"]})(PORT = {self.config["port"]}))
            (CONNECT_DATA =
            (SERVER = DEDICATED)
            (SERVICE_NAME = {self.config["service"]})))
        """

        self.connection = cx_Oracle.connect(
            user=self.config["user"],
            password=self.config["pass"],
            dsn=dsn,
            encoding="UTF-8",
        )

        return self.connection

    def disconnect(self):
        """Disconnect from the DB"""
        self.connection.close()
        self.connection = None

    def get_cursor(self) -> cx_Oracle.Cursor:
        """Get the cursor of the connection if active, otherwise connect first.

        Returns:
            cx_Oracle.Cursor: DB connection cursor needed to run queries.
        """
        if self.connection is not None:
            return self.connection.cursor()

        return self.connect().cursor()
