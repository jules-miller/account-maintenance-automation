############## DBQuery ###########################################################
# Runs SQL queries for gather user data 										##
# Inherits DBConnect and opens a new db connection when DBQuery is instantiated ##
# Reserved for READ ONLY SQL statements (queries) 								##
# SQL transactions that WRITE to a db need to go in the DBWrite class			##
##################################################################################

import logging
import traceback
import pyodbc
from db_connect import DBConnect

class DBQuery(DBConnect):
	"""
	Used to run READ-ONLY SQL queries.  
	Inherits DBConnect and opens a DB connection on class instantiation.
	"""

	def __init__(self, logger: logging.Logger, odbcVer: int, server: str, db: str, app: str) -> None:
		super().__init__(logger, odbcVer, server, db) # instantiates DBConnect and inherits all methods and properties from DBConnect
		self._app = app
		
	# Create getters for fields
	@property
	def app(self):
		return self._app
	
	# User query used for BFI and BFC to pull lists of de-duped inactive users
	def QueryInactiveUsers(self, qNotifyInact: str, qRemoveInact: str) -> dict:
		"""
		Runs two queries.
		Stores the results in a dictionary where each value is a list containing the query results.

		SQL query use cases: 
		- SqlConfig.bfcQueryNotify
		- SqlConfig.bfcQueryRemove
		- SqlConfig.bfiQueryNotify
		- SqlConfig.bfiQueryRemove
		"""
		try:
			self._logger.debug(f"Running SQL query to obtain inactive users who meet the notification threshold for {self._app} in db '{self._db}'")
			self._cursorMain.execute(qNotifyInact)
			
			inactiveNotifyUsers = []
			for i in self._cursorMain:
				inactiveNotifyUsers.append(i[0])

			self._logger.debug(f"Running SQL query to obtain inactive users who meet the removal threshold for {self._app} in db '{self._db}'")
			self._cursorMain.execute(qRemoveInact)
			
			inactiveRemoveUsers = []
			for i in self._cursorMain:
				inactiveRemoveUsers.append(i[0])

			result = {"inactiveNotifyUsers" : inactiveNotifyUsers, "inactiveRemoveUsers" : inactiveRemoveUsers}
		except pyodbc.ProgrammingError as e:
			self._logger.error(f"SQL Syntax Error: Failed to query inactive users with DB '{self._db}' on server '{self._server}' for {self._app} - {e}")
			self._logger.debug(traceback.format_exc())
			result = {"inactiveNotifyUsers" : ['SyntaxError'], "inactiveRemoveUsers" : ['SyntaxError']}
		except pyodbc.OperationalError as e:
			self._logger.error(f"Possible query time out: Failed to query inactive users with DB '{self._db}' on server '{self._server}' for {self._app} - {e}")
			self._logger.debug(traceback.format_exc())
			result = {"inactiveNotifyUsers" : ['TimeoutError'], "inactiveRemoveUsers" : ['TimeoutError']}	
		except Exception as e:
			self._logger.error(f"Failed to query inactive users with DB '{self._db}' on server '{self._server}' for {self._app} - {e}")
			self._logger.debug(traceback.format_exc())
			result = {"inactiveNotifyUsers" : ['QueryError'], "inactiveRemoveUsers" : ['QueryError']}
		
		return result
	
	# User query used for Web reports to pull lists of inactive and active users
	# This output needs to be de-duped 
	def QueryAllUsers(self, qNotifyInact: str, qRemoveInact: str, qNotifyAct: str, qRemoveAct: str) -> dict:
		"""
		Runs four queries.
		Stores the results in a dictionary where each value is a list containing the query results.

		SQL query use cases: 
		- SqlConfig.wrQuNotifActi
		- SqlConfig.wrQuRemovActi
		- SqlConfig.wrQuNotifInact
		- SqlConfig.wrQuRemovInact
		"""
		try:
			result = self.QueryInactiveUsers(qNotifyInact, qRemoveInact) # First, run QueryInactiveUsers() for the first two queries.

			self._logger.debug(f"Running SQL query to obtain active users who meet the notification threshold for {self._app} in db '{self._db}'")
			self._cursorMain.execute(qNotifyAct)
			
			activeNotifyUsers = []
			for i in self._cursorMain:
				activeNotifyUsers.append(i[0])
			
			self._logger.debug(f"Running SQL query to obtain active users who meet the removal threshold for {self._app} in db '{self._db}'")
			self._cursorMain.execute(qRemoveAct)
			
			activeRemoveUsers = []
			for i in self._cursorMain:
				activeRemoveUsers.append(i[0])

			# append to the dictionary result returned by QueryInactiveUsers()
			result["activeNotifyUsers"] = activeNotifyUsers
			result["activeRemoveUsers"] = activeRemoveUsers
		except pyodbc.ProgrammingError as e:
			self._logger.error(f"SQL Syntax Error: Failed to query users with DB '{self._db}' on server '{self._server}' for {self._app} - {e}")
			self._logger.debug(traceback.format_exc())
			result["activeNotifyUsers"] = ['SyntaxError']
			result["activeRemoveUsers"] = ['SyntaxError']
		except pyodbc.OperationalError as e:
			self._logger.error(f"Possible query time out: Failed to query users with DB '{self._db}' on server '{self._server}' for {self._app} - {e}")
			self._logger.debug(traceback.format_exc())
			result["activeNotifyUsers"] = ['TimeoutError']
			result["activeRemoveUsers"] = ['TimeoutError']
		except Exception as e:
			self._logger.error(f"Failed to query users with DB '{self._db}' on server '{self._server}' for {self._app} - {e}")
			self._logger.debug(traceback.format_exc())
			result["activeNotifyUsers"] = ['QueryError']
			result["activeRemoveUsers"] = ['QueryError']
		
		return result

	# User query used for Console to pull lists of de-duped inactive users
	def QueryConUsers(self, qNotifyInact: str, qRemoveInact: str) -> dict:
		"""
		Runs two queries.
		Stores the results in a dictionary where the values are also dictionaries.

		SQL query use cases:
		- SqlConfig.conQueryNotify
		- SqlConfig.conQueryRemove
		"""
		try:
			self._logger.debug(f"Running SQL query to obtain inactive users who meet the notification threshold for {self._app} in db '{self._db}'")
			self._cursorMain.execute(qNotifyInact)
			
			# Store the username amd description field
			# Username is the key and the description is the value in the dictionary
			inactiveNotifyUsers = {}
			for i in self._cursorMain:
				inactiveNotifyUsers[f'{i[0]}'] = f'{i[1]}'

			self._logger.debug(f"Running SQL query to obtain inactive users who meet the removal threshold for {self._app} in db '{self._db}'")
			self._cursorMain.execute(qRemoveInact)
			
			# Store the username and description field
			# Username is the key and the description is the value in the dictionary
			inactiveRemoveUsers = {}
			for i in self._cursorMain:
				inactiveRemoveUsers[f'{i[0]}'] = f'{i[1]}'

			result = {"inactiveNotifyUsers" : inactiveNotifyUsers, "inactiveRemoveUsers" : inactiveRemoveUsers}
		except pyodbc.ProgrammingError as e:
			self._logger.error(f"SQL Syntax Error: Failed to query inactive users with DB '{self._db}' on server '{self._server}' for {self._app} - {e}")
			self._logger.debug(traceback.format_exc())
			result = {"inactiveNotifyUsers" : 'SyntaxError', "inactiveRemoveUsers" : 'SyntaxError'}
		except pyodbc.OperationalError as e:
			self._logger.error(f"Possible query time out: Failed to query inactive users with DB '{self._db}' on server '{self._server}' for {self._app} - {e}")
			self._logger.debug(traceback.format_exc())
			result = {"inactiveNotifyUsers" : 'TimeoutError', "inactiveRemoveUsers" : 'TimeoutError'}
		except Exception as e:
			self._logger.error(f"Failed to query inactive users with DB '{self._db}' on server '{self._server}' for {self._app} - {e}")
			self._logger.debug(traceback.format_exc())
			result = {"inactiveNotifyUsers" : 'QueryError', "inactiveRemoveUsers" : 'QueryError'}
		
		return result

	# Run query in VADW
	def QueryVadw(self, query: str) -> list:
		"""
		Used for SQL queries sent to VADW.AD.Users in the data warehouse.  
		The SQL query should already be in the correct format before calling this method.
		
		Returns a list of fields from the DB table.
		Only fields from the first column are returned.
		For example, if your select statement looks like:
			SELECT UserName, LoginTime
		Only fields from UserName will be returned in the list.
		"""
		
		if self._db.lower() != 'vadw':
			raise ValueError("Incorrect database used for VADW SQL query.")
		try:
			self._logger.debug(f"Running SQL query in VADW for {self._app}")
			self._cursorMain.execute(query)

			result = []
			for i in self._cursorMain:
				result.append(i[0])
		except pyodbc.ProgrammingError as e:
			self._logger.error(f"SQL Syntax Error: Failed query with DB '{self._db}' on server '{self._server}' for {self._app} - {e}")
			self._logger.error(f"Failed Query: {query}")
			self._logger.debug(traceback.format_exc())
			result = ['SyntaxError']
		except pyodbc.OperationalError as e:
			self._logger.error(f"Possible query time out: Failed query with DB '{self._db}' on server '{self._server}' for {self._app} - {e}")
			self._logger.error(f"Failed Query: {query}")
			self._logger.debug(traceback.format_exc())
			result = ['TimeoutError']
		except Exception as e:
			self._logger.error(f"Failed query with DB '{self._db}' on server '{self._server}' for {self._app} - {e}")
			self._logger.error(f"Failed Query: {query}")
			self._logger.debug(traceback.format_exc())
			result = ['QueryError']
		
		return result


if __name__ == "__main__":

	from log_config import LogConfig
	logSetup = LogConfig('db_query_Test', 20000000, 5, logLevel=logging.DEBUG)
	testLogger = logSetup.ConfigureLogger()
	
	instance = DBQuery(logger=testLogger, odbcVer=18, server='server.domain', db='BESReporting', app="Test App")

	print("Cursor Object", instance.cursor)
	print("SQL Conn Object", instance.sqlConn)
	print("App:", instance.app)


	instance.DbClose()

	help(DBQuery.QueryVadw)