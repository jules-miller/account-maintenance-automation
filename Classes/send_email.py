############### SendEmail #######################################
# Handles all email methods for all components ##################
# Recipients must be set via getter before calling SendMessage ##
#################################################################

import logging
import traceback
import smtplib
from email.message import EmailMessage
import datetime

class SendEmail:
	"""
	Use for SMTP message.
	IMPORTANT: You must set the recipients prior to running SendMessage().

	This can be used to send error/complete notifications to the BigFix team or notification emails to users.
	"""
	smtpServer = 'smtp.domain.domain'
	
	def __init__(self, logger: logging.Logger, app: str, timeout: int, notifyDay: int, removalDay: int ) -> None:
		self._logger = logger
		self._app = app
		self._timeout = timeout
		self._recipients = None
		self._notifyDay = notifyDay
		self._removalDay = removalDay

	# Getters and setters
	@property
	def recipients(self):
		return self._recipients
	
	@recipients.setter
	def recipients(self, value: list):
		if type(value) != list:
			raise TypeError("Recipients must be a list even if there is only one recipient")
		self._recipients = value

	#####################################################################
	### Message Content Creation - START ###
	#####################################################################
	# Create the error message
	def _MsgErr(self, errMsg: str) -> str:
		currentTime = datetime.datetime.now()
		msg = rf"""<!DOCTYPE html>
				<html>
				<head>
				<title>Account Maintenance Failed</title>
				<style>
					body {{
					margin: 0;
					padding: 0;
					}}
				</style>
				</head>
				<body>
				Application: {self._app}<br>
				TimeStamp: {currentTime}<br>
				Message: {errMsg}<br>
				</body>
				</html>
			"""
		return msg
	
	# Create the user notification message
	def _MsgUserNotify(self) -> str:
		msg = rf"""<!DOCTYPE html>
				<html>
				<head>
				<style>
					body {{
					margin: 0;
					padding: 0;
					}}
				</style>
				</head>
				<body>
				This notification is to inform you that your {self._app} access has reached {self._notifyDay} days of inactivity.  If you still require access, please login.<br>
				Inactive accounts are removed after {self._removalDay} days.<br>
				<br>
				Thank you,
				<br>
				BigFix Team
				</body>
				</html>
			"""
		return msg

	# Create the all clear/complete message
	def _MsgComplete(self, statusValues: dict) -> str:
		htmlPreBody = """<!DOCTYPE html>
						<html>
						<head>
						<style>
							body {{
							margin: 0;
							padding: 0;
							}}
						</style>
						</head>
						<body>
					"""
		htmlBody = "\n".join( # Create a list of strings that is joined into one multi-line string. this is so that conditionals can be used in setting specific lines
			[
				f"Component: {statusValues.get("Component")}<br>",
				f"Last Run: {statusValues.get("Last Run")}<br>",
				f"User Notification Status: {statusValues.get("User Notification Status")}<br>",
				f"AD Removal Status: {statusValues.get("AD Removal Status")}<br>" if statusValues.get("AD Removal Status") is not None else "AD Removal Status = N/A<br>",
				f"DB Removal Status: {statusValues.get("DB Removal Status")}<br>" if statusValues.get("DB Removal Status") is not None else "DB Removal Status = N/A<br>",
				f"User Notifications: {statusValues.get("User Notifications")}<br>",
				f"User Removals: {statusValues.get("User Removals")}<br>" if statusValues.get("User Removals") is not None else "User Removals = N/A<br>"
			]
		)

		htmlPostBody = """</body>
						</html>
					"""

		msg = htmlPreBody + "\n" + htmlBody +"\n" + htmlPostBody
		return msg

	#####################################################################
	### Message Content Creation - END ###
	#####################################################################

	#####################################################################
	### Email and SMTP setup + sends the message - START ###
	#####################################################################
	
	def _SendAll(self, msg: str, subject: str) -> None:
		email = EmailMessage()
		email.set_content(msg, subtype = 'html')

		email['Subject'] = f'{self._app} - {subject}'
		email['From'] = "INSERT_FROM_ADDRESS"
		email['To'] = self._recipients

		self._SMTP(email)
		self._logger.debug(f"SMTP Notification Sent - Subject: {subject} | Recipients: {self._recipients}")

	def _SendLoop(self, msg: str, subject: str) -> None:
		email = EmailMessage()
		email.set_content(msg, subtype = 'html')

		for user in self._recipients:
			email['Subject'] = f'{self._app} - {subject}'
			email['From'] = "INSERT_FROM_ADDRESS"
			email['To'] = user

			self._SMTP(email)
			self._logger.info(f"SMTP Notification Sent - Subject: {subject} | Recipient: {user}")

	def _SMTP(self, email: EmailMessage) -> None: # smtp exceptions raised here will be caught in SendMessage()
		s = smtplib.SMTP(SendEmail.smtpServer, timeout=self._timeout)
		s.starttls()
		s.send_message(email)
		s.quit()
		del email['Subject']
		del email['From']
		del email['To']
		

	#####################################################################
	### Email and SMTP setup + sends the message - END ###
	#####################################################################
	
	# The public method that should be called from main
	def SendMessage(self, msgType: str, msg: str = None, statusValues: dict = None) -> int:
		"""
		IMPORTANT: Configure the recipients before running this method!
		Raises a ValueError if recipients are not set.

		The msgType must be 'err', 'notify', or 'complete'
		The relevant message will be set based on the msgType and the msg/statusValues if relevant.

		Return values:
		0=Success
		1=Failed
		"""
		if self._recipients == None:
			raise ValueError("Recipients must be set to send an email!")
		try:
			match msgType:
					case 'err':
						if msg == None:
							raise ValueError("Message content not specified")
						msgStr = self._MsgErr(msg)
						self._SendAll(msgStr, 'Account Maintenance Error')
					case 'notify':
						msgStr = self._MsgUserNotify()
						self._SendLoop(msgStr, 'Account Inactivity Notification')
					case 'complete':
						if statusValues == None or type(statusValues) != dict:
							raise ValueError("Status values not specified OR incorrect type")
						msgStr = self._MsgComplete(statusValues)
						self._SendAll(msgStr, "Account Maintenance Report")
					case _:
						raise ValueError("Invalid message type")
			exitCode = 0
		except ValueError as e:
			self._logger.error(f"Failed to send email - {e}")
			self._logger.debug(traceback.format_exc())
			exitCode = 1
		except TimeoutError as e:
			self._logger.error(f"The smtp server connection timed out: Current timeout = {self._timeout} - {e}")
			self._logger.debug(traceback.format_exc())
			exitCode = 1
		except smtplib.SMTPConnectError as e:
			self._logger.error(f"An error occurred while establishing a connection with the smtp server - {e}")
			self._logger.debug(traceback.format_exc())
			exitCode = 1
		except smtplib.SMTPServerDisconnected as e:
			self._logger.error(f"smtp server unexpectedly disconnected - {e}")
			self._logger.debug(traceback.format_exc())
			exitCode = 1
		except smtplib.SMTPDataError as e:
			self._logger.error(f"The smtp server refused to accept the message data - {e}")
			self._logger.debug(traceback.format_exc())
			exitCode = 1
		except smtplib.SMTPException as e:
			self._logger.error(e)
			self._logger.debug(traceback.format_exc())
			exitCode = 1
		except Exception as e:
			self._logger.error(e)
			self._logger.debug(traceback.format_exc())
			exitCode = 1
		
		return exitCode
		


if __name__ == '__main__':
	from log_config import LogConfig
	logSetup = LogConfig('sendemailTest', 20000000, 5, logLevel=logging.DEBUG)
	testLogger = logSetup.ConfigureLogger()

	instance = SendEmail(testLogger, 'UnitTest', 30, 76, 90)
	instance.recipients = ['INSERT_UPN_HERE']
	instance.SendMessage('err', msg="Test Error Message")
