############## DBWrite ###########################################################
# Runs SQL transactions                 										##
# Inherits DBConnect and opens a new db connection when DBWrite is instantiated ##
# Reserved for WRITE SQL transactions            								##
# SQL queries that are READ ONLY need to go in the DBQuery class			    ##
##################################################################################

import logging
import traceback
import pyodbc
from db_connect import DBConnect

class DBWrite(DBConnect):
	"""
	Used to execute SQL transactions.
	Inherits DBConnect and opens a DB connection on class instantiation.
	"""
	def __init__(self, logger: logging.Logger, odbcVer: int, server: str, db: str, app: str) -> None:
		super().__init__(logger, odbcVer, server, db) # instantiates DBConnect and inherits all methods and properties from DBConnect
		self._app = app
		
	# Create getters for fields
	@property
	def app(self):
		return self._app
	
	def MarkDeleted(self, transaction: str) -> int:
		"""
		Executes a SQL transaction.
		Used for marking users as deleted in the BFC and BFI databases

		Return values:
		0 = Success
		1 = Pyodbc programming err
		2 = Pyodbc operational err
		3 = Other exception
		"""
		try:
			self._logger.info(f"Executing SQL transaction to mark users as deleted in '{self._db}' on '{self._server}'")
			self._cursorMain.execute(transaction)
			self._msSqlConn.commit()
			result = 0
		except pyodbc.ProgrammingError as e:
			self._logger.error(f"SQL Syntax Error: Failed transaction with DB '{self._db}' on server '{self._server}' for {self._app} - {e}")
			self._logger.debug(traceback.format_exc())
			result = 1
		except pyodbc.OperationalError as e:
			self._logger.error(f"Possible query time out: Failed transaction with DB '{self._db}' on server '{self._server}' for {self._app} - {e}")
			self._logger.debug(traceback.format_exc())
			result = 2
		except Exception as e:
			self._logger.error(f"Failed transaction with DB '{self._db}' on server '{self._server}' for {self._app} - {e}")
			self._logger.debug(traceback.format_exc())
			result = 3
		
		return result


if __name__ == "__main__":

	from log_config import LogConfig
	logSetup = LogConfig('db_query_Test', 20000000, 5, logLevel=logging.DEBUG)
	testLogger = logSetup.ConfigureLogger()
	
	instance = DBWrite(logger=testLogger, odbcVer=18, server='server.domain', db='BESReporting', app="Test App")

	print("Cursor Object", instance.cursor)
	print("SQL Conn Object", instance.sqlConn)
	print("App:", instance.app)


	instance.DbClose()

	help(DBWrite.MarkDeleted)