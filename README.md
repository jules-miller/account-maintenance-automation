# BES-ACCOUNT-MAINTENANCE

**BES-ACCOUNT-MAINTENANCE** automates the account maintenance process the the BigFix platform. This includes Web Reports, BigFix Compliance, BigFix Inventory, and the Console.

:heavy_exclamation_mark: The Microsoft ODBC driver and PowerShell Active Directory module must be installed on the host.

:heavy_exclamation_mark: This is designed to run as a service with admin privileges and automate the full account maintenance process in a mult-server and multi-component environment. It needs a service wrapper such as 'NSSM' to be installed as a service.

:heavy_exclamation_mark: The service account used to run the executable must have permissions to all relevant databases and AD groups.

***NOTE: Some components have been partially redacted. This is for portfolio purposes only.***

### Includes the following features
	- User notifications (inactivity threshold configurable)
	- Option to exclude a subset of users
	- Scheduled run times per component
	- Active Directory removals (inactivity threshold configurable)
	- Database removals (inactivity threshold configurable)
	- Administrative summary notifications

## :package: Build Details

### Prerequisites

- Windows OS 
- **Python 3.10** or higher
- pyodbc
- schedule
- pyinstaller

### Manually build from source

    git clone https://github.com/jules-miller/account-maintenance-automation.git
    cd account-maintenance-automation
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    update the acct_maint_version_file.txt file to match the new build
    pyinstaller.exe --clean --uac-admin --onedir --icon="./<INSERT_ICON_FILE>.ico" -n BESAcctMaint.exe --version-file .\acct_maint_version_file.txt -p ".\Classes" --log-level DEBUG .\AcctMaintMain.py --contents-directory "."
    Ensure the AD PowerShell scripts are added to the final build.

## :file_folder: Project Structure

    |   .gitignore
    |   AcctMaintMain.py
    |   acct_maint_version_file.txt
    |   CHANGELOG.md
    |   README.md
    |   requirements.txt
    |   settings.conf
    |   
    +---PS
    |       bfc_remove_users_AD.ps1
    |       bfi_remove_users_AD.ps1
    |       wr_remove_users_AD.ps1
    |       
    +---src
    |   |   ad_write.py
    |   |   db_connect.py
    |   |   db_query.py
    |   |   db_write.py
    |   |   filter_data.py
    |   |   log_config.py
    |   |   pre_exec.py
    |   |   send_email.py
    |   |   settings_config.py
    |   |   signal_handlers.py
    |   |   sql_config.py
    |   |   startup_args.py
    |   |   utilities.py
    |   |   validation.py
    |   |   __init__.py
    |   |   
    |           
    \---tests
        |   test_ad_write.py
        |   test_db_connect.py
        |   test_db_query.py
        |   test_db_write.py
        |   test_filter_data.py
        |   test_log_config.py
        |   test_pre_exec.py
        |   test_send_email.py
        |   test_settings_config.py
        |   test_signal_handlers.py
        |   test_sql_config.py
        |   test_utilities.py
        |   test_validation.py
        |   __init__.py
        |   
        +---ConfFiles
        |       test_ReadUsersFile.txt
        |       test_settings_bad_syntax.conf
        |       test_settings_invalid_type.conf
        |       test_settings_missing_fields.conf
        |       test_settings_missing_fields_cp.conf
        |       test_settings_missing_section_header.conf
        |       test_settings_missing_smtp_header.conf
        |       test_settings_missing_smtp_header_cp.conf
        |       test_settings_missing_value.conf
        |       test_settings_new.conf
        |       test_settings_valid_file.conf
        |       test_settings_values.conf
        |       test_tempFile.txt
        |       
   
## :test_tube: Testing

Unit tests can be run from the root folder utilizing the built-in unittest framework. This will run all available unit tests.

To manually run tests:

    **python -m unittest discover -s tests**

