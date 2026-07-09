# Changelog

#### 1/4/24
	- Original deployment

#### 2/1/24
	- - Built with Python  3.11.1 using pyinstaller==6.3.0
	- Added: 
		- requirements.txt
		- TestImports.py
	- Modules (v1.1 was built with the following):
		- altgraph==0.17.4
		- packaging==23.2
		- pefile==2023.2.7
		- pyinstaller==6.3.0
		- pyinstaller-hooks-contrib==2024.0
		- pyodbc==5.0.1
		- pywin32==306
		- pywin32-ctypes==0.2.2
		- schedule==1.2.1

#### 4/22/24
	- WR, BFC, and BFI all updated to v1.2
	- Console not modified
	- In WR, BFC and BFI: Fixed a bug in the query_results validation
		- The query_results were not being properly validated for 'Connection_Error'.
		- Looping through nested lists incorrectly was causing the problem
		- Replaced with 'any' function and list comprehension: Ex. if any("Connection_Error" in item for item in bfi_queries)

#### 5/15/24
	- Console, WR, BFC, and BFI all updated to v1.3
	- The ODBC version was hardcoded in the installedApps() function.  In v1.3, this funciton has been modifed to use the odbcVer parameter.

#### 10/28/24
	- Console, WR, BFC, and BFI all updated to v1.4
	- Built with Python 3.12.0 and updated packages
		- Used Pyinstaller 6.11.0
		- pyodbc==5.2.0
		- pywin32==308
		- schedule==1.2.2

#### 03/13/25
	- Refactored all utilities
	- Now one app to rule them all
	- Built with Python 3.13
		- pillow==11.1.0 (only used to convert .ico in build process)
		- pyinstaller==6.12.0
		- pyodbc==5.2.0
		- schedule==1.2.2
	- Changes:
		- OOP
		- improved validation
		- improved logging
		- improved error checking
		- improved testing
		- easier to read/maintain
	- Added 119 unit tests

#### 03/18/25
	- archived the old utilities 

#### 03/19/25
	- added logging handler check in LogConfig.ConfigureLogger() to prevent duplicate handlers and log entries
	- fixed a log message typo in RunConsole

#### 01/21/26
	- Version 1.6
	- Built with Python 3.14.0
		- pillow==12.1.0
		- pyinstaller==6.18.0
		- pyodbc==5.3.0
		- schedule==1.2.2
	- Removed 'return' statement out of all 'finally' blocks
	- Fixed file path issues in the unit tests files 'test_utilities.py, test_settings_config.py, test_filter_data.py'
        - All file paths referenced in this file are now relative to the parent directory.
        - Ex. besFile = (Path(__file__).parent /  "ConfFiles/test_tempFile.txt").resolve().as_posix()
	- Added "delimiters='='" to ConfigParser constructor in def _CreateSettingsFile() in settings_config.py
	- Added test_SendMessageNoRecipientsSet Unit Test in test_send_email
	- Changed log level for log messages in Validation.ValidateRecipients() from error to warning
	- Added docstrings to methods in settings_config.py
	- Added new method (ValidateFQDN()) in the Validation class to verify server FQDNs
	- Added new method (_AddSettingsToFile()) in the SettingsConfig class to support appending missing settings if conf file exists
	- Updated SettingsConfig._AssignSetting to call _AddSettingsToFile if the setting is missing
	- Added additional case to SettingsConfig._ValidateSetting() for server FQDNs
	- Added new server fields in SettingsConfig and created getters for each.  Also added them to Settings.Config._CreateSettingsFile()
	- Added four unit tests in test_validation for the new ValidateFQDN method
	- Added TestSettingsConfig.test_AddSettingToFile unit test
	- In AcctMaintMain, removed all hardcoded server FQDNs and replaced them with the relevant getter in SettingsConfig()
	- In AcctMaintMain, in each query and run function, added checks for valid server fqdns before continuing.
