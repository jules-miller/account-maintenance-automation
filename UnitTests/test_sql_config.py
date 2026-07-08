# Run test with DEBUG logging enabled and reference Logs test_sql_config_unittesting.log for details

import unittest
from unittest.mock import patch
import sys
import os
import logging

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../Classes'))

from log_config import LogConfig
from sql_config import SqlConfig
from settings_config import SettingsConfig as SC

logSetup = LogConfig('test_sql_config_unittesting', 20000000, 5, logLevel=logging.DEBUG)
testLogger = logSetup.ConfigureLogger()

class TestSQLConfig(unittest.TestCase):

	# Test bfcQueryNotify Success
	def test_BFCNotifySuccess(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.bfcQueryNotify, None, "BFC query notify should not be set yet")
		instance.bfcQueryNotify = {"notifThres" : "70", "removThres" : "98"}
		self.assertIn("DAY, - 70", instance.bfcQueryNotify, "The notify threshold was not set correctly")
		self.assertIn("DAY, - 98", instance.bfcQueryNotify, "The removal threshold was not set correctly")
	
	# Test bfcQueryNotify Fail
	def test_BFCNotifyFail(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.bfcQueryNotify, None, "BFC query notify should not be set yet")
		instance.bfcQueryNotify = {"notifThres" : "1", "removThres" : "150"}
		self.assertIn(f"DAY, - {SC.defaultNotifyThresBFC}", instance.bfcQueryNotify, "The notify threshold was not set correctly - should have reverted to default values")
		self.assertIn(f"DAY, - {SC.defaultRemovalThresBFC}", instance.bfcQueryNotify, "The removal threshold was not set correctly - should have reverted to default values")

	 # Test bfcQueryNotify Exceptions
	def test_BFCNotifyExc(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.bfcQueryNotify, None, "BFC query notify should not be set yet")
		with self.assertRaises(TypeError):
			instance.bfcQueryNotify = "wrong data type"
		with self.assertRaises(ValueError):
			instance.bfcQueryNotify = {"wrong key value" : "1", "removThres" : "150"}
			
	# Test bfcQueryRemove Success
	def test_BFCRemoveSuccess(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.bfcQueryRemove, None, "BFC query remove should not be set yet")
		instance.bfcQueryRemove = 98
		self.assertIn("DAY, - 98", instance.bfcQueryRemove, "The removal threshold was not set correctly")
	
	# Test bfcQueryRemove Fail
	def test_BFCRemoveFail(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.bfcQueryRemove, None, "BFC query remove should not be set yet")
		instance.bfcQueryRemove = 1
		self.assertIn(f"DAY, - {SC.defaultRemovalThresBFC}", instance.bfcQueryRemove, "The removal threshold was not set correctly - should have reverted to default values")
		
	# Test bfiQueryNotify Success
	def test_BFINotifySuccess(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.bfiQueryNotify, None, "BFI query notify should not be set yet")
		instance.bfiQueryNotify = {"notifThres" : "70", "removThres" : "98"}
		self.assertIn("DAY, - 70", instance.bfiQueryNotify, "The notify threshold was not set correctly")
		self.assertIn("DAY, - 98", instance.bfiQueryNotify, "The removal threshold was not set correctly")
	
	# Test bfiQueryNotify Fail
	def test_BFINotifyFail(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.bfiQueryNotify, None, "BFI query notify should not be set yet")
		instance.bfiQueryNotify = {"notifThres" : "1", "removThres" : "150"}
		self.assertIn(f"DAY, - {SC.defaultNotifyThresBFI}", instance.bfiQueryNotify, "The notify threshold was not set correctly - should have reverted to default values")
		self.assertIn(f"DAY, - {SC.defaultRemovalThresBFI}", instance.bfiQueryNotify, "The removal threshold was not set correctly - should have reverted to default values")

	 # Test bfiQueryNotify Exceptions
	def test_BFINotifyExc(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.bfiQueryNotify, None, "BFI query notify should not be set yet")
		with self.assertRaises(TypeError):
			instance.bfiQueryNotify = "wrong data type"
		with self.assertRaises(ValueError):
			instance.bfiQueryNotify = {"wrong key value" : "1", "removThres" : "150"}
			
	# Test bfiQueryRemove Success
	def test_BFIRemoveSuccess(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.bfiQueryRemove, None, "BFI query remove should not be set yet")
		instance.bfiQueryRemove = 98
		self.assertIn("DAY, - 98", instance.bfiQueryRemove, "The removal threshold was not set correctly")
	
	# Test bfiQueryRemove Fail
	def test_BFIRemoveFail(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.bfiQueryRemove, None, "BFI query remove should not be set yet")
		instance.bfiQueryRemove = 1
		self.assertIn(f"DAY, - {SC.defaultRemovalThresBFI}", instance.bfiQueryRemove, "The removal threshold was not set correctly - should have reverted to default values")
		
	# Test wrQuNotifActi Success
	def test_WRNotifyActiveSuccess(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.wrQuNotifActi, None, "Instance variable should not be set yet")
		instance.wrQuNotifActi = 80
		self.assertIn("DAY, -80", instance.wrQuNotifActi, "The notify threshold was not set correctly")
		
	# Test wrQuNotifActi failure
	def test_WRNotifyActiveFail(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.wrQuNotifActi, None, "Instance variable should not be set yet")
		instance.wrQuNotifActi = 1
		self.assertIn(f"DAY, -{SC.defaultNotifyThresWR}", instance.wrQuNotifActi, "The notify threshold was not set correctly")
		
	# Test wrQuRemovActi Success
	def test_WRRemoveActiveSuccess(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.wrQuRemovActi, None, "Instance variable should not be set yet")
		instance.wrQuRemovActi = 80
		self.assertIn("DAY, -80", instance.wrQuRemovActi, "The notify threshold was not set correctly")
		
	# Test wrQuRemovActi failure
	def test_WRRemoveActiveFail(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.wrQuRemovActi, None, "Instance variable should not be set yet")
		instance.wrQuRemovActi = 1
		self.assertIn(f"DAY, -{SC.defaultRemovalThresWR}", instance.wrQuRemovActi, "The notify threshold was not set correctly")

	# Test wrQuNotifInact Success
	def test_WRNotifyInactiveSuccess(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.wrQuNotifInact, None, "Instance variable should not be set yet")
		instance.wrQuNotifInact = {"notifThres" : "70", "removThres" : "98"}
		self.assertIn("DAY, -70", instance.wrQuNotifInact, "The notify threshold was not set correctly")
		self.assertIn("DAY, -98", instance.wrQuNotifInact, "The removal threshold was not set correctly")
	
	# Test wrQuNotifInact Fail
	def test_WRNotifyInactiveFail(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.wrQuNotifInact, None, "Instance variable should not be set yet")
		instance.wrQuNotifInact = {"notifThres" : "1", "removThres" : "150"}
		self.assertIn(f"DAY, -{SC.defaultNotifyThresWR}", instance.wrQuNotifInact, "The notify threshold was not set correctly - should have reverted to default values")
		self.assertIn(f"DAY, -{SC.defaultRemovalThresWR}", instance.wrQuNotifInact, "The removal threshold was not set correctly - should have reverted to default values")

	 # Test wrQuNotifInact Exceptions
	def test_WRNotifyInactiveExc(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.wrQuNotifInact, None, "Instance variable should not be set yet")
		with self.assertRaises(TypeError):
			instance.wrQuNotifInact = "wrong data type"
		with self.assertRaises(ValueError):
			instance.wrQuNotifInact = {"wrong key value" : "1", "removThres" : "150"}
			
	# Test wrQuRemovInact Success
	def test_WRRemoveInactiveSuccess(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.wrQuRemovActi, None, "Instance variable should not be set yet")
		instance.wrQuRemovActi = 80
		self.assertIn("DAY, -80", instance.wrQuRemovActi, "The notify threshold was not set correctly")
		
	# Test wrQuRemovInact failure
	def test_WRRemoveInactiveFail(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.wrQuRemovActi, None, "Instance variable should not be set yet")
		instance.wrQuRemovActi = 1
		self.assertIn(f"DAY, -{SC.defaultRemovalThresWR}", instance.wrQuRemovActi, "The notify threshold was not set correctly")
		
	# Test conQueryNotify Success
	def test_CONNotifySuccess(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.conQueryNotify, None, "Instance variable should not be set yet")
		instance.conQueryNotify = {"notifThres" : "70", "removThres" : "98"}
		self.assertIn("DAY, - 70", instance.conQueryNotify, "The notify threshold was not set correctly")
		self.assertIn("DAY, - 98", instance.conQueryNotify, "The removal threshold was not set correctly")
	
	# Test conQueryNotify Fail
	def test_CONNotifyFail(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.conQueryNotify, None, "Instance variable should not be set yet")
		instance.conQueryNotify = {"notifThres" : "1", "removThres" : "150"}
		self.assertIn(f"DAY, - {SC.defaultNotifyThresCon}", instance.conQueryNotify, "The notify threshold was not set correctly - should have reverted to default values")
		self.assertIn(f"DAY, - {SC.defaultRemovalThresCon}", instance.conQueryNotify, "The removal threshold was not set correctly - should have reverted to default values")

	 # Test conQueryNotify Exceptions
	def test_CONNotifyExc(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.conQueryNotify, None, "Instance variable should not be set yet")
		with self.assertRaises(TypeError):
			instance.conQueryNotify = "wrong data type"
		with self.assertRaises(ValueError):
			instance.conQueryNotify = {"wrong key value" : "1", "removThres" : "150"}
			
	# Test conQueryRemove Success
	def test_CONRemoveSuccess(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.conQueryRemove, None, "Instance variable should not be set yet")
		instance.conQueryRemove = 98
		self.assertIn("DAY, - 98", instance.conQueryRemove, "The removal threshold was not set correctly")
	
	# Test conQueryRemove Fail
	def test_CONRemoveFail(self):
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.conQueryRemove, None, "Instance variable should not be set yet")
		instance.conQueryRemove = 1
		self.assertIn(f"DAY, - {SC.defaultRemovalThresCon}", instance.conQueryRemove, "The removal threshold was not set correctly - should have reverted to default values")
		
	# Test upnToDnQuery Success
	def test_upnToDnQuerySuccess(self):
		userStr = "'user1@domain.domain','user''2@domain.domain'"
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.upnToDnQuery, None, "Instance variable should not be set yet")
		instance.upnToDnQuery = userStr
		self.assertIn(userStr, instance.upnToDnQuery)
	
	# Test upnToDnQuery Fail
	def test_upnToDnQueryFail(self):
		userStr = "'user1@domain.domain','user''2@domain.domain',"
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.upnToDnQuery, None, "Instance variable should not be set yet")
		with self.assertRaises(ValueError):
			instance.upnToDnQuery = userStr

	# Test samToUpnQuery Success
	def test_samToUpnQuerySuccess(self):
		userStr = "'user1@domain.domain','user''2@domain.domain'"
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.samToUpnQuery, None, "Instance variable should not be set yet")
		instance.samToUpnQuery = userStr
		self.assertIn(userStr, instance.samToUpnQuery)
	
	# Test samToUpnQuery Fail
	def test_samToUpnQueryFail(self):
		userStr = "'user1@domain.domain','user''2@domain.domain',"
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.samToUpnQuery, None, "Instance variable should not be set yet")
		with self.assertRaises(ValueError):
			instance.samToUpnQuery = userStr
		
	# Test delTransBfc Success
	def test_delTransBfcSuccess(self):
		userStr = "'user1@domain.domain','user''2@domain.domain'"
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.delTransBfc, None, "Instance variable should not be set yet")
		instance.delTransBfc = userStr
		self.assertIn(userStr, instance.delTransBfc)
	
	# Test delTransBfc Fail
	def test_delTransBfcFail(self):
		userStr = "'user1@domain.domain','user''2@domain.domain',"
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.delTransBfc, None, "Instance variable should not be set yet")
		with self.assertRaises(ValueError):
			instance.delTransBfc = userStr

	# Test delTransBfi Success
	def test_delTransBfiSuccess(self):
		userStr = "'user1@domain.domain','user''2@domain.domain'"
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.delTransBfi, None, "Instance variable should not be set yet")
		instance.delTransBfi = userStr
		self.assertIn(userStr, instance.delTransBfi)
	
	# Test delTransBfc Fail
	def test_delTransBfiFail(self):
		userStr = "'user1@domain.domain','user''2@domain.domain',"
		instance = SqlConfig(testLogger)
		self.assertEqual(instance.delTransBfi, None, "Instance variable should not be set yet")
		with self.assertRaises(ValueError):
			instance.delTransBfi = userStr
			
		
if __name__ == '__main__':
	unittest.main()