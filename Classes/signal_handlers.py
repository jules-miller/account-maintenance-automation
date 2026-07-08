################################ SignalHandlers ##########################################
# Configure all signal handlers ##########################################################
# signal handlers are always executed in the main Python thread of the main interpreter ##
##########################################################################################

import signal
import logging
import traceback
import sys

class SignalHanders:
	"""
	Configures handlers for the following signals.
	- SIGINT | 2
	- SIGABRT | 6
	"""

	def __init__(self, logger: logging.Logger, test: bool = 0) -> None:
		self._logger = logger
		self._test = test
		# Add additional signals to handle here
		signal.signal(signal.SIGINT, self._HandleSignal)
		signal.signal(signal.SIGABRT, self._HandleSignal)

	def _HandleSignal(self, sigNum: int, frame) -> None:
		sigName = signal.Signals(sigNum).name
		self._logger.critical(f"Signal Received: {sigName} - {sigNum}.  Exiting now!")
		
		### FOR TESTING ###
		if self._test == 1:
			print(f"Signal Received: {sigName} - {sigNum}.  Exiting now!")
		##################

		sys.exit(10)

if __name__ == '__main__':
	import time
	import os
	from log_config import LogConfig
	logSetup = LogConfig('signalTest', 20000000, 5, logLevel=logging.DEBUG)
	testLogger = logSetup.ConfigureLogger()

	sigTest = SignalHanders(testLogger, test=1)
	currentPID = os.getpid()

	### Testing  - check signalTest.log for details - confirm exit code if running in PS with $LastExitCode ###
	# Only have one test uncommented at a time
	
	# Test 1 - SIGINT
	#signal.raise_signal(signal.SIGINT)

	# Test 2 - SIGABRT
	signal.raise_signal(signal.SIGABRT)
