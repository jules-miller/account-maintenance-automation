############## ADWrite #######################################################
# Runs a PowerShell script that removes users from relevant security groups ##
##############################################################################

import logging
import traceback
import os
import sys
import subprocess
from pathlib import Path

class ADWrite:
	"""
	Allows for execution of a PowerShell script that loops through the relevant Acitve Directory groups to remove users.
	The relevant PowerShell script and distinguishedName file (containing the users to remove) must already exist.
	Both files are assigned on class instantiation based on the app string passed to the constructor.
	"""

	psTimeout = 30

	def __init__(self, logger: logging.Logger, app: str) -> None:
		self._logger = logger
		self._app = app
		self._psScript = self._SetPSScript(app)
		self._dnPath = self._SetDNPath(app)

	# Create getters for fields
	@property
	def app(self):
		return self._app
	
	@property
	def psScript(self):
		return self._psScript
	
	@property
	def dnPath(self):
		return self._dnPath
		
	def _SetPSScript(self, app: str) -> str:
		match app.lower():
			case 'bfc':
				if getattr(sys, 'frozen', False): # If running as bundled exe, this should be true
					script = Path(__file__).parent / 'PS/bfc_remove_users_AD.ps1'
				else:
					script = Path(__file__).parent / '../PS/bfc_remove_users_AD.ps1'
			case 'bfi':
				if getattr(sys, 'frozen', False): # If running as bundled exe, this should be true
					script = Path(__file__).parent / 'PS/bfi_remove_users_AD.ps1'
				else:
					script = Path(__file__).parent / '../PS/bfi_remove_users_AD.ps1'
			case 'wr':
				if getattr(sys, 'frozen', False): # If running as bundled exe, this should be true
					script = Path(__file__).parent / 'PS/wr_remove_users_AD.ps1'
				else:
					script = Path(__file__).parent / '../PS/wr_remove_users_AD.ps1'
			case _:
				script = ''
		return script	

	def _SetDNPath(self, app: str) -> None:
		match app.lower():
			case 'bfc':
				if getattr(sys, 'frozen', False): # If running as bundled exe, this should be true
					filePath = Path(__file__).parent / 'PS/BFC_All_Cores_Inactive_DN.txt'
				else:
					filePath = Path(__file__).parent / '../PS/BFC_All_Cores_Inactive_DN.txt'
			case 'bfi':
				if getattr(sys, 'frozen', False): # If running as bundled exe, this should be true
					filePath = Path(__file__).parent / 'PS/BFI_All_Cores_Inactive_DN.txt'
				else:
					filePath = Path(__file__).parent / '../PS/BFI_All_Cores_Inactive_DN.txt'
			case 'wr':
				if getattr(sys, 'frozen', False): # If running as bundled exe, this should be true
					filePath = Path(__file__).parent / 'PS/WR_All_Cores_Inactive_DN.txt'
				else:
					filePath = Path(__file__).parent / '../PS/WR_All_Cores_Inactive_DN.txt'
			case _:
				filePath = ''
		return filePath	

	def WriteAD(self) -> bool:
		"""
		Uses the script path and DN file path set in the constructor (based on which app is passed).
		If either file is missing, raises a FileNotFoundError.
		The PS script loops through all relevant AD groups and removes the users in the DN file.

		Returns True if no stderr was found in the PS output. Else False.
		"""
		psStdout = ''
		psStderr = ''

		if not os.path.isfile(self._psScript):
			self._logger.error(f"File missing: {self._psScript}")
			raise FileNotFoundError
		if not os.path.isfile(self._dnPath):
			self._logger.error(f"File missing: {self._dnPath}")
			raise FileNotFoundError
		
		# Run the PS script
		self._logger.info(f"Removing users from Active Directory: {self._psScript}")
		try: 
			runPS = subprocess.run(
				["powershell.exe", self._psScript],
				capture_output=True, timeout=ADWrite.psTimeout
			)
		except subprocess.TimeoutExpired as e:
			self._logger.error(f"The PowerShell script '{self._psScript}' to remove AD users timed out after {ADWrite.psTimeout} seconds. | {e}")
			self._logger.debug(traceback.format_exc())
		except Exception as e:
			self._logger.error(f"The PowerShell script '{self.psScript} encountered an exception. | {e}")
			self._logger.debug(traceback.format_exc())

		# Check PS output after running the script and decode both stdout and stderr
		try:
			runPS
			psStdout = runPS.stdout.decode("utf-8")
			self._logger.debug(f"PS Stdout: {psStdout}")
			psStderr = runPS.stderr.decode("utf-8")
			self._logger.debug(f"PS Stderr: {psStderr}")
		except NameError:
			psStderr = 'Script execution raised an exception'

		if len(psStderr) != 0: # if any stderr exists, the ps script failed
			result = False
		else:
			result = True
		
		return result

if __name__ == "__main__":
	from log_config import LogConfig
	logSetup = LogConfig('adWriteTest', 20000000, 5, logLevel=logging.DEBUG)
	testLogger = logSetup.ConfigureLogger()
	instance = ADWrite(testLogger, 'bfi')
	print(instance.psScript)