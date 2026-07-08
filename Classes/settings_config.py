################# SettingsConfig #########################
# Creates the settings config file  ######################
# Use to read in all settings before each scheduled run ##
##########################################################

from pathlib import Path
import configparser
import os
from typing import Union
import logging
import traceback
import re
import sys

from validation import Validation

class SettingsConfig:
	"""
	Instantiate the class and then use the class object to access each setting via the getter.
	Class instantiation will configure all settings based on what is in the settings.conf file.

	If there is an issue with the settings.conf file or the setting itself, default values will be used.
	If the settings.conf file is missing, it will be created with the default values.
	"""
	if getattr(sys, 'frozen', False): # If running as bundled exe, this should be true
		settingsFile = Path(__file__).parent / "settings.conf"
	else:
		settingsFile = Path(__file__).parent / "../settings.conf"

	# Default values
	defaultODBC = '18'
	defaultSMTPList = ''
	defaultSMTPTmout = '30' # Seconds
	defaultLogSize = '50000000' # Bytes
	defaultLogsToKeep = '5'
	defaultLogsDebug = '0' # false
	defaultNotifyThresBFI = '76'
	defaultRemovalThresBFI = '90'
	defaultNotifyThresBFC = '76'
	defaultRemovalThresBFC = '90'
	defaultNotifyThresWR = '76'
	defaultRemovalThresWR = '90'
	defaultNotifyThresCon = '76'
	defaultRemovalThresCon = '90'
	defaultExclusionBFI = '1' # true
	defaultExclusionBFC = '1' # true
	defaultExclusionWR = '1' # true
	defaultExclusionCon = '1' # true
	defaultRunTimeBFI = '12:00:00'
	defaultRunTimeBFC = '12:02:00'
	defaultRunTimeWR = '12:05:00'
	defaultRunTimeCon = '12:07:00'
	defaultBFCServers = ''
	defaultBFIServers = ''
	defaultWRServers = ''
	defaultprdDW = ''

	# Min/Max Values
	smtpTmoutMin = 5
	smtpTmoutMax = 60
	logSizeMin = 2000000
	logSizeMax = 100000000
	thresMin = 60 
	thresMax = 120

	def __init__(self, logger: logging.Logger) -> None:
		self._logger = logger # This should be its own unique logger that uses pre-defined values for size & keep since this will be created before the config settings are read
		self._CreateSettingsFile() # Create the settings file if it doesn't exist
		self._loadSettings = self._LoadSettings() # From the file, load all settings

		# Assign fields
		self._odbcVer = int(self._AssignSetting('PYODBC', 'ms_odbc_driver_version', SettingsConfig.defaultODBC))
		self._bfcServers = list(self._AssignSetting('PYODBC', 'bfc_servers', SettingsConfig.defaultBFCServers))
		self._bfiServers = list(self._AssignSetting('PYODBC', 'bfi_servers', SettingsConfig.defaultBFIServers))
		self._wrServers = list(self._AssignSetting('PYODBC', 'wr_servers', SettingsConfig.defaultWRServers))
		self._dwServer = list(self._AssignSetting('PYODBC', 'dw_server', SettingsConfig.defaultprdDW))
		self._smtpList = list(self._AssignSetting('SMTP', 'smtp_recipient_list', SettingsConfig.defaultSMTPList))
		self._smtpTmout = int(self._AssignSetting('SMTP', 'smtp_time_out', SettingsConfig.defaultSMTPTmout))
		self._logSize = int(self._AssignSetting('LOGGING', 'size_bytes', SettingsConfig.defaultLogSize))
		self._logKeep = int(self._AssignSetting('LOGGING', 'logs_to_keep', SettingsConfig.defaultLogsToKeep))
		self._logDebug = bool(self._AssignSetting('LOGGING', 'debug', SettingsConfig.defaultLogsDebug))
		self._bfiNotify = int(self._AssignSetting('INACTIVE THRESHOLD', 'notify_bfi', SettingsConfig.defaultNotifyThresBFI))
		self._bfiRemoval = int(self._AssignSetting('INACTIVE THRESHOLD', 'removal_bfi', SettingsConfig.defaultRemovalThresBFI))
		self._bfcNotify = int(self._AssignSetting('INACTIVE THRESHOLD', 'notify_bfc', SettingsConfig.defaultNotifyThresBFC))
		self._bfcRemoval = int(self._AssignSetting('INACTIVE THRESHOLD', 'removal_bfc', SettingsConfig.defaultRemovalThresBFC))
		self._wrNotify = int(self._AssignSetting('INACTIVE THRESHOLD', 'notify_wr', SettingsConfig.defaultNotifyThresWR))
		self._wrRemoval = int(self._AssignSetting('INACTIVE THRESHOLD', 'removal_wr', SettingsConfig.defaultRemovalThresWR))
		self._conNotify = int(self._AssignSetting('INACTIVE THRESHOLD', 'notify_con', SettingsConfig.defaultNotifyThresCon))
		self._conRemoval = int(self._AssignSetting('INACTIVE THRESHOLD', 'removal_con', SettingsConfig.defaultRemovalThresCon))
		self._bfiExcl = bool(self._AssignSetting('EXCLUSIONS', 'use_exclusions_bfi', SettingsConfig.defaultExclusionBFI))
		self._bfcExcl = bool(self._AssignSetting('EXCLUSIONS', 'use_exclusions_bfc', SettingsConfig.defaultExclusionBFC))
		self._wrExcl = bool(self._AssignSetting('EXCLUSIONS', 'use_exclusions_wr', SettingsConfig.defaultExclusionWR))
		self._conExcl = bool(self._AssignSetting('EXCLUSIONS', 'use_exclusions_con', SettingsConfig.defaultExclusionCon))
		self._bfiRunTime = str(self._AssignSetting('SCHEDULE', 'run_time_bfi', SettingsConfig.defaultRunTimeBFI))
		self._bfcRunTime = str(self._AssignSetting('SCHEDULE', 'run_time_bfc', SettingsConfig.defaultRunTimeBFC))
		self._wrRunTime = str(self._AssignSetting('SCHEDULE', 'run_time_wr', SettingsConfig.defaultRunTimeWR))
		self._conRunTime = str(self._AssignSetting('SCHEDULE', 'run_time_con', SettingsConfig.defaultRunTimeCon))

	# Create getters for fields
	@property
	def odbcVer(self):
		return self._odbcVer
	@property
	def bfcServers(self):
		return self._bfcServers
	@property
	def bfiServers(self):
		return self._bfiServers
	@property
	def wrServers(self):
		return self._wrServers
	@property
	def dwServer(self):
		return self._dwServer
	@property
	def smtpList(self):
		return self._smtpList
	@property
	def smtpTmout(self):
		return self._smtpTmout
	@property
	def logSize(self):
		return self._logSize
	@property
	def logKeep(self):
		return self._logKeep
	@property
	def logDebug(self):
		return self._logDebug
	@property
	def bfiNotify(self):
		return self._bfiNotify
	@property
	def bfiRemoval(self):
		return self._bfiRemoval
	@property
	def bfcNotify(self):
		return self._bfcNotify
	@property
	def bfcRemoval(self):
		return self._bfcRemoval
	@property
	def wrNotify(self):
		return self._wrNotify
	@property
	def wrRemoval(self):
		return self._wrRemoval
	@property
	def conNotify(self):
		return self._conNotify
	@property
	def conRemoval(self):
		return self._conRemoval
	@property
	def bfiUseExcl(self):
		return self._bfiExcl
	@property
	def bfcUseExcl(self):
		return self._bfcExcl
	@property
	def wrUseExcl(self):
		return self._wrExcl
	@property
	def conUseExcl(self):
		return self._conExcl
	@property
	def bfiRunTime(self):
		return self._bfiRunTime
	@property
	def bfcRunTime(self):
		return self._bfcRunTime
	@property
	def wrRunTime(self):
		return self._wrRunTime
	@property
	def conRunTime(self):
		return self._conRunTime

	# Create the settingsFile
	def _CreateSettingsFile(self) -> None:
		"""
		If the settings conf file is missing, this will recreate the file with all available settings.
		"""
		settings = configparser.ConfigParser(allow_no_value=True, delimiters='=')

		if not os.path.isfile(SettingsConfig.settingsFile):
			settings['PYODBC'] = {}
			settings['PYODBC']['ms_odbc_driver_version'] = SettingsConfig.defaultODBC
			settings['PYODBC']['bfc_servers'] = SettingsConfig.defaultBFCServers
			settings['PYODBC']['bfi_servers'] = SettingsConfig.defaultBFIServers
			settings['PYODBC']['wr_servers'] = SettingsConfig.defaultWRServers
			settings['PYODBC']['dw_server'] = SettingsConfig.defaultprdDW
			settings['SMTP'] = {'# Email addresses need to be separated by a comma without spaces. Ex. user1@domain,user2@domain':None}
			settings['SMTP']['smtp_recipient_list'] = SettingsConfig.defaultSMTPList
			settings['SMTP']['smtp_time_out'] = SettingsConfig.defaultSMTPTmout
			settings['LOGGING'] = {'# Log rotation settings. size_bytes must be in bytes.':None}
			settings['LOGGING']['size_bytes'] = SettingsConfig.defaultLogSize
			settings['LOGGING']['logs_to_keep'] = SettingsConfig.defaultLogsToKeep
			settings['LOGGING']['debug'] = SettingsConfig.defaultLogsDebug
			settings['INACTIVE THRESHOLD'] = {'# Thresholds for inactive users':None}
			settings['INACTIVE THRESHOLD']['notify_bfi'] = SettingsConfig.defaultNotifyThresBFI
			settings['INACTIVE THRESHOLD']['removal_bfi'] = SettingsConfig.defaultRemovalThresBFI
			settings['INACTIVE THRESHOLD']['notify_bfc'] = SettingsConfig.defaultNotifyThresBFC
			settings['INACTIVE THRESHOLD']['removal_bfc'] = SettingsConfig.defaultRemovalThresBFC
			settings['INACTIVE THRESHOLD']['notify_wr'] = SettingsConfig.defaultNotifyThresWR
			settings['INACTIVE THRESHOLD']['removal_wr'] = SettingsConfig.defaultRemovalThresWR
			settings['INACTIVE THRESHOLD']['notify_con'] = SettingsConfig.defaultNotifyThresCon
			settings['INACTIVE THRESHOLD']['removal_con'] = SettingsConfig.defaultRemovalThresCon
			settings['EXCLUSIONS'] = {'# use_exclusions should be set to True or False.  if use_exclusions is False, users will not be excluded from notifications and removals even if users are present in the exclusion file':None}
			settings['EXCLUSIONS']['use_exclusions_bfi'] = SettingsConfig.defaultExclusionBFI
			settings['EXCLUSIONS']['use_exclusions_bfc'] = SettingsConfig.defaultExclusionBFC
			settings['EXCLUSIONS']['use_exclusions_wr'] = SettingsConfig.defaultExclusionWR
			settings['EXCLUSIONS']['use_exclusions_con'] = SettingsConfig.defaultExclusionCon
			settings['SCHEDULE'] = {'# configure the time the account maintenance will run. must be hh:mm:ss': None}
			settings['SCHEDULE']['run_time_bfi'] = SettingsConfig.defaultRunTimeBFI
			settings['SCHEDULE']['run_time_bfc'] = SettingsConfig.defaultRunTimeBFC
			settings['SCHEDULE']['run_time_wr'] = SettingsConfig.defaultRunTimeWR
			settings['SCHEDULE']['run_time_con'] = SettingsConfig.defaultRunTimeCon

			with open(SettingsConfig.settingsFile, 'w') as file:
				settings.write(file)

	# Load in all settings from the settingsFile
	def _LoadSettings(self) -> Union[configparser.ConfigParser, bool]:
		"""
		Reads and loads all the settings in the conf file.
		
		:return: Returns an object containing all of the loaded settings as key:value pairs. Returns False if there is an exception.
		:rtype: ConfigParser | bool
		"""
		settings = configparser.ConfigParser()
		try:
			settings.read(SettingsConfig.settingsFile) # read the ini file
		except configparser.MissingSectionHeaderError as e:
			self._logger.error(f"Config file read error. - {e}")
			self._logger.debug(traceback.format_exc())
			return False
		except configparser.ParsingError as e:
			self._logger.error(f"Config file read error.  Config File syntax is wrong. - {e}")
			self._logger.debug(traceback.format_exc())
			return False

		return settings
	
	def _AddSettingToFile(self, header: str, field: str, value: str) -> None:
		"""
		Adds a setting and value (key/value pair) to an existing conf file. If the header is missing it will also be created.
		
		:param header: The name of the header in the conf file that the field is under
		:type header: str
		:param field: The setting name (key name)
		:type field: str
		:param value: The value to assign to the field
		:type value: str
		"""
		if self._loadSettings == False: # This will be False if _LoadSettings handled an exception while reading the settings.conf file
			self._logger.error(f"Initial loading of settings failed.  Unable to add '{header}|{field}={value}' to conf file.")
			return
		
		# Verify header exists
		try:
			if not self._loadSettings.has_section(header):
				self._loadSettings[header] = {}
				self._loadSettings[header][field] = value
		except Exception as e:
			self._logger.error(f"Failed to add header '{header}' to conf file. Skipping attempt to append '{header}={field}' | {e}")
			self._logger.debug(traceback.format_exc())
			return
		# Set field=value setting
		try:
			if not self._loadSettings.has_option(header, field):
				self._loadSettings[header][field] = value
		except Exception as e:
			self._logger.error(f"Failed to add setting to conf file. '{header}|{field}={value}' | {e}")
			self._logger.debug(traceback.format_exc())
			return
		
		# Write new setting to conf file
		try:
			with open(SettingsConfig.settingsFile, 'w') as file:
				self._loadSettings.write(file)
			self._logger.info(f"Successfully added setting to conf file: '{header}|{field}={value}'")
		except Exception as e:
			self._logger.error(f"Failed to write setting to conf file. '{header}={field}' | {e}")
			self._logger.debug(traceback.format_exc())

	# Query individual settings
	def _AssignSetting(self, header: str, field: str, defaultValue: str) -> Union[int, str, bool]:
		"""
		Reads the conf file settings loaded from the conf file during class instantiation. Validates the existing value, or if the setting is missing, utilizes the default value.
		If the field is missing it will call _AddSettingToFile in an attempt to append the field to the conf file.
		
		:param header: The name of the header in the conf file that the field is under
		:type header: str
		:param field: The setting name (key name)
		:type field: str
		:param defaultValue: The default value to assign to the field if the setting does not exist or does not pass validation
		:type defaultValue: str
		:return: The value that will be available via the relevant getter for the field.
		:rtype: str
		"""
		if self._loadSettings == False: # This will be False if _LoadSettings handled an exception while reading the settings.conf file
			value = defaultValue
			return value
		try:
			if self._loadSettings.has_option(header, field):
				value = self._loadSettings[header][field]
			else:
				self._AddSettingToFile(header=header, field=field, value=defaultValue) # add missing setting to conf file
				value = defaultValue
		except Exception as e:
			self._logger.error(f"Configuration parse error.  The '{field}' value is missing. Using default values: {defaultValue} | {e}")
			self._logger.debug(traceback.format_exc())
			self._AddSettingToFile(header=header, field=field, value=defaultValue) # add missing setting to conf file
			value = defaultValue
		finally:
			validatedValue = self._ValidateSetting(field, value, defaultValue) # Validate setting beofre returning the final value
		
		return validatedValue
	
	# Validate the setting
	def _ValidateSetting(self, field: str, setting: str, defaultValue: str) -> Union[int, str, bool]:
		"""
		Validates setting values. This should be called in _AssignSetting prior to setting the field value that is available via the class getters.
		
		:param field: The setting name (key name)
		:type field: str
		:param setting: The value of the setting
		:type setting: str
		:param defaultValue: The default value to use if the 'setting' arg does not pass validation
		:type defaultValue: str
		:return: Returns either the validated 'setting' value or the default value in the relevant data type
		:rtype: int | str | bool
		"""
		try:
			match field:
				case 'ms_odbc_driver_version' | 'logs_to_keep':
					value = int(Validation.ValidateType(self._logger, 'int', setting, defaultValue))
				case 'smtp_recipient_list':
					value = list(Validation.ValidateRecipients(self._logger, setting, defaultValue))
				case 'smtp_time_out':
					value = int(Validation.ValidateIntRange(self._logger, setting, defaultValue, self.smtpTmoutMin, self.smtpTmoutMax, field))
				case 'size_bytes':
					value = int(Validation.ValidateIntRange(self._logger, setting, defaultValue, self.logSizeMin, self.logSizeMax, field))
				case 'debug' | 'use_exclusions_bfi' | 'use_exclusions_bfc' | 'use_exclusions_wr' | 'use_exclusions_con':
					value = bool(Validation.ValidateType(self._logger, 'bool', setting, defaultValue))
				case 'notify_bfi' | 'removal_bfi' | 'notify_bfc' | 'removal_bfc' | 'notify_wr' | 'removal_wr' | 'notify_con' | 'removal_con':
					value = int(Validation.ValidateIntRange(self._logger, setting, defaultValue, self.thresMin, self.thresMax, field))
				case 'run_time_bfi' | 'run_time_bfc' | 'run_time_wr' | 'run_time_con':
					value = str(Validation.ValidateRunTime(self._logger, setting, defaultValue, field))
				case 'bfc_servers' | 'bfi_servers' | 'wr_servers' | 'dw_server':
					value = list(Validation.ValidateFQDN(self._logger, field, setting, defaultValue))
		except Exception as e:
			value = defaultValue
			self._logger.error(f"Exception encounterd setting {field}. Using default value: {defaultValue} | {e}")
			self._logger.debug(traceback.format_exc())
		
		return value


##############################################################################################

if __name__ == "__main__":
	from log_config import LogConfig
	logSetup = LogConfig('setupError', 20000000, 5, logLevel=logging.DEBUG)
	setupLogger = logSetup.ConfigureLogger()

	print("Log Level:", logSetup.logLevel)
	print("Logs to Keep:", logSetup.maxKeep)
	print("Log Max Size:", logSetup.maxSize)

	settingsTest = SettingsConfig(setupLogger)
	print(type(settingsTest))
	print("ODBC Version:", settingsTest.odbcVer)
	print("SMTP List:", settingsTest.smtpList)
	print("BFC Servers:", settingsTest.bfcServers)
	print("BFI Servers:", settingsTest.bfiServers)
	print("WR Servers:", settingsTest.wrServers)
	print("DW Servers:", settingsTest.dwServer)
	print("SMTP Timeout:", settingsTest.smtpTmout)
	print("Log Size:", settingsTest.logSize)
	print("Log Keep:", settingsTest.logKeep)
	print("Log Debug:", settingsTest.logDebug)
	print("Inactive BFI Notify Threshold:", settingsTest.bfiNotify)
	print("Inactive BFI Removal Threshold:", settingsTest.bfiRemoval)
	print("Inactive BFC Notify Threshold:", settingsTest.bfcNotify)
	print("Inactive BFC Removal Threshold:", settingsTest.bfcRemoval)
	print("Inactive WR Notify Threshold:", settingsTest.wrNotify)
	print("Inactive WR Removal Threshold:", settingsTest.wrRemoval)
	print("Inactive CON Notify Threshold:", settingsTest.conNotify)
	print("Inactive CON Removal Threshold:", settingsTest.conRemoval)
	print("Use BFI Exclusions", settingsTest.bfiUseExcl)
	print("Use BFC Exclusions", settingsTest.bfcUseExcl)
	print("Use WR Exclusions", settingsTest.wrUseExcl)
	print("Use CON Exclusions", settingsTest.conUseExcl)
	print("BFI Run Time", settingsTest.bfiRunTime)
	print("BFC Run Time", settingsTest.bfcRunTime)
	print("WR Run Time", settingsTest.wrRunTime)
	print("CON Run Time", settingsTest.conRunTime)

	assert settingsTest.bfcServers == ['']
	assert settingsTest.bfiServers == ['']
	assert settingsTest.wrServers == ['']
	assert settingsTest.dwServer == ['']
	assert settingsTest.smtpList != ['']
	
	
