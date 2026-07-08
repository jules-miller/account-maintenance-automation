# Run test with DEBUG logging enabled and reference Logs db_query_unittesting.log for details

import unittest
from unittest.mock import patch
import sys
import os
import logging
import pyodbc

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../Classes'))

from log_config import LogConfig
from db_query import DBQuery

logSetup = LogConfig('db_connect_unittesting', 20000000, 5, logLevel=logging.DEBUG)
testLogger = logSetup.ConfigureLogger()

# Test queries that should always return a result from PPD BESReporting
# these can be used to test QueryInactiveUsers(), QueryAllUsers(), and QueryConUsers()
besrepQ1 = '''SELECT Name,ID
FROM BESReporting.dbo.ROLES
Where Name = 'Administrator'
'''
besrepQ2 ='''SELECT Name,ID
FROM BESReporting.dbo.ROLES
Where Name = 'Normal'
'''
besrepQ3 = '''SELECT ReportName,ID
FROM BESReporting.dbo.WEBREPORTS
Where ReportName = 'Operator List'
'''
besrepQ4 = '''SELECT ReportName,ID
FROM BESReporting.dbo.WEBREPORTS
Where ReportName = 'Action List'
'''
besRepQErr = '''SELECT NameID
FROM BESReporting.dbo.ROLES
Where Name = 'Administrator'
'''

### CHANGE THE QUERIED USER IF THIS USER NO LONGER EXISTS ###
vadwUPN = "SELECT userPrincipalName FROM [VADW].[AD].[Users] where sAMAccountName in ('user1')"
vadwErr = "SELECT userPrincipalName FROM [VADW].[AD].[Users] where sAMAccountName in ('user2')"

class TestDBQuery(unittest.TestCase):

	# Test successful class instantiation and getters - also tests that class inheritance is successful
	def test_DbQuerySqlConn(self):
		instance = DBQuery(testLogger, 18, 'server@domain', 'BESReporting', app='test app')
		self.assertEqual(type(instance.sqlConn), pyodbc.Connection, "This should be the sql connection object returned by DbLogin")
		self.assertEqual(type(instance.cursor), pyodbc.Cursor, "This should be the cursor object returned by DbLogin")
		self.assertEqual(instance.server, 'server@domain', "This should be the server passed to the super constructor")
		self.assertEqual(instance.db, 'BESReporting', "This should be the database passed to the super constructor")
		self.assertEqual(instance.app, 'test app', "This should be the app passed to the constructor")
		instance.DbClose()
	
	# Success: QueryInactiveUsers
	def test_DbQueryInaUserSuccess(self):
		instance = DBQuery(testLogger, 18, 'server@domain', 'BESReporting', app='test app')
		queryResult = instance.QueryInactiveUsers(besrepQ1, besrepQ2)
		expectedResult = {"inactiveNotifyUsers" : ['Administrator'], "inactiveRemoveUsers" : ['Normal']}
		self.assertEqual(type(queryResult), dict, "queryResult should be a dictionary")
		self.assertDictEqual(queryResult, expectedResult)

	# Failure: QueryInactiveUsers
	def test_DbQueryInaUserFail(self):
		instance = DBQuery(testLogger, 18, 'server@domain', 'BESReporting', app='test app')
		queryResult = instance.QueryInactiveUsers(besRepQErr, besrepQ2)
		expectedResult = {"inactiveNotifyUsers" : ['SyntaxError'], "inactiveRemoveUsers" : ['SyntaxError']}
		self.assertEqual(type(queryResult), dict, "queryResult should be a dictionary")
		self.assertDictEqual(queryResult, expectedResult)

	# Success: QueryAllUsers
	def test_DbQueryAllUserSuccess(self):
		instance = DBQuery(testLogger, 18, 'server@domain', 'BESReporting', app='test app')
		queryResult = instance.QueryAllUsers(besrepQ1, besrepQ2, besrepQ3, besrepQ4)
		expectedResult = {"inactiveNotifyUsers" : ['Administrator'], "inactiveRemoveUsers" : ['Normal'], "activeNotifyUsers" : ['Operator List'], "activeRemoveUsers" : ['Action List']}
		self.assertEqual(type(queryResult), dict, "queryResult should be a dictionary")
		self.assertDictEqual(queryResult, expectedResult)
	
	# Failure: QueryAllUsers
	def test_DbQueryAllUserFail(self):
		instance = DBQuery(testLogger, 18, 'server@domain', 'BESReporting', app='test app')
		queryResult = instance.QueryAllUsers(besRepQErr, besrepQ2, besRepQErr, besrepQ4)
		expectedResult = {"inactiveNotifyUsers" : ['SyntaxError'], "inactiveRemoveUsers" : ['SyntaxError'], "activeNotifyUsers" : ['SyntaxError'], "activeRemoveUsers" : ['SyntaxError']}
		self.assertEqual(type(queryResult), dict, "queryResult should be a dictionary")
		self.assertDictEqual(queryResult, expectedResult)
	
	# Success: QueryConUsers
	def test_DbQueryConUserSuccess(self):
		instance = DBQuery(testLogger, 18, 'server@domain', 'BESReporting', app='test app')
		queryResult = instance.QueryConUsers(besrepQ1, besrepQ2)
		expectedResult = {'inactiveNotifyUsers': {'Administrator': '1'}, 'inactiveRemoveUsers': {'Normal': '2'}}
		self.assertEqual(type(queryResult), dict, "queryResult should be a dictionary")
		self.assertDictEqual(queryResult, expectedResult)
		adminValue = (queryResult['inactiveNotifyUsers']['Administrator'])
		self.assertEqual(adminValue, '1')

	# Failure: QueryConUsers
	def test_DbQueryConUserFail(self):
		instance = DBQuery(testLogger, 18, 'server@domain', 'BESReporting', app='test app')
		queryResult = instance.QueryConUsers(besRepQErr, besrepQ2)
		expectedResult = {'inactiveNotifyUsers': 'SyntaxError', 'inactiveRemoveUsers': 'SyntaxError'}
		self.assertEqual(type(queryResult), dict, "queryResult should be a dictionary")
		self.assertDictEqual(queryResult, expectedResult)
		errVal = (queryResult['inactiveNotifyUsers'])
		self.assertEqual(errVal, 'SyntaxError')
	
	# Success: QueryVadw
	def test_DbQueryVadwSuccess(self):
		instance = DBQuery(testLogger, 18, 'server@domain', 'VADW', app='test app')
		queryResult = instance.QueryVadw(vadwUPN)
		expectedResult = ['INSERT_UPN_HERE']
		self.assertEqual(type(queryResult), list, "Result should be a list")
		self.assertEqual(queryResult[0].lower(), expectedResult[0].lower())

	# Failure: QueryVadw - Syntax error
	def test_DbQueryVadwFail(self):
		instance = DBQuery(testLogger, 18, 'server@domain', 'VADW', app='test app')
		queryResult = instance.QueryVadw(vadwErr)
		expectedResult = ['SyntaxError']
		self.assertEqual(type(queryResult), list, "Result should be a list")
		self.assertEqual(queryResult[0].lower(), expectedResult[0].lower())

	# Failure: Value Error raised
	def test_DbQueryVadwValueErr(self):
		instance = DBQuery(testLogger, 18, 'server@domain', 'BESReporting', app='test app')
		with self.assertRaises(ValueError):
			instance.QueryVadw(vadwUPN)
	

		
if __name__ == '__main__':
	unittest.main()