# Run test with DEBUG logging enabled and reference Logs/validationError_unittesting.log for details

import unittest
from unittest.mock import patch
import sys
import os
import logging

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../Classes'))

from log_config import LogConfig
from validation import Validation

logSetup = LogConfig('validationError_unittesting', 20000000, 5, logLevel=logging.DEBUG)
validationLogger = logSetup.ConfigureLogger()

class TestValidation(unittest.TestCase):
	
	### Validation.ValidType Tests ###
	# Test Validation.ValidateType for strings
	def test_ValidateTypeStr(self):
		value = Validation.ValidateType(validationLogger, 'str', 'testString', 'defaultTestString')
		self.assertEqual(value, 'testString', "Failed to return the correct value")
		self.assertEqual(type(value), str, "Failed to return the correct type")
		
	# Test Validation.ValidateType for valid int
	def test_ValidateTypeInt(self):
		value = Validation.ValidateType(validationLogger, 'int', '30', '20')
		self.assertEqual(value, 30, "Failed to return the correct value")
		self.assertEqual(type(value), int, "Failed to return the correct type")
		
	# Validation.ValidateType for invalid int
	def test_ValidateTypeIntInvalid(self):
		value = Validation.ValidateType(validationLogger, 'int', 'invalidInt', '20')
		self.assertEqual(value, '20', "Failed to return the correct value")
		self.assertEqual(type(value), str, "Failed to return the correct type")

	# Validation.ValidateType for valid bool (starting as a str)
	def test_ValidateTypeBool(self):
		value = Validation.ValidateType(validationLogger, 'bool', 'True', '0')
		self.assertEqual(value, True, "Failed to return the correct value")
		self.assertEqual(type(value), bool, "Failed to return the correct type")

	# Validation.ValidateType for valid bool (starting as an int)
	def test_ValidateTypeBool2(self):
		value = Validation.ValidateType(validationLogger, 'bool', '1', '0')
		self.assertEqual(value, True, "Failed to return the correct value")
		self.assertEqual(type(value), bool, "Failed to return the correct type")

	# Validation.ValidateType for invalid bool
	def test_ValidateTypeBoolInvalid(self):
		value = Validation.ValidateType(validationLogger, 'bool', 'invalidBool', '0')
		self.assertEqual(value, '0', "Failed to return the correct value")
		self.assertEqual(type(value), str, "Failed to return the correct type")
		
	### Validation.ValidateRunTime Tests ###
	# Valid run time
	def test_ValidateRunTimeValid(self):
		value = Validation.ValidateRunTime(validationLogger, '12:09:00', '12:07:00', 'Test App')
		self.assertEqual(value, '12:09:00', "Failed to set the correct time. Check regex.")
	
	# Invalid run time 1 - check that the regex works 
	def test_ValidateRunTimeInvalid1(self):
		value = Validation.ValidateRunTime(validationLogger, '12:09:00:', '12:07:00', 'Test App')
		self.assertEqual(value, '12:07:00', "Failed to set the correct time. Check regex.")

	# Invalid run time 2 - check that the regex works 
	def test_ValidateRunTimeInvalid2(self):
		value = Validation.ValidateRunTime(validationLogger, '12:09', '12:07:00', 'Test App')
		self.assertEqual(value, '12:07:00', "Failed to set the correct time. Check regex.")

	# Invalid run time 3 - check that the regex works 
	def test_ValidateRunTimeInvalid3(self):
		value = Validation.ValidateRunTime(validationLogger, '', '12:07:00', 'Test App')
		self.assertEqual(value, '12:07:00', "Failed to set the correct time. Check regex.")

	### Validation.ValidateIntRange Tests ###
	# Valid int
	def test_ValidateIntRange(self):
		value = Validation.ValidateIntRange(validationLogger, 20, '30', 10, 60, 'test smtp timeout')
		self.assertEqual(value, 20, "Value outisde of specified range")
		value = Validation.ValidateIntRange(validationLogger, 20350000, '20000000', 10000000, 30000000, 'test log size')
		self.assertEqual(value, 20350000, "Value outisde of specified range")

	# Invalid int
	def test_ValidateIntRangeInvalid(self):
		value = Validation.ValidateIntRange(validationLogger, '75', '30', 10, 60, 'test smtp timeout')
		self.assertEqual(value, 30, "Value outisde of specified range")
		value = Validation.ValidateIntRange(validationLogger, 3500000, '20000000', 10000000, 30000000, 'test log size')
		self.assertEqual(value, 20000000, "Value outisde of specified range")
	
	# ValidateSqlUsers True
	def test_ValidateSqlUsersTrue(self):
		users = "'user1@domain','user''2@domain','user3@domain'"
		result = Validation.ValidateSqlUsers(validationLogger, users)
		self.assertEqual(result, True)
		users = "'user1@domain'"
		result = Validation.ValidateSqlUsers(validationLogger, users)
		self.assertEqual(result, True)
		users = "'user1@domain','apiuser'"
		result = Validation.ValidateSqlUsers(validationLogger, users)
		self.assertEqual(result, True)

	# ValidateSqlUsers False
	def test_ValidateSqlUsersFalse(self):
		users = "'user1@domain,'user''2@domain','user3@domain'"
		result = Validation.ValidateSqlUsers(validationLogger, users)
		self.assertEqual(result, False)
		users = "'user1@domain','user''2@domain','user3@domain',"
		result = Validation.ValidateSqlUsers(validationLogger, users)
		self.assertEqual(result, False)
		users = "'user1@domain"
		result = Validation.ValidateSqlUsers(validationLogger, users)
		self.assertEqual(result, False)

	# ValidateRecipients Success
	def test_ValidateRecipientsValid(self):
		users = 'user1@domain,user2@domain,user3@domain'
		defaultUsers = 'user1@domain,user2@domain'
		expectedResult = users.split(',')
		result = Validation.ValidateRecipients(validationLogger, smtpValue=users, defaultValue=defaultUsers)
		self.assertTrue(result, expectedResult)

	# ValidateRecipients Remove users
	def test_ValidateRecipientsRem(self):
		users = 'user1@domain,badEmail@bad.domain,user3@domain'
		defaultUsers = 'user1@domain,user2@domain'
		expectedResult = ['user1@domain', 'user3@domain']
		result = Validation.ValidateRecipients(validationLogger, smtpValue=users, defaultValue=defaultUsers)
		self.assertTrue(result, expectedResult)

	# ValidateRecipients Fail - no valid users - use default value
	def test_ValidateRecipientsDef(self):
		users = 'invalidSyntax,badEmail@bad.domain,user3@gov'
		defaultUsers = 'user1@domain,user2@domain'
		expectedResult = defaultUsers
		result = Validation.ValidateRecipients(validationLogger, smtpValue=users, defaultValue=defaultUsers)
		self.assertTrue(result, expectedResult)

	def test_ValidateFQDNEmpty(self):
		""" Checks that an empty value and default value return a list with a single empty string """
		value = ''
		defaultValue = ''
		expectedResult = ['']
		result = Validation.ValidateFQDN(validationLogger, field='test1', value=value, defaultValue=defaultValue)
		self.assertTrue(result, expectedResult)

	def test_ValidateFQDNValid(self):
		""" Uses a value that contains only valid server FQDNs """
		value = 'server1@domain,server2@domain,server3@domain'
		defaultValue = ''
		expectedResult = list(value)
		result = Validation.ValidateFQDN(validationLogger, field='test1', value=value, defaultValue=defaultValue)
		self.assertTrue(result, expectedResult)

	def test_ValidateFQDNRem(self):
		""" Uses a value that contains valid and invalid server FQDNs resulting in the invalid entries being removed from the final list"""
		value = 'server1@domain,server2.invalid.domain,server3@domain'
		defaultValue = ''
		expectedResult = ['server1@domain', 'server3@domain']
		result = Validation.ValidateFQDN(validationLogger, field='test1', value=value, defaultValue=defaultValue)
		self.assertTrue(result, expectedResult)

	def test_ValidateFQDNDef(self):
		""" Uses an value containing only invalid FQDNS resulting in the defaultValue being used"""
		value = 'server1.invalid.domain,server2.invalid.domain,server3.invalid.domain'
		defaultValue = ''
		expectedResult = ['']
		result = Validation.ValidateFQDN(validationLogger, field='test1', value=value, defaultValue=defaultValue)
		self.assertTrue(result, expectedResult)


if __name__ == '__main__':
	unittest.main()