# Run test with DEBUG logging enabled and reference Logs/pre_exec_unittesting.log for details

import unittest
from unittest.mock import patch
import sys
import os
import logging

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../Classes'))

from log_config import LogConfig
from pre_exec import PreExec

logSetup = LogConfig('pre_exec_unittesting', 20000000, 5, logLevel=logging.DEBUG)
testLogger = logSetup.ConfigureLogger()

folderPath = 'tempfolder9467853162'
filePath = 'temp.txt'

def CreateFolder(path):
	if not os.path.isdir(path):
		os.mkdir(path)

def RemoveFolder(path):
	if os.path.isdir(path):
		os.rmdir(path)

def CreateFile(file):
	if not os.path.isfile(file):
		with open(file, 'w') as f:
			f.write("Used for unit testing")

def RemoveFile(file):
	if os.path.isfile(file):
		os.remove(file)

class TestPreExec(unittest.TestCase):
	
	# Test PreExec.OsCheck for success
	def test_OsCheckTrue(self):
		instance = PreExec(testLogger)
		self.assertTrue(instance.OsCheck())

	# Test PreExec.OsCheck for failure
	# mock the requiredOS class var with a different os
	@patch.object(PreExec, "requiredOS", "linux")
	def test_OsCheckFalse(self):
		instance = PreExec(testLogger)
		self.assertFalse(instance.OsCheck())

	# Test FolderCheck for 0=folder exists and create = False
	def test_FolderCheck0False(self):
		CreateFolder(folderPath)
		instance = PreExec(testLogger)
		result = instance.FolderCheck(folderPath)
		self.assertEqual(result, 0, "Folder should already exist")

	# Test FolderCheck for 0=folder exists and create = True
	def test_FolderCheck0True(self):
		CreateFolder(folderPath)
		instance = PreExec(testLogger)
		result = instance.FolderCheck(folderPath, create=True)
		self.assertEqual(result, 0, "Folder should already exist")

	# Test FolderCheck for 1=folder is missing
	def test_FolderCheck1(self):
		RemoveFolder(folderPath)
		instance = PreExec(testLogger)
		result = instance.FolderCheck(folderPath)
		self.assertEqual(result, 1, "Folder should not exist")

	# Test FolderCheck for 2=folder was created
	def test_FolderCheck2(self):
		RemoveFolder(folderPath)
		instance = PreExec(testLogger)
		result = instance.FolderCheck(folderPath, create=True)
		self.assertEqual(result, 2, "Folder should be created")

	# Test FolderCheck for 3=error creating folder
	def test_FolderCheck3(self):
		instance = PreExec(testLogger)
		result = instance.FolderCheck(r'a[];\':"/.,', create=True)
		self.assertEqual(result, 3, "Folder create should error")

	# Test File Check: File Exists
	def test_FileCheckTrue(self):
		CreateFile(filePath)
		instance = PreExec(testLogger)
		result = instance.FileCheck(filePath)
		self.assertEqual(result, True, "File should exist")

	# Test File Check: File Missing
	def test_FileCheckFalse(self):
		RemoveFile(filePath)
		instance = PreExec(testLogger)
		result = instance.FileCheck(filePath)
		self.assertEqual(result, False, "File should not exist")

	# Test PsModuleCheck - module exists | in PS run to get a list of installed modules: Get-Module * -ListAvailable
	def test_PsModuleCheckTrue(self):
		module = 'DirectAccessClientComponents'
		instance = PreExec(testLogger)
		result = instance.PsModuleCheck(module)
		self.assertEqual(result, True, f"PS Module should exist: {module}")

	# Test PsModuleCheck - module does not exist
	def test_PsModuleCheckFalse(self):
		module = 'activedirectory1'
		instance = PreExec(testLogger)
		result = instance.PsModuleCheck(module)
		self.assertEqual(result, False, f"PS Module should NOT exist: {module}")

	# Test PsModuleCheck - TimeoutExpired
	# mock the psTimeout class var with a smaller value to force the timeout exception
	@patch.object(PreExec, "psTimeout", .1)
	def test_PsModuleCheckTmout(self):
		module = 'activedirectory'
		instance = PreExec(testLogger)
		with self.assertLogs(testLogger, level='DEBUG') as cm: # Check that the logger wrote the error when TimeoutExpired was caught
			result = instance.PsModuleCheck(module)
			self.assertEqual(result, False, f"PS Module should return false and hit TimeoutExpired exception: {module}")
		self.assertIn("ERROR:pre_exec_unittesting:The PowerShell module check timed out after 0.1 seconds. | Command '['powershell.exe', 'Get-Module activedirectory -ListAvailable']' timed out after 0.1 seconds", cm.output)

	# Test IsSoftwareInstalled - software exists
	def test_IsSoftwareInstalledTrue(self):
		key = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
		subKey = "DisplayName"
		software = 'Microsoft ODBC Driver 18 for SQL Server'
		instance = PreExec(testLogger)
		result = instance.IsSoftwareInstalled(key, subKey, software)
		self.assertEqual(result, True, "software should be installed")

	# Test IsSoftwareInstalled - software does not exist
	def test_IsSoftwareInstalledFalse(self):
		key = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
		subKey = "DisplayName"
		software = 'MissingSoftware'
		instance = PreExec(testLogger)
		result = instance.IsSoftwareInstalled(key, subKey, software)
		self.assertEqual(result, False, "software should Not be installed")

	# Test IsSoftwareInstalled - registry key does not exist - FileNotFoundError
	def test_IsSoftwareInstalledFileErr(self):
		key = "cantopenmissingkey"
		subKey = "DisplayName"
		software = 'MissingSoftware'
		instance = PreExec(testLogger)
		with self.assertLogs(testLogger, level='DEBUG') as cm: # Check that the logger wrote the error when FileNotFoundError was caught
			result = instance.IsSoftwareInstalled(key, subKey, software)
			self.assertEqual(result, False, "Should return false after hitting FileNotFoundError exception")
		self.assertIn("ERROR:pre_exec_unittesting:Registry key failed to open: cantopenmissingkey", cm.output)

	@classmethod
	def tearDownClass(cls):
		# Code to be executed after all tests in the class
		RemoveFolder(folderPath)
		RemoveFile(filePath)


if __name__ == '__main__':
	unittest.main()