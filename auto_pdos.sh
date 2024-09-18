#!/usr/bin/env bash

echo "-----------------------"
echo "Starting auto_pdos"

# ------- EDIT BY USER SECTION -----------------------------------------------------------------------
# Select Seagliders to copy baselog. Make sure the same gliders are in the auto_resend2.py script
declare -a sg_list=("sg664" "sg665" "sg666" "sg683" "sg684")

# Home directory where sgXXX dirs are located
sgHomeDir='/home/jails/aoml/gliderjail/home'
# -----------------------------------------------------------------------------------------------------

# ------ WARNING - DO NOT CHANGE FROM HERE ---------------------------------------------------------------------
# Create directory to store baselog copies if it doesn't exist yet
new_dir=$(pwd)/baselog_copies
new_dir2=$(pwd)/auto_resend_logs
new_dir3=$(pwd)/commlog_copies
mkdir -p $new_dir
mkdir -p $new_dir2
mkdir -p $new_dir3

# Copy baselog from each sgxxx folder
for i in ${sg_list[@]}
do
	# copy only if different with -u update
	cp -u $sgHomeDir/$i/baselog.log $new_dir/$i.log
	echo "Baselog from $sgHomeDir/$i updated to $new_dir"
done

echo "Done updating baselogs"
echo "-----------------------"

for i in ${sg_list[@]}
do
        # copy only if different with -u update
        cp -u $sgHomeDir/$i/comm.log $new_dir3/$i.log
        echo "comm.log from $sgHomeDir/$i updated to $new_dir3"
done

echo "Done updating Commlogs"
echo "-----------------------"

echo ""
echo "Executing python script..."
echo ""

# export list to shell environment for use in python script
export ids="${sg_list[@]}"

# After copying baselog, execute python script
# NOTE: Comment the following commands to stop auto_resend script
echo "executing $HOME/autoPDOS/auto_resend7.1.py"
python3 $(pwd)/auto_resend7.2.py





