
# bootstraping from docker image is faster and includes more dependencies
Bootstrap: docker
#From: ubuntu:latest
From: python:latest


%help
	for container help:
	$ ./<singularity_file_name> --help



#%environment
#	fabsim_repo=https://github.com/djgroen/FabSim3.git

	
%post
	echo 'export fabsim_repo=https://github.com/djgroen/FabSim3.git' >> $SINGULARITY_ENVIRONMENT

	# set default python version to 3
	rm /usr/bin/python
	ln -s /usr/bin/python3 /usr/bin/python

	# Update to the latest pip (newer than repo)
	pip install --upgrade pip

	# install dependencies
	pip install fabric3 \
				pyyaml \
				pytest \
				pytest-pep8 \
				numpy

	#-- our help files will be stored here
	mkdir /fabsim_container_files

#-----------------------------------------------------------------
#
#				make the help file
#				------------------
#
cat << EOF_HELP > /fabsim_container_files/runscript.help

How to use FabSim3 singularity image :)

USAGE:
	./<singularity_file_name> [option]

OPTIONS:
	--help, --run-help : print container help


EOF_HELP
#-----------------------------------------------------------------
#
#				 make the fabsim_env file
#				--------------------------
#
cat << EOF_FabSim_ENV > /fabsim_container_files/fabsim_env.conf
#export PYTHONPATH=\${fabsim_INSTALL_DIR}:\$PYTHONPATH
export fabsim_INSTALL_DIR=\${fabsim_INSTALL_DIR}
alias fab="\$PWD/fabsim.img"
EOF_FabSim_ENV
#-----------------------------------------------------------------
#
#				make the setup_fabsim_env file	
#				------------------------------
#
cat << EOF_setup_fabsim_env > /fabsim_container_files/setup_fabsim_env

please add/load the generated fabsim_env.conf in your ~/.bashrc

	To load: 
			$ source \${fabsim_INSTALL_DIR}/fabsim_env.conf

	To add to your ~/.bashrc
			$ echo \"source \${fabsim_INSTALL_DIR}/fabsim_env.conf\" >> ~/.bashrc
			$ source ~/.bashrc


EOF_setup_fabsim_env

#-----------------------------------------------------------------
#				
#				make the fabsim_env_warning file	
#				--------------------------------
#
cat << EOF_fabsim_env_warning > /fabsim_container_files/fabsim_env_warning

environment variable \$fabsim_INSTALL_DIR is empty !!!

Please make sure you install fabsim by
		./<singularity_file_name> -i [install directory PATH]
		or
		./<singularity_file_name> --install [install directory PATH]

if you did the previous step, please add/load the generated fabsim_env.conf in your ~/.bashrc
	
	To load: 
			$ source <fabsim_INSTALL_DIR>/fabsim_env.conf

	To add to your ~/.bashrc
			$ echo "source <fabsim_INSTALL_DIR>/fabsim_env.conf" >> ~/.bashrc
			$ source ~/.bashrc

	In both cases, <fabsim_INSTALL_DIR> should be replaced by your local fabsim installation directory
EOF_fabsim_env_warning

#-----------------------------------------------------------------


# The difference between exec and run is that exec runs the command you write directly but run passes whatever you write to the script you've written in %runscript
%runscript
	
	if [ -z "$1" ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
	    cat /fabsim_container_files/runscript.help
	    return 0
	fi

	if [ "$1" = "-i" ] || [ "$1" = "--install" ]; then
		echo "Installing FabSim3 . . ."

		if [ -z "$2" ]; then
			fabsim_INSTALL_DIR=$PWD	
		else
			fabsim_INSTALL_DIR="$2"
		fi

		fabsim_INSTALL_DIR=${fabsim_INSTALL_DIR}/FabSim3
		echo "fabsim_INSTALL_DIR = "$fabsim_INSTALL_DIR

		
		#-- clone FabSim3 github repository
		mkdir -p ${fabsim_INSTALL_DIR}
		git clone ${fabsim_repo} ${fabsim_INSTALL_DIR}
		
		#-- generate machines_user.yml file
		if [ ! -f ${fabsim_INSTALL_DIR}/deploy/machines_user.yml ]; then
			cp ${fabsim_INSTALL_DIR}/deploy/machines_user_example.yml ${fabsim_INSTALL_DIR}/deploy/machines_user.yml
			sed -i "s/your-username/`whoami`/g;s#~/Codes/FabSim#${fabsim_INSTALL_DIR}#g"  ${fabsim_INSTALL_DIR}/deploy/machines_user.yml
		fi


		#-- setup fabsim localhost		
		old_PATH="$PWD"
		cd ${fabsim_INSTALL_DIR}
		fab localhost setup_fabsim
		cd "$old_PATH"

		#-- create fabsim_env file to be added inside ~/.bashrc
		echo  "$(eval "echo  \"$(cat /fabsim_container_files/fabsim_env.conf)\"")" > ${fabsim_INSTALL_DIR}/fabsim_env.conf

		echo  "$(eval "echo  \"$(cat /fabsim_container_files/setup_fabsim_env)\"")"
	
	    return 0
	fi 

	if [ -z "$fabsim_INSTALL_DIR" ]; then
		cat /fabsim_container_files/fabsim_env_warning
		return 0
	fi

	old_PATH="$PWD"
	cd "$fabsim_INSTALL_DIR"
	echo "RUNNING : fab " "$@"
	echo ""
	fab "$@"
	cd "$old_PATH"

