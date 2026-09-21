# Run test with DEBUG logging enabled and reference Logs db_connect_unittesting.log for details

import unittest
from unittest.mock import MagicMock, patch
import logging
import pyodbc

# Append the Classes directory to Python's path so that it can find the module imports
#sys.path.append(os.path.join(os.path.dirname(__file__), '../Classes'))

from src.log_config import LogConfig
from src.db_connect import DBConnect

logSetup = LogConfig('db_connect_unittesting', 20000000, 5, logLevel=logging.DEBUG)
testLogger = logSetup.ConfigureLogger()

test_server = "test_server.subdomain.domain"
test_db = 'test_db'

class TestDBConnect(unittest.TestCase):

	@patch('src.db_connect.pyodbc.connect')
	def test_DbConnectSqlConn(self, mock_connect):
		""""Test successful db connection"""
		# Setup the mock connection and cursor
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_connect.return_value = mock_conn

		instance = DBConnect(testLogger, 18, test_server, test_db)
		self.assertEqual(instance.server, test_server, "This should be the server passed to the constructor")
		self.assertEqual(instance.db, test_db, "This should be the database passed to the constructor")
		instance.DbClose()

		# Verify pyodbc.connect was called with the correct string
		mock_connect.assert_called_once()
		args, kwargs = mock_connect.call_args
		self.assertIn(f'Server={test_server}', args[0])
		self.assertIn(f'Database={test_db}', args[0])

		self.assertEqual(mock_conn.timeout, 30) # Verify timeout properties were set
		mock_conn.cursor.assert_called_once() # Verify cursor was created

	@patch('src.db_connect.pyodbc.connect')
	def test_DbConnectInterErr(self, mock_connect):
		"""Test failed DB connection (interface error)"""
		# Setup the mock connection and cursor
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_connect.return_value = mock_conn
		mock_connect.side_effect = pyodbc.InterfaceError("Failed Connection")

		instance = DBConnect(testLogger, 18, test_server, test_db)
		self.assertEqual(instance.server, test_server, "This should be the server passed to the constructor")
		self.assertEqual(instance.db, test_db, "This should be the database passed to the constructor")

		# Verify pyodbc.connect was called with the correct string
		mock_connect.assert_called_once()
		args, kwargs = mock_connect.call_args
		self.assertIn(f'Server={test_server}', args[0])
		self.assertIn(f'Database={test_db}', args[0])
		self.assertEqual(instance.sqlConn, 1)
		self.assertEqual(instance.cursor, 1)

	@patch('src.db_connect.pyodbc.connect')
	def test_DbConnectOpErr(self, mock_connect):
		"""Test failed DB connection (operational error)"""
		# Setup the mock connection and cursor
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_connect.return_value = mock_conn
		mock_connect.side_effect = pyodbc.OperationalError("Failed Connection")

		instance = DBConnect(testLogger, 18, test_server, test_db)
		self.assertEqual(instance.server, test_server, "This should be the server passed to the constructor")
		self.assertEqual(instance.db, test_db, "This should be the database passed to the constructor")

		# Verify pyodbc.connect was called with the correct string
		mock_connect.assert_called_once()
		args, kwargs = mock_connect.call_args
		self.assertIn(f'Server={test_server}', args[0])
		self.assertIn(f'Database={test_db}', args[0])
		self.assertEqual(instance.sqlConn, 2)
		self.assertEqual(instance.cursor, 2)

	@patch('src.db_connect.pyodbc.connect')
	def test_DbConnectConnCheckFalse(self, mock_connect):
		"""Test failed DB conn check returns False"""
		# Setup the mock connection and cursor
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_connect.return_value = mock_conn
		mock_connect.side_effect = pyodbc.OperationalError("Failed Connection")

		instance = DBConnect(testLogger, 18, test_server, test_db)
		self.assertEqual(instance.server, test_server, "This should be the server passed to the constructor")
		self.assertEqual(instance.db, test_db, "This should be the database passed to the constructor")

		# Verify pyodbc.connect was called with the correct string
		mock_connect.assert_called_once()
		args, kwargs = mock_connect.call_args
		self.assertIn(f'Server={test_server}', args[0])
		self.assertIn(f'Database={test_db}', args[0])
		self.assertEqual(instance.sqlConn, 2)
		self.assertEqual(instance.cursor, 2)
		self.assertEqual(instance.DbConnCheck(), False)

	@patch('src.db_connect.pyodbc.connect')
	def test_DbConnectClose(self, mock_connect):
		"""Test DBClose()"""
		# Setup the mock connection and cursor
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_connect.return_value = mock_conn

		instance = DBConnect(testLogger, 18, test_server, test_db)
		with self.assertLogs(testLogger, level='DEBUG') as cm: # Check that the logger wrote the 'Closing connection...' entry
			instance.DbClose()
			self.assertEqual(instance.DbConnCheck(), False, "DB connection should be closed")
		self.assertIn(f"DEBUG:db_connect_unittesting:Closing connection to DB '{test_db}' on server '{test_server}'", cm.output)

		# Verify pyodbc.connect was called with the correct string
		mock_connect.assert_called_once()
		self.assertEqual(mock_conn.timeout, 30) # Verify timeout properties were set
		mock_conn.cursor.assert_called_once() # Verify cursor was created

if __name__ == '__main__':
	unittest.main()

	