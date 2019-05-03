

# FabSim3 singularity : How to use
In this document, we will explain how to download, setup, and run [FabSim3](https://github.com/djgroen/FabSim3) within a singularity container image

## Dependencies
#### What you need:
- [Singularity](https://www.sylabs.io), which you can download and install from [here](https://www.sylabs.io/guides/3.0/user-guide/installation.html).
- [OpenSSH Server](https://www.openssh.com/) : 
	- Installation under Ubuntu Linux
       > `sudo apt install openssh-server`
	- Installations under CentOS Linux
      > ``sudo yum install -y openssh-server``

## Installation
1. Download the singularity image from [Singularity Hub](https://singularity-hub.org/)
	> `singularity pull --name fabsim.simg shub://arabnejad/FabSim3`
	> <br/><br/>note that the download image should be kept as `fabsim.simg`, this filename will be used later for setting environment variable and alias names in your `bashrc` file

2.  To see How to use fabsim singularity
	> 	`./fabsim.simg --help` <br/> OR <br/> `./fabsim.simg -h`

3. Running the following will download the [FabSim3](https://github.com/djgroen/FabSim3) library in your local machine
	> `./fabsim.simg --install [fabsim_INSTALL_DIR]`<br/>
	OR <br/>
	`./fabsim.simg -i [fabsim_INSTALL_DIR]`
	<br/>by default, it will be downloaded in sub-folder `FabSim3` in your current directory, you also can set the installation directory by setting `[fabsim_INSTALL_DIR]` parameter<br/>

4. At the end of installation part, you will received a message, which explain how you should setup your PC for further usage
	> `./fabsim.simg -i [fabsim_INSTALL_DIR]`
	> ``` sh
	> please add/load the generated fabsim_env.conf in your ~/.bashrc
	>      To load:
	>          $ source \${fabsim_INSTALL_DIR}/fabsim_env.conf 
	>      To add to your ~/.bashrc
	>          $ echo \"source \${fabsim_INSTALL_DIR}/fabsim_env.conf\" >> ~/.bashrc 	
	>          $ source ~/.bashrc 	
	> ```
	> `fabsim_INSTALL_DIR` will be replaced by your local machine path

5. After, loading the environment variable from `fabsim_env.conf` into your into the current shell script, `fab` command will be available as a alias name to run for singularity image and accept all FabSim3 command.

6. For [QCG](http://www.qoscosgrid.org/trac/qcg) users, 
	- please create a `globus` in your `$HOME` directory, If Not Exist : `mkdir -p ~/.globus`
	- copy `usercert.pem` and `userkey.pem` from your account to `~/.globus`
		> `scp plg<user>@eagle.man.poznan.pl:~/.globus/usercert.pem ~/.globus`<br/>
		> `scp plg<user>@eagle.man.poznan.pl:~/.globus/userkey.pem ~/.globus`
	- please make sure, you udpate/replace `username: "plg<your-username>"` with your username account in `{fabsim_INSTALL_DIR}/deploy/machines_user.yml`
		
## FabSim3 Usage
- To enable use of FabSim3 on your local host, type `fab localhost setup_fabsim`
- and, then you can use all FabSim3 commands as it mentioned in GitHub page :)
