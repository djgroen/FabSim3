
# FabSim3 Docker : How to use
In this document, we will explain how to download, setup, and run [FabSim3](https://github.com/djgroen/FabSim3) within a Docker  image

## Dependencies
#### What you need:
- [Docker](https://www.docker.com), which you can download and install from [here](https://docs.docker.com/install/).
- [GitHub](https://github.com/)

## Installation
1. Download the Docker image from [Docker Hub](https://hub.docker.com/)
	> `docker pull vecmafabsim3/fabsimdocker`
	> <br/>you can check if the docker image is downloaded and listed as the available image in your system by `docker images fabsim`

2. Download the FabSim3 GitHub repository 
	> `git clone https://github.com/djgroen/FabSim3.git`

3. Create `machines_user.yml` in the `deploy/` subdirectory,  and fill it by
	> `File : /deploy/machines_user.yml`
	> ``` yaml
	> default:
	>     local_results: "/FabSim3/results"
	>     local_configs: "/FabSim3/config_files"
	>     username: "root"
	> ```

4. For [QCG](http://www.qoscosgrid.org/trac/qcg) users, 
	-  create a `globus` where you download the FabSim3 repo, If Not Exist : `mkdir -p ./.globus` 
	- copy `usercert.pem` and `userkey.pem` from your account to `./.globus`
		> `scp plg<your-username>@eagle.man.poznan.pl:~/.globus/usercert.pem ./.globus`<br/>
		> `scp plg<your-username>@eagle.man.poznan.pl:~/.globus/userkey.pem ./.globus`
	- update `machines_user.yml` in the `deploy/` subdirectory, with
		> `File : /deploy/machines_user.yml`
		> ``` yaml
		> qcg: # remote machine name 
		>     username: "plg<your-username>"
		>     local_results: "/FabSim3/results"
		>     local_configs: "/FabSim3/config_files"
		> ```
			
## FabSim3 Docker Usage
- run  `chmod +x FabSim_Docker_run.sh` and you will be logged in to the docker image
