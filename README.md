# Account Maintenance Utility

## Summary

This is an account maintenance application that covers all BigFix componenents (WR, BFC, BFI, and Console).  
These app is designed to run as a service and automate the full account maintenance process in a mult-server and multi-component environment.

**NOTE: Some components have been partially redacted. This is for portfolio purposes only.**

#### It features the following:
	- User notifications (inactivity threshold configurable)
	- Option to exclude a subset of users
	- Scheduled run times per component
	- Active Directory removals (inactivity threshold configurable)
	- Database removals (inactivity threshold configurable)
	- Administrative summary notifications

## Build details
- Package in one-dir mode only.  If one-file mode is used, the relative paths will be broken as the exe is extracted to a tmp folder at run time.
- Use --uac-admin to require admin rights to run.  

- Example build command: 
	- `pyinstaller.exe --clean --uac-admin --onedir --icon="./va_logo_small.ico" -n BESAcctMaint.exe --version-file .\acct_maint_version_file.txt -p ".\Classes" --log-level DEBUG .\AcctMaintMain.py --contents-directory "."`
- Ensure the PowerShell scripts are added to the final build.


