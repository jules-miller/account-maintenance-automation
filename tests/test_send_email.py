# Run test with DEBUG logging enabled and reference Logs/send_email_unittesting.log for details

import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import logging
import smtplib
from email.message import EmailMessage

# Append the Classes directory to Python's path so that it can find the module imports
#sys.path.append(os.path.join(os.path.dirname(__file__), '../Classes'))

from src.log_config import LogConfig
from src.send_email import SendEmail

logSetup = LogConfig('send_email_unittesting', 20000000, 5, logLevel=logging.DEBUG)
testLogger = logSetup.ConfigureLogger()

validRecipients = ['test_user@subdomain.domain']
invalidRecipients = 'invalidType'
timeout = 30

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
validStatus['User Notifications'] = ['user1@subdomain.domain', 'user2@subdomain.domain']
validStatus['User Removals'] = ['user3@subdomain.domain', 'user4@subdomain.domain']

email = EmailMessage()
email.set_content("test", subtype = 'html')

class TestSendEmail(unittest.TestCase):

	def test_setRecipientsValid(self):
		"""Test Class instantiation and the recipients setter with a valid type"""
		instance = SendEmail(testLogger, 'Unit Test', timeout, 76, 90)
		self.assertEqual(instance.recipients, None, "Recipients should not be currently set")
		instance.recipients = validRecipients
		self.assertEqual(instance.recipients, validRecipients, "Recipients should be a list of users")

	def test_setRecipientsInvalid(self):
		"""Tests the recipients setter with an invalid type"""
		instance = SendEmail(testLogger, 'Unit Test', timeout, 76, 90)
		self.assertEqual(instance.recipients, None, "Recipients should not be currently set")
		with self.assertRaises(TypeError):
			instance.recipients = invalidRecipients
	def test_SendMessageNoRecipientsSet(self):
		""" Running SendEmail.SendMessage() before the recipients field is set ('None' value) should raise a ValueError """
		instance = SendEmail(testLogger, 'Unit Test', timeout=timeout, notifyDay=76, removalDay=90)
		with self.assertRaises(ValueError):
			instance.SendMessage('notify')

	@patch('src.send_email.smtplib.SMTP')
	def test_SendMessage_err(self, mock_smtp_class):
		"""Test successful email send with SendMessage: err type"""
		mock_smtp_instance = MagicMock()
		mock_smtp_class.return_value = mock_smtp_instance
		
		instance = SendEmail(testLogger, 'Unit Test', timeout, 76, 90)
		instance.recipients = ['user1@subdomain.domain']
		result = instance.SendMessage('err', msg="Test Account Maintenance Failure")

		self.assertEqual(result, 0)
		mock_smtp_class.assert_called_once_with(instance.smtpServer, timeout=timeout) # verify SMTP was initialized with correct server parameters
		mock_smtp_instance.send_message.assert_called_once() # verify send_message was called exactly once
		
		# Extract the email message object passed into send_message to inspect contents
		called_msg = mock_smtp_instance.send_message.call_args[0][0]
		self.assertIn('Message: Test Account Maintenance Failure', called_msg.get_content())
		mock_smtp_instance.quit.assert_called_once() # verify quit() was called after sending

	@patch('src.send_email.smtplib.SMTP')
	def test_SendMessage_notify(self, mock_smtp_class):
		"""Test successful email send with SendMessage: notify type"""
		mock_smtp_instance = MagicMock()
		mock_smtp_class.return_value = mock_smtp_instance
		
		instance = SendEmail(testLogger, 'Unit Test', timeout, 76, 90)
		instance.recipients = ['user1@subdomain.domain']
		result = instance.SendMessage('notify')

		self.assertEqual(result, 0)
		mock_smtp_class.assert_called_once_with(instance.smtpServer, timeout=timeout) # verify SMTP was initialized with correct server parameters
		mock_smtp_instance.send_message.assert_called_once() # verify send_message was called exactly once
		
		# Extract the email message object passed into send_message to inspect contents
		called_msg = mock_smtp_instance.send_message.call_args[0][0]
		self.assertIn('This notification is to inform you that your Unit Test access has reached 76 days of inactivity', called_msg.get_content())
		mock_smtp_instance.quit.assert_called_once() # verify quit() was called after sending

	@patch('src.send_email.smtplib.SMTP')
	def test_SendMessage_complete(self, mock_smtp_class):
		"""Test successful email send with SendMessage: complete type"""
		mock_smtp_instance = MagicMock()
		mock_smtp_class.return_value = mock_smtp_instance
		
		instance = SendEmail(testLogger, 'Unit Test', timeout, 76, 90)
		instance.recipients = ['user1@subdomain.domain']
		result = instance.SendMessage('complete', statusValues=validStatus)

		self.assertEqual(result, 0)
		mock_smtp_class.assert_called_once_with(instance.smtpServer, timeout=timeout) # verify SMTP was initialized with correct server parameters
		mock_smtp_instance.send_message.assert_called_once() # verify send_message was called exactly once
		
		# Extract the email message object passed into send_message to inspect contents
		called_msg = mock_smtp_instance.send_message.call_args[0][0]
		self.assertIn(f'Last Run: {validStatus.get("Last Run")}', called_msg.get_content())
		mock_smtp_instance.quit.assert_called_once() # verify quit() was called after sending
	
	def test_SendMessageFailure(self):
		"""Test failed message send"""
		instance = SendEmail(testLogger, 'Unit Test', 30, 76, 90)
		instance.recipients = validRecipients
		sendMsg = instance.SendMessage('complete', statusValues='wrong type')
		self.assertEqual(sendMsg, 1, "SendMessage should raise ValueError which should then be caught by except block")

	@patch('src.send_email.smtplib.SMTP')
	def test_SendAllConErr(self, mock_smtp):
		mock_smtp.side_effect = smtplib.SMTPConnectError(421, b"Service not available")
		instance = SendEmail(testLogger, 'Unit Test', timeout=timeout, notifyDay=76, removalDay=90)
		instance.recipients = validRecipients
		with self.assertRaises(smtplib.SMTPConnectError):
			instance._SendAll("failure test", "failure test")
	
	def test_SendAllValueErr(self):
		"""_SendAll should raise a ValueError and assert the log message"""
		instance = SendEmail(testLogger, 'Unit Test', timeout=30, notifyDay=76, removalDay=90)
		instance.recipients = validRecipients
		with self.assertLogs(testLogger, level='DEBUG') as cm: # Check that the logger wrote the error when ValueError was caught
			result = instance.SendMessage('invalidtype')
			self.assertEqual(result, 1, "SendMessage should fail and return exit code of 1")
		self.assertIn("ERROR:send_email_unittesting:Failed to send email - Invalid message type", cm.output)

	
if __name__ == '__main__':
	unittest.main()