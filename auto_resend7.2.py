#****************************************************************************
#******* AUTO RESEND v7 *****************************************************
# auto_pdos.sh and auto_resend7.2.py must be in the same directory

############################################################################################
# SCRIPT START - DON'T CHANGE ANYTHING 

# ALT+MC to show line number
# ALT+MI auto justify

###########################################
# Import libraries
import os
import datetime
import time
#from datetime import datetime

###########################################
# Import list of seagliders from bash
global glider_list, call_thd, dive_range
ids_bash = os.environ['ids'] # import glider list from bash [A]
glider_list = ids_bash.split() # import glider list from bash [B]
#glider_list = ['sg649','sg663','sg667','sg668','sg669','sg670'] # locally select gliders -> Comment [A] and [B] to use this

call_thd = 35 # time since last call threshold in minutes. Tdiff > 35 min --> ok to analyze
dive_range = 5 # dives before last one considered old and that should not be resent if requested by baselog. last_dive - dive2resend < 5 -> ok to resend 

###########################################
# Open baselog file

def process_baselog(glider_id):

	src_path = 'baselog_copies/'+glider_id+'.log'

	try:
		f = open(src_path)
		print('File '+src_path+ ' opened')
	except:
		print('File '+src_path+ ' not found')

	# Read each line
	if(f):
		n = 0
		while True:
		#for line in f:
			line = f.readline()
			# Detect end of file and stop loop
			if not line:
				break
			
			if('following files were not processed completely' in line):
				# Now keep lines starting in '/home/jails/aoml/gliderjail/home/ until 'Glider logout seen'
				#print('---------------------------------------------')
				#print('following...found -> clearing same_dive list')				
				same_dive = [] # list of lines belonging to same dive
				while True: 
					sub_line = f.readline() # read next line from file
				#	print('subline: ' + sub_line)
					if sub_line.startswith('    /home/jails/aoml/gliderjail/home/'): # if starts with /home/jails/aoml/gliderjail/home/ is the missing file
						sub_line = sub_line.split('/')[-1] # keep last part belonging to the file as /home/jails/aoml/gliderjail/home/sg663/sg0276dz.r
				#		print('subline file: ' + sub_line)
						same_dive.append(sub_line) # append to list of missing files in current dive
					
					# check fragment
					if sub_line.startswith('        Fragment'):
						sub_line = sub_line.split() # split by spaces
						for x in range(len(sub_line)):
							item = sub_line[x]
							if item.startswith('/home/jails/aoml/gliderjail/home/'):
								n = x
								break
						sub_line = sub_line[n].split('/')[-1] # split by slash and grab last item with fragment missing
						same_dive.append(sub_line)
					
					# end same dive loop
					if 'Glider logout' in sub_line:
				#		print('Glider logout BREAK')
						break # break loop because there are no more missing files in current dive
				#print('------------------')
				#print('Same_dive list:')
				#print(same_dive)
				#print('------------------')
				# at this point there's a list with files missing in current dive in the form of sg0276dz.r or sg0276dz.x01
				# create a command for each file but delete items that are complete files and contain only a chunk missing later in the list
				#print('Creating commands...')
				
				same_dive = processed_list(same_dive) # filter the list, delete file from list if only a chunk is missing. 
				#print('Same_dive list processed:')
				#print(same_dive) # If [sg0123dz.r,sg0123dz.x01,sg0125lz.r] -> [sg0123dz.x01,sg0125lz.r]
				
				#sort items by type of file (c->d->l)
				#same_dive.sort(key = lambda x: x.split('.')[-2])
				#print('Same_dive list precessed and sorted')
				#print(same_dive)
				
				# create text string with commands	
				command_string = ''
				inc_diveN = -999
				k = 0
				for element in same_dive:
					chunk = False
					if 'x' in element:
						chunk = True
						fragment = element.split('.')[1].replace('x','') # get the chunk x01 and delete x -> 01 
					inc_file = element.split('.')[0] # split incomplete file name and grab first part as sg0276dz
					inc_file = inc_file.replace('sg','') # delete sg and remains 0276dz
					file_type = inc_file[-2] # get 2nd to last char -> c, l or d
					if file_type == 'k':
						file_type = 'c'
					inc_diveN = int(inc_file[0:4]) # dive number is a fixed 4 digit number. Convert to integer
					#print('inc_diveN', inc_diveN)
					#if ( isinstance(inc_diveN, int)):
					#	pass
					#else:
					#	inc_diveN = -999

					
				#	print('------------------')
					if chunk == True:
						cmd = 'resend_dive /' + file_type + ' ' + str(inc_diveN) + ' ' + fragment
					else:
						cmd = 'resend_dive /' + file_type + ' ' + str(inc_diveN)
				#	print(str(k) + ' -> ' + cmd)
					# stack commands into one string
					command_string = command_string + cmd + '\n'
					k = k + 1
				# Increase number of incomplete messages
				n = n + 1
				# print commands within last loop
				#print('pdoscmd text:\n' + command_string)
				#print('---------------------------------------------')

			
	f.close() 
	print("\n%%%%%%%%%%%%%%%%%%%%%%%%%%%")
	try:
		print('Last dive claiming an incomplete processed file: ' + str(inc_diveN) + '\nCommands:\n' + command_string)
	except:
		inc_diveN = -999
		command_string = ''
		print('No incomplete dives found')

	print("%%%%%%%%%%%%%%%%%%%%%%%%%%%\n")
	print(str(n)+ ' lines with incomplete files')
	info_pair = [0,0]
	info_pair[0] = inc_diveN # last incomplete dive that needs to be resent as integer
	info_pair[1] = command_string # command text for .bat file
	return info_pair


###########################################
# Get last call date-time from comm.log
def get_call_datetime(glider_id):
	path = 'commlog_copies/'+glider_id+'.log'
	f = open(path) 
	while True:
		line = f.readline()
		
		if not line:
			break
		if 'logged in' in line:
			gps_line = f.readline() # keep last gps line when while loop ends 
	f.close()
	print('Last GPS line:')
	print(gps_line)
	gps_line = gps_line.split()[1]
	gps_line = gps_line.split(',') # GPS ddmmyy hhmmss ...
	call_date = gps_line[1]
	call_time = gps_line[2]
	# call day,month,year
	cday = int(call_date[0:2])
	cmonth = int(call_date[2:4])
	cyear = int('20' + call_date[4:6])
	# call hout, minute, second
	chour = int(call_time[0:2])
	cminute = int(call_time[2:4])
	csecond = int(call_time[4:6])
	# convert call datetime to epoch (yyyy,mm,dd,hh,mm,ss)
	cepoch = datetime.datetime(cyear, cmonth, cday, chour, cminute, csecond).strftime('%s') # seconds since 01/01/1970 00:00:00 
	print('GPS --> Date:' + num2digit(cmonth) + '/' + num2digit(cday) + '/' + str(cyear) + ' Time:' + num2digit(chour) + ':' + num2digit(cminute) + ':' + num2digit(csecond) )
	print('GPS --> epoch:' + str(cepoch) )	
	return cepoch


###########################################
# Get time difference between current epoch time and last call
def get_time_diff(glider_id):
	epoch_call = get_call_datetime(glider_id) # epoch time from comm.log
	
	#epoch_now = time.time() # current epoch. Keep this one last so delta is always positive 
	epoch_now = datetime.datetime.now().strftime('%s') # utc current time 
	print('Local --> epoch(utc):' + str(epoch_now))
	delta = int(epoch_now) - int(epoch_call) # + or - in seconds
	delta = delta/60 # in minutes

	return delta

###########################################
# Check if glider is in call or not. Return True/False
def check_call_time(glider_id):
	dt = get_time_diff(glider_id)
	dth = dt/60.0
	print( str(dt) + ' minutes since last call ( ' + str(dth) + ' hs )')		

	if dt > call_thd:
		print('Proceed --> time diff > ' + str(call_thd) + ' min - OK to analyze')
		return True
	else:
		print('Abort --> time diff < ' + str(call_thd) + ' min - DO NOT analyze')
		return False

###########################################
# Filter fragments only if available, otherwise keep complete file
def processed_list(list):
	newlist = []
	n = len(list)
	i = 0
	# leave only fragments
	for item in list:
		try:
			if 'x' not in item: # if x of chunk is not in item (i.e. x01)means is the whole file -> check if next item is a chunk
				a = item.split('.')
				next_a = list[i+1].split('.')
				if (a[0] == next_a[0]) and ('x' in next_a[1]): 
					list.remove(item)
			i=i+1
		except:
			pass	
	# place log files first
	for item in list:
		type = item.split('.')[0][-2]# c,d,l
		if type == 'l': # select here which file type you want to send to the top of the list
			temp = item # store item name
			list.remove(item) # remove from its current position
			list.insert(0,temp) # insert at the top of the list
	
	return list


###########################################
# Get last dive from directory

def get_last_cmdfile(glider_id):

	src_path = '/home/jails/aoml/gliderjail/home/'+glider_id
	file_list = os.listdir(src_path)
	
	dive_list = []
	for x in file_list:
		if x.startswith('cmdfile'):
			try:
				dive_num = x.split('.')[1] # keep number after dot
				dive_num = int(dive_num)
				dive_list.append(dive_num) # keep only cmdfile copies
			except: # for the case of the original cmdfile
				pass	
	#print('\nDive list:\n')
	#print(dive_list)
	dive_list.sort() # sort list of dives in the same list
	#print('Dive list sorted:')
	#print(dive_list)			
	last_dive = dive_list[-1]
	print('Last dive found in ' + src_path + ' -> ' + str(last_dive))

	return last_dive # return as integer


###########################################
# Get last pdoscmd.bat

def search_bat(glider_id):
	
	src_path = '/home/jails/aoml/gliderjail/home/'+glider_id
	file_list = os.listdir(src_path)
	active = False
	pdos_list = []
	for x in file_list:
		if x.startswith('pdoscmds'):
			if x.endswith('.bat'):
				active = True
	return active


###########################################
# Check text in .bat file

def check_bat_content(glider_id):
	src_path = '/home/jails/aoml/gliderjail/home/' + glider_id + '/pdoscmds.bat'
	f = open(src_path)
	bat_content = []
	if f:
		print('pdoscmds.bat opened...')
		for line in f:
			bat_content.append(line)	
	f.close()
	print('---------------------------------------------')
	print('pdoscmds.bat content:')
	print(bat_content)
	print('---------------------------------------------')
	bat_string = ''
	for line in bat_content:
		bat_string = bat_string + line
	return bat_string # return list with content


###########################################
# Convert number to 4 digit format

def num4digit(num):

	ns = ''
	if num < 1:
		ns = '0000'
	elif num < 10:
		ns = '000' + str(num)
	elif num < 100:
		ns = '00' + str(num)
	elif num < 1000:
		ns = '0' + str(num)
	elif num < 10000:
		ns = str(num)

	return ns	

def num2digit(num):
	n = ''
	if num < 1:
		n = '00'
	elif num < 10:
		n = '0' + str(num)
	else:
		n = str(num)
	
	return n
		

###########################################
# Convert command lines to file names missing

def cmd2file( glider_id, txt):
	print('Converting command to file name...')
	cmd2list = txt.split('\n') # if more than one line split each and store as list
	#print('cmd2list: ')
	#print(cmd2list)
	file_list = []
	for line in cmd2list:
		if len(line) > 2:
			linels = line.split() # split by space [resend_dive, /x, yyy]
			#print('line: ')
			#print(linels)
			diveN = num4digit( int(linels[2]) ) # return 4 digit number
			ftype = linels[1].replace('/','') # delete slash
			# get file extension
			ext = ''
			if ftype == 'd':
				ext = '.dat'
			if ftype == 'c':
				ext = '.cap'
			if ftype == 'l':
				ext = '.log'
			file = 'p' + glider_id.replace('sg','') + diveN + ext	 
			file_list.append(file)

	#print(file_list)
	return file_list


###########################################
# Convert cmd text to list

def cmd2list(txt):

	#print('Converting command to file name...')
	cmd2list = txt.split('\n') # if more than one line split each and store as list
	cmdls = []
	for cmd in cmd2list:
		if len(cmd) > 2:
			cmdls.append(cmd) # append command line only and filter out \n char
	
	return cmdls # list of commands  


###########################################
# Search for files that according to resend_dive command should be resent

def search_files( glider_id, files2search):
	src_path = '/home/jails/aoml/gliderjail/home/'+glider_id
	files_in_dir = os.listdir(src_path) # list containing all files in the directory including .dat .log .cap
	foundls = []
	for file in files2search: # for each file to search
		if file in files_in_dir: # if it's in the directory 1, else 0
			foundls.append(1)
		else:
			foundls.append(0)

	return foundls # list of files found [1] or not found [0]
			
###########################################
# List of dives to be resent

def get_last_dive(flist):
	
	lst = [] # list of dives to resend
	for f in flist:
		dive = f.split('.')[0]
		dive = int(dive[4:])
		lst.append(dive)
	lst.sort()
	#print('Dives to resend:')
	#print(lst)
	return lst[-1] # return last dive to return as integer


###########################################
# check whether to create a new .bat file w/commands or not

def get_final_cmd( glider_id, info_pair, last_cmd_dive):
	
	# --- Condition 1 --- search active pdoscmds.bat
	cond1 = False # first condition to create .bat
	if search_bat(glider_id): # check active pdoscmd.bat True/False
		print('BAT file active') # if active, check the content
		bat_string = check_bat_content(glider_id) #  .bat content
		# if content contains 'resend_dive' overwrite, otherwise (target or other command) don't
		if 'resend_dive' in bat_string:
			print('bat file can be overwritten')
			cond1 = True # if there's a resend_dive, is old or is the same .bat we want to create. No problem here
		else:
			print('do not overwrite bat file')
			save_log(glider_id,'Other command found in .bat')
			cond1 = False # remain false, we don't want to change it if it's another command
	else:
		print('No active BAT file')
		save_log(glider_id,'No active BAT file')
		# if there's no .bat file, no danger to write a new one
		cond1 = True
	
	# --- Condition 2 --- search existing files in directory
	# check if required files to be resent are already there. Search .dat .log and .cap
	# format ex. p6630298.log p6630298.dat p6630298.cap
	cmdls = cmd2list(info_pair[1]) # list of commands in same order as files2search
	files2search = cmd2file(glider_id,info_pair[1]) # list of files to search
	print('Files to search:')
	print(files2search)
	files_found = search_files(glider_id,files2search) # list of files found in order: 1 found, 0 not found ex. [1,0,0] for 3 files
	print('Found files binary [1 found, 0 not found]:') 
	print(files_found)	
	#print('Last dive to resend:')
	last2resend = get_last_dive(files2search) # greatest dive number to be resent
	print('Last dive to resend: ' + str(last2resend))
	# For each command check which one need to be sent according to files found
	n = 0
	filtered_cmds = ''
	for cmd in cmdls:
		if  files_found[n] == 0: # if corredponding file was not found, request resend, else don't
			filtered_cmds = filtered_cmds + cmd + '\n'
		else:
			print('File corresponding to ' + cmd + ' already exists' )
		n = n + 1
	
	# --- Condition 3 --- dive to be resent must be not more than dive_range dives older than last dive
	cond3 = False
	if ( (last_cmd_dive - last2resend) < dive_range ):	
		cond3 = True
		print('File to resend < ' + str(dive_range) + ' - OK, recent dive')
		
	else:
		print('File to resend > ' + str(dive_range) + ' - NOT OK, old dive')

	# -- FINAL DECISION
	final_cmd = ''
	if cond1 and cond3 and len(filtered_cmds)>2:
		final_cmd = filtered_cmds
	else:
		final_cmd = 'NO'	
	
	return final_cmd # return the command text to create .bat file or NO to not create the file 

###########################################
# Create pdoscmds.bat file in glider directory after passing the filters

def create_pdos(glider_id,cmd):
	
	dst_path = '/home/jails/aoml/gliderjail/home/' + glider_id + '/pdoscmds.bat'
	#dst_path = 'pdoscmds.bat' # test locally 
	fout = open(dst_path,'w')
	fout.write(cmd)
	fout.close()
	print('***********************************')
	save_log(glider_id,'**************************************')
	print('File created:' + dst_path)
	save_log(glider_id,'-> File created: ' + dst_path)
	print('Content:')
	save_log(glider_id,'Content:')
	print(cmd)
	save_log(glider_id,cmd)
	print('***********************************')
	save_log(glider_id,'**************************************')
	
###########################################
# Decide to delete the .bat only if all files already exist, and the content has a resend_dive
def decide_delete(glider_id):

		delete = False
		# check .bat active
		if search_bat(glider_id):
			print('Active pdoscmds.bat found')
			# read content
			bat_string = check_bat_content(glider_id)
			if 'resend_dive' in bat_string:
				print('File contains resend_dive')
				save_log(glider_id,'File content:')
				save_log(glider_id,bat_string)
				cmdls = cmd2list(bat_string) # .bat string content to list
				files2search = cmd2file(glider_id,bat_string) # list of files to search
				files_found = search_files(glider_id,files2search) # list of files found -> 1 found, 0 not found
				# if all files found, delete .bat
				print('Files to search:')
				print(files2search)
				print('Files found:')
				print(files_found)
			# check if ALL files were found
			all_found = True
			for bit in files_found:
				all_found = (all_found and bit) # do a A & B for every file. If one is 0, result is 0. If all 1, result is 1					
						# if all were found, then delete 
			if all_found == True:
				delete = True
				dst_path = '/home/jails/aoml/gliderjail/home/' + glider_id + '/pdoscmds.bat' # remove .bat
				os.remove(dst_path)
				print(dst_path + ' deleted')
		else:
			print('No active pdoscmds.bat found')
	
		return delete


###########################################
# save info to log file
def save_log(glider_id,text):

	#dst_path = '/home2/' + glider_id + '/auto_resend.log'
	dst_path = 'auto_resend_logs/'+ glider_id + '_auto_resend.log'
	flog = open(dst_path, 'a')
	flog.write(text + '\n')
	flog.close()

###########################################
# get current date and time as string
def date_time():

	now = datetime.datetime.now()
		
	return num2digit(now.month)+'-'+num2digit(now.day)+'-'+str(now.year)+'  '+num2digit(now.hour)+':'+num2digit(now.minute)+':'+num2digit(now.second)

###########################################
# Chekc current state of AUTO_RESEND file to determine if it's ON or OFF // be careful to not hit ENTER after writing 'ON'
def check_state(glider_id):
	
	dir_path = '/home/jails/aoml/gliderjail/home/' + glider_id
	file_list = os.listdir(dir_path) 
	file_path = dir_path + '/AUTO_RESEND'

	if 'AUTO_RESEND' in file_list:
		f = open(file_path)
		file_content = f.readline()
		f.close()
		#print(file_path, ' contains ', file_content)
	
		#if file_content == 'ON':
		if 'ON' in file_content:
			print('AUTO_RESEND is ON')
			return True
		else:
			print('AUTO_RESEND is OFF')
			return False
	else:
		return False
		


############################################################################################
# MAIN

def main():
	
	txt = ''
	count = 0
	for a in glider_list:
		txt = txt + a + ' - '
		count = count + 1
	print('STARTING ANALYSYS ON ' + txt)
	
	for glider_id in glider_list: 
		print('--------------------------------------------------------------------------------------------')
		print('Analyzing ' + glider_id)
		
		# Look for AUTO_RESEND status file
		switch_state = False # initialize for each glider
		switch_state = check_state(glider_id) # 
		
		# Check last call time
		
		not_in_call = False
		not_in_call = check_call_time(glider_id) # true if not in call, False if its in a call
		
		# Analyze if AUTO_RESEND exists and is ON, AND time_diff < 35 min
		if (switch_state == True and not_in_call == True) == True:
			print('AUTO_RESEND is ON and Time from last call > 35 min')
			save_log(glider_id,'--------------------------------------------------------------------------------------------')
			save_log(glider_id, date_time() + ' (utc) - ' + glider_id)
			print('////////////////////////////')
			print('\nOpening baselog file...\n')
			info_pair = process_baselog(glider_id) # returns last dive incomplete [0] and text command for .bat file [1]
			
			if info_pair[0] == -999:
				print("No incomplete dives were fond")
				save_log(glider_id,'--------------------------------------------------------------------------------------------')
				save_log(glider_id, date_time() + ' (utc) - ' + glider_id)
				save_log(glider_id,'No incomplete dives were found')

				pass
			else:
			
				inc_last_dive = info_pair[0] # last dive that needs to be resent as integer
				command = info_pair[1] # string of commands to create .bat file
				print('End of baselog process')
				print('////////////////////////////')
				print('\nSearching cmdfiles in dir...\n')
				cmdfile_last_dive = get_last_cmdfile(glider_id) # returns last dive found in glider directory cmdfile.xxx as integer. Use as real last dive 
				save_log(glider_id,'Last dive in directory: ' + str(cmdfile_last_dive))
				print('////////////////////////////')
	
				print('Deciding to create pdoscmds.bat...')
				final_cmd = get_final_cmd(glider_id,info_pair,cmdfile_last_dive) # returns the final command text to create .bat file. If 'NO', then don't create file.	
				print('final_cmd result: ' + final_cmd )
			
				if final_cmd != 'NO' and final_cmd != '':
					print('Creating pdoscomds.bat...')
					create_pdos(glider_id,final_cmd)
				else:
					print('Decided not to create pdoscmds with the following commands:')
					print(command)
					save_log(glider_id,'pdoscmds.bat not created')
		
				print('Deciding to delete pdoscmds.bat...')
				if decide_delete(glider_id):
					print('pdoscmds.bat deleted')
					save_log(glider_id,'-> File/s found in directory: pdoscmds.bat deleted')
				else:
					print('pdoscmds.bat not deleted')
					save_log(glider_id,'pdoscmds.bat not deleted')
				print('////////////////////////////')
		
		
				print(glider_id + ' - done')
				print('--------------------------------------------------------------------------------------------')
				save_log(glider_id,glider_id + ' - done')

		else:
			print(glider_id + ' Abort analysis --> AUTO_RESEND is OFF or time since call < ' + str(call_thd) + ' min')
			save_log(glider_id,'--------------------------------------------------------------------------------------------')
			save_log(glider_id, date_time() + ' (utc) - ' + glider_id)
			save_log(glider_id,'Abort analysis --> AUTO_RESEND is OFF or time since call < ' + str(call_thd) + ' min')
	
	print('ALL ' + str(count) + ' GLIDERS WERE ANALYZED')
	
	print('PROGRAM FINISHED')
	
############################################################################################
if __name__ == "__main__":
	main()
