######### DBConnect ####################
# Sets up a DB connection ##############
# Inherited by: DBQuery and DBWrite ####
########################################

import logging
import traceback
from typing import Union
import pyodbc

class DBConnect:
	"""
	Opens a SQL DB connection utilizing the credentials from the run-time user.
	The DB connection happens on class instantiation.

	DB connection status can be checked with DbClose()
	The DB conn can be closed with DbConnCheck()
	"""

	def __init__(self, logger: logging.Logger, odbcVer: int, server: str, db: str) -> None:
		self._logger = logger
		self._odbcVer = odbcVer
		self._server = server
		self._db = db
		self._msSqlConn, self._cursorMain = self.DbLogin() # Assign the reference to the db (mysqlConn), and the cursor

	# Create getters for fields
	@property
	def sqlConn(self):
		return self._msSqlConn
	
	@property
	def cursor(self):
		return self._cursorMain

	@property
	def server(self):
		return self._server
	
	@property
	def db(self):
		return self._db


	def DbLogin(self) -> Union[tuple[pyodbc.Connection, pyodbc.Cursor], int]:
		"""
		Configures a DB connection and logs in with the credentials of the user running the app
		The timeout for the DB connection attempt and the timeout for SQL queries are hard-coded in the try block

		Returns the connection and cursor object if successful.
		Returns an int (acting as an err code) if it fails.
		"""
		try:
			self._logger.debug(f"Opening connection to DB '{self._db}' on server '{self._server}'")
			sqlConn = pyodbc.connect(f'Driver=ODBC Driver {self._odbcVer} for SQL Server;'
									f'Server={self._server};'
									f'Database={self._db};'
									'Trusted_Connection=yes;',
									timeout=30) # this is the timeout for the database connection attempt

			sqlConn.timeout = 30 # This is the timeout for sql queries
			cursor = sqlConn.cursor()
		except pyodbc.InterfaceError as e:
			self._logger.error(f"Login Failed: Unable to establish a connection to database '{self._db}' on server '{self._server}' - {e}")
			self._logger.debug(traceback.format_exc())
			sqlConn = 1
			cursor = 1
		except pyodbc.OperationalError as e:
			self._logger.error(f"Login Failed - Possible connection attempt timeout: Unable to establish a connection to database '{self._db}' on server '{self._server}' - {e}")
			self._logger.debug(traceback.format_exc())
			sqlConn = 2
			cursor = 2
		except Exception as e:
			self._logger.error(f"Unable to establish a connection to database '{self._db}' on server '{self._server}' - {e}")
			self._logger.debug(traceback.format_exc())
			sqlConn = 3
			cursor = 3
		
		return sqlConn, cursor # Return the reference to the db (sqlConn), and the cursor
		
	def DbClose(self) -> None:
		"""
		Closes the DB connection and cursor.
		Resets the connection and cursor objects to an int (0)

		No return value.
		"""
		if self.DbConnCheck() == True:
			self._logger.debug(f"Closing connection to DB '{self._db}' on server '{self._server}'")
			self._cursorMain.close()
			self._msSqlConn.close()
			# Reset _cursorMain and _msSqlConn so the data type becomes an int, this will make the DbConnCheck return false after DbClose is called
			self._msSqlConn = 0
			self._cursorMain = 0

	def DbConnCheck(self) -> bool:
		"""
		Checks if there is a current DB connection open.

		Returns a True/False
		"""
		# The conn and cursor objects will only be an int if there was an error during the DB setup, or if DbClose() was called
		if type(self._cursorMain) == int or type(self._msSqlConn) == int:
			return False
		else:
			return True


if __name__ == "__main__":

	from log_config import LogConfig
	logSetup = LogConfig('db_connect_Test', 20000000, 5, logLevel=logging.DEBUG)
	testLogger = logSetup.ConfigureLogger()

	instance = DBConnect(testLogger, 18, 'server.domain', 'BESReporting')

	print("Cursor Object", instance.cursor)
	print("SQL Conn Object", instance.sqlConn)

	print("Cursor Object TYPE", type(instance.cursor))
	print("SQL Conn Object TYPE", type(instance.sqlConn))

	instance.DbClose()