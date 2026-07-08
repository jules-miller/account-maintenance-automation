######## ###Validation #######################
# Static validation methods usable anywhere ##
##############################################

import logging
import traceback
import re
from typing import Union

class Validation:
	"""
	Collection of static methods used to validate data.
	"""

	def __init__(self):
		pass

	@staticmethod
	def ValidateType(logger: logging.Logger, dataType: str, value: str, defaultValue: str) -> Union[int, str, bool]:
		"""
		Used for validating application settings.
		
		Validates that the passed str 'value' can be converted to the relevant 'dataType'.

		Returns the value cast as the relevant dataType.
		If there is a ValueError, the default value will be used.
		"""
		try:
			match dataType:
				case 'int':
					setting = int(value)
				case 'bool': # settings.conf could contain [Tt]rue/[Ff]alse or 0|1
					trueMatches = ['true', '1']
					falseMatches = ['false', '0']
					if value.lower() in trueMatches:
						setting = True
					elif value.lower() in falseMatches:
						setting = False
					else:
						raise ValueError
				case 'str':
					setting = str(value)
				case _:
					setting = value
		except ValueError as e:
			setting = defaultValue
			logger.error(f"{value} is not configured as {dataType}. Using default value: {defaultValue} | {e}")
			logger.debug(traceback.format_exc())

		return setting   
	
	@staticmethod
	def ValidateIntRange(logger: logging.Logger, value: str, defaultValue: str, minInt: int, maxInt: int, component: str) -> int:
		"""
		Used to validate that the passed 'value' falls within the range of 'minInt' and 'maxInt'

		Returns the value cast as an int.
		If there is a ValueError, the default value will be used.
		"""
		try:
			if int(value) >= minInt and int(value) <= maxInt: # verify the value is withing the specified range
				val = int(value)
			else:
				val = int(defaultValue)
				logger.error(f"The value '{value}' for {component} is outside the required range. Using default value: {defaultValue}")
		except ValueError as e:
			val = int(defaultValue)
			logger.error(f"The {value} for {component} is not configured as an INT. Using default value: {defaultValue} | {e}")
			logger.debug(traceback.format_exc())
		
		return val
	
	@staticmethod
	def ValidateRunTime(logger: logging.Logger, value: str, defaultValue: str, app: str) -> str:
		"""
		Used to validate the syntax of the run time setting.
		Example of valid syntax:
		12:07:00

		If the syntax is invalid, the default value is used.
		"""
		pattern = re.compile("^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]$") # pattern match example: 12:07:00
		if pattern.match(value):
			setting = value
		else:
			setting = defaultValue
			logger.error(f"Run time {value} for {app} is not using the correct format. Using default value: {defaultValue}")
		
		return setting
	
	@staticmethod
	def ValidateRecipients(logger: logging.Logger, smtpValue: str, defaultValue: str) -> list:
		"""
		Use to validate the SMTP recipients in settings.conf.
		Verifies a valid email address is present for each recipient.

		Invalid email addresses are removed.  If no valid email addresses exist, the default value is used.
		"""
		smtpList = smtpValue.split(',')
		tempList = []
		for item in smtpList:
			if item.count('@domain.domain') == 1:
				tempList.append(item)
			else:
				logger.warning(f"Removing invalid SMTP recipient: {item}")

		if len(tempList) == 0:
			logger.warning(f"No valid SMTP recipients were found.  Using default value: {defaultValue}")
			defaultList = defaultValue.split(',')
			return defaultList
		else:
			return tempList

	@staticmethod
	def ValidateFQDN(logger: logging.Logger, field: str, value: str, defaultValue: str) -> list:
		"""
		Validates FQDN values before returning final result as a list.
		
		:param logger: The logger to write to.
		:type logger: logging.Logger
		:param field: The setting name.
		:type field: str
		:param value: The value to validate. Should be a comma separated string value of FQDNs
		:type value: str
		:param defaultValue: The default value to use if no valid 'values' are found
		:type defaultValue: str
		:return: Returns the validated value that has been converted from a string to a list
		:rtype: list
		"""
		valuesList = value.split(',')
		tempList = []
		for item in valuesList:
			if item == '':
				continue
			if item.count('.domain.domain') == 1:
				tempList.append(item)
			else:
				logger.warning(f"Removing invalid {field} FQDN: {item}")

		if len(tempList) == 0:
			logger.warning(f"No valid {field} FQDNs were found.  Using default value: {defaultValue}")
			defaultList = defaultValue.split(',')
			return defaultList
		else:
			return tempList
	
	@staticmethod
	def ValidateSqlUsers(logger: logging.Logger, value: str) -> bool:
		"""
		Validates the string of users passed to a SQL query.

		This is not a 100% perfect validation.
		Splits the user string into a list on the ","
		Then iterates over the list to check for correct syntax

		Using a single regex pattern for the entire {value} string will not catch everything
		As it is currently, it will also not catch absoultey everything
		The split+iterate method is slower and more cumbersome than a single regex match, but necessary in this case.

		Example:
		Pass: 'user1@domain.domain','user''2@domain.domain' 
		Pass: 'user1@domain.domain'
		Fail: 'user1@domain.domain','user''2@domain.domain','user3@domain.domain',
		Fail: 'user1@domain.domain

		Pass: 'user1@domain.domain user2@domain.domain'
		Ideally, the above string would not pass.  However, due to the way the string is constructed, it will always pass.  
		Including extra regex to require @domain.domain would only fix this is certain cases.  However, this isn't desirable because local api accounts \
		without the @domain.domain suffix can be passed to the query.  In the case of the name conversion queires, SQL will just ignore it, \
		so it doesn't cause an issue. 
		"""
		userList = value.split(',')
		pattern = re.compile("^'.*'$")
		
		result = True
		for item in userList:
			if not pattern.match(item):
				result = False
				logger.error("The user list is not formatted correctly")
				logger.debug(f"Incorrectly formatted user list: {value}")
				break
		
		return result
