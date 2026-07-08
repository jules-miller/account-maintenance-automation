############## SqlConfig #########
# Configures SQL queries to use ##
# Used in DBQuery, DBWrite #######
##################################

import logging
import traceback
from settings_config import SettingsConfig as SC
from validation import Validation as V

class SqlConfig():
	"""
	This contains all SQL queries and transaction statements needed for account maintenance.
	The setters validate the values as best as possible before setting the SQL (this is also done when the settings are initially created on startup)
	The additional validation in the setters is to account for potential modifications where the queries are set without the values from the config file
	"""

	def __init__(self, logger: logging.Logger) -> None:
		self._logger = logger
		self._bfcQueryNotify = None
		self._bfcQueryRemove = None
		self._bfiQueryNotify = None
		self._bfiQueryRemove = None
		self._wrQuNotifActi = None
		self._wrQuRemovActi = None
		self._wrQuNotifInact = None
		self._wrQuRemovInact = None
		self._conQueryNotify = None
		self._conQueryRemove = None
		self._upnToDnQuery = None
		self._samToUpnQuery = None
		self._delTransBfc = None
		self._delTransBfi = None

	# Getters and setters
	@property
	def bfcQueryNotify(self):
		return self._bfcQueryNotify
	
	@bfcQueryNotify.setter
	def bfcQueryNotify(self, thresholds: dict) -> None:
		if type(thresholds) != dict:
			raise TypeError("Thresholds must be in a dictionary")
		if "notifThres" not in thresholds.keys():
			raise ValueError("notify threshold missing")
		if "removThres" not in thresholds.keys():
			raise ValueError("removal threshold missing")
		# validate the threshold (validation also happens in SettingsConfig) before setting the query
		# validation should not be necessary if using a value from an instance of the SettingsConfig class
		notify = V.ValidateIntRange(logger=self._logger, 
							 		value=thresholds["notifThres"],
									defaultValue=SC.defaultNotifyThresBFC,
									minInt=SC.thresMin,
									maxInt=SC.thresMax,
									component="BFC")
		removal = V.ValidateIntRange(logger=self._logger, 
							 		value=thresholds["removThres"],
									defaultValue=SC.defaultRemovalThresBFC,
									minInt=SC.thresMin,
									maxInt=SC.thresMax,
									component="BFC")
		self._bfcQueryNotify = self._BfcQueryNotify(notifThres=notify, removThres=removal)

	@property
	def bfcQueryRemove(self):
		return self._bfcQueryRemove
	
	@bfcQueryRemove.setter
	def bfcQueryRemove(self, removeThres: int) -> None:
		# validate the threshold (validation also happens in SettingsConfig) before setting the query
		# validation should not be necessary if using a value from an instance of the SettingsConfig class
		removal = V.ValidateIntRange(logger=self._logger, 
							 		value=removeThres,
									defaultValue=SC.defaultRemovalThresBFC,
									minInt=SC.thresMin,
									maxInt=SC.thresMax,
									component="BFC")
		self._bfcQueryRemove = self._BfcQueryRemove(removal)

	@property
	def bfiQueryNotify(self):
		return self._bfiQueryNotify
	
	@bfiQueryNotify.setter
	def bfiQueryNotify(self, thresholds: dict) -> None:
		if type(thresholds) != dict:
			raise TypeError("Thresholds must be in a dictionary")
		if "notifThres" not in thresholds.keys():
			raise ValueError("notify threshold missing")
		if "removThres" not in thresholds.keys():
			raise ValueError("removal threshold missing")
		# validate the threshold (validation also happens in SettingsConfig) before setting the query
		# validation should not be necessary if using a value from an instance of the SettingsConfig class
		notify = V.ValidateIntRange(logger=self._logger, 
							 		value=thresholds["notifThres"],
									defaultValue=SC.defaultNotifyThresBFI,
									minInt=SC.thresMin,
									maxInt=SC.thresMax,
									component="BFI")
		removal = V.ValidateIntRange(logger=self._logger, 
							 		value=thresholds["removThres"],
									defaultValue=SC.defaultRemovalThresBFI,
									minInt=SC.thresMin,
									maxInt=SC.thresMax,
									component="BFI")
		self._bfiQueryNotify = self._BfiQueryNotify(notifThres=notify, removThres=removal)

	@property
	def bfiQueryRemove(self):
		return self._bfiQueryRemove
	
	@bfiQueryRemove.setter
	def bfiQueryRemove(self, removeThres: int) -> None:
		# validate the threshold (validation also happens in SettingsConfig) before setting the query
		# validation should not be necessary if using a value from an instance of the SettingsConfig class
		removal = V.ValidateIntRange(logger=self._logger, 
							 		value=removeThres,
									defaultValue=SC.defaultRemovalThresBFI,
									minInt=SC.thresMin,
									maxInt=SC.thresMax,
									component="BFI")
		self._bfiQueryRemove = self._BfiQueryRemove(removal)

	@property
	def wrQuNotifActi(self):
		return self._wrQuNotifActi
	
	@wrQuNotifActi.setter
	def wrQuNotifActi(self, notifThres: int) -> None:
		# validate the threshold (validation also happens in SettingsConfig) before setting the query
		# validation should not be necessary if using a value from an instance of the SettingsConfig class
		notify = V.ValidateIntRange(logger=self._logger, 
							 		value=notifThres,
									defaultValue=SC.defaultNotifyThresWR,
									minInt=SC.thresMin,
									maxInt=SC.thresMax,
									component="WR")
		self._wrQuNotifActi = self._WrQuNotifActi(notify)

	@property
	def wrQuRemovActi(self):
		return self._wrQuRemovActi
	
	@wrQuRemovActi.setter
	def wrQuRemovActi(self, removeThres: int) -> None:
		# validate the threshold (validation also happens in SettingsConfig) before setting the query
		# validation should not be necessary if using a value from an instance of the SettingsConfig class
		remove = V.ValidateIntRange(logger=self._logger, 
							 		value=removeThres,
									defaultValue=SC.defaultRemovalThresWR,
									minInt=SC.thresMin,
									maxInt=SC.thresMax,
									component="WR")
		self._wrQuRemovActi = self._WrQuRemovActi(remove)

	@property
	def wrQuNotifInact(self):
		return self._wrQuNotifInact
	
	@wrQuNotifInact.setter
	def wrQuNotifInact(self, thresholds: dict) -> None:
		if type(thresholds) != dict:
			raise TypeError("Thresholds must be in a dictionary")
		if "notifThres" not in thresholds.keys():
			raise ValueError("notify threshold missing")
		if "removThres" not in thresholds.keys():
			raise ValueError("removal threshold missing")
		# validate the threshold (validation also happens in SettingsConfig) before setting the query
		# validation should not be necessary if using a value from an instance of the SettingsConfig class
		notify = V.ValidateIntRange(logger=self._logger, 
							 		value=thresholds["notifThres"],
									defaultValue=SC.defaultNotifyThresWR,
									minInt=SC.thresMin,
									maxInt=SC.thresMax,
									component="WR")
		removal = V.ValidateIntRange(logger=self._logger, 
							 		value=thresholds["removThres"],
									defaultValue=SC.defaultRemovalThresWR,
									minInt=SC.thresMin,
									maxInt=SC.thresMax,
									component="WR")
		self._wrQuNotifInact = self._WrQuNotifInact(notifThres=notify, removThres=removal)

	@property
	def wrQuRemovInact(self):
		return self._wrQuRemovInact
	
	@wrQuRemovInact.setter
	def wrQuRemovInact(self, removeThres: int) -> None:
		# validate the threshold (validation also happens in SettingsConfig) before setting the query
		# validation should not be necessary if using a value from an instance of the SettingsConfig class
		remove = V.ValidateIntRange(logger=self._logger, 
							 		value=removeThres,
									defaultValue=SC.defaultRemovalThresWR,
									minInt=SC.thresMin,
									maxInt=SC.thresMax,
									component="WR")
		self._wrQuRemovInact= self._WrQuRemovInact(remove)

	@property
	def conQueryNotify(self):
		return self._conQueryNotify
	
	@conQueryNotify.setter
	def conQueryNotify(self, thresholds: dict) -> None:
		if type(thresholds) != dict:
			raise TypeError("Thresholds must be in a dictionary")
		if "notifThres" not in thresholds.keys():
			raise ValueError("notify threshold missing")
		if "removThres" not in thresholds.keys():
			raise ValueError("removal threshold missing")
		# validate the threshold (validation also happens in SettingsConfig) before setting the query
		# validation should not be necessary if using a value from an instance of the SettingsConfig class
		notify = V.ValidateIntRange(logger=self._logger, 
							 		value=thresholds["notifThres"],
									defaultValue=SC.defaultNotifyThresCon,
									minInt=SC.thresMin,
									maxInt=SC.thresMax,
									component="CON")
		removal = V.ValidateIntRange(logger=self._logger, 
							 		value=thresholds["removThres"],
									defaultValue=SC.defaultRemovalThresCon,
									minInt=SC.thresMin,
									maxInt=SC.thresMax,
									component="CON")
		self._conQueryNotify = self._ConQueryNotify(notifThres=notify, removThres=removal)

	@property
	def conQueryRemove(self):
		return self._conQueryRemove
	
	@conQueryRemove.setter
	def conQueryRemove(self, removeThres: int) -> None:
		# validate the threshold (validation also happens in SettingsConfig) before setting the query
		# validation should not be necessary if using a value from an instance of the SettingsConfig class
		removal = V.ValidateIntRange(logger=self._logger, 
							 		value=removeThres,
									defaultValue=SC.defaultRemovalThresCon,
									minInt=SC.thresMin,
									maxInt=SC.thresMax,
									component="CON")
		self._conQueryRemove = self._ConQueryRemove(removal)

	@property
	def upnToDnQuery(self):
		return self._upnToDnQuery
	
	@upnToDnQuery.setter
	def upnToDnQuery(self, userStr: str) -> None:
		# validate the user string before setting the query
		isValid = V.ValidateSqlUsers(logger=self._logger, value=userStr)
		if isValid == False:
			raise ValueError("SQL user string not formatted correctly")
		self._upnToDnQuery = self._UpnToDnQuery(userStr)

	@property
	def samToUpnQuery(self):
		return self._samToUpnQuery
	
	@samToUpnQuery.setter
	def samToUpnQuery(self, userStr: str) -> None:
		# validate the user string before setting the query
		isValid = V.ValidateSqlUsers(logger=self._logger, value=userStr)
		if isValid == False:
			raise ValueError("SQL user string not formatted correctly")
		self._samToUpnQuery = self._SamToUpnQuery(userStr)

	@property
	def delTransBfc(self):
		return self._delTransBfc
	
	@delTransBfc.setter
	def delTransBfc(self, userStr: str) -> None:
		# validate the user string before setting the query
		isValid = V.ValidateSqlUsers(logger=self._logger, value=userStr)
		if isValid == False:
			raise ValueError("SQL user string not formatted correctly")
		self._delTransBfc = self._DelTransBfc(userStr)

	@property
	def delTransBfi(self):
		return self._delTransBfi
	
	@delTransBfi.setter
	def delTransBfi(self, userStr: str) -> None:
		# validate the user string before setting the query
		isValid = V.ValidateSqlUsers(logger=self._logger, value=userStr)
		if isValid == False:
			raise ValueError("SQL user string not formatted correctly")
		self._delTransBfi = self._DelTransBfi(userStr)

	##########################################################################################################
	##### SQL Queries/Transactions #####		
	def _BfcQueryNotify(self, notifThres: int, removThres: int) -> str:
		query = f''';with a as (SELECT 
					u.username
					,max(u.last_login_time) last_login_time
				FROM BFCDW.dbo.users u
				INNER JOIN BFCDW.dbo.roles_users ru ON u.id = ru.user_id and u.CoreServerID=ru.coreserverid
				WHERE u.deleted = 0
					AND ru.role_id != 0
				group by u.username
				)
				select a.username, au.distinguishedName, a.last_login_time from a join vadw.ad.users au on a.username=au.userPrincipalName
				where last_login_time < DATEADD(DAY, - {notifThres}, GETDATE()) AND last_login_time > DATEADD(DAY, - {removThres}, GETDATE())
				'''
		return query
	
	def _BfcQueryRemove(self, removeThres: int) -> str:
		query = f''';with a as (SELECT 
					u.username
					,max(u.last_login_time) last_login_time
				FROM BFCDW.dbo.users u
				INNER JOIN BFCDW.dbo.roles_users ru ON u.id = ru.user_id and u.CoreServerID=ru.coreserverid
				WHERE u.deleted = 0
					AND ru.role_id != 0
				group by u.username
				)
				select a.username, au.distinguishedName, a.last_login_time from a join vadw.ad.users au on a.username=au.userPrincipalName
				where last_login_time < DATEADD(DAY, - {removeThres}, GETDATE())
				'''
		return query
	
	def _BfiQueryNotify(self, notifThres: int, removThres: int) -> str:
		query = f''';with a as (SELECT 
					u.username
					,max(u.last_login_time) last_login_time
				FROM BFIDW.dbo.users u
				INNER JOIN BFIDW.dbo.roles_users ru ON u.id = ru.user_id and u.CoreServerID=ru.coreserverid
				WHERE u.deleted = 0
					AND ru.role_id != 0
				group by u.username
				)
				select a.username, au.distinguishedName, a.last_login_time from a join vadw.ad.users au on a.username=au.userPrincipalName
				where last_login_time < DATEADD(DAY, - {notifThres}, GETDATE()) AND last_login_time > DATEADD(DAY, - {removThres}, GETDATE())
				'''
		return query

	def _BfiQueryRemove(self, removeThres: int) -> str:
		query = f''';with a as (SELECT 
					u.username
					,max(u.last_login_time) last_login_time
				FROM BFIDW.dbo.users u
				INNER JOIN BFIDW.dbo.roles_users ru ON u.id = ru.user_id and u.CoreServerID=ru.coreserverid
				WHERE u.deleted = 0
					AND ru.role_id != 0
				group by u.username
				)
				select a.username, au.distinguishedName, a.last_login_time from a join vadw.ad.users au on a.username=au.userPrincipalName
				where last_login_time < DATEADD(DAY, - {removeThres}, GETDATE())
				'''
		return query
	
	def _WrQuNotifActi(self, notifThres: int) -> str:
		query = f'''SELECT LoginName,LastLoginTime
				FROM BESReporting.dbo.USER_NAMES 
				WHERE LastLoginTime > DATEADD(DAY, -{notifThres}, GETDATE())
				'''
		return query

	def _WrQuRemovActi(self, removeThres: int) -> str:
		query = f'''SELECT LoginName,LastLoginTime
			FROM BESReporting.dbo.USER_NAMES 
			WHERE LastLoginTime > DATEADD(DAY, -{removeThres}, GETDATE())
			'''
		return query
	
	def _WrQuNotifInact(self, notifThres: int, removThres: int) -> str:
		query = f'''SELECT LoginName,LastLoginTime
				FROM BESReporting.dbo.USER_NAMES 
				WHERE LastLoginTime < DATEADD(DAY, -{notifThres}, GETDATE()) AND LastLoginTime > DATEADD(DAY, -{removThres}, GETDATE())
				'''
		return query
	
	def _WrQuRemovInact(self, removeThres: int) -> str:
		query = f'''SELECT LoginName,LastLoginTime
				FROM BESReporting.dbo.USER_NAMES 
				WHERE LastLoginTime < DATEADD(DAY, -{removeThres}, GETDATE()) AND LastLoginTime > DATEADD(DAY, -180, GETDATE())
				'''
		return query
	
	def _ConQueryNotify(self, notifThres: int, removThres: int) -> str:
		query = f''';with a as (SELECT 
					u.username
					,max(ru.LastLoginTime) last_login_time
				FROM bfdw.dbo.userinfo u
				INNER JOIN BFDW.dbo.USER_LOGIN ru ON u.UserID = ru.UserLoginID and u.CoreServerID=ru.coreserverid
				WHERE u.IsDeleted = 0
					--AND ru.role_id != 0
				group by u.username
				)
				select a.username, au.description, a.last_login_time from a join vadw.ad.users au on a.username=au.userPrincipalName
				where last_login_time < DATEADD(DAY, - {notifThres}, GETDATE()) AND last_login_time > DATEADD(DAY, - {removThres}, GETDATE()) AND a.Username LIKE '%0@domain%'
				'''
		return query
	
	def _ConQueryRemove(self, removeThres: int) -> str:
		query = f''';with a as (SELECT 
					u.username
					,max(ru.LastLoginTime) last_login_time
				FROM bfdw.dbo.userinfo u
				INNER JOIN BFDW.dbo.USER_LOGIN ru ON u.UserID = ru.UserLoginID and u.CoreServerID=ru.coreserverid
				WHERE u.IsDeleted = 0
					--AND ru.role_id != 0
				group by u.username
				)
				select a.username, au.description, a.last_login_time from a join vadw.ad.users au on a.username=au.userPrincipalName
				where last_login_time < DATEADD(DAY, - {removeThres}, GETDATE()) AND a.Username LIKE '%0@domain%'
				'''
		return query
	
	def _UpnToDnQuery(self, users: str) -> str:
		query = f"SELECT distinguishedName FROM [VADW].[AD].[Users] where userPrincipalName in ({users})"
		return query

	def _SamToUpnQuery(self, users: str) -> str:
		query = f"SELECT userPrincipalName FROM [VADW].[AD].[Users] where sAMAccountName in ({users})"
		return query

	def _DelTransBfc(self, users: str) -> str:
		transaction = f'''UPDATE tem_analytics.dbo.users
						SET deleted = 1
						WHERE tem_analytics.dbo.users.id IN (SELECT tem_analytics.dbo.users.id FROM tem_analytics.dbo.users INNER JOIN tem_analytics.dbo.roles_users ON tem_analytics.dbo.users.id = tem_analytics.dbo.roles_users.user_id WHERE username in ({users}));
						'''
		return transaction
	
	def _DelTransBfi(self, users: str) -> str:
		transaction = f'''UPDATE temadb.dbo.users
					SET deleted = 1
					WHERE temadb.dbo.users.id IN (SELECT temadb.dbo.users.id FROM temadb.dbo.users INNER JOIN temadb.dbo.roles_users ON temadb.dbo.users.id = temadb.dbo.roles_users.user_id WHERE username in ({users}));
					'''
		return transaction
	
########################################################################
if __name__ == "__main__":
	from log_config import LogConfig
	logSetup = LogConfig('sqlConfigTest', 20000000, 5, logLevel=logging.DEBUG)
	testLogger = logSetup.ConfigureLogger()

	instance = SqlConfig(testLogger)
	print(instance.bfcQueryNotify)
	instance.bfcQueryNotify = {"notifThres" : 76, "removThres" : 90}
	print(instance.bfcQueryNotify)