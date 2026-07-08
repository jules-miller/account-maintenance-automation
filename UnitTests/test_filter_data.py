# Run test with DEBUG logging enabled and reference Logs filter_data_unittesting.log for details
# Ensure current working directory contains the ConfFiles sub directory

import unittest
from unittest.mock import patch
import sys
import os
import logging
from pathlib import Path

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../Classes'))

from log_config import LogConfig
from filter_data import FilterData

logSetup = LogConfig('filter_data_unittesting', 20000000, 5, logLevel=logging.DEBUG)
testLogger = logSetup.ConfigureLogger()

def WriteFileFromList(filePath: str, valueList: list ) -> None:
		with open(filePath, 'w') as file:
			for user in valueList:
				file.write(f"{user}\n")
				
def RemoveFile(file):
	if os.path.exists(file):
		os.remove(file)

class TestFilterData(unittest.TestCase):
	readUsersFile = (Path(__file__).parent /  "ConfFiles/test_ReadUsersFile.txt").resolve().as_posix()
	nonExistingFile = (Path(__file__).parent /  "missing/missing.fail").resolve().as_posix()
	excludedUserFile = (Path(__file__).parent /  "ConfFiles/test_excludedUsers.txt").resolve().as_posix()
	
	# ReadUsersFile() successfully reading the file 
	def test_ReadUsersFileSuccess(self):
		userList = ['user1@domain', 'user2@domain']
		WriteFileFromList(self.readUsersFile, userList)
		result = FilterData.ReadUsersFile(self.readUsersFile)
		self.assertEqual(result, userList)

	# ReadUsersFile() raises filenotfounderror 
	def test_ReadUsersFileRaise(self):
		with self.assertRaises(FileNotFoundError):
			FilterData.ReadUsersFile(self.nonExistingFile)

	# FilterUsers() test excluded users
	def test_FilterUsersExcl(self):
		excludedUsers = ['user2@domain', 'user4@domain']
		inactiveUsers = ['user1@domain', 'user2@domain', 'user3@domain', 'user4@domain']
		expectedResult = ['user1@domain', 'user3@domain']
		result = FilterData.FilterUsers(inactiveList=inactiveUsers, exclList=excludedUsers)
		self.assertEqual(result, expectedResult)

	# FilterUsers() test empty excluded users list
	def test_FilterUsersEmptyExcl(self):
		excludedUsers = []
		inactiveUsers = ['user1@domain', 'user2@domain', 'user3@domain', 'user4@domain']
		expectedResult = inactiveUsers = ['user1@domain', 'user2@domain', 'user3@domain', 'user4@domain']
		result = FilterData.FilterUsers(inactiveList=inactiveUsers, exclList=excludedUsers)
		self.assertEqual(result, expectedResult)
	
	# FilterUsers() test flagged users and excluded users
	def test_FilterUsersFlag(self):
		excludedUsers = ['user2@domain', 'user4@domain']
		flaggedUsers = ['user1@domain']
		inactiveUsers = ['user1@domain', 'user2@domain', 'user3@domain', 'user4@domain']
		expectedResult = ['user3@domain']
		result = FilterData.FilterUsers(inactiveList=inactiveUsers, exclList=excludedUsers, flagList=flaggedUsers)
		self.assertEqual(result, expectedResult)

	# FilterUsers() test active users and excluded users
	def test_FilterUsersActive(self):
		excludedUsers = ['user2@domain', 'user4@domain']
		activeUsers = ['user1@domain']
		inactiveUsers = ['user1@domain', 'user2@domain', 'user3@domain', 'user4@domain']
		expectedResult = ['user3@domain']
		result = FilterData.FilterUsers(inactiveList=inactiveUsers, exclList=excludedUsers, activeList=activeUsers)
		self.assertEqual(result, expectedResult)

	# FilterUsers() test all args at once
	def test_FilterUsersAll(self):
		excludedUsers = ['user2@domain', 'user4@domain']
		flaggedUsers = ['user5@domain.domain']
		activeUsers = ['user1@domain']
		inactiveUsers = ['user1@domain', 'user2@domain', 'user3@domain', 'user4@domain', 'user5@domain.domain', 'user6@domain.domain']
		expectedResult = ['user3@domain', 'user6@domain.domain']
		result = FilterData.FilterUsers(inactiveList=inactiveUsers, exclList=excludedUsers, flagList=flaggedUsers, activeList=activeUsers)
		self.assertEqual(result, expectedResult)

	# DedupeList()
	def test_DedupeList(self):
		value = ['user1@domain', 'user2@domain', 'user3@domain', 'user3@domain', 'user5@domain.domain', 'user6@domain.domain', 'user6@domain.domain']
		expectedResult = ['user1@domain', 'user2@domain', 'user3@domain', 'user5@domain.domain', 'user6@domain.domain']
		dedupedList = FilterData.DedupeList(value)
		self.assertEqual(dedupedList, expectedResult, "List deduplication failed")

	# FormatSQL() - regular usernames without quotes in the name
	def test_FormatSQL1(self):
		users = ['user1@domain', 'user2@domain', 'user3@domain']
		expectedResult = "'user1@domain','user2@domain','user3@domain'"
		result = FilterData.FormatSQL(users)
		self.assertEqual(result, expectedResult)

	# FormatSQL() - usernames with quotes in the name
	def test_FormatSQL2(self):
		users = ['user1@domain', "user'2@domain.domain", "user'3@domain.domain"]
		expectedResult = "'user1@domain','user''2@domain.domain','user''3@domain.domain'"
		result = FilterData.FormatSQL(users)
		self.assertEqual(result, expectedResult)

	# FilterConDescr
	def test_FilterConDescr(self):
		userDescriptions = ["ADMIN:user1", "ADMIN:user'2"]
		expectedResult = "'user1','user''2'"
		result = FilterData.FilterConDescr(userDescriptions)
		self.assertEqual(result, expectedResult)

	# ConvertKeystoList()
	def test_ConvertKeystoList(self):
		values = {"key1" : "value1", "key2" : "value2", "key3" : "value3"}
		expectedResult = ['key1', 'key2', 'key3']
		result = FilterData.ConvertKeystoList(values)
		self.assertEqual(result, expectedResult)

	# ConvertValuestoList()
	def test_ConvertValuestoList(self):
		values = {"key1" : "value1", "key2" : "value2", "key3" : "value3"}
		expectedResult = ['value1', 'value2', 'value3']
		result = FilterData.ConvertValuestoList(values)
		self.assertEqual(result, expectedResult)
		

if __name__ == '__main__':
	unittest.main()