# Run test with DEBUG logging enabled and reference Logs db_query_unittesting.log for details

import unittest
from unittest.mock import MagicMock, patch
import logging
import pyodbc

from src.log_config import LogConfig
from src.db_query import DBQuery

logSetup = LogConfig('db_connect_unittesting', 20000000, 5, logLevel=logging.DEBUG)
testLogger = logSetup.ConfigureLogger()

test_server = "test_server.subdomain.domain"
test_db = 'test_db'
app = "test app"

class TestDBQuery(unittest.TestCase):
	@patch('src.db_query.pyodbc.connect')
	def test_DbQuerySqlConn(self, mock_connect):
		""""Test successful db connection"""
		# Setup the mock connection and cursor
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_connect.return_value = mock_conn

		instance = DBQuery(testLogger, 18, test_server, test_db, app=app)
		self.assertEqual(instance.server, test_server, "This should be the server passed to the constructor")
		self.assertEqual(instance.db, test_db, "This should be the database passed to the constructor")
		self.assertEqual(instance.app, 'test app', "This should be the app passed to the constructor")
		instance.DbClose()

		# Verify pyodbc.connect was called with the correct string
		mock_connect.assert_called_once()
		args, kwargs = mock_connect.call_args
		self.assertIn(f'Server={test_server}', args[0])
		self.assertIn(f'Database={test_db}', args[0])

		self.assertEqual(mock_conn.timeout, 30) # Verify timeout properties were set
		mock_conn.cursor.assert_called_once() # Verify cursor was created

	@patch('src.db_query.pyodbc.connect')
	def test_DbQueryInaUserSuccess(self, mock_connect):
		"""test successful QueryInactiveUsers() call"""
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_connect.return_value = mock_conn
		mock_cursor.__iter__.side_effect = [
            iter([("user1",), ("user2",)]),  # For qNotifyInact
            iter([("user3",)])               # For qRemoveInact
        ]
		instance = DBQuery(testLogger, 18, test_server, test_db, app=app)
		mock_connect.assert_called_once()

		result = instance.QueryInactiveUsers("SELECT notify", "SELECT remove")
		self.assertEqual(result, {'inactiveNotifyUsers': ['user1', 'user2'], 'inactiveRemoveUsers': ['user3']})
		self.assertEqual(mock_cursor.execute.call_count, 2)

	@patch('src.db_query.pyodbc.connect')
	def test_DbQueryInaUserFail(self, mock_connect):
		"""test pyodbc.ProgrammingError for QueryInactiveUsers()"""
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_connect.return_value = mock_conn
		mock_cursor.execute.side_effect = pyodbc.ProgrammingError("Syntax Error")

		instance = DBQuery(testLogger, 18, test_server, test_db, app=app)
		mock_connect.assert_called_once()
		result = instance.QueryInactiveUsers("invalid", "invalid")
		self.assertEqual(result, {"inactiveNotifyUsers" : ['SyntaxError'], "inactiveRemoveUsers" : ['SyntaxError']})
		self.assertEqual(mock_cursor.execute.call_count, 1)

	@patch('src.db_query.DBQuery.QueryInactiveUsers')
	@patch('src.db_query.pyodbc.connect')
	def test_DbQueryAllUserSuccess(self, mock_connect, mock_inactive_query):
		"""test QueryAllUsers() success"""
		mock_inactive_query.return_value = {'inactiveNotifyUsers': ['user1', 'user2'], 'inactiveRemoveUsers': ['user3']}
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_connect.return_value = mock_conn
		mock_cursor.__iter__.side_effect = [
			iter([("user4",), ("user5",)]),  # For activeNotifyUsers
			iter([("user6",)])               # For activeRemoveUsers
		]

		instance = DBQuery(testLogger, 18, test_server, test_db, app=app)
		mock_connect.assert_called_once()

		result = instance.QueryAllUsers("SELECT notify", "SELECT remove", "SELECT notify", "SELECT remove")
		self.assertEqual(result, {'inactiveNotifyUsers': ['user1', 'user2'], 'inactiveRemoveUsers': ['user3'], "activeNotifyUsers" : ['user4', 'user5'], "activeRemoveUsers" : ['user6']})
		self.assertEqual(mock_cursor.execute.call_count, 2)

	@patch('src.db_query.DBQuery.QueryInactiveUsers')
	@patch('src.db_query.pyodbc.connect')
	def test_DbQueryAllUserFail(self, mock_connect, mock_inactive_query):
		"""test pyodbc.ProgrammingError for QueryAllUsers()"""
		mock_inactive_query.return_value = {"inactiveNotifyUsers" : ['SyntaxError'], "inactiveRemoveUsers" : ['SyntaxError']}
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_connect.return_value = mock_conn
		mock_cursor.execute.side_effect = pyodbc.ProgrammingError("Syntax Error")

		instance = DBQuery(testLogger, 18, test_server, test_db, app=app)
		mock_connect.assert_called_once()
		result = instance.QueryAllUsers("invalid", "invalid", "invalid", "invalid")
		self.assertEqual(result, {"inactiveNotifyUsers" : ['SyntaxError'], "inactiveRemoveUsers" : ['SyntaxError'], "activeNotifyUsers" : ['SyntaxError'], "activeRemoveUsers" : ['SyntaxError']})
		self.assertEqual(mock_cursor.execute.call_count, 1)

	@patch('src.db_query.pyodbc.connect')
	def test_DbQueryConUserSuccess(self, mock_connect):
		"""test successful QueryConUsers() call"""
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_connect.return_value = mock_conn
		mock_cursor.__iter__.side_effect = [
			iter([("user1", "user1_descr",), ("user2", "user2_descr",)]),  # For qNotifyInact
			iter([("user3", "user3_descr",)])               # For qRemoveInact
		]
		instance = DBQuery(testLogger, 18, test_server, test_db, app=app)
		mock_connect.assert_called_once()

		result = instance.QueryConUsers("SELECT notify", "SELECT remove")
		self.assertEqual(result, {'inactiveNotifyUsers': {"user1": "user1_descr", "user2": "user2_descr"}, 'inactiveRemoveUsers': {"user3": "user3_descr"}})
		self.assertEqual(mock_cursor.execute.call_count, 2)

	@patch('src.db_query.pyodbc.connect')
	def test_DbQueryConUserFail(self, mock_connect):
		"""test pyodbc.ProgrammingError for QueryConUsers()"""
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_connect.return_value = mock_conn
		mock_cursor.execute.side_effect = pyodbc.ProgrammingError("Syntax Error")

		instance = DBQuery(testLogger, 18, test_server, test_db, app=app)
		mock_connect.assert_called_once()
		result = instance.QueryConUsers("invalid", "invalid")
		self.assertEqual(result, {"inactiveNotifyUsers" : 'SyntaxError', "inactiveRemoveUsers" : 'SyntaxError'})
		self.assertEqual(mock_cursor.execute.call_count, 1)

	@patch('src.db_query.pyodbc.connect')
	def test_DbQueryVadwSuccess(self, mock_connect):
		"""test successful QueryVadw() call"""
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_connect.return_value = mock_conn
		mock_cursor.__iter__.side_effect = [
			iter([("user1",)]),
		]
		instance = DBQuery(testLogger, 18, test_server, "vadw", app=app)
		mock_connect.assert_called_once()

		result = instance.QueryVadw("SELECT notify")
		self.assertEqual(result, ['user1'])
		self.assertEqual(mock_cursor.execute.call_count, 1)

	@patch('src.db_query.pyodbc.connect')
	def test_DbQueryVadwFail(self, mock_connect):
		"""test pyodbc.ProgrammingError for QueryVadw()"""
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_connect.return_value = mock_conn
		mock_cursor.execute.side_effect = pyodbc.ProgrammingError("Syntax Error")

		instance = DBQuery(testLogger, 18, test_server, "vadw", app=app)
		mock_connect.assert_called_once()
		result = instance.QueryVadw("invalid")
		self.assertEqual(result, ['SyntaxError'])
		self.assertEqual(mock_cursor.execute.call_count, 1)

	@patch('src.db_query.pyodbc.connect')
	def test_DbQueryVadwValueErr(self, mock_connect):
		"""Failure: Value Error raised for incorrect db"""
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_connect.return_value = mock_conn
		instance = DBQuery(testLogger, 18, test_server, 'invalid_DB', app='test app')
		with self.assertRaises(ValueError):
			instance.QueryVadw("SELECT query")

		
if __name__ == '__main__':
	unittest.main()