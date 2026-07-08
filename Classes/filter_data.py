############## FilterData ##########################
# Static Methods for filtering and refining data ###
####################################################

import logging
import traceback
import re
import os

class FilterData():
	"""
	Contains static methods for filtering, formatting, and reading data.
	"""
	def __init__(self):
		pass
	
	@staticmethod
	def ReadUsersFile(filePath: str) -> list:
		"""
		Reads in file contents to a list.
		Trailing whitespace is removed from each line
		If the file is missing it will raise a FileNotFoundError
		"""
		if not os.path.isfile(filePath):
			raise FileNotFoundError
		
		userList = []
		with open(filePath) as file:
			for line in file:
				userList.append(line.rstrip())
		return userList
	
	@staticmethod
	def FilterUsers(inactiveList: list, exclList: list, flagList: list = None, activeList: list = None) -> list:
		"""
		Filter inactive users against the relevant lists
		Inactive user list and excluded user list are required
		Flagged user list and active user lists are optional

		Can be used to filter for excluded users, flagged users, and against active users (wr)
		Returns a list containg the fully inactive users
		"""
		formatInactive = [user.lower() for user in inactiveList]
		formatExcl = [user.lower() for user in exclList]

		if activeList is not None:
			formatActive = [user.lower() for user in activeList]
			formatInactive = [user for user in formatInactive if user not in formatActive]

		if flagList is not None:
			formatFlag = [user.lower() for user in flagList]
			inactiveUsers = [user for user in formatInactive if user.lower() not in formatExcl and user.lower() not in formatFlag]
		else:
			inactiveUsers = [user for user in formatInactive if user.lower() not in formatExcl]
		
		return inactiveUsers
	
	# De-duplicate list 
	@staticmethod
	def DedupeList(listData: list) -> list:
		"""
		Creates a dictionary from the list arg, then converts back to a list
		Dictionary keys must be unique which will automatically remove duplicates

		Returns a list
		"""
		dedupedList = list(dict.fromkeys(listData))
		return dedupedList
	
	# Format user list for use in SQL 
	@staticmethod
	def FormatSQL(userList: list) -> str:
		"""
		Formats a SQL query with the correct syntax
		
		Read in a list and add single quotes to each item.
		Escape single quotes that exist in the item
		Add commas after every item
		Remove final comma

		Example:
		Method called with the following userList arg:
			['user1@domain.domain', "user'2@domain.domain", "user'3@domain.domain"]
		Method returns the following string:
			"'user1@domain.domain','user''2@domain.domain','user''3@domain.domain'"

		Example use case:
		SELECT userPrincipalName FROM [VADW].[AD].[Users] where sAMAccountName in ('user1@domain.domain','user''2@domain.domain','user''3@domain.domain')
		"""
		formattedUPNList = []
		for user in userList:
			# escape single quotes in username for sql
			user = re.sub(r"'", "''", user)
			formattedUPNList.append(f"'{user}',")
		# Convert formattedUPNList to a string and remove the final comma
		formattedUPNStr = ''.join(formattedUPNList)
		formattedUPNStr = formattedUPNStr[:-1]

		return formattedUPNStr

	# Filter out MEA sAMAccountName from Console
	@staticmethod
	def FilterConDescr(userList: list) -> str:
		"""
		Use specifically for parsing the Console Inactive user SQL query output
		Filters the Description column from that output to pull out the users samAccountName

		Once the values have been parsed, FormatSQL() is called to format the values for another SQL query
		The return string is used in another SQL query to return UPNs from the samAccountNames in VADW
		"""
		newList = []
		for user in userList:
			# use split to return a list of strings and grab the second element in the list.  All descriptions should start with 'ADMIN' as their first field and the samaccountname should always be the second element
			samAccountName = user.split(":")[1]
			newList.append(samAccountName)

		# add single quotes to each user. add commas after every user
		formattedUPNStr = FilterData.FormatSQL(newList)

		return formattedUPNStr
	
	@staticmethod
	def ConvertKeystoList(dictionary: dict) -> list:
		"""
		Converts dictionary keys to a list.

		Returns a list.
		"""
		valueList = [key for key in dictionary.keys()]
		return valueList
	
	@staticmethod
	def ConvertValuestoList(dictionary: dict) -> list:
		"""
		Converts dictionary values to a list.

		Returns a list.
		"""
		valueList = [value for value in dictionary.values()]
		return valueList

if __name__ == "__main__":

	from log_config import LogConfig
	logSetup = LogConfig('filter_data_test', 20000000, 5, logLevel=logging.DEBUG)
	testLogger = logSetup.ConfigureLogger()