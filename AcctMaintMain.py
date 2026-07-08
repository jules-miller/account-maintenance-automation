### BigFix Account Maintenance ###
# Main entry point for the program
"""
A restart is needed to read in a new scheduled execution time for the maintenance when running as a service.
All other settings can be changed during the current runtime.
"""

import datetime
import logging
import traceback
import sys
from pathlib import Path
import os
import schedule
import argparse
import itertools
import time

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'Classes/'))

from log_config import LogConfig
from startup_args import StartupArgs
from settings_config import SettingsConfig
from pre_exec import PreExec
from signal_handlers import SignalHanders
from validation import Validation
from utilities import Utilities
from sql_config import SqlConfig
from send_email import SendEmail
from filter_data import FilterData
from db_connect import DBConnect
from db_query import DBQuery
from db_write import DBWrite
from ad_write import ADWrite

########
appVersion = 1.6
queryOutDir = Path(__file__).parent / "QueryOutput"
flaggedUsersDir = Path(__file__).parent / "FlaggedUsers"
exclusionsDir = Path(__file__).parent / "Exclusions"
psDir = Path(__file__).parent / "PS"
logDir = Path(__file__).parent / "Logs"

uninstallKey = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
adModule = 'activedirectory'

## BFC Vars ##
bfcFlagFile =  os.path.join(flaggedUsersDir, 'bfc_flagged_users.txt')
bfcExcFile = os.path.join(exclusionsDir, 'bfc_excluded_users_upn.txt')
bfcDnFile = os.path.join(psDir, 'BFC_All_Cores_Inactive_DN.txt')
bfcPsFile = os.path.join(psDir, 'bfc_remove_users_AD.ps1')
bfcQoFile = os.path.join(queryOutDir, 'bfc_query_only_output.txt')

## BFI Vars ##
bfiFlagFile =  os.path.join(flaggedUsersDir, 'bfi_flagged_users.txt')
bfiExcFile = os.path.join(exclusionsDir, 'bfi_excluded_users_upn.txt')
bfiDnFile = os.path.join(psDir, 'BFI_All_Cores_Inactive_DN.txt')
bfiPsFile = os.path.join(psDir, 'bfi_remove_users_AD.ps1')
bfiQoFile = os.path.join(queryOutDir, 'bfi_query_only_output.txt')

## WR Vars ##
wrFlagFile =  os.path.join(flaggedUsersDir, 'wr_flagged_users.txt')
wrFlagRemoveFile = os.path.join(flaggedUsersDir, 'wr_flagged_remove_users.txt')
wrExcFile = os.path.join(exclusionsDir, 'wr_excluded_users_upn.txt')
wrDnFile = os.path.join(psDir, 'WR_All_Cores_Inactive_DN.txt')
wrPsFile = os.path.join(psDir, 'wr_remove_users_AD.ps1')
wrQoFile = os.path.join(queryOutDir, 'wr_query_only_output.txt')

## Console Vars ##
conFlagFile =  os.path.join(flaggedUsersDir, 'con_flagged_users.txt')
conExcFile = os.path.join(exclusionsDir, 'con_excluded_users_upn.txt')
conQoFile = os.path.join(queryOutDir, 'con_query_only_output.txt')


########

### Initial Startup ###
def Initialize() -> argparse.ArgumentParser:
	"""
	This only needs to be run once on app startup.
	"""
	startup = StartupArgs()
	parser = startup.Parser() # use the parser to access the help page and exit
	args = startup.ParseArgs() # use this to access the actual arguments

	# Exit if number of passed args is not 1 - returns a dictionary of the the args where the values are True/False \
	# Values will only be True if that specific arg was passed to the app \
	# Loop through each arg and keep count of the number of 'True' args - must be exactly one to proceed
	argCheck2 = sum(1 for arg in vars(args).values() if arg is True)
	if argCheck2 != 1:
		parser.print_help()
		parser.exit(2)
	
	return args

### Setup ###
def Setup() -> SettingsConfig:
	"""
	Run this each time queries or full account maintenance is executed.  
	This will allow new settings to be read without restarting the app.

	The run_time settings are the only settings that will require a restart if changed.
	"""
	logSetup = LogConfig('setupError', 20000000, 5, logLevel=logging.DEBUG)
	setupLogger = logSetup.ConfigureLogger()

	return SettingsConfig(setupLogger)

### Signal Handlers ###
def HandleSigs() -> None:
	"""
	This only needs to be run once on app startup.
	"""
	logSetup = LogConfig('sigHandler', 20000000, 5, logLevel=logging.DEBUG)
	signalLogger = logSetup.ConfigureLogger()

	SignalHanders(signalLogger)

### PreExec checks ###
def PreExecQuery(logger: logging.Logger, useExcl: bool, exclFile: str, odbcVer: int) -> None:
	"""
	Call this prior to each query-only mode run.
	"""
	logger.info("START - pre-execution checks")
	preExec = PreExec(logger)
	
	# Verify Folders
	logger.info("Verifying app folders...")
	verifyQoDir = preExec.FolderCheck(queryOutDir, create=True)
	verifyExcDir = preExec.FolderCheck(exclusionsDir)
	verifyFlsDir = preExec.FolderCheck(flaggedUsersDir, create=True)
	verifyPsDir = preExec.FolderCheck(psDir)

	dirVerifyRes = [verifyQoDir, verifyExcDir, verifyFlsDir, verifyPsDir]
	if 1 in dirVerifyRes or 3 in dirVerifyRes:
		logger.critical("Exiting due to missing app folders.")
		sys.exit(1)

	# Verify ODBC Driver
	logger.info("Verifying ODBC driver...")
	verifyOdbc = preExec.IsSoftwareInstalled(uninstallKey, "DisplayName", f'Microsoft ODBC Driver {odbcVer} for SQL Server')
	if verifyOdbc != True:
		logger.critical(f"Exiting due to missing Microsoft ODBC Driver {odbcVer} for SQL Server")
		sys.exit(1)
	
	# Verify Exclusion File
	logger.info("Verifying Exclusions file...")
	if useExcl == True:
		verifyExcFile = preExec.FileCheck(exclFile)
		if verifyExcFile != True:
			logger.critical("Use exclusions is enabled.  Exiting due to missing exclusions file.")
			sys.exit(1)
	
	logger.info("END - pre-execution checks")

### Query Only BFC ###
def QueryBFC():
	"""
	Writes query-only output to file (bfcQoFile).
	Captures users who meet both the notification and removal threshold.

	Runs against flagged users.
	"""
	currentTime = datetime.datetime.now()
	settings = Setup()
	
	### Configure Logging ###
	if settings.logDebug:
		level = 10
	else:
		level = 20

	logSetup = LogConfig('bfc', settings.logSize, settings.logKeep, logLevel=level)
	bfcLogger = logSetup.ConfigureLogger()
	bfcLogger.info(70 * '#')
	bfcLogger.info("Starting query-only mode...")
	bfcLogger.info(f"ODBC DRIVER VERSION: {settings.odbcVer}")
	bfcLogger.info(f"MAX LOG SIZE (BYTES): {settings.logSize}")
	bfcLogger.info(f"LOGS TO KEEP: {settings.logKeep}")
	bfcLogger.info(f"DEBUG LOGGING: {settings.logDebug}")
	bfcLogger.info(f"NOTIFICATION THRESHOLD: {settings.bfcNotify}")
	bfcLogger.info(f"REMOVAL THRESHOLD: {settings.bfcRemoval}")
	bfcLogger.info(f"USE EXCLUSIONS: {settings.bfcUseExcl}")
	bfcLogger.info(f"DW SERVER: {settings.dwServer}")

	### Pre execution checks ###
	PreExecQuery(bfcLogger, settings.bfcUseExcl, bfcExcFile, settings.odbcVer)
	if settings.dwServer == ['']: # this will be [''] if the setting was empty in the conf file or the setting values did not pass validation
		bfcLogger.critical(f"The DataWarehouse server FQDN is either not set or invalid in {settings.settingsFile}. Exiting BFC Query now!")
		return

	### Query Users ###
	# Configure SQL queries
	bfcLogger.debug("Configuring SQL queries to obtain inactive users...")
	queryConfig = SqlConfig(bfcLogger)
	try:
		queryConfig.bfcQueryNotify = {"notifThres" : settings.bfcNotify, "removThres" : settings.bfcRemoval}
	except TypeError as e:
		bfcLogger.critical(f"An invalid data type was used to configure bfcQueryNotify - {e}")
		return
	except ValueError as e:
		bfcLogger.critical(f"Invalid dictionary keys were used to configure bfcQueryNotify - {e}")
		return

	queryConfig.bfcQueryRemove = settings.bfcRemoval

	# Run queries
	bfcLogger.info("Running SQL queries to obtain inactive users...")
	dbQuery = DBQuery(logger=bfcLogger, odbcVer=settings.odbcVer, server=settings.dwServer[0], db='BFCDW', app="BFC")
	inactiveUsers = dbQuery.QueryInactiveUsers(queryConfig.bfcQueryNotify, queryConfig.bfcQueryRemove)
	dbQuery.DbClose()

	bfcLogger.info("Verifying SQL query status...")
	errVals =['SyntaxError', 'TimeoutError', 'QueryError']
	if len(inactiveUsers["inactiveNotifyUsers"]) != 0:
		if inactiveUsers["inactiveNotifyUsers"][0] in errVals:
			bfcLogger.critical("Exiting due to failed queries.")
			return

	# Filter query data
	bfcLogger.info("Filtering data...")
	try:
		flaggedUsers = FilterData.ReadUsersFile(bfcFlagFile)
	except FileNotFoundError:
		bfcLogger.warning(f"Flagged users file is missing: {bfcFlagFile}")
		flaggedUsers = []
	
	if settings.bfcUseExcl == True:
		exclUsers = FilterData.ReadUsersFile(bfcExcFile)
	else:
		exclUsers = []

	notifyUsers = FilterData.FilterUsers(inactiveUsers["inactiveNotifyUsers"], exclUsers, flaggedUsers)
	removalUsers = FilterData.FilterUsers(inactiveUsers["inactiveRemoveUsers"], exclUsers)
	queryOutput = [f'TimeStamp: {currentTime}', 'Users relevant for notifications:', notifyUsers, 'Users relevant for removal', removalUsers]
	
	# Write query data to file
	bfcLogger.info(f"Writing results to file: {bfcQoFile}")
	Utilities.WriteFileFromList(bfcQoFile, queryOutput)
	bfcLogger.info("Query-only mode complete!")
	return
	
### Query Only BFI ###
def QueryBFI():
	"""
	Writes query-only output to file (bfiQoFile).
	Captures users who meet both the notification and removal threshold.

	Runs against flagged users.
	"""
	currentTime = datetime.datetime.now()
	settings = Setup()
	
	### Configure Logging ###
	if settings.logDebug:
		level = 10
	else:
		level = 20

	logSetup = LogConfig('bfi', settings.logSize, settings.logKeep, logLevel=level)
	bfiLogger = logSetup.ConfigureLogger()
	bfiLogger.info(70 * '#')
	bfiLogger.info("Starting query-only mode...")
	bfiLogger.info(f"ODBC DRIVER VERSION: {settings.odbcVer}")
	bfiLogger.info(f"MAX LOG SIZE (BYTES): {settings.logSize}")
	bfiLogger.info(f"LOGS TO KEEP: {settings.logKeep}")
	bfiLogger.info(f"DEBUG LOGGING: {settings.logDebug}")
	bfiLogger.info(f"NOTIFICATION THRESHOLD: {settings.bfiNotify}")
	bfiLogger.info(f"REMOVAL THRESHOLD: {settings.bfiRemoval}")
	bfiLogger.info(f"USE EXCLUSIONS: {settings.bfiUseExcl}")
	bfiLogger.info(f"DW SERVER: {settings.dwServer}")

	### Pre execution checks ###
	PreExecQuery(bfiLogger, settings.bfiUseExcl, bfiExcFile, settings.odbcVer)
	if settings.dwServer == ['']: # this will be [''] if the setting was empty in the conf file or the setting values did not pass validation
		bfiLogger.critical(f"The DataWarehouse server FQDN is either not set or invalid in {settings.settingsFile}. Exiting BFI Query now!")
		return

	### Query Users ###
	# Configure SQL queries
	bfiLogger.debug("Configuring SQL queries to obtain inactive users...")
	queryConfig = SqlConfig(bfiLogger)
	try:
		queryConfig.bfiQueryNotify = {"notifThres" : settings.bfiNotify, "removThres" : settings.bfiRemoval}
	except TypeError as e:
		bfiLogger.critical(f"An invalid data type was used to configure bfiQueryNotify - {e}")
		return
	except ValueError as e:
		bfiLogger.critical(f"Invalid dictionary keys were used to configure bfiQueryNotify - {e}")
		return
	queryConfig.bfiQueryRemove = settings.bfiRemoval

	# Run queries
	bfiLogger.info("Running SQL queries to obtain inactive users...")
	dbQuery = DBQuery(logger=bfiLogger, odbcVer=settings.odbcVer, server=settings.dwServer[0], db='BFIDW', app="BFI")
	inactiveUsers = dbQuery.QueryInactiveUsers(queryConfig.bfiQueryNotify, queryConfig.bfiQueryRemove)
	dbQuery.DbClose()

	bfiLogger.debug("Verifying SQL query status...")
	errVals =['SyntaxError', 'TimeoutError', 'QueryError']
	if len(inactiveUsers["inactiveNotifyUsers"]) != 0:
		if inactiveUsers["inactiveNotifyUsers"][0] in errVals:
			bfiLogger.critical("Exiting due to failed queries.")
			return

	# Filter query data
	bfiLogger.info("Filtering data...")
	try:
		flaggedUsers = FilterData.ReadUsersFile(bfiFlagFile)
	except FileNotFoundError:
		bfiLogger.warning(f"Flagged users file is missing: {bfiFlagFile}")
		flaggedUsers = []
	
	if settings.bfiUseExcl == True:
		exclUsers = FilterData.ReadUsersFile(bfiExcFile)
	else:
		exclUsers = []

	notifyUsers = FilterData.FilterUsers(inactiveUsers["inactiveNotifyUsers"], exclUsers, flaggedUsers)
	removalUsers = FilterData.FilterUsers(inactiveUsers["inactiveRemoveUsers"], exclUsers)
	queryOutput = [f'TimeStamp: {currentTime}', 'Users relevant for notifications:', notifyUsers, 'Users relevant for removal', removalUsers]
	
	# Write query data to file
	bfiLogger.info(f"Writing results to file: {bfiQoFile}")
	Utilities.WriteFileFromList(bfiQoFile, queryOutput)
	bfiLogger.info("Query-only mode complete!")
	return

### Query Only WR ###
def QueryWR():
	"""
	Writes query-only output to file (wrQoFile).
	Captures users who meet both the notification and removal threshold.

	Runs against flagged users.
	"""
	currentTime = datetime.datetime.now()
	settings = Setup()
	
	### Configure Logging ###
	if settings.logDebug:
		level = 10
	else:
		level = 20

	logSetup = LogConfig('wr', settings.logSize, settings.logKeep, logLevel=level)
	wrLogger = logSetup.ConfigureLogger()
	wrLogger.info(70 * '#')
	wrLogger.info("Starting query-only mode...")
	wrLogger.info(f"ODBC DRIVER VERSION: {settings.odbcVer}")
	wrLogger.info(f"MAX LOG SIZE (BYTES): {settings.logSize}")
	wrLogger.info(f"LOGS TO KEEP: {settings.logKeep}")
	wrLogger.info(f"DEBUG LOGGING: {settings.logDebug}")
	wrLogger.info(f"NOTIFICATION THRESHOLD: {settings.wrNotify}")
	wrLogger.info(f"REMOVAL THRESHOLD: {settings.wrRemoval}")
	wrLogger.info(f"USE EXCLUSIONS: {settings.wrUseExcl}")
	wrLogger.info(f"WR SERVERS: {settings.wrServers}")

	### Pre execution checks ###
	PreExecQuery(wrLogger, settings.wrUseExcl, wrExcFile, settings.odbcVer)
	if settings.wrServers == ['']: # this will be [''] if the setting was empty in the conf file or the setting values did not pass validation
		wrLogger.critical(f"The Web Reports server FQDNs are either not set or invalid in {settings.settingsFile}. Exiting WR Query now!")
		return

	### Query Users ###
	# Configure SQL queries
	wrLogger.debug("Configuring SQL queries to obtain active and inactive users...")
	queryConfig = SqlConfig(wrLogger)
	queryConfig.wrQuNotifActi = settings.wrNotify
	queryConfig.wrQuRemovActi = settings.wrRemoval
	try:
		queryConfig.wrQuNotifInact = {"notifThres" : settings.wrNotify, "removThres" : settings.wrRemoval}
	except TypeError as e:
		wrLogger.critical(f"An invalid data type was used to configure wrQuNotifInact - {e}")
		return
	except ValueError as e:
		wrLogger.critical(f"Invalid dictionary keys were used to configure wrQuNotifInact - {e}")
		return
	
	queryConfig.wrQuRemovInact = settings.wrRemoval

	# Run queries
	wrQueries = {}
	for item in settings.wrServers:
		wrLogger.info(f"Running SQL queries for {item}")
		dbQuery = DBQuery(logger=wrLogger, odbcVer=settings.odbcVer, server=item, db='BESReporting', app="WR")
		queryResults = dbQuery.QueryAllUsers(qNotifyInact=queryConfig.wrQuNotifInact, qRemoveInact=queryConfig.wrQuRemovInact, qNotifyAct=queryConfig.wrQuNotifActi, qRemoveAct=queryConfig.wrQuRemovActi)
		dbQuery.DbClose()
		# Store the result in wrQueries - The value for each key (server name) will be a dictionary containing all four query results
		wrQueries[item] = queryResults

	wrLogger.debug("Verifying SQL query status...")
	errVals =['SyntaxError', 'TimeoutError', 'QueryError']
	for key, val in wrQueries.items():
		if len(val["inactiveNotifyUsers"]) != 0:
			if val["inactiveNotifyUsers"][0] in errVals:
				wrLogger.critical("Exiting due to failed queries.")
				return
		if len(val["activeNotifyUsers"]) != 0:
			if val["activeNotifyUsers"][0] in errVals:
				wrLogger.critical("Exiting due to failed queries.")
				return

	# Combine lists from all cores and de-dupe (val is the server name)
	allInactNotif = list(itertools.chain.from_iterable([val["inactiveNotifyUsers"] for key, val in wrQueries.items()]))
	allInactRemov = list(itertools.chain.from_iterable([val["inactiveRemoveUsers"] for key, val in wrQueries.items()]))
	allActNotif = list(itertools.chain.from_iterable([val["activeNotifyUsers"] for key, val in wrQueries.items()]))
	allActRemov = list(itertools.chain.from_iterable([val["activeRemoveUsers"] for key, val in wrQueries.items()]))

	deDupInactNotif = FilterData.DedupeList(allInactNotif)
	deDupInactRemov = FilterData.DedupeList(allInactRemov)
	deDupActNotif = FilterData.DedupeList(allActNotif)
	deDupActRemov = FilterData.DedupeList(allActRemov)

	# Filter query data
	wrLogger.info("Filtering data...")
	try:
		flaggedUsers = FilterData.ReadUsersFile(wrFlagFile)
	except FileNotFoundError:
		wrLogger.warning(f"Flagged users file is missing: {wrFlagFile}")
		flaggedUsers = []

	try:
		flaggedRemoved = FilterData.ReadUsersFile(wrFlagRemoveFile)
	except FileNotFoundError:
		wrLogger.warning(f"Flagged Removed users file is missing: {wrFlagRemoveFile}")
		flaggedRemoved = []
	
	if settings.wrUseExcl == True:
		exclUsers = FilterData.ReadUsersFile(wrExcFile)
	else:
		exclUsers = []
	
	notifyUsers = FilterData.FilterUsers(inactiveList=deDupInactNotif, exclList=exclUsers, flagList=flaggedUsers, activeList=deDupActNotif)
	removalUsers = FilterData.FilterUsers(inactiveList=deDupInactRemov, exclList=exclUsers, flagList=flaggedRemoved, activeList=deDupActRemov)
	queryOutput = [f'TimeStamp: {currentTime}', 'Users relevant for notifications:', notifyUsers, 'Users relevant for removal', removalUsers]
	
	# Write query data to file
	wrLogger.info(f"Writing results to file: {wrQoFile}")
	Utilities.WriteFileFromList(wrQoFile, queryOutput)
	wrLogger.info("Query-only mode complete!")
	return

### Query Only Con ###
def QueryCon():
	"""
	Writes query-only output to file (conQoFile).
	Captures users who meet both the notification and removal threshold.

	Runs against flagged users.
	"""
	currentTime = datetime.datetime.now()
	settings = Setup()
	
	### Configure Logging ###
	if settings.logDebug:
		level = 10
	else:
		level = 20

	logSetup = LogConfig('console', settings.logSize, settings.logKeep, logLevel=level)
	conLogger = logSetup.ConfigureLogger()
	conLogger.info(70 * '#')
	conLogger.info("Starting query-only mode...")
	conLogger.info(f"ODBC DRIVER VERSION: {settings.odbcVer}")
	conLogger.info(f"MAX LOG SIZE (BYTES): {settings.logSize}")
	conLogger.info(f"LOGS TO KEEP: {settings.logKeep}")
	conLogger.info(f"DEBUG LOGGING: {settings.logDebug}")
	conLogger.info(f"NOTIFICATION THRESHOLD: {settings.conNotify}")
	conLogger.info(f"REMOVAL THRESHOLD: {settings.conRemoval}")
	conLogger.info(f"USE EXCLUSIONS: {settings.conUseExcl}")
	conLogger.info(f"DW SERVER: {settings.dwServer}")

	### Pre execution checks ###
	PreExecQuery(conLogger, settings.conUseExcl, conExcFile, settings.odbcVer)
	if settings.dwServer == ['']: # this will be [''] if the setting was empty in the conf file or the setting values did not pass validation
		conLogger.critical(f"The DataWarehouse server FQDN is either not set or invalid in {settings.settingsFile}. Exiting Console Query now!")
		return

	### Query Users ###
	# Configure SQL queries
	conLogger.debug("Configuring SQL queries to obtain inactive users...")
	queryConfig = SqlConfig(conLogger)
	try:
		queryConfig.conQueryNotify = {"notifThres" : settings.conNotify, "removThres" : settings.conRemoval}
	except TypeError as e:
		conLogger.critical(f"An invalid data type was used to configure conQueryNotify - {e}")
		return
	except ValueError as e:
		conLogger.critical(f"Invalid dictionary keys were used to configure conQueryNotify - {e}")
		return
		
	queryConfig.conQueryRemove = settings.conRemoval

	# Run queries
	conLogger.info("Running SQL queries to obtain inactive users...")
	dbQuery = DBQuery(logger=conLogger, odbcVer=settings.odbcVer, server=settings.dwServer[0], db='BFDW', app="CON")
	inactiveUsers = dbQuery.QueryConUsers(queryConfig.conQueryNotify, queryConfig.conQueryRemove)
	dbQuery.DbClose()
	
	conLogger.debug("Verifying SQL query status...")
	errVals =['SyntaxError', 'TimeoutError', 'QueryError']
	if type(inactiveUsers["inactiveNotifyUsers"]) == str:
		if inactiveUsers["inactiveNotifyUsers"] in errVals:
			conLogger.critical("Exiting due to failed queries.")
			return
	
	# Filter query data
	conLogger.info("Filtering data...")
	try:
		flaggedUsers = FilterData.ReadUsersFile(conFlagFile)
	except FileNotFoundError:
		conLogger.warning(f"Flagged users file is missing: {conFlagFile}")
		flaggedUsers = []
	
	if settings.conUseExcl == True:
		exclUsers = FilterData.ReadUsersFile(conExcFile)
	else:
		exclUsers = []

	# Convert inactive users keys (these are the '0' account samAccountNames) into a list
	inactiveNotifyUserList = FilterData.ConvertKeystoList(inactiveUsers["inactiveNotifyUsers"])
	inactiveRemoveUserList = FilterData.ConvertKeystoList(inactiveUsers["inactiveRemoveUsers"])
	
	# Filter the user lists
	filtNotifyUsers = FilterData.FilterUsers(inactiveNotifyUserList, exclUsers, flaggedUsers)
	filtRemovalUsers = FilterData.FilterUsers(inactiveRemoveUserList, exclUsers)
	
	# Create a new dictionary where only valid inactive users are present
	notifyUsers = {key: val for key, val in inactiveUsers["inactiveNotifyUsers"].items() if key.lower() in filtNotifyUsers}
	removalUsers = {key: val for key, val in inactiveUsers["inactiveRemoveUsers"].items() if key.lower() in filtRemovalUsers}

	# Skip notify user parsing if empty
	if len(notifyUsers) > 0:
		# Convert the description field (values in the inactiveUsers["inactiveNotifyUsers"] dictionary to a list)
		notifyDescrList: list = FilterData.ConvertValuestoList(notifyUsers)

		# Pull the MEA samAccountName out of the description (the values in the dictionary)
		notifySam: str = FilterData.FilterConDescr(notifyDescrList)

		# Set the sam to upn query
		try:
			queryConfig.samToUpnQuery = notifySam
		except ValueError as e:
			conLogger.critical(f"Invalid user string format when configuring samToUpnQuery. Exiting now. - {e}")
			return

		# Query VADW to return the UPNs of each user relevant for notifications
		conLogger.info("Running SQL queries to convert samAccountNames to UPNs...")
		dbQuery = DBQuery(logger=conLogger, odbcVer=settings.odbcVer, server=settings.dwServer[0], db='VADW', app="CON")
		try:
			notifyUpn = dbQuery.QueryVadw(queryConfig.samToUpnQuery)
		except ValueError as e:
			conLogger.error(f"Incorrect DB specified: {e}")
			notifyUpn = ['QueryError']
		finally:
			dbQuery.DbClose()

		errVals =['SyntaxError', 'TimeoutError', 'QueryError']
		if len(notifyUpn) != 0:
			if notifyUpn[0] in errVals:
				notifyUpn = 'Error querying user UPNs'
	else:
		notifyUpn = 'None'


	queryOutput = [f'TimeStamp: {currentTime}', 'Users relevant for notifications:', notifyUpn, 'Users relevant for removal', FilterData.ConvertKeystoList(removalUsers)]
	
	# Write query data to file
	conLogger.info(f"Writing results to file: {conQoFile}")
	Utilities.WriteFileFromList(conQoFile, queryOutput)
	conLogger.info("Query-only mode complete!")
	return

### Execute BFC Account Maintenance ###
def RunBFC():
	"""
	Executes the full account maintenance process for BFC.
	"""
	currentTime = datetime.datetime.now()
	settings = Setup()
	
	### Configure Logging ###
	if settings.logDebug:
		level = 10
	else:
		level = 20

	logSetup = LogConfig('bfc', settings.logSize, settings.logKeep, logLevel=level)
	bfcLogger = logSetup.ConfigureLogger()
	bfcLogger.info(70 * '#')
	bfcLogger.info("Starting BFC Account Maintenance...")
	bfcLogger.info(f"ODBC DRIVER VERSION: {settings.odbcVer}")
	bfcLogger.info(f"SMTP RECIPIENTS: {settings.smtpList}")
	bfcLogger.info(f"SMTP TIMEOUT: {settings.smtpTmout}")
	bfcLogger.info(f"MAX LOG SIZE (BYTES): {settings.logSize}")
	bfcLogger.info(f"LOGS TO KEEP: {settings.logKeep}")
	bfcLogger.info(f"DEBUG LOGGING: {settings.logDebug}")
	bfcLogger.info(f"NOTIFICATION THRESHOLD: {settings.bfcNotify}")
	bfcLogger.info(f"REMOVAL THRESHOLD: {settings.bfcRemoval}")
	bfcLogger.info(f"USE EXCLUSIONS: {settings.bfcUseExcl}")
	bfcLogger.info(f"SCHEDULED RUN TIME: {settings.bfcRunTime}")
	bfcLogger.info(f"DW SERVER: {settings.dwServer}")
	bfcLogger.info(f"BFC SERVERS: {settings.bfcServers}")

	# Setup SendEmail Instance
	email = SendEmail(logger=bfcLogger, app='BigFix Compliance', timeout=settings.smtpTmout, notifyDay=settings.bfcNotify, removalDay=settings.bfcRemoval)
	try:
		email.recipients = settings.smtpList
	except TypeError as e:
		bfcLogger.critical(f"Invalid smtp recipient list '{settings.smtpList}'. Exiting now. {e}")
		return

	### PreExec checks ###
	bfcLogger.info("START - pre-execution checks")
	preExec = PreExec(bfcLogger)
	if settings.dwServer == ['']: # this will be [''] if the setting was empty in the conf file or the setting values did not pass validation
		bfcLogger.critical(f"The DataWarehouse server FQDN is either not set or invalid in {settings.settingsFile}. Exiting BFC maintenance now!")
		return
	if settings.bfcServers == ['']: # this will be [''] if the setting was empty in the conf file or the setting values did not pass validation
		bfcLogger.critical(f"The BFC server FQDNs are either not set or invalid in {settings.settingsFile}. Exiting BFC maintenance now!")
		return

	# Verify Folders
	bfcLogger.info("Verifying app folders...")
	verifyQoDir = preExec.FolderCheck(queryOutDir, create=True)
	verifyExcDir = preExec.FolderCheck(exclusionsDir)
	verifyFlsDir = preExec.FolderCheck(flaggedUsersDir, create=True)
	verifyPsDir = preExec.FolderCheck(psDir)

	dirVerifyRes = [verifyQoDir, verifyExcDir, verifyFlsDir, verifyPsDir]
	if 1 in dirVerifyRes or 3 in dirVerifyRes:
		bfcLogger.warning("Sending error notification and exiting due to missing app folders.")
		email.SendMessage('err', msg="One or more application folders are missing.")
		sys.exit(1)

	# Verify ODBC Driver
	bfcLogger.info("Verifying ODBC driver...")
	verifyOdbc = preExec.IsSoftwareInstalled(uninstallKey, "DisplayName", f'Microsoft ODBC Driver {settings.odbcVer} for SQL Server')
	if verifyOdbc != True:
		bfcLogger.warning(f"Sending error notification and exiting due to missing Microsoft ODBC Driver {settings.odbcVer} for SQL Server")
		email.SendMessage('err', msg=f"The ODBC driver is missing: Microsoft ODBC Driver {settings.odbcVer} for SQL Server.")
		sys.exit(1)

	# Verify PS Module
	bfcLogger.info("Verifying the AD PowerShell Module...")
	verifyAdMod = preExec.PsModuleCheck(adModule)
	if verifyAdMod != True:
		bfcLogger.warning(f"Sending error notification and exiting due to missing PowerShell module: {adModule}")
		email.SendMessage('err', msg=f"The following PowerShell module is missing: {adModule}")
	
	# Verify Exclusion File
	bfcLogger.info("Verifying Exclusions file...")
	if settings.bfcUseExcl == True:
		verifyExcFile = preExec.FileCheck(bfcExcFile)
		if verifyExcFile != True:
			bfcLogger.critical("Use exclusions is enabled.  Sending error notification and exiting due to missing exclusions file.")
			email.SendMessage('err', msg=f"The exclusions file is missing: {bfcExcFile}")
			return

	bfcLogger.info("END - pre-execution checks")

	### Query Users ###
	# Configure SQL queries
	bfcLogger.debug("Configuring SQL queries for inactive users...")
	queryConfig = SqlConfig(bfcLogger)
	try:
		queryConfig.bfcQueryNotify = {"notifThres" : settings.bfcNotify, "removThres" : settings.bfcRemoval}
	except TypeError as e:
		bfcLogger.critical(f"An invalid data type was used to configure bfcQueryNotify. Exiting now. - {e}")
		email.SendMessage('err', msg=f"An invalid data type was used to configure bfcQueryNotify: {e}")
		return
	except ValueError as e:
		bfcLogger.critical(f"Invalid dictionary keys were used to configure bfcQueryNotify. Exiting now. - {e}")
		email.SendMessage('err', msg=f"Invalid dictionary keys were used to configure bfcQueryNotify: {e}")
		return

	queryConfig.bfcQueryRemove = settings.bfcRemoval

	# Run queries
	bfcLogger.info("Running SQL queries for inactive users...")
	bfcDwQuery = DBQuery(logger=bfcLogger, odbcVer=settings.odbcVer, server=settings.dwServer[0], db='BFCDW', app="BFC")
	inactiveUsers = bfcDwQuery.QueryInactiveUsers(queryConfig.bfcQueryNotify, queryConfig.bfcQueryRemove)
	bfcDwQuery.DbClose()

	# Exit if queries failed
	bfcLogger.debug("Verifying SQL query status...")
	errVals =['SyntaxError', 'TimeoutError', 'QueryError']
	if len(inactiveUsers["inactiveNotifyUsers"]) != 0:
		if inactiveUsers["inactiveNotifyUsers"][0] in errVals:
			bfcLogger.critical("Sending error notification and exiting due to failed queries.")
			email.SendMessage('err', msg=f"SQL queries failed: {inactiveUsers["inactiveNotifyUsers"]}")
			return

	# Filter query data
	bfcLogger.info("Filtering data...")
	try:
		flaggedUsers = FilterData.ReadUsersFile(bfcFlagFile)
	except FileNotFoundError:
		bfcLogger.warning(f"Flagged users file is missing: {bfcFlagFile}")
		flaggedUsers = []
	
	if settings.bfcUseExcl == True:
		exclUsers = FilterData.ReadUsersFile(bfcExcFile)
	else:
		exclUsers = []

	bfcLogger.debug(f"Flagged Users: {flaggedUsers}")
	bfcLogger.debug(f"Excluded Users: {exclUsers}")

	# Filter each user list and assign to their own object
	notifyUsers = FilterData.FilterUsers(inactiveUsers["inactiveNotifyUsers"], exclUsers, flaggedUsers)
	removalUsers = FilterData.FilterUsers(inactiveUsers["inactiveRemoveUsers"], exclUsers)

	### Send Notifications ###
	if len(notifyUsers) > 0:
		bfcLogger.info("Starting user notification process...")
		try:
			email.recipients = notifyUsers # set email recipients to the list of filtered inactive users
		except TypeError as e:
			bfcLogger.critical(f"Invalid smtp recipient list - '{notifyUsers}'. Exiting now. {e}")
			return
		bfcLogger.debug(f"Notification List: {notifyUsers}")
		notifyStatus = email.SendMessage('notify') # Loops through all users and sends individual notification emails
		try:
			# Reset email recipients back to the list from the settings.conf file
			email.recipients = settings.smtpList
		except TypeError as e:
			bfcLogger.critical(f"Invalid smtp recipient list - '{settings.smtpList}'. Exiting now. {e}")
			return

		# Overwrite the flagged users file with the original unfiltered inactive user list
		bfcLogger.info("Overwriting flagged users file")
		Utilities.WriteFileFromList(bfcFlagFile, inactiveUsers["inactiveNotifyUsers"])
	else:
		bfcLogger.info("User notification list empty. Skipping notification process.")
		notifyStatus = 2 # Notification list is empty

	match notifyStatus:
		case 0:
			notifyStat = 'Success'
		case 1:
			notifyStat = 'Failed'
		case 2:
			notifyStat = 'Skipped'

	# Exit if removal list is empty
	if len(removalUsers) == 0:
		completeStatus = {}
		completeStatus['Component'] = 'BigFix Compliance'
		completeStatus['Last Run'] = currentTime
		completeStatus['User Notification Status'] = notifyStat
		completeStatus['AD Removal Status'] = 'Skipped'
		completeStatus['DB Removal Status'] = 'Skipped'
		completeStatus['User Notifications'] = notifyUsers
		completeStatus['User Removals'] = ''
		bfcLogger.info("User removal list is empty. Sending complete message and exiting.")
		email.SendMessage('complete', statusValues=completeStatus)
		return

	### Removal Setup ###
	bfcLogger.debug("Configuring SQL query to convert UPNs to DNs...")
	usrRemovStrSql = FilterData.FormatSQL(removalUsers) # Format user list for sql
	try:
		queryConfig.upnToDnQuery = usrRemovStrSql
	except ValueError as e:
		bfcLogger.critical(f"Invalid user string format when configuring upnToDnQuery. Exiting now. - {e}")
		email.SendMessage('err', msg=f"Invalid user string format when configuring upnToDnQuery: {e}")
		return

	# Convert removal UPNs to DNs
	bfcLogger.info("Running SQL queries to convert UPNs to DNs...")
	vadwQuery = DBQuery(logger=bfcLogger, odbcVer=settings.odbcVer, server=settings.dwServer[0], db='VADW', app="BFC")
	try:
		removalDNs = vadwQuery.QueryVadw(queryConfig.upnToDnQuery)
	except ValueError as e:
		bfcLogger.error(f"Incorrect DB specified: {e}")
		removalDNs = ['QueryError']
	finally:
		vadwQuery.DbClose()

	# Exit if query failed
	errVals =['SyntaxError', 'TimeoutError', 'QueryError']
	if len(removalDNs) != 0:
		if removalDNs[0] in errVals:
			bfcLogger.critical("Sending error notification and exiting due to failed queries.")
			email.SendMessage('err', msg=f"SQL query to convert UPNs to DNs failed: {removalDNs[0]}")
			return

	# Write DNs to file
	bfcLogger.debug(f"Writing DNs to file: {bfcDnFile}")
	Utilities.WriteFileFromList(bfcDnFile, removalDNs)

	### Remove Users ###
	# Remove Users from AD
	adRemove = ADWrite(bfcLogger, 'bfc')
	try:
		adRemoveStat = adRemove.WriteAD()
	except FileNotFoundError:
		adRemoveStat = False

	# Mark users deleted in DB
	if adRemoveStat == True:
		bfcLogger.info("AD removal successful")
		bfcLogger.info("Configuring SQL transaction to mark users as deleted in the DB")
		adRemoveStatus = 'Success'
		try:
			queryConfig.delTransBfc = usrRemovStrSql
		except ValueError as e:
			bfcLogger.critical(f"Invalid user string format when configuring delTransBfc. Exiting now. - {e}")
			email.SendMessage('err', msg=f"Invalid user string format when configuring delTransBfc: {e}.  Aborted maintenance after AD removals but before DB removals.")
			return
		dbRemoveStat = {}
		for item in settings.bfcServers:
			dbWrite = DBWrite(logger=bfcLogger, odbcVer=settings.odbcVer, server=item, db='tem_analytics', app="BFC")
			status = dbWrite.MarkDeleted(queryConfig.delTransBfc)
			dbWrite.DbClose()
			# Convert status to friendly values
			if status == 0:
				stat = "Success"
			else:	
				stat = "Failed"
			dbRemoveStat[item] = stat
	else:
		bfcLogger.warning("AD removal failed. Skipping DB removal...")
		dbRemoveStat = 'Skipped'
		adRemoveStatus = 'Failed'

	# Send All complete message
	completeStatus = {}
	completeStatus['Component'] = 'BigFix Compliance'
	completeStatus['Last Run'] = currentTime
	completeStatus['User Notification Status'] = notifyStat
	completeStatus['AD Removal Status'] = adRemoveStatus
	completeStatus['DB Removal Status'] = dbRemoveStat
	completeStatus['User Notifications'] = notifyUsers
	completeStatus['User Removals'] = removalUsers
	email.SendMessage('complete', statusValues=completeStatus)
	bfcLogger.info("BFC account maintenance is complete!")
	
	return


### Execute BFI Account Maintenance ###
def RunBFI():
	"""
	Executes the full account maintenance process for BFI.
	"""
	currentTime = datetime.datetime.now()
	settings = Setup()
	
	### Configure Logging ###
	if settings.logDebug:
		level = 10
	else:
		level = 20

	logSetup = LogConfig('bfi', settings.logSize, settings.logKeep, logLevel=level)
	bfiLogger = logSetup.ConfigureLogger()
	bfiLogger.info(70 * '#')
	bfiLogger.info("Starting BFI Account Maintenance...")
	bfiLogger.info(f"ODBC DRIVER VERSION: {settings.odbcVer}")
	bfiLogger.info(f"SMTP RECIPIENTS: {settings.smtpList}")
	bfiLogger.info(f"SMTP TIMEOUT: {settings.smtpTmout}")
	bfiLogger.info(f"MAX LOG SIZE (BYTES): {settings.logSize}")
	bfiLogger.info(f"LOGS TO KEEP: {settings.logKeep}")
	bfiLogger.info(f"DEBUG LOGGING: {settings.logDebug}")
	bfiLogger.info(f"NOTIFICATION THRESHOLD: {settings.bfiNotify}")
	bfiLogger.info(f"REMOVAL THRESHOLD: {settings.bfiRemoval}")
	bfiLogger.info(f"USE EXCLUSIONS: {settings.bfiUseExcl}")
	bfiLogger.info(f"SCHEDULED RUN TIME: {settings.bfiRunTime}")
	bfiLogger.info(f"DW SERVER: {settings.dwServer}")
	bfiLogger.info(f"BFI SERVERS: {settings.bfiServers}")

	# Setup SendEmail Instance
	email = SendEmail(logger=bfiLogger, app='BigFix Inventory', timeout=settings.smtpTmout, notifyDay=settings.bfiNotify, removalDay=settings.bfiRemoval)
	try:
		email.recipients = settings.smtpList
	except TypeError as e:
		bfiLogger.critical(f"Invalid smtp recipient list - '{settings.smtpList}'. Exiting now. {e}")
		return

	### PreExec checks ###
	bfiLogger.info("START - pre-execution checks")
	preExec = PreExec(bfiLogger)
	if settings.dwServer == ['']: # this will be [''] if the setting was empty in the conf file or the setting values did not pass validation
		bfiLogger.critical(f"The DataWarehouse server FQDN is either not set or invalid in {settings.settingsFile}. Exiting BFI maintenance now!")
		return
	if settings.bfiServers == ['']: # this will be [''] if the setting was empty in the conf file or the setting values did not pass validation
		bfiLogger.critical(f"The BFI server FQDNs are either not set or invalid in {settings.settingsFile}. Exiting BFI maintenance now!")
		return
	
	# Verify Folders
	bfiLogger.info("Verifying app folders...")
	verifyQoDir = preExec.FolderCheck(queryOutDir, create=True)
	verifyExcDir = preExec.FolderCheck(exclusionsDir)
	verifyFlsDir = preExec.FolderCheck(flaggedUsersDir, create=True)
	verifyPsDir = preExec.FolderCheck(psDir)

	dirVerifyRes = [verifyQoDir, verifyExcDir, verifyFlsDir, verifyPsDir]
	if 1 in dirVerifyRes or 3 in dirVerifyRes:
		bfiLogger.warning("Sending error notification and exiting due to missing app folders.")
		email.SendMessage('err', msg="One or more application folders are missing.")
		sys.exit(1)

	# Verify ODBC Driver
	bfiLogger.info("Verifying ODBC driver...")
	verifyOdbc = preExec.IsSoftwareInstalled(uninstallKey, "DisplayName", f'Microsoft ODBC Driver {settings.odbcVer} for SQL Server')
	if verifyOdbc != True:
		bfiLogger.warning(f"Sending error notification and exiting due to missing Microsoft ODBC Driver {settings.odbcVer} for SQL Server")
		email.SendMessage('err', msg=f"The ODBC driver is missing: Microsoft ODBC Driver {settings.odbcVer} for SQL Server.")
		sys.exit(1)

	# Verify PS Module
	bfiLogger.info("Verifying the AD PowerShell Module...")
	verifyAdMod = preExec.PsModuleCheck(adModule)
	if verifyAdMod != True:
		bfiLogger.warning(f"Sending error notification and exiting due to missing PowerShell module: {adModule}")
		email.SendMessage('err', msg=f"The following PowerShell module is missing: {adModule}")
	
	# Verify Exclusion File
	bfiLogger.info("Verifying Exclusions file...")
	if settings.bfiUseExcl == True:
		verifyExcFile = preExec.FileCheck(bfiExcFile)
		if verifyExcFile != True:
			bfiLogger.critical("Use exclusions is enabled.  Sending error notification and exiting due to missing exclusions file.")
			email.SendMessage('err', msg=f"The exclusions file is missing: {bfiExcFile}")
			return

	bfiLogger.info("END - pre-execution checks")

	### Query Users ###
	# Configure SQL queries
	bfiLogger.debug("Configuring SQL queries for inactive users...")
	queryConfig = SqlConfig(bfiLogger)
	try:
		queryConfig.bfiQueryNotify = {"notifThres" : settings.bfiNotify, "removThres" : settings.bfiRemoval}
	except TypeError as e:
		bfiLogger.critical(f"An invalid data type was used to configure bfiQueryNotify. Exiting now. - {e}")
		email.SendMessage('err', msg=f"An invalid data type was used to configure bfiQueryNotify: {e}")
		return
	except ValueError as e:
		bfiLogger.critical(f"Invalid dictionary keys were used to configure bfiQueryNotify. Exiting now. - {e}")
		email.SendMessage('err', msg=f"Invalid dictionary keys were used to configure bfiQueryNotify: {e}")
		return
	
	queryConfig.bfiQueryRemove = settings.bfiRemoval

	# Run queries
	bfiLogger.info("Running SQL queries for inactive users...")
	bfiDwQuery = DBQuery(logger=bfiLogger, odbcVer=settings.odbcVer, server=settings.dwServer[0], db='BFIDW', app="BFI")
	inactiveUsers = bfiDwQuery.QueryInactiveUsers(queryConfig.bfiQueryNotify, queryConfig.bfiQueryRemove)
	bfiDwQuery.DbClose()

	# Exit if queries failed
	bfiLogger.debug("Verifying SQL query status...")
	errVals =['SyntaxError', 'TimeoutError', 'QueryError']
	if len(inactiveUsers["inactiveNotifyUsers"]) != 0:
		if inactiveUsers["inactiveNotifyUsers"][0] in errVals:
			bfiLogger.critical("Sending error notification and exiting due to failed queries.")
			email.SendMessage('err', msg=f"SQL queries failed: {inactiveUsers["inactiveNotifyUsers"]}")
			return

	# Filter query data
	bfiLogger.info("Filtering data...")
	try:
		flaggedUsers = FilterData.ReadUsersFile(bfiFlagFile)
	except FileNotFoundError:
		bfiLogger.warning(f"Flagged users file is missing: {bfiFlagFile}")
		flaggedUsers = []
	
	if settings.bfiUseExcl == True:
		exclUsers = FilterData.ReadUsersFile(bfiExcFile)
	else:
		exclUsers = []

	bfiLogger.debug(f"Flagged Users: {flaggedUsers}")
	bfiLogger.debug(f"Excluded Users: {exclUsers}")

	# Filter each user list and assign to their own object
	notifyUsers = FilterData.FilterUsers(inactiveUsers["inactiveNotifyUsers"], exclUsers, flaggedUsers)
	removalUsers = FilterData.FilterUsers(inactiveUsers["inactiveRemoveUsers"], exclUsers)

	### Send Notifications ###
	if len(notifyUsers) > 0:
		bfiLogger.info("Starting user notification process...")
		try:
			email.recipients = notifyUsers # set email recipients to the list of filtered inactive users
		except TypeError as e:
			bfiLogger.critical(f"Invalid smtp recipient list - '{notifyUsers}'. Exiting now. {e}")
			return
		bfiLogger.debug(f"Notification List: {notifyUsers}")
		notifyStatus = email.SendMessage('notify') # Loops through all users and sends individual notification emails
		try:
			# Reset email recipients back to the list from the settings.conf file
			email.recipients = settings.smtpList
		except TypeError as e:
			bfiLogger.critical(f"Invalid smtp recipient list - '{settings.smtpList}'. Exiting now. {e}")
			return

		# Overwrite the flagged users file with the original unfiltered inactive user list
		bfiLogger.info("Overwriting flagged users file")
		Utilities.WriteFileFromList(bfiFlagFile, inactiveUsers["inactiveNotifyUsers"])
	else:
		bfiLogger.info("User notification list empty. Skipping notification process.")
		notifyStatus = 2 # Notification list is empty

	match notifyStatus:
		case 0:
			notifyStat = 'Success'
		case 1:
			notifyStat = 'Failed'
		case 2:
			notifyStat = 'Skipped'

	# Exit if removal list is empty
	if len(removalUsers) == 0:
		completeStatus = {}
		completeStatus['Component'] = 'BigFix Inventory'
		completeStatus['Last Run'] = currentTime
		completeStatus['User Notification Status'] = notifyStat
		completeStatus['AD Removal Status'] = 'Skipped'
		completeStatus['DB Removal Status'] = 'Skipped'
		completeStatus['User Notifications'] = notifyUsers
		completeStatus['User Removals'] = ''
		bfiLogger.info("User removal list is empty. Sending complete message and exiting.")
		email.SendMessage('complete', statusValues=completeStatus)
		return

	### Removal Setup ###
	bfiLogger.debug("Configuring SQL query to convert UPNs to DNs...")
	usrRemovStrSql = FilterData.FormatSQL(removalUsers) # Format user list for sql
	try:
		queryConfig.upnToDnQuery = usrRemovStrSql
	except ValueError as e:
		bfiLogger.critical(f"Invalid user string format when configuring upnToDnQuery. Exiting now. - {e}")
		email.SendMessage('err', msg=f"Invalid user string format when configuring upnToDnQuery: {e}")
		return

	# Convert removal UPNs to DNs
	bfiLogger.info("Running SQL queries to convert UPNs to DNs...")
	vadwQuery = DBQuery(logger=bfiLogger, odbcVer=settings.odbcVer, server=settings.dwServer[0], db='VADW', app="BFI")
	try:
		removalDNs = vadwQuery.QueryVadw(queryConfig.upnToDnQuery)
	except ValueError as e:
		bfiLogger.error(f"Incorrect DB specified: {e}")
		removalDNs = ['QueryError']
	finally:
		vadwQuery.DbClose()

	# Exit if query failed
	errVals =['SyntaxError', 'TimeoutError', 'QueryError']
	if len(removalDNs) != 0:
		if removalDNs[0] in errVals:
			bfiLogger.critical("Sending error notification and exiting due to failed queries.")
			email.SendMessage('err', msg=f"SQL query to convert UPN to DN failed: {removalDNs[0]}")
			return

	# Write DNs to file
	bfiLogger.debug(f"Writing DNs to file: {bfiDnFile}")
	Utilities.WriteFileFromList(bfiDnFile, removalDNs)

	### Remove Users ###
	# Remove Users from AD
	adRemove = ADWrite(bfiLogger, 'bfi')
	try:
		adRemoveStat = adRemove.WriteAD()
	except FileNotFoundError:
		adRemoveStat = False

	# Mark users deleted in DB
	if adRemoveStat == True:
		bfiLogger.info("AD removal successful")
		bfiLogger.info("Configuring SQL transaction to mark users as deleted in the DB")
		adRemoveStatus = 'Success'
		try:
			queryConfig.delTransBfi = usrRemovStrSql
		except ValueError as e:
			bfiLogger.critical(f"Invalid user string format when configuring delTransBfi. Exiting now. - {e}")
			email.SendMessage('err', msg=f"Invalid user string format when configuring delTransBfi: {e}.  Aborted maintenance after AD removals but before DB removals.")
			return
		dbRemoveStat = {}
		for item in settings.bfiServers:
			dbWrite = DBWrite(logger=bfiLogger, odbcVer=settings.odbcVer, server=item, db='temadb', app="BFI")
			status = dbWrite.MarkDeleted(queryConfig.delTransBfi)
			dbWrite.DbClose()
			# Convert status to friendly values
			if status == 0:
				stat = "Success"
			else:	
				stat = "Failed"
			dbRemoveStat[item] = stat
	else:
		bfiLogger.warning("AD removal failed. Skipping DB removal...")
		dbRemoveStat = 'Skipped'
		adRemoveStatus = 'Failed'

	# Send All complete message
	completeStatus = {}
	completeStatus['Component'] = 'BigFix Inventory'
	completeStatus['Last Run'] = currentTime
	completeStatus['User Notification Status'] = notifyStat
	completeStatus['AD Removal Status'] = adRemoveStatus
	completeStatus['DB Removal Status'] = dbRemoveStat
	completeStatus['User Notifications'] = notifyUsers
	completeStatus['User Removals'] = removalUsers
	email.SendMessage('complete', statusValues=completeStatus)
	bfiLogger.info("BFI account maintenance is complete!")
	
	return

### Execute WR Account Maintenance ###
def RunWR():
	"""
	Executes the full account maintenance process for Web Reports
	"""
	currentTime = datetime.datetime.now()
	settings = Setup()
	
	### Configure Logging ###
	if settings.logDebug:
		level = 10
	else:
		level = 20

	logSetup = LogConfig('wr', settings.logSize, settings.logKeep, logLevel=level)
	wrLogger = logSetup.ConfigureLogger()
	wrLogger.info(70 * '#')
	wrLogger.info("Starting Web Reports Account Maintenance...")
	wrLogger.info(f"ODBC DRIVER VERSION: {settings.odbcVer}")
	wrLogger.info(f"SMTP RECIPIENTS: {settings.smtpList}")
	wrLogger.info(f"SMTP TIMEOUT: {settings.smtpTmout}")
	wrLogger.info(f"MAX LOG SIZE (BYTES): {settings.logSize}")
	wrLogger.info(f"LOGS TO KEEP: {settings.logKeep}")
	wrLogger.info(f"DEBUG LOGGING: {settings.logDebug}")
	wrLogger.info(f"NOTIFICATION THRESHOLD: {settings.wrNotify}")
	wrLogger.info(f"REMOVAL THRESHOLD: {settings.wrRemoval}")
	wrLogger.info(f"USE EXCLUSIONS: {settings.wrUseExcl}")
	wrLogger.info(f"SCHEDULED RUN TIME: {settings.wrRunTime}")
	wrLogger.info(f"DW SERVER: {settings.dwServer}")
	wrLogger.info(f"WR SERVERS: {settings.wrServers}")

	# Setup SendEmail Instance
	email = SendEmail(logger=wrLogger, app='BigFix Web Reports', timeout=settings.smtpTmout, notifyDay=settings.wrNotify, removalDay=settings.wrRemoval)
	try:
		email.recipients = settings.smtpList
	except TypeError as e:
		wrLogger.critical(f"Invalid smtp recipient list - '{settings.smtpList}'. Exiting now. {e}")
		return

	### Pre execution checks ###
	wrLogger.info("START - pre-execution checks")
	preExec = PreExec(wrLogger)
	if settings.dwServer == ['']: # this will be [''] if the setting was empty in the conf file or the setting values did not pass validation
		wrLogger.critical(f"The DataWarehouse server FQDN is either not set or invalid in {settings.settingsFile}. Exiting WR maintenance now!")
		return
	if settings.wrServers == ['']: # this will be [''] if the setting was empty in the conf file or the setting values did not pass validation
		wrLogger.critical(f"The WR server FQDNs are either not set or invalid in {settings.settingsFile}. Exiting WR maintenance now!")
		return
	
	# Verify Folders
	wrLogger.info("Verifying app folders...")
	verifyQoDir = preExec.FolderCheck(queryOutDir, create=True)
	verifyExcDir = preExec.FolderCheck(exclusionsDir)
	verifyFlsDir = preExec.FolderCheck(flaggedUsersDir, create=True)
	verifyPsDir = preExec.FolderCheck(psDir)

	dirVerifyRes = [verifyQoDir, verifyExcDir, verifyFlsDir, verifyPsDir]
	if 1 in dirVerifyRes or 3 in dirVerifyRes:
		wrLogger.warning("Sending error notification and exiting due to missing app folders.")
		email.SendMessage('err', msg="One or more application folders are missing.")
		sys.exit(1)

	# Verify ODBC Driver
	wrLogger.info("Verifying ODBC driver...")
	verifyOdbc = preExec.IsSoftwareInstalled(uninstallKey, "DisplayName", f'Microsoft ODBC Driver {settings.odbcVer} for SQL Server')
	if verifyOdbc != True:
		wrLogger.warning(f"Sending error notification and exiting due to missing Microsoft ODBC Driver {settings.odbcVer} for SQL Server")
		email.SendMessage('err', msg=f"The ODBC driver is missing: Microsoft ODBC Driver {settings.odbcVer} for SQL Server.")
		sys.exit(1)

	# Verify PS Module
	wrLogger.info("Verifying the AD PowerShell Module...")
	verifyAdMod = preExec.PsModuleCheck(adModule)
	if verifyAdMod != True:
		wrLogger.warning(f"Sending error notification and exiting due to missing PowerShell module: {adModule}")
		email.SendMessage('err', msg=f"The following PowerShell module is missing: {adModule}")
	
	# Verify Exclusion File
	wrLogger.info("Verifying Exclusions file...")
	if settings.wrUseExcl == True:
		verifyExcFile = preExec.FileCheck(wrExcFile)
		if verifyExcFile != True:
			wrLogger.critical("Use exclusions is enabled.  Sending error notification and exiting due to missing exclusions file.")
			email.SendMessage('err', msg=f"The exclusions file is missing: {wrExcFile}")
			return

	wrLogger.info("END - pre-execution checks")

	### Query Users ###
	# Configure SQL queries
	wrLogger.debug("Configuring SQL queries to obtain active and inactive users...")
	queryConfig = SqlConfig(wrLogger)
	queryConfig.wrQuNotifActi = settings.wrNotify
	queryConfig.wrQuRemovActi = settings.wrRemoval
	try:
		queryConfig.wrQuNotifInact = {"notifThres" : settings.wrNotify, "removThres" : settings.wrRemoval}
	except TypeError as e:
		wrLogger.critical(f"An invalid data type was used to configure wrQuNotifInact. Exiting now. - {e}")
		email.SendMessage('err', msg=f"An invalid data type was used to configure wrQuNotifInact: {e}")
		return
	except ValueError as e:
		wrLogger.critical(f"Invalid dictionary keys were used to configure wrQuNotifInact. Exiting now. - {e}")
		email.SendMessage('err', msg=f"Invalid dictionary keys were used to configure wrQuNotifInact: {e}")
		return
	
	queryConfig.wrQuRemovInact = settings.wrRemoval

	# Run queries
	wrQueries = {}
	for item in settings.wrServers:
		wrLogger.info(f"Running SQL queries for {item}")
		dbQuery = DBQuery(logger=wrLogger, odbcVer=settings.odbcVer, server=item, db='BESReporting', app="WR")
		queryResults = dbQuery.QueryAllUsers(qNotifyInact=queryConfig.wrQuNotifInact, qRemoveInact=queryConfig.wrQuRemovInact, qNotifyAct=queryConfig.wrQuNotifActi, qRemoveAct=queryConfig.wrQuRemovActi)
		dbQuery.DbClose()
		# Store the result in wrQueries - The value for each key (server name) will be a dictionary containing all four query results
		wrQueries[item] = queryResults

	# Exit if queries failed
	wrLogger.debug("Verifying SQL query status...")
	errVals =['SyntaxError', 'TimeoutError', 'QueryError']
	for key, val in wrQueries.items():
		if len(val["inactiveNotifyUsers"]) != 0:
			if val["inactiveNotifyUsers"][0] in errVals:
				wrLogger.critical("Sending error notification and exiting due to failed queries.")
				email.SendMessage('err', msg=f"SQL queries failed: {val["inactiveNotifyUsers"][0]}")
				return
		if len(val["activeNotifyUsers"]) != 0:
			if val["activeNotifyUsers"][0] in errVals:
				wrLogger.critical("Sending error notification and exiting due to failed queries.")
				email.SendMessage('err', msg=f"SQL queries failed: {val["activeNotifyUsers"][0]}")
				return

	# Combine lists from all cores and de-dupe (val is the server name)
	wrLogger.debug("Concatenating user lists from all cores.")
	allInactNotif = list(itertools.chain.from_iterable([val["inactiveNotifyUsers"] for key, val in wrQueries.items()]))
	allInactRemov = list(itertools.chain.from_iterable([val["inactiveRemoveUsers"] for key, val in wrQueries.items()]))
	allActNotif = list(itertools.chain.from_iterable([val["activeNotifyUsers"] for key, val in wrQueries.items()]))
	allActRemov = list(itertools.chain.from_iterable([val["activeRemoveUsers"] for key, val in wrQueries.items()]))
	
	wrLogger.debug("De-duplicating user lists.")
	deDupInactNotif = FilterData.DedupeList(allInactNotif)
	deDupInactRemov = FilterData.DedupeList(allInactRemov)
	deDupActNotif = FilterData.DedupeList(allActNotif)
	deDupActRemov = FilterData.DedupeList(allActRemov)

	# Filter query data
	wrLogger.info("Filtering data...")
	"""
	flaggedUsers contains the users previously sent notifications.
	This is used to prevent multiple notifications to the same user day after day.
	This is overwritten on each run.  Non-relevant users will drop off the list.
	"""
	try:
		flaggedUsers = FilterData.ReadUsersFile(wrFlagFile)
	except FileNotFoundError:
		wrLogger.warning(f"Flagged users file is missing: {wrFlagFile}")
		flaggedUsers = []

	"""
	flaggedRemoved is only present to cut down processing time on removals. 
	Since users are never marked deleted in the BESReporting DB, the full inactive list (up to 180 days) is returned from the query.
	flaggedRemoved keeps track of users removed on the last run to cut down the amount of users to loop through in ADWrite.
	This is overwritten on each run with the removed user list.  Non-relevant users will drop off the list.
	"""
	try:
		flaggedRemoved = FilterData.ReadUsersFile(wrFlagRemoveFile)
	except FileNotFoundError:
		wrLogger.warning(f"Flagged Removed users file is missing: {wrFlagRemoveFile}")
		flaggedRemoved = []
	
	if settings.wrUseExcl == True:
		exclUsers = FilterData.ReadUsersFile(wrExcFile)
	else:
		exclUsers = []

	wrLogger.debug(f"Flagged Notify Users: {flaggedUsers}")	
	wrLogger.debug(f"Flagged Removal Users (full list of inactive users up to 180 days): {flaggedRemoved}")
	wrLogger.debug(f"Excluded Users: {exclUsers}")

	# Filter each user list and assign to their own object
	notifyUsersFlagNotRemoved = FilterData.FilterUsers(inactiveList=deDupInactNotif, exclList=exclUsers, activeList=deDupActNotif)
	notifyUsers = FilterData.FilterUsers(inactiveList=deDupInactNotif, exclList=exclUsers, flagList=flaggedUsers, activeList=deDupActNotif)
	removalUsers = FilterData.FilterUsers(inactiveList=deDupInactRemov, exclList=exclUsers, flagList=flaggedRemoved, activeList=deDupActRemov)
	removalUsersFlagNotRemoved = FilterData.FilterUsers(inactiveList=deDupInactRemov, exclList=exclUsers, activeList=deDupActRemov)

	### Send Notifications ###
	if len(notifyUsers) > 0:
		wrLogger.info("Starting user notification process...")
		try:
			email.recipients = notifyUsers # set email recipients to the list of filtered inactive users
		except TypeError as e:
			wrLogger.critical(f"Invalid smtp recipient list - '{notifyUsers}'. Exiting now. {e}")
			return
		wrLogger.debug(f"Notification List: {notifyUsers}")
		notifyStatus = email.SendMessage('notify') # Loops through all users and sends individual notification emails
		try:
			# Reset email recipients back to the list from the settings.conf file
			email.recipients = settings.smtpList
		except TypeError as e:
			wrLogger.critical(f"Invalid smtp recipient list - '{settings.smtpList}'. Exiting now. {e}")
			return

		# Overwrite the flagged users file with the original inactive user list (filtered against active and exlcuded users but NOT against flagged users)
		wrLogger.info("Overwriting flagged users file")
		Utilities.WriteFileFromList(wrFlagFile, notifyUsersFlagNotRemoved)
	else:
		wrLogger.info("User notification list empty. Skipping notification process.")
		notifyStatus = 2 # Notification list is empty

	match notifyStatus:
		case 0:
			notifyStat = 'Success'
		case 1:
			notifyStat = 'Failed'
		case 2:
			notifyStat = 'Skipped'

	# Exit if removal list is empty
	if len(removalUsers) == 0:
		completeStatus = {}
		completeStatus['Component'] = 'BigFix Web Reports'
		completeStatus['Last Run'] = currentTime
		completeStatus['User Notification Status'] = notifyStat
		completeStatus['AD Removal Status'] = 'Skipped'
		completeStatus['User Notifications'] = notifyUsers
		completeStatus['User Removals'] = ''
		wrLogger.info("User removal list is empty. Sending complete message and exiting.")
		email.SendMessage('complete', statusValues=completeStatus)
		return

	### Removal Setup ###
	wrLogger.debug("Configuring SQL query to convert UPNs to DNs...")
	usrRemovStrSql = FilterData.FormatSQL(removalUsers) # Format user list for sql
	try:
		queryConfig.upnToDnQuery = usrRemovStrSql
	except ValueError as e:
		wrLogger.critical(f"Invalid user string format when configuring upnToDnQuery. Exiting now. - {e}")
		email.SendMessage('err', msg=f"Invalid user string format when configuring upnToDnQuery: {e}")
		return

	# Convert removal UPNs to DNs
	wrLogger.info("Running SQL queries to convert UPNs to DNs...")
	vadwQuery = DBQuery(logger=wrLogger, odbcVer=settings.odbcVer, server=settings.dwServer[0], db='VADW', app="WR")
	try:
		removalDNs = vadwQuery.QueryVadw(queryConfig.upnToDnQuery)
	except ValueError as e:
		wrLogger.error(f"Incorrect DB specified: {e}")
		removalDNs = ['QueryError']
	finally:
		vadwQuery.DbClose()

	# Exit if query failed
	errVals =['SyntaxError', 'TimeoutError', 'QueryError']
	if len(removalDNs) != 0:
		if removalDNs[0] in errVals:
			wrLogger.critical("Sending error notification and exiting due to failed queries.")
			email.SendMessage('err', msg=f"SQL query to convert UPN to DN failed: {removalDNs[0]}")
			return

	# Write DNs to file
	wrLogger.debug(f"Writing DNs to file: {wrDnFile}")
	Utilities.WriteFileFromList(wrDnFile, removalDNs)

	### Remove Users ###
	# Remove Users from AD
	adRemove = ADWrite(wrLogger, 'wr')
	try:
		adRemoveStat = adRemove.WriteAD()
	except FileNotFoundError:
		adRemoveStat = False

	# Verify Results
	if adRemoveStat == True:
		wrLogger.info("AD removal successful")
		adRemoveStatus = 'Success'

		# Overwrite the flagged remove users file with the original inactive user list (filtered against active and exlcuded users but NOT against flagged removed users)
		wrLogger.info("Overwriting flagged-removed users file")
		Utilities.WriteFileFromList(wrFlagRemoveFile, removalUsersFlagNotRemoved)
	else:
		wrLogger.warning("AD removal failed.")
		adRemoveStatus = 'Failed'

	# Send All complete message
	completeStatus = {}
	completeStatus['Component'] = 'BigFix Web Reports'
	completeStatus['Last Run'] = currentTime
	completeStatus['User Notification Status'] = notifyStat
	completeStatus['AD Removal Status'] = adRemoveStatus
	completeStatus['User Notifications'] = notifyUsers
	completeStatus['User Removals'] = removalUsers
	email.SendMessage('complete', statusValues=completeStatus)
	wrLogger.info("Web Reports account maintenance is complete!")
	
	return


### Execute Console Account Maintenance ###
def RunCon():
	"""
	Executes the full account maintenance process for the BigFix Console.
	"""
	currentTime = datetime.datetime.now()
	settings = Setup()
	
	### Configure Logging ###
	if settings.logDebug:
		level = 10
	else:
		level = 20

	logSetup = LogConfig('console', settings.logSize, settings.logKeep, logLevel=level)
	conLogger = logSetup.ConfigureLogger()
	conLogger.info(70 * '#')
	conLogger.info("Starting Console Account Maintenance...")
	conLogger.info(f"ODBC DRIVER VERSION: {settings.odbcVer}")
	conLogger.info(f"SMTP RECIPIENTS: {settings.smtpList}")
	conLogger.info(f"SMTP TIMEOUT: {settings.smtpTmout}")
	conLogger.info(f"MAX LOG SIZE (BYTES): {settings.logSize}")
	conLogger.info(f"LOGS TO KEEP: {settings.logKeep}")
	conLogger.info(f"DEBUG LOGGING: {settings.logDebug}")
	conLogger.info(f"NOTIFICATION THRESHOLD: {settings.conNotify}")
	conLogger.info(f"REMOVAL THRESHOLD: {settings.conRemoval}")
	conLogger.info(f"USE EXCLUSIONS: {settings.conUseExcl}")
	conLogger.info(f"SCHEDULED RUN TIME: {settings.conRunTime}")
	conLogger.info(f"DW SERVER: {settings.dwServer}")

	# Setup SendEmail Instance
	email = SendEmail(logger=conLogger, app='BigFix Console', timeout=settings.smtpTmout, notifyDay=settings.conNotify, removalDay=settings.conRemoval)
	try:
		email.recipients = settings.smtpList
	except TypeError as e:
		conLogger.critical(f"Invalid smtp recipient list - '{settings.smtpList}'. Exiting now. {e}")
		return

	### PreExec checks ###
	conLogger.info("START - pre-execution checks")
	preExec = PreExec(conLogger)
	if settings.dwServer == ['']: # this will be [''] if the setting was empty in the conf file or the setting values did not pass validation
		conLogger.critical(f"The DataWarehouse server FQDN is either not set or invalid in {settings.settingsFile}. Exiting Console maintenance now!")
		return
	
	# Verify Folders
	conLogger.info("Verifying app folders...")
	verifyQoDir = preExec.FolderCheck(queryOutDir, create=True)
	verifyExcDir = preExec.FolderCheck(exclusionsDir)
	verifyFlsDir = preExec.FolderCheck(flaggedUsersDir, create=True)
	verifyPsDir = preExec.FolderCheck(psDir)

	dirVerifyRes = [verifyQoDir, verifyExcDir, verifyFlsDir, verifyPsDir]
	if 1 in dirVerifyRes or 3 in dirVerifyRes:
		conLogger.warning("Sending error notification and exiting due to missing app folders.")
		email.SendMessage('err', msg="One or more application folders are missing.")
		sys.exit(1)

	# Verify ODBC Driver
	conLogger.info("Verifying ODBC driver...")
	verifyOdbc = preExec.IsSoftwareInstalled(uninstallKey, "DisplayName", f'Microsoft ODBC Driver {settings.odbcVer} for SQL Server')
	if verifyOdbc != True:
		conLogger.warning(f"Sending error notification and exiting due to missing Microsoft ODBC Driver {settings.odbcVer} for SQL Server")
		email.SendMessage('err', msg=f"The ODBC driver is missing: Microsoft ODBC Driver {settings.odbcVer} for SQL Server.")
		sys.exit(1)
	
	# Verify Exclusion File
	conLogger.info("Verifying Exclusions file...")
	if settings.conUseExcl == True:
		verifyExcFile = preExec.FileCheck(conExcFile)
		if verifyExcFile != True:
			conLogger.critical("Use exclusions is enabled.  Sending error notification and exiting due to missing exclusions file.")
			email.SendMessage('err', msg=f"The exclusions file is missing: {conExcFile}")
			return

	conLogger.info("END - pre-execution checks")

	### Query Users ###
	# Configure SQL queries
	conLogger.debug("Configuring SQL queries to obtain inactive users...")
	queryConfig = SqlConfig(conLogger)
	try:
		queryConfig.conQueryNotify = {"notifThres" : settings.conNotify, "removThres" : settings.conRemoval}
	except TypeError as e:
		conLogger.critical(f"An invalid data type was used to configure conQueryNotify. Exiting now. - {e}")
		email.SendMessage('err', msg=f"An invalid data type was used to configure conQueryNotify: {e}")
		return
	except ValueError as e:
		conLogger.critical(f"Invalid dictionary keys were used to configure conQueryNotify. Exiting now. - {e}")
		email.SendMessage('err', msg=f"Invalid dictionary keys were used to configure conQueryNotify: {e}")
		return
	
	queryConfig.conQueryRemove = settings.conRemoval

	# Run queries
	conLogger.info("Running SQL queries to obtain inactive users...")
	dbQuery = DBQuery(logger=conLogger, odbcVer=settings.odbcVer, server=settings.dwServer[0], db='BFDW', app="CON")
	inactiveUsers = dbQuery.QueryConUsers(queryConfig.conQueryNotify, queryConfig.conQueryRemove)
	dbQuery.DbClose()
	
	conLogger.debug("Verifying SQL query status...")
	errVals =['SyntaxError', 'TimeoutError', 'QueryError']
	if type(inactiveUsers["inactiveNotifyUsers"]) == str:
		if inactiveUsers["inactiveNotifyUsers"] in errVals:
			conLogger.critical("Sending error notification and exiting due to failed queries.")
			email.SendMessage('err', msg=f"SQL queries failed: {inactiveUsers["inactiveNotifyUsers"]}")
			return
	
	# Filter query data
	conLogger.info("Filtering data...")
	try:
		flaggedUsers = FilterData.ReadUsersFile(conFlagFile)
	except FileNotFoundError:
		conLogger.warning(f"Flagged users file is missing: {conFlagFile}")
		flaggedUsers = []
	
	if settings.conUseExcl == True:
		exclUsers = FilterData.ReadUsersFile(conExcFile)
	else:
		exclUsers = []

	# Convert inactive users keys (these are the '0' account samAccountNames) into a list
	inactiveNotifyUserList = FilterData.ConvertKeystoList(inactiveUsers["inactiveNotifyUsers"])
	inactiveRemoveUserList = FilterData.ConvertKeystoList(inactiveUsers["inactiveRemoveUsers"])
	
	# Filter the user lists
	filtNotifyUsers = FilterData.FilterUsers(inactiveNotifyUserList, exclUsers, flaggedUsers)
	filtRemovalUsers = FilterData.FilterUsers(inactiveRemoveUserList, exclUsers)
	
	# Create a new dictionary where only valid inactive users are present
	notifyUsers = {key: val for key, val in inactiveUsers["inactiveNotifyUsers"].items() if key.lower() in filtNotifyUsers}
	removalUsers = {key: val for key, val in inactiveUsers["inactiveRemoveUsers"].items() if key.lower() in filtRemovalUsers}

	# Skip notify user parsing if empty
	if len(notifyUsers) > 0:
		# Convert the description field (values in the inactiveUsers["inactiveNotifyUsers"] dictionary to a list)
		notifyDescrList: list = FilterData.ConvertValuestoList(notifyUsers)

		# Pull the MEA samAccountName out of the description (the values in the dictionary)
		notifySam: str = FilterData.FilterConDescr(notifyDescrList)

		# Set the sam to upn query
		try:
			queryConfig.samToUpnQuery = notifySam
		except ValueError as e:
			conLogger.critical(f"Invalid user string format when configuring samToUpnQuery. Exiting now. - {e}")
			email.SendMessage('err', msg=f"Invalid user string format when configuring samToUpnQuery: {e}")
			return

		# Query VADW to return the UPNs of each user relevant for notifications
		conLogger.info("Running SQL queries to convert samAccountNames to UPNs...")
		dbQuery = DBQuery(logger=conLogger, odbcVer=settings.odbcVer, server=settings.dwServer[0], db='VADW', app="CON")
		try:
			notifyUpn = dbQuery.QueryVadw(queryConfig.samToUpnQuery)
		except ValueError as e:
			conLogger.error(f"Incorrect DB specified: {e}")
			notifyUpn = ['QueryError']
		finally:
			dbQuery.DbClose()

		errVals =['SyntaxError', 'TimeoutError', 'QueryError']
		if len(notifyUpn) != 0:
			if notifyUpn[0] in errVals:
				conLogger.critical("Sending error notification and exiting due to failed queries.")
				email.SendMessage('err', msg=f"SQL query to convert samAccountNames to UPNs failed: {notifyUpn[0]}")
				return
	else:
		notifyUpn = []

	### Send Notifications ###
	if len(notifyUpn) > 0:
		conLogger.info("Starting user notification process...")
		try:
			email.recipients = notifyUpn # set email recipients to the list of filtered inactive users
		except TypeError as e:
			conLogger.critical(f"Invalid smtp recipient list - '{notifyUpn}'. Exiting now. {e}")
			return
		conLogger.debug(f"Notification List: {notifyUpn}")
		notifyStatus = email.SendMessage('notify') # Loops through all users and sends individual notification emails
		try:
			# Reset email recipients back to the list from the settings.conf file
			email.recipients = settings.smtpList
		except TypeError as e:
			conLogger.critical(f"Invalid smtp recipient list - '{settings.smtpList}'. Exiting now. {e}")
			return

		# Overwrite the flagged users file with the original unfiltered inactive user list
		conLogger.info("Overwriting flagged users file")
		Utilities.WriteFileFromList(conFlagFile, inactiveNotifyUserList)
	else:
		conLogger.info("User notification list empty. Skipping notification process.")
		notifyStatus = 2 # Notification list is empty

	match notifyStatus:
		case 0:
			notifyStat = 'Success'
		case 1:
			notifyStat = 'Failed'
		case 2:
			notifyStat = 'Skipped'

	# Send All complete message
	completeStatus = {}
	completeStatus['Component'] = 'BigFix Console'
	completeStatus['Last Run'] = currentTime
	completeStatus['User Notification Status'] = notifyStat
	completeStatus['User Notifications'] = notifyUpn
	completeStatus['User Removals'] = removalUsers
	email.SendMessage('complete', statusValues=completeStatus)
	conLogger.info("Console account maintenance is complete!")
	
	return


if __name__ == "__main__":
	### Runs on startup ###
	isWin = PreExec.OsCheck()
	if isWin == False:
		sys.exit(1)

	# Create Logs folder
	if not os.path.isdir(logDir):
		try:
			os.mkdir(logDir)
		except OSError as e:
			sys.exit(3)
	
	# Configures StartupArgs
	args = Initialize()
	if args.version:
		print(appVersion)
		sys.exit(0)
	
	# Configure signal handlers
	HandleSigs()

	# Configure Settings
	logSetup = LogConfig('setupError', 20000000, 5, logLevel=logging.DEBUG)
	setupLogger = logSetup.ConfigureLogger()
	settings = Setup()
	
	# Configure root logger
	if settings.logDebug:
		level = 10
	else:
		level = 20

	rootLogSetup = LogConfig('init', settings.logSize, settings.logKeep, logLevel=level)
	rootLogger = rootLogSetup.ConfigureLogger()
	rootLogger.info(70 * '#')

	# Log settings
	rootLogger.info("Starting the BigFix Account Maintenance Application.")
	rootLogger.info(f"ODBC DRIVER VERSION: {settings.odbcVer}")
	rootLogger.info(f"DW SERVER: {settings.dwServer}")
	rootLogger.info(f"WR SERVERS: {settings.wrServers}")
	rootLogger.info(f"BFC SERVERS: {settings.bfcServers}")
	rootLogger.info(f"BFI SERVERS: {settings.bfiServers}")
	rootLogger.info(f"SMTP RECIPIENTS: {settings.smtpList}")
	rootLogger.info(f"SMTP TIMEOUT: {settings.smtpTmout}")
	rootLogger.info(f"MAX LOG SIZE (BYTES): {settings.logSize}")
	rootLogger.info(f"LOGS TO KEEP: {settings.logKeep}")
	rootLogger.info(f"DEBUG LOGGING: {settings.logDebug}")
	rootLogger.info(f"BFC NOTIFICATION THRESHOLD: {settings.bfcNotify}")
	rootLogger.info(f"BFC REMOVAL THRESHOLD: {settings.bfcRemoval}")
	rootLogger.info(f"BFI NOTIFICATION THRESHOLD: {settings.bfiNotify}")
	rootLogger.info(f"BFI REMOVAL THRESHOLD: {settings.bfiRemoval}")
	rootLogger.info(f"WR NOTIFICATION THRESHOLD: {settings.wrNotify}")
	rootLogger.info(f"WR REMOVAL THRESHOLD: {settings.wrRemoval}")
	rootLogger.info(f"CONSOLE NOTIFICATION THRESHOLD: {settings.conNotify}")
	rootLogger.info(f"CONSOLE REMOVAL THRESHOLD: {settings.conRemoval}")
	rootLogger.info(f"BFC USE EXCLUSIONS: {settings.bfcUseExcl}")
	rootLogger.info(f"BFI USE EXCLUSIONS: {settings.bfiUseExcl}")
	rootLogger.info(f"WR USE EXCLUSIONS: {settings.wrUseExcl}")
	rootLogger.info(f"CONSOLE USE EXCLUSIONS: {settings.conUseExcl}")
	rootLogger.info(f"BFC SCHEDULED RUN TIME: {settings.bfcRunTime}")
	rootLogger.info(f"BFI SCHEDULED RUN TIME: {settings.bfiRunTime}")
	rootLogger.info(f"WR SCHEDULED RUN TIME: {settings.wrRunTime}")
	rootLogger.info(f"CONSOLE SCHEDULED RUN TIME: {settings.conRunTime}")

	###########################
	# Query args
	if args.querybfc:
		QueryBFC()
		sys.exit(0)
	if args.querybfi:
		QueryBFI()
		sys.exit(0)
	if args.querywr:
		QueryWR()
		sys.exit(0)
	if args.querycon:
		QueryCon()
		sys.exit(0)
	if args.queryall:
		QueryBFC()
		QueryBFI()
		QueryWR()
		QueryCon()
		sys.exit(0)

	###########################
	# Run on-demand args
	if args.runbfc:
		RunBFC()
		sys.exit(0)
	if args.runbfi:
		RunBFI()
		sys.exit(0)
	if args.runwr:
		RunWR()
		sys.exit(0)
	if args.runcon:
		RunCon()
		sys.exit(0)
	if args.runall:
		RunBFC()
		RunBFI()
		RunWR()
		RunCon()
		sys.exit(0)

	###########################
	# Schedule args
	if args.runonschedule:
		schedule.every().day.at(settings.bfcRunTime).do(RunBFC)
		schedule.every().day.at(settings.bfiRunTime).do(RunBFI)
		schedule.every().day.at(settings.wrRunTime).do(RunWR)
		schedule.every().day.at(settings.conRunTime).do(RunCon)
		while True:
			schedule.run_pending()
			time.sleep(1)
		