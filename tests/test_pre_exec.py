# Run test with DEBUG logging enabled and reference Logs/pre_exec_unittesting.log for details

import unittest
from unittest.mock import patch, MagicMock
import subprocess
import os
import logging

from src.log_config import LogConfig
from src.pre_exec import PreExec

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

	@patch("subprocess.run")
	def test_PsModuleCheckTmout(self, mock_run):
		"""Thest PSModule check timeout"""
		mock_process = MagicMock()
		mock_process.returncode = 0
		mock_process.stdout = b"Manifest   1.0.1.0    ActiveDirectory\n"
		mock_process.stderr = b""
		mock_run.return_value = mock_process
		mock_run.side_effect = subprocess.TimeoutExpired

		module = 'activedirectory'
		instance = PreExec(testLogger)
		result = instance.PsModuleCheck(module)
		self.assertEqual(result, False)
		
		mock_run.assert_called_once_with(
			["powershell.exe", f"Get-Module {module} -ListAvailable"], 
			capture_output=True,
			timeout=instance.psTimeout
		)

	@patch("subprocess.run")
	def test_PsModuleCheckTrue(self, mock_run):
		"""Thest successful PSModule check"""
		mock_process = MagicMock()
		mock_process.returncode = 0
		mock_process.stdout = b"Manifest   1.0.1.0    ActiveDirectory\n"
		mock_process.stderr = b""
		mock_run.return_value = mock_process

		module = 'activedirectory'
		instance = PreExec(testLogger)
		result = instance.PsModuleCheck(module)
		self.assertEqual(result, True)
		
		mock_run.assert_called_once_with(
			["powershell.exe", f"Get-Module {module} -ListAvailable"], 
			capture_output=True,
			timeout=instance.psTimeout
		)

	@patch("subprocess.run")
	def test_PsModuleCheckFalse(self, mock_run):
		"""Thest PSModule check that does not exist"""
		mock_process = MagicMock()
		mock_process.returncode = 0
		mock_process.stdout = b"empty"
		mock_process.stderr = b"does not exist"
		mock_run.return_value = mock_process

		module = 'missing_module'
		instance = PreExec(testLogger)
		result = instance.PsModuleCheck(module)
		self.assertEqual(result, False)
		
		mock_run.assert_called_once_with(
			["powershell.exe", f"Get-Module {module} -ListAvailable"], 
			capture_output=True,
			timeout=instance.psTimeout
		)

	@patch('winreg.OpenKey')
	@patch('winreg.EnumKey')
	@patch('winreg.QueryValueEx')
	@patch('winreg.CloseKey')
	def test_software_found(self, mock_close, mock_query, mock_enum, mock_open):
		"""Test that the function returns True when the target software matches."""
		# Mock EnumKey to return two keys, then raise an OSError to break the loop
		mock_enum.side_effect = ['App1', 'App2', OSError("No more keys")]
		
		# Mock QueryValueEx to simulate the return value for each key
		# Format: (value, type) -> your code reads index 0
		mock_query.side_effect = [
			('WrongSoftware', 1),  # First iteration ('App1')
			('TargetSoftware', 1)  # Second iteration ('App2')
		]
		
		# Mock OpenKey to return dummy handles (not strictly required to change, but avoids errors)
		mock_open.return_value = MagicMock()

		# Run your function
		instance = PreExec(testLogger)
		result = instance.IsSoftwareInstalled("Software\\MyPath", "DisplayName", "TargetSoftware")
		
		# Verify the function successfully identified the software
		self.assertTrue(result)
		
		# Assertions to ensure it checked the right amount of keys
		self.assertEqual(mock_enum.call_count, 2)  # It should break early on the match
		self.assertEqual(mock_query.call_count, 2)

	@patch('winreg.OpenKey')
	@patch('winreg.EnumKey')
	@patch('winreg.QueryValueEx')
	@patch('winreg.CloseKey')
	def test_software_not_found(self, mock_close, mock_query, mock_enum, mock_open):
		"""Test that it loops through everything and returns False if no software matches."""
		mock_enum.side_effect = ['App1', OSError("No more keys")]
		mock_query.side_effect = [('WrongSoftware', 1)]
		mock_open.return_value = MagicMock()

		instance = PreExec(testLogger)
		result = instance.IsSoftwareInstalled("Software\\MyPath", "DisplayName", "TargetSoftware")
		
		self.assertFalse(result)
		self.assertEqual(mock_enum.call_count, 2) # 1 for 'App1', 1 for the breaking exception

	@patch('winreg.OpenKey')
	@patch('winreg.EnumKey')
	@patch('winreg.QueryValueEx')
	@patch('winreg.CloseKey')
	def test_software_missing_key(self, mock_close, mock_query, mock_enum, mock_open):
		"""Test that a missing key throws a FileNotFoundError and returns False."""
		mock_open.side_effect = [FileNotFoundError("Key missing")]

		instance = PreExec(testLogger)

		with self.assertLogs(testLogger, level='DEBUG') as cm: 
			result = instance.IsSoftwareInstalled("Software\\MyPath", "DisplayName", "TargetSoftware")
			self.assertEqual(result, False, f"This should handle a FileNotFoundError and return False")
		self.assertIn(f"ERROR:pre_exec_unittesting:Registry key failed to open: Software\\MyPath", cm.output)

	@classmethod
	def tearDownClass(cls):
		# Code to be executed after all tests in the class
		RemoveFolder(folderPath)
		RemoveFile(filePath)


if __name__ == '__main__':
	unittest.main()