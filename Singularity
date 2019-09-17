Bootstrap: docker
From: ubuntu:latest


%labels
	MAINTAINER hamid.arabnejad@gmail.com


%help
	This Singularity container makes your life easier by installing	all the necessary required packages for fabsim3 program.
	See https://github.com/djgroen/FabSim3.git for more information

	How it works !!!, just run :)
		./fabsim.simg --help
		OR
		./fabsim.simg -h
	

%post
	echo "export fabsim_repo=https://github.com/djgroen/FabSim3.git" >> $SINGULARITY_ENVIRONMENT

	# Installing required packages
	apt-get update
	apt-get install -y --no-install-recommends openjdk-8-jdk git ant subversion wget gnupg python3-pip python3-dev openssh-server rsync
	apt-get purge -y openjdk-11*

	# Installing EGI certificates	
	wget -q -O - https://dist.eugridpma.info/distribution/igtf/current/GPG-KEY-EUGridPMA-RPM-3 | apt-key add -
    echo "#### EGI Trust Anchor Distribution ####" >> /etc/apt/sources.list && \
    echo "deb http://repository.egi.eu/sw/production/cas/1/current egi-igtf core" >> /etc/apt/sources.list
    apt-get update
    apt-get install -y ca-policy-egi-core
	
	# setting up python and installing packages
	cd /usr/local/bin
	ln -s /usr/bin/python3 python
    pip3 install --upgrade pip
    pip install -U pip setuptools
    pip install pyyaml numpy fabric3 cryptography==2.4.2
    pip install easyvvuq muscle3


    # clean up    
    rm -rf /var/lib/apt/lists/*
	


	# Installing QCG client
	SVN=https://apps.man.poznan.pl/svn/qcg-broker/branches/vecma/
	SVN_USER=piontek
	SVN_PASSWD=piontek		
	mkdir -p /QCG-client
	svn co --username ${SVN_USER} --password ${SVN_PASSWD} --non-interactive ${SVN} /QCG-client/source
	ant -f /QCG-client/source/build.xml client-rebuild
	rm -r -f /QCG-client/build
	ant -f /QCG-client/source/build.xml -Ddeploy.dir=/QCG-client/build deploy-client-single-dir
	rm -r -f /QCG-client/source

	#	To save help files
	mkdir /fabsim_container_files

	
	#-----------------------------------------------------------------
	#					runscript.help
	#
	cat << EOF_HELP > /fabsim_container_files/runscript.help

	How to use FabSim3 singularity image :)

	USAGE:
		./fabsim.simg [option]

	OPTIONS:
		-h|--help				print container help
		-i|--install [PATH]     install fabsim3 in in your local machine
					by default, it will be downloaded in sub-folder ./FabSim3 in your current directory
					you also can set the installation directory by setting PATH parameter

EOF_HELP

	#-----------------------------------------------------------------
	#				 fabsim_env.conf
	#
	cat << EOF_FabSim_ENV > /fabsim_container_files/fabsim_env.conf
	
	#export PYTHONPATH=\${fabsim_INSTALL_DIR}:\$PYTHONPATH
	export fabsim_INSTALL_DIR=\${fabsim_INSTALL_DIR}
	alias fab="\$PWD/fabsim.simg"

EOF_FabSim_ENV

	#-----------------------------------------------------------------
	#				make the setup_fabsim_env file	
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
	#				fabsim_env_warning	
	#
	cat << EOF_fabsim_env_warning > /fabsim_container_files/fabsim_env_warning

	environment variable \$fabsim_INSTALL_DIR is empty !!!

	1)	Please make sure you install fabsim by
			$ ./fabsim.simg -i [preferred install directory]
			or
			$ ./fabsim.simg --install [preferred install directory]

	OR

	2)	if you did the previous step, 
		please go <fabsim_INSTALL_DIR> and add/load the generated fabsim_env.conf in your ~/.bashrc
		
		To load: 
				$ source <fabsim_INSTALL_DIR>/fabsim_env.conf

		To add to your ~/.bashrc
				$ echo "source <fabsim_INSTALL_DIR>/fabsim_env.conf" >> ~/.bashrc
				$ source ~/.bashrc

	NOTE:	In all cases, <fabsim_INSTALL_DIR> should be replaced 
		by your local fabsim installation directory

EOF_fabsim_env_warning


%environment
    export QCG_ENV_CONFIGURATION_FILE=/QCG-client/build/etc/qcg-broker-client.conf
    export QCG_ENV_CLIENT_LOCATION_DEFAULT=/QCG-client/build
    export PATH=/QCG-client/build/bin/:${PATH}

    export QCG_ENV_URL=httpg://broker.plgrid.qcg.psnc.pl:8443/qcg/services/
    export QCG_ENV_DN=/C=PL/O=GRID/O=PSNC/CN=qcg-broker/broker.plgrid.qcg.psnc.pl
    export QCG_ENV_CERTIFICATES=/etc/grid-security/certificates
    export QCG_ENV_GFTP_HOSTNAME=eagle.man.poznan.pl  

%runscript

	#-----------------------------------------------------------------
	#				$ ./fabsim.simg
	#				$ ./fabsim.simg -h	
	#				$ ./fabsim.simg --help
	#
	if [ -z "$1" ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
	    cat /fabsim_container_files/runscript.help
	    return 0
	fi

	#-----------------------------------------------------------------
	#				$ ./fabsim.simg -i [PATH]
	#				$ ./fabsim.simg --install [PATH]
	#
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

		id
		
		#-- create fabsim_env file to be added inside ~/.bashrc
		echo  "$(eval "echo  \"$(cat /fabsim_container_files/fabsim_env.conf)\"")" > ${fabsim_INSTALL_DIR}/fabsim_env.conf

		echo  "$(eval "echo  \"$(cat /fabsim_container_files/setup_fabsim_env)\"")"
	
	    return 0
	fi 

	#-----------------------------------------------------------------
	#				check if FabSim is installed or NOT 
	#				before executing any additional command
	#				$ ./fabsim.simg ...
	
	echo "args :" "$@" 
	echo "fabsim_INSTALL_DIR -> " $fabsim_INSTALL_DIR
	if [ -z "$fabsim_INSTALL_DIR" ]; then
		cat /fabsim_container_files/fabsim_env_warning
		return 0
	fi


	old_PATH="$PWD"
	cd $fabsim_INSTALL_DIR
	pwd
	echo "RUNNING : fab " "$@"
	echo ""
	fab "$@"
	cd "$old_PATH"
