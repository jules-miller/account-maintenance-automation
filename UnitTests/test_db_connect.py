# Run test with DEBUG logging enabled and reference Logs db_connect_unittesting.log for details

import unittest
from unittest.mock import patch
import sys
import os
import logging
import pyodbc

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../Classes'))

from log_config import LogConfig
from db_connect import DBConnect

logSetup = LogConfig('db_connect_unittesting', 20000000, 5, logLevel=logging.DEBUG)
testLogger = logSetup.ConfigureLogger()

class TestDBConnect(unittest.TestCase):

	# Test successful class instantiation and getters
	def test_DbConnectSqlConn(self):
		instance = DBConnect(testLogger, 18, 'server@domain', 'BESReporting')
		self.assertEqual(type(instance.sqlConn), pyodbc.Connection, "This should be the sql connection object returned by DbLogin")
		self.assertEqual(type(instance.cursor), pyodbc.Cursor, "This should be the cursor object returned by DbLogin")
		self.assertEqual(instance.server, 'server@domain', "This should be the server passed to the constructor")
		self.assertEqual(instance.db, 'BESReporting', "This should be the database passed to the constructor")
		instance.DbClose()

	# Test interface error - connecting to an existing server that is not a SQL server or is not listening on the sql port 
	def test_DbConnectInterErr(self):
		instance = DBConnect(testLogger, 18, 'server@domain', 'tableDoesNotExist')
		self.assertEqual(instance.sqlConn, 1, "The connection attempt should handle the InterfaceError exception")
		instance.DbClose()

	# Test operational error - connecting to a non-existing server should force the timeout
	def test_DbConnectOpErr(self):
		instance = DBConnect(testLogger, 18, 'server@domain', 'BESReporting')
		self.assertEqual(instance.sqlConn, 2, "The connection attempt should handle the OperationalError exception due to connection timeout")
		instance.DbClose()

	# Test DbConnCheckTrue
	def test_DbConnectConnCheckTrue(self):
		instance = DBConnect(testLogger, 18, 'server@domain', 'BESReporting')
		connCheck = instance.DbConnCheck()
		self.assertEqual(connCheck, True, "A successful db connection should be established")
		instance.DbClose()

	# Test dbConnCheckFalse
	def test_DbConnectConnCheckFalse(self):
		instance = DBConnect(testLogger, 18, 'server@domain', 'tableDoesNotExist')
		connCheck = instance.DbConnCheck()
		self.assertEqual(connCheck, False, "A successful db connection should be established")
		instance.DbClose()

	# Test DbClose - assert debug log entry
	def test_DbConnectClose(self):
		instance = DBConnect(testLogger, 18, 'server@domain', 'BESReporting')
		with self.assertLogs(testLogger, level='DEBUG') as cm: # Check that the logger wrote the 'Closing connection...' entry
			instance.DbClose()
			self.assertEqual(instance.DbConnCheck(), False, "DB connection should be closed")
		self.assertIn("DEBUG:db_connect_unittesting:Closing connection to DB 'BESReporting' on server 'server@domain'", cm.output)

if __name__ == '__main__':
	unittest.main()

	