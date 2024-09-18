# Seaglider_autoPDOS_resend
The script automatically checks for missing glider files in the SFTP and requests those missing.

## Crontab setup
Run the script in the server from the user's directory.  
Edit crontab: crontab -e  (or -l read)  
To specify the editor use:
EDITOR=nano crontab -e   use nano as editor

Line in crontab:
0 * * * * $HOME/auto_pdos.sh > $HOME/MyCrontab.log

## AUTO_RESEND setup
1-Edit the list of gliders you want to automate in the auto_pdos.sh file  

2-Create the AUTO_RESEND file in the sgXXX directory: When creating the AUTO_RESEND file ‘switch’ to turn On/OFF the autopdos, make sure the file permissions are RW for all the users: chmod g+rw AUTO_RESEND
