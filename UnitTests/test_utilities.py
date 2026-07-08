# Run test with DEBUG logging enabled and reference Logs utilities_unittesting.log for details
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
from utilities import Utilities

logSetup = LogConfig('utilities_unittesting', 20000000, 5, logLevel=logging.DEBUG)
testLogger = logSetup.ConfigureLogger()

def RemoveFile(file):
	if os.path.exists(file):
		os.remove(file)

def ReadFile(filePath):
	userList = []
	with open(filePath) as file:
		for line in file:
			userList.append(line.rstrip())
	return userList
		
class TestUtilities(unittest.TestCase):
	tempFile = (Path(__file__).parent /  "ConfFiles/test_tempFile.txt").resolve().as_posix()
	
	# WriteFileFromList
	def test_WriteFileFromList(self):
		RemoveFile(self.tempFile)
		tempList = ['user1', 'user2']
		Utilities.WriteFileFromList(self.tempFile, tempList)
		fileExists = os.path.isfile(self.tempFile)
		self.assertEqual(fileExists, True, "File creation failed")
		# Read file and assert the contents
		fileContents = ReadFile(self.tempFile)
		self.assertIn('user1', fileContents, "File contents not written")
		self.assertIn('user2', fileContents, "File contents not written")

	# WriteEmptyFile
	def test_WriteEmptyFile(self):
		RemoveFile(self.tempFile)
		Utilities.WriteEmptyFile(self.tempFile)
		fileExists = os.path.isfile(self.tempFile)
		self.assertEqual(fileExists, True, "File creation failed")
		# Read file and assert the contents
		fileContents = ReadFile(self.tempFile)
		self.assertEqual(len(fileContents), 0, "File should be empty")
	

if __name__ == '__main__':
	unittest.main()