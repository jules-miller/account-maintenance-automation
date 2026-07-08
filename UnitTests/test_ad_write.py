# Run test with DEBUG logging enabled and reference Logs ad_write_unittesting.log for details

import unittest
from unittest.mock import patch
import sys
import os
import logging
from pathlib import Path
import socket

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../Classes'))

from log_config import LogConfig
from ad_write import ADWrite

logSetup = LogConfig('ad_write_unittesting', 20000000, 5, logLevel=logging.DEBUG)
testLogger = logSetup.ConfigureLogger()
hostname = socket.gethostname()
bfiScript = Path(__file__).parent / '../PS/bfi_remove_users_AD.ps1'
bfiDN = Path(__file__).parent / '../PS/BFI_All_Cores_Inactive_DN.txt'

def CreateFile(file, text):
	if not os.path.isfile(file):
		with open(file, 'w') as f:
			f.write(f"{text}")

def RemoveFile(file):
	if os.path.isfile(file):
		os.remove(file)

class TestADWrite(unittest.TestCase):
	
	# Test instantiation and fields
	def test_ADWriteInit(self):
		CreateFile(bfiScript, 'script')
		CreateFile(bfiDN, 'dn')
		instance = ADWrite(testLogger, 'bfi')

		testScriptExists = os.path.isfile(bfiScript)
		classScriptExists = os.path.isfile(instance.psScript)
		testDnExists = os.path.isfile(bfiDN)
		classDnExists = os.path.isfile(instance.dnPath)
		# The pathlib Path element is different if it originates from the test vs the ADWrite class
		# checking that the actual file exists for both to ensure it points to the same file
		self.assertEqual(instance.app, 'bfi')
		self.assertEqual(testScriptExists, True)
		self.assertEqual(classScriptExists, True)
		self.assertEqual(testDnExists, True)
		self.assertEqual(classDnExists, True)
		
	# Test WriteAD success
	def test_WriteADSuccess(self):
		CreateFile(bfiScript, 'hostname')
		CreateFile(bfiDN, 'dn')
		instance = ADWrite(testLogger, 'bfi')
		with self.assertLogs(testLogger, level='DEBUG') as cm:
			writeAD = instance.WriteAD()
			self.assertEqual(writeAD, True)
		self.assertIn(f"DEBUG:ad_write_unittesting:PS Stdout: {hostname}", cm.output[1].strip())

	# Test WriteAD missing script
	def test_WriteADMissingScript(self):
		CreateFile(bfiDN, 'dn')
		instance = ADWrite(testLogger, 'bfi')
		with self.assertRaises(FileNotFoundError):
			instance.WriteAD()

	# Test WriteAD missing dn file
	def test_WriteADMissingDnFile(self):
		CreateFile(bfiScript, 'hostname')
		instance = ADWrite(testLogger, 'bfi')
		with self.assertRaises(FileNotFoundError):
			instance.WriteAD()

	# Test WriteAD PS Errors - pass an invalid command
	def test_WriteADPsErrors(self):
		CreateFile(bfiScript, 'hostname -invalidarg')
		CreateFile(bfiDN, 'dn')
		instance = ADWrite(testLogger, 'bfi')
		result = instance.WriteAD()
		self.assertEqual(result, False)

	# Test PS timeout
	# mock the psTimeout class var with a smaller value to force the timeout exception
	@patch.object(ADWrite, "psTimeout", .1)
	def test_WriteADPsTmout(self):
		CreateFile(bfiScript, 'hostname')
		CreateFile(bfiDN, 'dn')
		instance = ADWrite(testLogger, 'bfi')
		with self.assertLogs(testLogger, level='DEBUG') as cm:
			result = instance.WriteAD()
			self.assertEqual(result, False)
		self.assertIn(f"to remove AD users timed out after {ADWrite.psTimeout} seconds. | Command '['powershell.exe'", cm.output[1])
	
	# Executes after every individual test
	def tearDown(self):
		RemoveFile(bfiScript)
		RemoveFile(bfiDN)
	

if __name__ == '__main__':
	unittest.main()