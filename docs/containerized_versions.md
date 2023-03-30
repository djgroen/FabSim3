

### Singularity Usage

In this tutorial, we will explain how to download, setup, and run [FabSim3](https://github.com/djgroen/FabSim3) within a singularity container image.

#### Dependencies
* [Singularity](https://www.sylabs.io/), which you can download and install from [here](https://www.sylabs.io/guides/3.0/user-guide/installation.html).
* [OpenSSH Server](https://www.openssh.com/).

Installation under Ubuntu Linux:
```sh
sudo apt install openssh-server
```
Installations under CentOS Linux:
```sh
sudo yum install -y openssh-server
```

#### FabSim3 Singularity Installation
Download the singularity image from [Singularity Hub](https://singularity-hub.org/):
```sh
singularity pull --name fabsim.simg shub://arabnejad/FabSim3
```
!!! tip
	The download image should be kept as `fabsim.simg`, this filename will be used later for setting environment variables and alias names in your `~/.bashrc` file.

* To see How to Use Fabsim3 singularity:
```sh
./fabsim.simg --help
or
./fabsim.simg -h
```

* Running the following will download the FabSim3 library in your local machine:
```sh
./fabsim.simg --install [fabsim_INSTALL_DIR]
or
./fabsim.simg -i [fabsim_INSTALL_DIR]
```

	By default, it will be downloaded in sub-folder `FabSim3` in your current directory, you also can set the installation directory by setting `[fabsim_INSTALL_DIR]` parameter.

	At the end of installation part, you will receive a message, which explains how you should setup your PC for further usage.

	Please add/load the generated `fabsim_env.conf` in your `~/.bashrc`.

* To load:
```sh
source \${fabsim_INSTALL_DIR}/fabsim_env.conf
```

* To add to your `~/.bashrc`:
```sh
echo \"source \${fabsim_INSTALL_DIR}/fabsim_env.conf\" >> ~/.bashrc
source ~/.bashrc
```
	`fabsim_INSTALL_DIR` will be replaced by your local machine path.

After loading the environment variable from `fabsim_env.conf` into your current shell script, `fab` command will be available as a alias name to run for singularity image and accept all FabSim3 commands.	

##### For QCG users

* Please make sure, you update/replace username: `#!yaml "plg<your-username>"` with your username account in `{fabsim_INSTALL_DIR}/deploy/machines_user.yml`.
* Sets up SSH key pairs for FabSim3 access:
```sh
fab qcg setup_ssh_keys
```
* Please create a **globus** in your `$HOME` directory, If Not Exist:
```sh
mkdir -p ~/.globus
```
* Copy `usercert.pem` and `userkey.pem` from your account to `~/.globus`:
```sh
scp plg<user>@eagle.man.poznan.pl:~/.globus/usercert.pem ~/.globus
scp plg<user>@eagle.man.poznan.pl:~/.globus/userkey.pem ~/.globus
```

### FabSim3 with QCG middleware

To execute jobs through remote resource schedulers, some **essential** machine-specific configurations are required to be set and stored. These parameters will be applied to all applications run on that remote machine.

First, you need to add your username for the remote machine in `FabSim3/fabsim/deploy/machines_user.yml` file as:
```yaml
qcg: # machine name
     username: "plg..."
```
Then, set up configuration for remote machine in `FabSim3/fabsim/deploy/machines.yml` file. Here is a simple example:
```yaml
qcg: # machine name
     remote: 'eagle.man.poznan.pl'
     home_path_template: '/home/plgrid/$username'
     manual_ssh: true
     dispatch_jobs_on_localhost: true
     job_dispatch : 'qcg-sub'
     batch_header: qcg-eagle
     stat: 'qcg-list -Q -s all -F "%-22I %-16S %-8H" | awk "{if(NR>2)print}"'
     job_dispatch: 'qcg-sub'
     cancel_job_command: 'qcg-cancel $jobID'
     job_info_command : 'qcg-info -Q $jobID'
```

* `qcg`: the name of target remote machine, it will use by FabSim3 as `fab qcg <command>`. Internally, FabSim3 uses `<$user_name>@<$remote>` to connect to the remote machine.
* `remote`: the remote machine address. FabSim3 uses `<$user_name>@<$remote>` template internally for all connections. The user_name parameter is taken from `FabSim3/fabsim/deploy/machines.yml` file.
* `home_path_template`: used to the storage space to checkout and build on the remote machine.
* `manual_ssh`: when enabled, FabSim3 will connect directly using an ssh client instead of using the paramiko api.
* `dispatch_jobs_on_localhost`: if it is set to `true`, job dispatch is done locally. Otherwise, FabSim3 executes commands directly inside the remote machine by **ssh** connection. To dispatch a job locally, the command-line interface for job management should be installed in your local machine.
* `batch_header`: it can be used to add some predefined templates to the submitted job script. The template file should be stored at `FabSim3/fabsim/deploy/templates`.
* `stat`: filled by the command line that displays report on the submitted jobs. In this example, according to our grid broker, `qcg-list` command displays a table with information about tasks.
