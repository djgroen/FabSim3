#!/bin/bash


# set variables
SOURCE='source'
TARGET='client'
SVN_URL='https://apps.man.poznan.pl/svn/qcg-broker/branches/compat'
SVN_USER='piontek'
SVN_PASSWD='piontek'


command_not_found_handle()
{
  if  [ -x /usr/lib/command-not-found ]; then
     /usr/lib/command-not-found -- "$1" 
     return $?
  else
     return 127
  fi	    
}


# check Java Version
JAVA_VERSION=$(java -version 2>&1 >/dev/null | grep 'java version' | awk '{print $3}')
if [ -z "$JAVA_VERSION" ]
then
      printf "\n\t\tInstall Oracle Java 8\n\n"
      printf "Step 1 : Run below commands to install Java 8 on Ubuntu and LinuxMint\n\n"
      printf "\t sudo add-apt-repository ppa:webupd8team/java \n"
      printf "\t sudo apt-get update \n"
      printf "\t sudo apt-get install oracle-java8-installer \n\n"
      printf "Step 2 – Verify Java Inatallation\n\n"
      printf "\t sudo apt-get install oracle-java8-set-default \n\n"
      printf "Step 3 – Configures the default for java and javac (Java compiler) to java-8-oracle\n\n"
      printf "\t sudo update-alternatives --config java \n"
      printf "\t sudo update-alternatives --config javac \n\n"

      exit 1
fi


# check if the required packages is installed or not
CHECKED_PACKAGES=("svn" "ant")
for CMD in "${CHECKED_PACKAGES[@]}"
do
	command  -v $CMD >/dev/null 2>&1
	if [ $? -ne 0 ]; then
		#echo "Package svn is NOT installed !!!"
		command_not_found_handle $CMD
		exit 1	 	
	fi
done






# download, build, deploy
svn co --username $SVN_USER --password $SVN_PASSWD --non-interactive $SVN_URL source

ant -f source/build.xml cleanall
ant -f source/build.xml client-rebuild
rm -r -f qcg-client
ant -f source/build.xml -Ddeploy.dir=`pwd`/qcg-client deploy-client-single-dir


# Replace qcg-broker-client.conf with new ENV parameters
cat > ./qcg-client/etc/qcg-broker-client.conf << EOF
export QCG_URL_DEFAULT="httpg://broker.plgrid.qcg.psnc.pl:8443/qcg/services/"
export QCG_DN_DEFAULT="/C=PL/O=GRID/O=PSNC/CN=qcg-broker/broker.plgrid.qcg.psnc.pl"

export QCG_CLIENT_LOCATION_DEFAULT=`pwd`/qcg-client/
export GFTP_HOSTNAME=eagle.man.poznan.pl # qcg-client.man.poznan.pl
export GFTP_PORT=2811

export GLOBUS_TCP_PORT_RANGE=20000,21000
export QCG_PROXY_DURATION_DEFAULT=600
export QCG_PROXY_DURATION_MIN=480
export QCG_CONNECT_TIMEOUT=60

export QCG_CERTIFICATES=/etc/grid-security/certificates

export QCG_JOB_FORMAT="%-22I  %-15T  %-15E  %-16S  %-20D";
export QCG_USER_JOB_FORMAT="%-22I  %-15T  %-15E  %-16S  %-20D  %-18U";
export QCG_TASK_FORMAT="%-22I  %-20N  %-15T  %-15X  %-15E  %-16S  %-8H  %-7F  %-20D";
export QCG_USER_TASK_FORMAT="%-22I  %-20N  %-15T  %-15X  %-15E  %-16S  %-8H  %-5F  %-20D  %-18U";
export QCG_RESERVATION_FORMAT="%-22I  %-20N  %-15T  %-15X  %-15E  %-16S  %-8H  %-5C  %-20D";
export QCG_USER_RESERVATION_FORMAT="%-22I  %-20N  %-15T  %-15X  %-15E  %-16S  %-8H  %-5C  %-20D %-18U";
export QCG_LIST_TIME_FORMAT="dd.MM.yy HH:mm"
export QCG_ENV_RES_QUEUE_FORMAT="%-15N  %-10J  %-10R  %-10W  %-15T  %-10E  %-10S";
export QCG_ENV_RES_APPLICATION_FORMAT="%-20A  %-70H";
export QCG_ENV_RES_MODULE_FORMAT="%-50M  %-60H";
export QCG_ENV_RES_USER_FORMAT="%-15A  %-70V %-60H";
export QCG_ENV_RES_SUMMARY_FORMAT="%-10H  %-5N  %-5T %-12P %-10F %-10D  %-5A  %-7M  %-5U  %-5J  %-5W %-5B  %-6Q  %-6R  %-5V";
export QCG_ENV_RES_TYPE_FORMAT="%-15T  %-30A";
EOF


# add qcg-client command into $PATH
if [[ -z "$(grep "qcg-client/bin" ~/.bashrc)" ]]
then
  echo "export PATH=$PATH:`pwd`/qcg-client/bin/" >> ~/.bashrc
  source ~/.bashrc
fi


# set cog.properties file
rm -r -f $HOME/.globus
mkdir -p $HOME/.globus
cat > $HOME/.globus/cog.properties << EOF
usercert=$HOME/.globus/usercert.pem
userkey=$HOME/.globus/userkey.pem
EOF

printf "Next steps : \n"
printf "\n\t\t Step1 : run\t\t source ~/.bashrc \t\t to load qcg-client command\n"
printf "\n\t\t Step2 : copy usercred.p12, userkey.pem, and usercert.pem from ~/.globus @ man.poznan.pl into your local machine\n\n"


