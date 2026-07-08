# Run test with DEBUG logging enabled and reference Logs db_write_unittesting.log for details

import unittest
from unittest.mock import patch
import sys
import os
import logging

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../Classes'))

from log_config import LogConfig
from db_write import DBWrite
import pyodbc

logSetup = LogConfig('db_write_unittesting', 20000000, 5, logLevel=logging.DEBUG)
testLogger = logSetup.ConfigureLogger()

############################################################
### Requires a test user in the BFC PPD tem_analytics DB ###
# If this is failing, check the user exists ################
############################################################
testUser = 'testMaintUser' # Created in BFCPPD on 2/24/25

readUserQuery = """SELECT deleted
FROM [tem_analytics].[dbo].[users]
WHERE username = 'testMaintUser'"""
delUserTransaction = f'''UPDATE tem_analytics.dbo.users
SET deleted = 1
WHERE tem_analytics.dbo.users.username = '{testUser}';'''
undelUserTransaction = f'''UPDATE tem_analytics.dbo.users
SET deleted = 0
WHERE tem_analytics.dbo.users.username = '{testUser}';'''
besRepQErr = '''SELECT NameID
FROM BESReporting.dbo.ROLES
Where Name = 'Administrator'
''' # NameID column does not exist

class TestDBWrite(unittest.TestCase):
	# Test instantiation and fields
	def test_DbQuerySqlConn(self):
		instance = DBWrite(testLogger, 18, 'server@domain', 'BESReporting', app='test app')
		self.assertEqual(type(instance.sqlConn), pyodbc.Connection, "This should be the sql connection object returned by DbLogin")
		self.assertEqual(type(instance.cursor), pyodbc.Cursor, "This should be the cursor object returned by DbLogin")
		self.assertEqual(instance.server, 'server@domain', "This should be the server passed to the super constructor")
		self.assertEqual(instance.db, 'BESReporting', "This should be the database passed to the super constructor")
		self.assertEqual(instance.app, 'test app', "This should be the app passed to the constructor")
		instance.DbClose()

	# Test MarkDeleted() Success
	def test_MarkDeletedSuccess(self):
		instance = DBWrite(testLogger, 18, 'server@domain', 'tem_analytics', app='test app')
		instance.MarkDeleted(undelUserTransaction) # Set deleted to 0
		instance._cursorMain.execute(readUserQuery) # Read DB for result
		for i in instance._cursorMain:
			result = i[0]
		self.assertEqual(result, 0)
		instance.MarkDeleted(delUserTransaction) # Set deleted to 1
		instance._cursorMain.execute(readUserQuery) # read db for result
		for i in instance._cursorMain:
			result = i[0]
		self.assertEqual(result, 1, "The transaction to mark the user deleted failed")
		instance.DbClose()

	# Test MarkDelted() Programming error - syntax error
	def test_MarkDeletedFail(self):
		instance = DBWrite(testLogger, 18, 'server@domain', 'BESReporting', app='test app')
		result = instance.MarkDeleted(besRepQErr)
		self.assertEqual(result, 1)

if __name__ == '__main__':
	unittest.main()