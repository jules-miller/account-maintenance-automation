# Run test with DEBUG logging enabled and reference Logs db_write_unittesting.log for details

import unittest
from unittest.mock import patch, MagicMock
import logging

from src.log_config import LogConfig
from src.db_write import DBWrite
import pyodbc

logSetup = LogConfig('db_write_unittesting', 20000000, 5, logLevel=logging.DEBUG)
testLogger = logSetup.ConfigureLogger()

test_server = "test_server.subdomain.domain"
test_db = 'test_db'
app = "test app"

class TestDBWrite(unittest.TestCase):
	@patch('src.db_query.pyodbc.connect')
	def test_DbWriteSqlConn(self, mock_connect):
		""""Test successful db connection"""
		# Setup the mock connection and cursor
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_connect.return_value = mock_conn

		instance = DBWrite(testLogger, 18, test_server, test_db, app=app)
		self.assertEqual(instance.server, test_server, "This should be the server passed to the constructor")
		self.assertEqual(instance.db, test_db, "This should be the database passed to the constructor")
		self.assertEqual(instance.app, 'test app', "This should be the app passed to the constructor")

		# Verify pyodbc.connect was called with the correct string
		mock_connect.assert_called_once()
		args, kwargs = mock_connect.call_args
		self.assertIn(f'Server={test_server}', args[0])
		self.assertIn(f'Database={test_db}', args[0])

		self.assertEqual(mock_conn.timeout, 30) # Verify timeout properties were set
		mock_conn.cursor.assert_called_once() # Verify cursor was created

	@patch('src.db_query.pyodbc.connect')
	def test_MarkDeletedSuccess(self, mock_connect):
		"""test successful MarkDeleted() call"""
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_connect.return_value = mock_conn
		
		instance = DBWrite(testLogger, 18, test_server, test_db, app=app)
		mock_connect.assert_called_once()

		result = instance.MarkDeleted("mock sql transaction")
		self.assertEqual(result, 0)
		self.assertEqual(mock_cursor.execute.call_count, 1)
		self.assertEqual(mock_conn.commit.call_count, 1)

	@patch('src.db_query.pyodbc.connect')
	def test_MarkDeletedFail(self, mock_connect):
		"""test successful MarkDeleted() call"""
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_connect.return_value = mock_conn
		mock_cursor.execute.side_effect = pyodbc.ProgrammingError("Syntax Error")
		
		instance = DBWrite(testLogger, 18, test_server, test_db, app=app)
		mock_connect.assert_called_once()

		result = instance.MarkDeleted("mock sql transaction")
		self.assertEqual(result, 1)
		self.assertEqual(mock_cursor.execute.call_count, 1)
		self.assertEqual(mock_conn.commit.call_count, 0)

if __name__ == '__main__':
	unittest.main()