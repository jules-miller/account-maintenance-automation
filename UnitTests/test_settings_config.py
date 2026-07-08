# Run test with DEBUG logging enabled and reference Logs/setupError_unittesting.log for details

import unittest
from unittest.mock import patch
import sys
import os
import logging
from pathlib import Path
import filecmp
import shutil
import configparser

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../Classes'))

from log_config import LogConfig
from settings_config import SettingsConfig

logSetup = LogConfig('setupError_unittesting', 20000000, 5, logLevel=logging.DEBUG)
setupLogger = logSetup.ConfigureLogger()

def RemoveFile(file):
	if os.path.exists(file):
		os.remove(file)

class TestSettingsConfig(unittest.TestCase):
	validConf = (Path(__file__).parent /  "ConfFiles/test_settings_valid_file.conf").resolve().as_posix()
	validConfNoComments = (Path(__file__).parent /  "ConfFiles/test_settings_valid_file_missing_comments.conf").resolve().as_posix()
	newConf = (Path(__file__).parent /  "ConfFiles/test_settings_new.conf").resolve().as_posix()
	valuesConf = (Path(__file__).parent /  "ConfFiles/test_settings_values.conf").resolve().as_posix()
	missingHeaderConf = (Path(__file__).parent /  "ConfFiles/test_settings_missing_section_header.conf").resolve().as_posix()
	badSyntaxConf = (Path(__file__).parent /  "ConfFiles/test_settings_bad_syntax.conf").resolve().as_posix()
	missingValueConf = (Path(__file__).parent /  "ConfFiles/test_settings_missing_value.conf").resolve().as_posix()
	invalidTypeConf = (Path(__file__).parent /  "ConfFiles/test_settings_invalid_type.conf").resolve().as_posix()
	missingFieldsConf = (Path(__file__).parent /  "ConfFiles/test_settings_missing_fields.conf").resolve().as_posix()
	missingFieldsConfCp = (Path(__file__).parent /  "ConfFiles/test_settings_missing_fields_cp.conf").resolve().as_posix()
	missingSMTPHeader = (Path(__file__).parent /  "ConfFiles/test_settings_missing_smtp_header.conf").resolve().as_posix()
	missingSMTPHeaderCp = (Path(__file__).parent /  "ConfFiles/test_settings_missing_smtp_header_cp.conf").resolve().as_posix()
	
	# If the conf file is missing, ensure a new file is created with default values - requires a sample file containing the default values
	# Mock the 'settingsFile' class variable to point to a test conf file that doesn't exist
	@patch.object(SettingsConfig, "settingsFile", newConf)
	def test_ValidConf(self):
		RemoveFile(self.newConf)
		self.assertTrue(not os.path.exists(self.newConf), f"test_ValidConf could not run.  File '{self.newConf}' already exists")
		self.assertTrue(os.path.exists(self.validConf), f"test_ValidConf could not run.  File '{self.validConf}' does not exist")
		instance = SettingsConfig(setupLogger) # Instantiate SettingsConfig with the mocked settingsFile class var in @patch.object
		self.assertEqual(instance.settingsFile, self.newConf, "Mock conf file failed in test_ValidConf") # Verify class variable is mocked
		areFilesEqual = filecmp.cmp(self.newConf, self.validConf) # Compare both files
		self.assertEqual(areFilesEqual, True, f"Conf file not created with default values in {self.validConf}")

	# Ensure a successful SettingsConfig instantiation results in accessible and correct values (this will test success for all methods in SettingsConfig)
	# Mock the 'settingsFile' class variable to point to a test conf file that doesn't exist
	@patch.object(SettingsConfig, "settingsFile", valuesConf)
	def test_ValuesConf(self):
		RemoveFile(self.valuesConf)
		self.assertTrue(not os.path.exists(self.valuesConf), f"test_ValuesConf could not run.  File '{self.valuesConf}' already exists")
		instance = SettingsConfig(setupLogger) # Instantiate SettingsConfig with the mocked settingsFile class var in @patch.object
		self.assertEqual(instance.settingsFile, self.valuesConf, "Mock conf file failed in test_ValuesConf") # Verify class variable is mocked
		self.assertEqual(instance.odbcVer, 18, f"Value not accessible or not correct: {instance.odbcVer}")
		self.assertEqual(instance.smtpTmout, 30, f"Value not accessible or not correct: {instance.smtpTmout}")

	# Test the exception 'configparser.MissingSectionHeaderError' is handled in SettingsConfig._LoadSettings()
	# Mock the 'settingsFile' class variable to point to a test conf file containing '*&^%)}'
	@patch.object(SettingsConfig, "settingsFile", missingHeaderConf)
	def test_MissingSectionHeader(self):
		self.assertTrue(os.path.exists(self.missingHeaderConf), f"test_MissingSectionHeader could not run.  File '{self.missingHeaderConf}' does not exist")
		instance = SettingsConfig(setupLogger) # Instantiate SettingsConfig with the mocked settingsFile class var in @patch.object
		self.assertEqual(instance.settingsFile, self.missingHeaderConf, "Mock conf file failed in test_MissingSectionHeader") # Verify class variable is mocked
		self.assertEqual(instance._loadSettings, False, "Return status should be False due to handling this exception: configparser.MissingSectionHeaderError")

	# Test bad conf file syntax - the exception 'configparser.ParsingError' is handled in SettingsConfig._LoadSettings()
	@patch.object(SettingsConfig, "settingsFile", badSyntaxConf)
	def test_ParsingError(self):
		self.assertTrue(os.path.exists(self.badSyntaxConf), f"test_ParsingError could not run.  File '{self.badSyntaxConf}' does not exist")
		instance = SettingsConfig(setupLogger) # Instantiate SettingsConfig with the mocked settingsFile class var in @patch.object
		self.assertEqual(instance.settingsFile, self.badSyntaxConf, "Mock conf file failed in test_ParsingError") # Verify class variable is mocked
		self.assertEqual(instance._loadSettings, False, "Return status should be False due to handling this exception: configparser.ParsingError")

	# Test missing values in the config file - when SettingsConfig._AssignSetting() handles a KeyError exception
	@patch.object(SettingsConfig, "settingsFile", missingValueConf)
	def test_MissingValue(self):
		self.assertTrue(os.path.exists(self.missingValueConf), f"test_MissingValue could not run.  File '{self.missingValueConf}' does not exist")
		instance = SettingsConfig(setupLogger) # Instantiate SettingsConfig with the mocked settingsFile class var in @patch.object
		self.assertEqual(instance.settingsFile, self.missingValueConf, "Mock conf file failed in test_MissingValue") # Verify class variable is mocked
		self.assertEqual(instance.smtpTmout, 30, "Return status should be 30 due to handling this exception: KeyError")

	# Test invalid setting type
	@patch.object(SettingsConfig, "settingsFile", invalidTypeConf)
	def test_InvalidType(self):
		self.assertTrue(os.path.exists(self.invalidTypeConf), f"test_InvalidType could not run.  File '{self.invalidTypeConf}' does not exist")
		instance = SettingsConfig(setupLogger) # Instantiate SettingsConfig with the mocked settingsFile class var in @patch.object
		self.assertEqual(instance.settingsFile, self.invalidTypeConf, "Mock conf file failed in test_InvalidType") # Verify class variable is mocked
		self.assertEqual(instance.odbcVer, 18, f"Value not accessible or not correct: {instance.odbcVer}")

	# Test _ValidateSetting
	def test__ValidateSetting(self):
		instance = SettingsConfig(setupLogger)
		validateSMTPTmout = instance._ValidateSetting('smtp_time_out', '100', '20')
		validateDebug = instance._ValidateSetting('debug', '1', '0')
		validateRunTimeBFI = instance._ValidateSetting('run_time_bfi', '100', '12:07:01')
		self.assertEqual(validateSMTPTmout, 20)
		self.assertEqual(validateDebug, True)
		self.assertEqual(validateRunTimeBFI, '12:07:01')

	@patch.object(SettingsConfig, "settingsFile", missingFieldsConfCp)
	def test_AddSettingToFile(self):
		"""
		Test the _AddSettingToFile method by starting with a conf file that is missing settings (fields).
		Assert the missing settings (fields) were added to the relevant section headers.
		"""
		RemoveFile(self.missingFieldsConfCp)
		shutil.copyfile(self.missingFieldsConf, self.missingFieldsConfCp)
		self.assertTrue(os.path.exists(self.missingFieldsConfCp), f"test_AddSettingToFile could not run. File '{self.missingFieldsConfCp}' does not exist")
		instance = SettingsConfig(setupLogger) # Instantiate SettingsConfig with the mocked settingsFile class var in @patch.object
		self.assertEqual(instance.settingsFile, self.missingFieldsConfCp, "Mock conf file failed in test_AddSettingToFile") # Verify class variable is mocked
		### Fields Missing from self.missingFieldsConfCp
		bfiServers = 'bfi_servers'
		wrServers = 'wr_servers'
		smtpList = 'smtp_recipient_list'
		notifyCon = 'notify_con'
		useExclCon = 'use_exclusions_con'
		###
		settings = configparser.ConfigParser()
		settings.read(self.missingFieldsConfCp)
		test1 = settings.has_option('PYODBC', bfiServers)
		test2 = settings.has_option('PYODBC', wrServers)
		test3 = settings.has_option('SMTP', smtpList)
		test4 = settings.has_option('INACTIVE THRESHOLD', notifyCon)
		test5 = settings.has_option('EXCLUSIONS', useExclCon)
		self.assertTrue(test1)
		self.assertTrue(test2)
		self.assertTrue(test3)
		self.assertTrue(test4)
		self.assertTrue(test5)

	
	@patch.object(SettingsConfig, "settingsFile", missingSMTPHeaderCp)
	def test_AddHeaderToFile(self):
		"""
		Test the _AddSettingToFile method by starting with a conf file that is missing a header.
		Assert the missing header as added to the conf.
		"""
		RemoveFile(self.missingSMTPHeaderCp)
		shutil.copyfile(self.missingSMTPHeader, self.missingSMTPHeaderCp)
		self.assertTrue(os.path.exists(self.missingSMTPHeaderCp), f"test_AddSettingToFile could not run. File '{self.missingSMTPHeaderCp}' does not exist")
		instance = SettingsConfig(setupLogger) # Instantiate SettingsConfig with the mocked settingsFile class var in @patch.object
		self.assertEqual(instance.settingsFile, self.missingSMTPHeaderCp, "Mock conf file failed in test_AddSettingToFile") # Verify class variable is mocked
		### Headers and Fields Missing from self.missingSMTPHeaderCp
		smtpHeader = 'SMTP'
		smtpList = 'smtp_recipient_list'
		smtpTmOut = 'smtp_time_out'
		###
		settings = configparser.ConfigParser()
		settings.read(self.missingSMTPHeaderCp)
		test1 = settings.has_section(smtpHeader)
		test2 = settings.has_option(smtpHeader, smtpTmOut)
		test3 = settings.has_option(smtpHeader, smtpList)
		self.assertTrue(test1)
		self.assertTrue(test2)
		self.assertTrue(test3)

if __name__ == '__main__':
	#logSetup = LogConfig('setupError_unittesting', 20000000, 5, logLevel=logging.DEBUG)
	#setupLogger = logSetup.ConfigureLogger()
	unittest.main()