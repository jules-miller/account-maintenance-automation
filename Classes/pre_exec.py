############### PreExec #####################################
# Checks that should be run prior to executing maintenance ##
#############################################################

import logging
import traceback
from typing import Union
import os
import sys
import subprocess
import enum
import winreg

class PreExec:
	"""
	Contains methods that should be run prior to each maintenance run.
	Relevant to both query-only mode and running the full maintenance.
	"""
	requiredOS = 'nt'
	mutexID = "INSERT_MUTEX_HERE"
	psTimeout = 30

	def __init__(self, logger: logging.Logger) -> None:
		self._logger = logger
	
	@staticmethod
	def OsCheck() -> bool:
		result = True
		if not os.name == PreExec.requiredOS:
			result = False
		
		return result

	def FolderCheck(self, path: str, create: bool = False) -> int:
		"""
		Verifies folder existence.
		Optional create parameter will create the folder if create=True and the folder is missing.

		Return values:
		0=folder exists
		1=folder is missing
		2=folder was created
		3=error creating folder
		"""
		# Return values: 0=folder exists, 1=folder is missing, 2=folder was created, 3=error creating folder
		self._logger.info(f"Checking for folder existence: {path}")
		result = 0
		if not os.path.isdir(path):
			self._logger.warning(f"Folder missing: {path}")
			result = 1
		if create and not os.path.isdir(path):
			try:
				os.mkdir(path)
				self._logger.info(f"Created Folder: {path}")
				result = 2
			except OSError as e:
				self._logger.error(f"Error creating folder: {path} - {e}")
				self._logger.debug(traceback.format_exc())
				result = 3
		
		return result

	def FileCheck(self, path: str) -> bool:
		"""
		Verifies file existence.

		Return values:
		True=File exists
		False=File missing
		"""
		self._logger.info(f"Checking for file existence: {path}")
		result = True
		if not os.path.isfile(path):
			self._logger.warning(f"File missing: {path}")
			result = False
		
		return result

	def PsModuleCheck(self, module:str) -> bool:
		"""
		Executes a PowerShell command to check for the relevant module.

		Return values:
		True=Module exists
		False=Module missing
		"""
		self._logger.info(f"Checking for installed PowerShell module: {module}")
		psStdout = ''
		psStderr = ''

		try: # run PowerShell command to check for module existence
			runPS = subprocess.run(
				["powershell.exe", f"Get-Module {module} -ListAvailable"],
				capture_output=True, timeout=PreExec.psTimeout
			)
		except subprocess.TimeoutExpired as e:
			self._logger.error(f"The PowerShell module check timed out after {PreExec.psTimeout} seconds. | {e}")
			self._logger.debug(traceback.format_exc())
		except Exception as e:
			self._logger.error(f"The PowerShell module check encountered an exception. | {e}")
			self._logger.debug(traceback.format_exc())

		try:
			runPS
			psStdout = runPS.stdout.decode("utf-8")
			self._logger.debug(f"PsModuleCheck Stdout: {psStdout}")
			psStderr = runPS.stderr.decode("utf-8")
			self._logger.debug(f"PsModuleCheck Stderr: {psStderr}")
		except NameError:
			psStderr = 'Script execution raised an exception'

		if len(psStderr) != 0: # check the PS command output for the module
			result = False
		else:
			if module.lower() in psStdout.lower():
				result = True
			else:
				result = False
		
		return result

	# Installed Software Check
	def IsSoftwareInstalled(self, subKey: str, subKeyName: str, software: str) -> bool:
		"""
		Checks the registry for the relevant software.
		Loops through the 'subKey' parameter to find the software.

		Example: IsSoftwareInstalled("SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall", "DisplayName", 'Microsoft ODBC Driver 18 for SQL Server')

		Return values:
		True=Software is installed
		False=Software is not installed
		"""
		self._logger.info(f"Checking for installed software: {software}")
		hkey = None
		try:
			hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subKey, 0, winreg.KEY_READ) # opens the top level 'HKLM + path' passed to the function
			index = 0
			result = False
			while True: # loops through every subkey in the {hkey} path. once the index is out of range, it will raise the OSError exception and break the while loop
				try:
					keyName = winreg.EnumKey(hkey, index) # enumerate the keys in the {hkey} branch and grab the key name of the index number
					subKeyPath = subKey + "\\" + keyName # concatenate the initial path passed to the function with the name of the key that was just enumerated
					hsubkey = winreg.OpenKey(hkey, keyName) # open the subkey (subkey is the initial path passed to the function + the keyname that was enumerated in the first step of the loop)
					
					subKeyValue = None
					try:
						subKeyValue = winreg.QueryValueEx(hsubkey, subKeyName)[0] # query the value of the second argument passed to the function for the given opened key
					except OSError: # if the subKeyName does not exist in the hsubkey, an OSError will be raised
						pass

					winreg.CloseKey(hsubkey) # close the key
					
					# Check if the desired software is installed
					if subKeyValue == software:
						self._logger.debug(fr"Software found: HKEY_LOCAL_MACHINE\{subKeyPath} : {subKeyValue}")
						result = True
						raise OSError
					
					index += 1 # increment the index to loop through the next key
				except OSError:
					break
		except FileNotFoundError: # if the initial key can't be opened
			self._logger.error(f"Registry key failed to open: {subKey}")
			self._logger.debug(traceback.format_exc())
			result = False
		except Exception as e:
			self._logger.error(f"Registry enumeration failed: {subKey}")
			self._logger.debug(traceback.format_exc())
			result = False
		finally:
			if hkey:
				winreg.CloseKey(hkey)
			
		return result
	

if __name__ == '__main__':

	from log_config import LogConfig
	logSetup = LogConfig('preExecTest', 20000000, 5, logLevel=logging.DEBUG)
	testLogger = logSetup.ConfigureLogger()

	instance = PreExec(testLogger)
	
	osCheck = instance.OsCheck()
	