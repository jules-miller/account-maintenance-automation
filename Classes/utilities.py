############## Utilities #################
# Static Methods for various utilities ###
##########################################

import logging
import traceback
import re
import os

class Utilities():
	"""
	Collection of miscellaneous static methods.
	"""
	def __init__(self):
		pass


	@staticmethod
	def WriteFileFromList(filePath: str, valueList: list ) -> None:
		"""
		Writes to a file where each item in the list is its own line.
		IMPORTANT: This will overwrite the existing file.
		"""
		with open(filePath, 'w') as file:
			for user in valueList:
				file.write(f"{user}\n")
				
	@staticmethod
	def WriteEmptyFile(filePath: str) -> None:
		"""
		Creates an empty file.
		IMPORTANT: This will overwrite the existing file.
		"""
		with open(filePath, 'w') as file:
			pass
				

if __name__ == "__main__":

	from log_config import LogConfig
	logSetup = LogConfig('utilities_test', 20000000, 5, logLevel=logging.DEBUG)
	testLogger = logSetup.ConfigureLogger()