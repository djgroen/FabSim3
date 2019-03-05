
# FabSim3 singularity container usage

In this document, we will explain how to download, setup, and run [FabSim3](https://github.com/djgroen/FabSim3) in a singularity container image


#### What you need:

-   Singularity, which you can download and install from [here](https://www.sylabs.io/guides/3.0/user-guide/installation.html).

### Pull the container from library:
```sh
$ singularity pull --name fabsim.img shub://arabnejad/singularity_test
```
- note that the download image should be kept as `fabsim.img`, this filename will be used later for setting environment variable and alias names in your `bashrc` file

### Setting the container
Now, you can run the following to download and setup

make sure you run these commands for the first time in the same directory as the `fabsim.img` file is downloaded.

The documentation for the container can be accessed by running
```sh
$ ./fabsim.img --help
```
Running the following will download the [FabSim3](https://github.com/djgroen/FabSim3) library in your local machine 
- you also can set the installation directory by setting  `[FabSim-install-dir]`, by default, it will be downloaded in sub-folder `FabSim3` in your current directory
```sh
$ ./fabsim.img -i  [FabSim-install-dir]
```
or
```sh
$ ./fabsim.img --install [FabSim-install-dir]
```
at the end of installation part, you will received this message, which explain how you should setup your PC for further usage

- `fabsim_INSTALL_DIR` will be replaced by your local machine path
```sh
please add/load the generated fabsim_env.conf in your ~/.bashrc

	To load: 
			$ source \${fabsim_INSTALL_DIR}/fabsim_env.conf

	To add to your ~/.bashrc
			$ echo \"source \${fabsim_INSTALL_DIR}/fabsim_env.conf\" >> ~/.bashrc
			$ source ~/.bashrc
```
 
### Running the container
Now, you can execute FabSim3 by just following this pattern
```sh
$ fab <commands>
```