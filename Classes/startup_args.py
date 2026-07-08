import argparse
import sys



class StartupArgs():
	"""
	Configures the application description.
	Configures all application arguments.
	"""

	def __init__(self):
		self._parser = self._ConfigureArgs()

	def Parser(self):
		"""
		Use to access the parser's print_help() and exit() functions.
		"""
		return self._parser

	def ParseArgs(self):
		"""
		Use to access the parser's arguments.
		"""
		return self._parser.parse_args()

	def _ConfigureArgs(self):
		parser = argparse.ArgumentParser(
				prog='BigFix Account Maintenance Utility',
				description='''Perform account maintenance on all BigFix components.

		BFI: User notification, AD and DB Removals
		BFC: User notification, AD and DB Removals
		WR: User notification, AD Removals
		Console: User notification

		NOTE: Only one argument is required!''',
				epilog='This was created by ...',
				formatter_class=argparse.RawTextHelpFormatter
		)   

		parser.add_argument("-ra", "--runall", help="Runs the full account maintenance process for all components.", action="store_true")
		parser.add_argument("-ros", "--runonschedule", help="Runs the full account maintenance process at the run_time specified in the config file.  ONLY USE WHEN RUNNING AS A SERVICE.", action="store_true")
		parser.add_argument("-qa", "--queryall", help="Executes read-only queries for all components and writes to file.", action="store_true")
		parser.add_argument("-v", "--version", help="Display the utility version.", action="store_true")
		parser.add_argument("-qbfi", "--querybfi", help="Executes read-only queries for BFI and writes to file.", action="store_true")
		parser.add_argument("-qbfc", "--querybfc", help="Executes read-only queries for BFC and writes to file.", action="store_true")
		parser.add_argument("-qwr", "--querywr", help="Executes read-only queries for WR and writes to file.", action="store_true")
		parser.add_argument("-qcon", "--querycon", help="Executes read-only queries for Console and writes to file.", action="store_true")
		parser.add_argument("-rbfi", "--runbfi", help="Runs the full account maintenance process for BFI.", action="store_true")
		parser.add_argument("-rbfc", "--runbfc", help="Runs the full account maintenance process for BFC.", action="store_true")
		parser.add_argument("-rwr", "--runwr", help="Runs the full account maintenance process for WR.", action="store_true")
		parser.add_argument("-rcon", "--runcon", help="Runs the full account maintenance process for Console.", action="store_true")

		return parser

if __name__ == '__main__':
	appVersion = 1.5
	startup = StartupArgs()
	parser = startup.Parser()
	args = startup.ParseArgs()
	print(type(args))
	argCheck = vars(args)
	if not any(argCheck.values()):
		parser.print_help()
		parser.exit(1)

	if args.version:
		print(appVersion)
		parser.exit(0)
   