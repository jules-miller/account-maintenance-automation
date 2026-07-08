############################## LogConfig ###############################
# Use to configure loggers for each BigFix application #################
# To enable debug logging, set: logLevel=logging.DEBUG OR logLevel=10 ##
########################################################################

import logging
from logging.handlers import RotatingFileHandler
import traceback
from pathlib import Path
import sys

class LogConfig:
	"""
	Allows for custom logger configurations.  
	Once the class is instantiated, run ConfigureLogger() to create the logger.
	"""
	def __init__(self, loggerName: str, maxSize: int, maxKeep: int, logLevel: int = logging.INFO) -> None:
		self._loggerName = loggerName # This will double as the name of the log file
		self._maxSize = maxSize
		self._maxKeep = maxKeep

		# Validate logLevel (NOTSET=0, DEBUG=10, INFO=20, WARNING=30, ERROR=40, CRITICAL=50)
		if logLevel not in (0, 10, 20, 30, 40, 50):
			self._logLevel = logging.INFO
		else:
			self._logLevel = logLevel

	# Create getters for fields
	@property
	def maxKeep(self):
		return self._maxKeep
	@property
	def maxSize(self):
		return self._maxSize
	@property
	def logLevel(self):
		return self._logLevel

	def ConfigureLogger(self) -> logging.Logger:
		"""
		Creates the logger object with a rotating file handler.
		"""
		if getattr(sys, 'frozen', False): # If running as bundled exe, this should be true
			logFile = Path(__file__).parent / f"Logs/{self._loggerName}.log"
		else:
			logFile = Path(__file__).parent / f"../Logs/{self._loggerName}.log"

		l = logging.getLogger(self._loggerName)

		if not l.handlers:
			formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
			fileHandler = RotatingFileHandler(logFile, maxBytes=self._maxSize, backupCount=self._maxKeep)
			fileHandler.setFormatter(formatter)

			l.setLevel(self._logLevel)
			l.addHandler(fileHandler)
		
		logger = logging.getLogger(self._loggerName)

		return logger
	
if __name__ == "__main__":

	logSetup = LogConfig('testLog', 20000000, 5, logLevel=logging.DEBUG)
	testLogger = logSetup.ConfigureLogger()
	print(logSetup._logLevel)

	testLogger.info(30 * "#")
	testLogger.debug("Test - debug")
	testLogger.info("Test - info")
	testLogger.error("test - error")
	testLogger.critical("test - critical")
	
	testLogger.info("Exception Logging Testing...")
	try:
		var1 = 1/0
	except Exception as e:
		testLogger.error(f"testLogger.error line: {e}")
		testLogger.error(traceback.format_exc())

	print("Log Level:", logSetup.logLevel)
	print("Logs to Keep:", logSetup.maxKeep)
	print("Log Max Size:", logSetup.maxSize)