# Run test with DEBUG logging enabled and reference Logs/send_email_unittesting.log for details

import unittest
from unittest.mock import patch
import sys
import os
import logging
import smtplib
from email.message import EmailMessage

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../Classes'))

from log_config import LogConfig
from send_email import SendEmail

logSetup = LogConfig('send_email_unittesting', 20000000, 5, logLevel=logging.DEBUG)
testLogger = logSetup.ConfigureLogger()

validRecipients = ['user1@domain']
invalidRecipients = 'invalidType'

validStatus = {}
validStatus['Component'] = 'BigFix Inventory'
validStatus['Last Run'] = '12:07:00'
validStatus['User Notification Status'] = 'Success'
validStatus['AD Removal Status'] = 'Success'
validStatus['DB Removal Status'] = {'BFI-C' : 'Success',
                                    'BFI-1' : 'Success',
                                    'BFI-2': 'Success',
                                    'BFI-3' : 'Failed',
                                    'BFI-4' : 'Success',
                                    'BFI-5' : 'Success',
                                    'BFI-6' : 'Success'
                                    }
validStatus['User Notifications'] = ['user1@domain', 'user2@domain']
validStatus['User Removals'] = ['user3@domain', 'user4@domain']

email = EmailMessage()
email.set_content("test", subtype = 'html')

class TestSendEmail(unittest.TestCase):
	
	# Test Class instantiation and the recipients setter with a valid type
	def test_setRecipientsValid(self):
		instance = SendEmail(testLogger, 'Unit Test', 30, 76, 90)
		self.assertEqual(instance.recipients, None, "Recipients should not be currently set")
		instance.recipients = validRecipients
		self.assertEqual(instance.recipients, validRecipients, "Recipients should be a list of users")
		
	# Tests the recipients setter with an invalid type
	def test_setRecipientsInvalid(self):
		instance = SendEmail(testLogger, 'Unit Test', 30, 76, 90)
		self.assertEqual(instance.recipients, None, "Recipients should not be currently set")
		with self.assertRaises(TypeError):
			instance.recipients = invalidRecipients

	# Test successful email send with SendMessage: err type
	def test_SendMessageErr(self):
		instance = SendEmail(testLogger, 'Unit Test', 30, 76, 90)
		instance.recipients = validRecipients
		sendMsg = instance.SendMessage('err', msg="Test Account Maintenance Failure")
		self.assertEqual(sendMsg, 0, "SendMessage should be successful")
	
	# Test successful email send with SendMessage: notify type
	def test_SendMessageNotify(self):
		instance = SendEmail(testLogger, 'Unit Test', 30, 76, 90)
		instance.recipients = ['user@domain', 'user@domain']
		sendMsg = instance.SendMessage('notify')
		self.assertEqual(sendMsg, 0, "SendMessage should be successful")

	# Test successful email send with SendMessage: complete type
	def test_SendMessageComplete(self):
		instance = SendEmail(testLogger, 'Unit Test', 30, 76, 90)
		instance.recipients = validRecipients
		sendMsg = instance.SendMessage('complete', statusValues=validStatus)
		self.assertEqual(sendMsg, 0, "SendMessage should be successful")

	# Test failed email send with SendMessage
	def test_SendMessageFailure(self):
		instance = SendEmail(testLogger, 'Unit Test', 30, 76, 90)
		instance.recipients = validRecipients
		sendMsg = instance.SendMessage('complete', statusValues='wrong type')
		self.assertEqual(sendMsg, 1, "SendMessage should fail")

	# _SendAll should raise a TimeoutError
	# mock the smtpServer class var with an new value to force the Timeout exception
	@patch.object(SendEmail, "smtpServer", "0.0.0.0") # patch with a valid server that is NOT a smtp server
	def test_SendAllConErr(self):
		instance = SendEmail(testLogger, 'Unit Test', timeout=5, notifyDay=76, removalDay=90)
		instance.recipients = validRecipients
		with self.assertRaises(TimeoutError):
			instance._SendAll("failure test", "failure test")

	# _SendAll should raise a ValueError and assert the log message
	def test_SendAllValueErr(self):
		instance = SendEmail(testLogger, 'Unit Test', timeout=30, notifyDay=76, removalDay=90)
		instance.recipients = validRecipients
		with self.assertLogs(testLogger, level='DEBUG') as cm: # Check that the logger wrote the error when ValueError was caught
			result = instance.SendMessage('invalidtype')
			self.assertEqual(result, 1, "SendMessage should fail and return exit code of 1")
		self.assertIn("ERROR:send_email_unittesting:Failed to send email - Invalid message type", cm.output)

	def test_SendMessageNoRecipientsSet(self):
		""" Running SendEmail.SendMessage() before the recipients field is set ('None' value) should raise a ValueError """
		instance = SendEmail(testLogger, 'Unit Test', timeout=30, notifyDay=76, removalDay=90)
		with self.assertRaises(ValueError):
			instance.SendMessage('notify')
		

if __name__ == '__main__':
	unittest.main()
