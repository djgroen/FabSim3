# Installing WSL on Windows

## What is Windows Subsystem for Linux (WSL)?

**Windows Subsystem for Linux (WSL)** allows you to run a full Linux environment on Windows, enabling access to native Linux tools and utilities. It is a powerful tool for developers working on Unix-based systems who prefer to use Windows as their main operating system. With WSL, a lightweight virtual machine runs a Linux kernel, providing access to many Windows/Linux applications.

WSL is especially useful for running tools like **FabSim3**, which are designed for Unix-based systems. By installing WSL and a Linux distribution (like Ubuntu), you can run FabSim3 on your Windows machine as though you were working on a native Linux system.

## Installing WSL Using a BAT Script

To simplify the installation of WSL and Ubuntu, you can either download or copy the script below.

### Option 1: Clone GitHub Repository 

You can clone an automated script for WSL installation from [FabSim3_Jupyter](https://github.com/mzrghorbani/FabSim3_Jupyter.git). Once the repository is clonned, right-click on the `install_wsl.bat` script and **Run As Administrator**. Also, you can open a Powershell termial on Windows as administrator, go to directory where script is downloaded and run the script by tryping `.\install_wsl.bat`.

1. Press Windows Key + X and select Terminal for Windows PowerShell or Command Prompt.

2. Navigate to the Directory Where You Want to Clone the Repository:

```bash
cd C:\Users\YourUsername\Documents
```

3. Clone the GitHub Repository:

```bash
git clone https://github.com/mzrghorbani/FabSim3_Jupyter.git
```

4. Open Repository in Windows Explorer:

```bash
explorer.exe FabSim3_Jupyter
```

This will open Windows Explorer with the content of the repository. Righ_click on `install_wsl.bat` and **Run as Administrator**.

If you encountered any issues with `git : The term 'git' is not recognized`, please install git from here: https://git-scm.com/downloads/win

### Option 2: Copy the BAT Script

You can also copy and paste the following BAT script content into a file and run it as administrator. 

<span style="color: red;">**Note**</span>: Windows Defender may block the execution of `.bat` scripts as a security precaution. If you receive a security alert, review the details and choose to allow the script to run by selecting the appropriate option. Be sure that the script is from trusted source and safe before proceeding.

<span style="color: red;">**Important**</span>: Restarting is necessary to complete the WSL installation. It ensures that changes made during the installation are correctly applied. After the first restart, when you run the script again, you can safely answer **no** when prompted to restart. This allows the script to continue running the remaining steps without requiring another reboot.


```batch
@echo OFF

REM Configuring Windows 11 for Windows Subsystem for Linux (WSL)
echo Setup of Windows Subsystem for Linux (WSL) and installing a Linux distro.
echo If there is any problems during the automation, please execute the commands manually.

@echo off
REM Check for administrative privileges
echo Checking for administrative permissions...

NET SESSION >nul 2>&1
if %errorlevel% NEQ 0 (
    echo.
    echo You need to run this script as an administrator.
    echo Press Ctrl + C to exit and then right-click the script to 'Run as administrator'.
    pause >nul
    exit /b
)

echo Administrative permissions confirmed.

REM Detect if running on a 64-bit machine
if "%PROCESSOR_ARCHITECTURE%" == "AMD64" (
    echo Supported processor architecture.
) else if "%PROCESSOR_ARCHITEW6432%" == "AMD64" (
    echo Supported processor architecture.
) else (
    echo Unsupported processor architecture. WSL requires a 64-bit machine.
    pause >nul
    exit /b
)

REM Check if ARM64 architecture
echo Checking ARM64 architecture...
wmic cpu get Caption, Architecture | findstr /i "ARM64" > NUL
if errorlevel 1 (
    echo This is an x64-bit operating system running on a %PROCESSOR_ARCHITECTURE% processor.
) else (
    echo This is an ARM64 operating system running on a %PROCESSOR_ARCHITECTURE% processor.
)

REM Check if WSL is already enabled
echo Checking if WSL is already enabled...
powershell.exe -Command "Get-WindowsOptionalFeature -Online -FeatureName 'Microsoft-Windows-Subsystem-Linux' | Select-Object -ExpandProperty State" | find /i "enabled" >nul
if errorlevel 1 (
    REM Enable Windows Subsystem for Linux
    echo Enabling Windows Subsystem for Linux...
    powershell.exe -Command "Enable-WindowsOptionalFeature -Online -FeatureName 'Microsoft-Windows-Subsystem-Linux' -All -NoRestart"
) else (
    echo WSL is already enabled. Skipping the enabling process.
)

REM Check if Virtual Machine Platform is already enabled
echo Checking if Virtual Machine Platform is already enabled...
powershell.exe -Command "Get-WindowsOptionalFeature -Online -FeatureName 'VirtualMachinePlatform' | Select-Object -ExpandProperty State" | find /i "enabled" >nul
if errorlevel 1 (
    echo Enabling Virtual Machine Platform...
    powershell.exe -Command "Enable-WindowsOptionalFeature -Online -FeatureName 'VirtualMachinePlatform' -All -NoRestart"
) else (
    echo Virtual Machine Platform is already enabled. Skipping the enabling process.
)

REM Check if the BIOS manufacturer matches a virtual machine
echo If your machine is a Virtual Machine, enable Virtualisation by:
echo Turning on Hyper-V on Host Machine (e.g., Windows 11)
echo Open Settings on Windows 11.
echo Click on Apps.
echo Click the Optional features tab.
echo Under the “Related settings” section, click the “More Windows features” setting.
echo Check the Hyper-V option to enable the virtual machine platform on Windows 11.
echo Click the OK button.
echo Restart the host.

REM Prompt the user for restart confirmation
set /p restart=Do you want to restart your machine? (y/n): 
if /i "%restart%"=="y" (
    echo Restarting your machine...
    shutdown /r /t 0
    exit /b
) else (
    echo Skipping the restart process. You can manually restart your machine later.
    echo Continuing with the installation...
    timeout 2 >nul
)

REM Download and install the WSL Linux kernel package

REM Define the kernel package URLs for different architectures
set "x64_kernel_url=https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
set "arm64_kernel_url=https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_arm64.msi"

REM Choose the appropriate kernel URL based on the processor architecture
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    set "kernel_url=%arm64_kernel_url%"
) else (
    set "kernel_url=%x64_kernel_url%"
)

REM Check if the WSL Linux kernel package is already installed
echo Checking if the WSL Linux kernel package is already installed...
if exist wsl_kernel.msi (
    echo WSL Linux kernel package is already installed. Skipping the installation process.
) else (
    REM Download and install the WSL Linux kernel package
    echo Downloading the WSL Linux kernel package...
    powershell.exe -Command "Invoke-WebRequest -Uri '%kernel_url%' -OutFile 'wsl_kernel.msi'"

    echo Installing the WSL Linux kernel package...
    start /wait msiexec /i wsl_kernel.msi /qn

    echo Cleaning up the temporary files...
    @REM del wsl_kernel.msi >nul 2>&1

    REM Check if the WSL Linux kernel package is installed after installation
    echo Checking if the WSL Linux kernel package is installed after installation...
    if errorlevel 1 (
        echo Failed to install the WSL Linux kernel package.
        exit /b
    ) else (
        echo WSL Linux kernel package is installed.
    )
)

REM Check status of installed WSL
echo Checking status of installed WSL:
wsl --status

REM Set the default version of WSL to 2
echo Setting the default version of WSL to 2...
wsl --set-default-version 2

REM List the available Linux distros online
echo - List the available Linux distros online:
wsl --list --online

REM Replace Linux distro with a distro from online list
echo Linux distro is set to desired Linux distro (e.g., Ubuntu-22.04)
set "linux_distro=Ubuntu-22.04"

REM Check if the Linux distro is installed
echo Checking if the Linux distro is installed on system
wsl --list | findstr \c:"%linux_distro%" > nul
if errorlevel 1 (
    echo Linux distro is not installed. Choosing and installing...
    (
        REM Install the Linux distro
        echo Installing the Linux distro...
        wsl --install -d %linux_distro%

        REM Set the installed Linux distro to default
        echo Setting the installed Linux distro to default:
        wsl --set-default %linux_distro%
    )
) else (
    echo Linux distro is already installed. Skipping the installation process.
)

REM Prompt the user to exit the script
echo All commands executed successfully. Press any key to exit.

pause >nul
```

## Username and Password Setup in Ubuntu (WSL)

Once WSL Kenel and Ubuntu are installed, you will be asked to create a **new user** for the Linux environment. This is a typical process when setting up a new Linux system, and it’s important to follow the instructions carefully.

### Step 1: Create a Username

When prompted, you will need to choose a **username** for your Ubuntu environment. This username will be used for login and to run commands as that user.

- **Tip**: Choose a simple, memorable username. For example, you can use your first name, or a common username like `fabuser` you use on other systems. This is the equivalent of the user account name in Windows.

### Step 2: Set Your Password

After choosing a username, you will be prompted to **enter a password**. Please note the following:

- **Password Input is Hidden**: As is standard with Unix-based systems, the characters you type for the password will not appear on the screen. This is done for security reasons to prevent others from seeing your password.
- **Don't Worry if You Don't See Anything**: Even though it looks like nothing is happening while you type, rest assured that your password is being entered correctly.
- After entering your password, you’ll be asked to **confirm** it by typing it again.

- **Tip**: Choose a simple, memorable password. For example, `123456`. This password is used for your Ubuntu Linux environment and does not affect your Windows password.

Here’s an example of what the prompts look like:

```bash
Enter new UNIX username: your-chosen-username
New password: 
Retype new password:
```

## Updating Your System

After your user is created and the terminal is open, it's a good idea to update the system to ensure you have the latest software and security patches. This step also helps confirm that your user has administrative privileges (i.e., can run `sudo` commands).

Run the following command in the Ubuntu terminal:

```bash
sudo apt-get update && sudo apt-get upgrade
```

- The sudo command confirms that you have administrative privileges (you will be prompted for the password you just created).
- The apt-get update command fetches the latest package lists from the Ubuntu repositories.
- The apt-get upgrade command upgrades all installed packages to their latest versions.

Install Python developemnt and pip:

```bash
sudo apt-get install build-essential python3-dev python3-pip
```

## OpenSSH Server for SSH Connections

### Step 1: Install OpenSSH Server

First, ensure that the OpenSSH server is installed on your WSL Ubuntu system. You can install it by running the following command:

```bash
sudo apt-get install openssh-server
```

### Step 2: Start the SSH Service

Once the OpenSSH server is installed, start the SSH service and enable it with the following commands:

```bash
sudo service ssh start
sudo systemctl enable ssh
```

### Step 3: Verify SSH Service Status

After starting the SSH service, verify that it's running properly:

```bash
sudo service ssh status
```

### Step 4: Test SSH Connection

Once SSH is running, you can test the connection by running:

```bash
ssh localhost
```

If everything is set up correctly, you should be able to log in to localhost and exit without issues.

## Installing MPI Packages in WSL Ubuntu

To use **mpi4py** in Jupyter Notebook and run parallel simulations with **FabSim3**, we need to install **OpenMPI** (or another MPI implementation). Since we are using Ubuntu in WSL, we can install these packages easily using the `apt-get` package manager.

```bash
sudo apt-get install openmpi-bin openmpi-common libopenmpi-dev
```

## Verify MPI Installation
After the installation is complete, you can verify that OpenMPI is installed correctly by running the following command:

```bash
mpirun --version
```

This should display the version of OpenMPI that is installed, confirming that it is ready to use.

## After Updating Your System

Once your system has finished updating and upgrading, you’re ready to start using Ubuntu within WSL.

### Official WSL Installation Guide

For more detailed instructions on installing and configuring WSL, you can visit the official Microsoft documentation:

- [Manual Installation of WSL](https://learn.microsoft.com/en-us/windows/wsl/install-manual)

This guide provides more in-depth information about various installation methods, configuration options, and troubleshooting steps for WSL.

## Using FabSim3 in WSL

Follow these steps to set up and configure FabSim3 within your WSL environment (Ubuntu).

### Step 1: Clone the FabSim3 Repository

Open your WSL terminal (Ubuntu), navigate to the directory where you want to install FabSim3, and clone the FabSim3 repository:

```bash
mkdir -p ~/projects
cd ~/projects
```

### Step 2: Clone the FabSim3 repository

```bash
git clone https://github.com/djgroen/FabSim3.git
cd FabSim3
```

This command will download the FabSim3 repository to your local machine and navigate into the FabSim3 directory.

### Step 3: Configure FabSim3

FabSim3 provides an automated configuration script to set up the necessary files and dependencies. Run the following Python script to configure FabSim3:

```bash
python3 configure_fabsim.py
```

This script performs several configuration tasks, including setting environment variables and preparing the necessary directories for FabSim3 to work properly. You may need to follow on-screen prompts during this process. If dependencies like rich is missing, please install them using pip3.

### Step 4: Add FabSim3 to Your System Path

To make FabSim3 easily accessible from anywhere in your terminal, you need to add it to your system path. You can do this by modifying your .bashrc file (or .zshrc if you're using Zsh):

```bash
vim ~/.bashrc
```

Add the following line to the end of the file:

```bash
export PATH="$HOME/projects/FabSim3/bin:$PATH"
```

This ensures that the fabsim command can be run from any directory.

After editing .bashrc, apply the changes by running:

```bash
source ~/.bashrc
```

### Step 5: Verify FabSim3 Installation

To verify that FabSim3 has been successfully installed and that its path is correctly set, run the following command:

```bash
which fabsim
```

This command should return the path to the fabsim executable, which should be located in the FabSim3/bin directory.

Example output:

```bash
/home/your-username/projects/FabSim3/bin/fabsim
```

If the command returns the correct path, your FabSim3 installation is ready to use.

Please see installation section of [FabSim3 documetnation.](https://fabsim3.readthedocs.io/en/latest/installation/)

**Alternatively, you can use FabSim3 in Jupyter Notebook.**

## Setting Up Jupyter Notebook in WSL

**Jupyter Notebook** is a powerful tool that provides an interactive environment for running and sharing Python code. Since we are using Ubuntu in WSL, we can easily install and use Jupyter Notebook just as we would on a native Linux system.

Follow these steps to install and run Jupyter Notebook in your WSL environment:

### Step 1: Install Jupyter Notebook

1. **Install Python and Pip**: Jupyter Notebook requires Python and Pip (Python's package installer). If they aren’t already installed, run the following commands:
   
```bash
sudo apt-get install jupyter-notebook
```

### Step 2: Launch Jupyter Notebook
Once Jupyter Notebook is installed, you can launch it using the following command:

```bash
jupyter notebook
```

### Step 3: Access Jupyter Notebook from a Browser on Windows
When you run the jupyter notebook command, it will launch Jupyter on a local server within the WSL environment. Here’s how you can access it from your Windows browser:

After running jupyter notebook, you will see output in the terminal that looks something like this:

```bash
[I 13:27:13.890 NotebookApp] Serving notebooks from local directory: /home/your-username
[I 13:27:13.890 NotebookApp] 0 active kernels
[I 13:27:13.891 NotebookApp] The Jupyter Notebook is running at:
[I 13:27:13.891 NotebookApp] http://localhost:8888/?token=your_token
```

Click or Copy the URL (the one that looks like http://localhost:8888/?token=your_token) and paste it into your browser’s address bar on Windows.

You should now see the Jupyter Notebook interface in your browser. Please close the Jupyter Notebook and continue the instructions.

### Troubleshooting
- **Can't Access Jupyter Notebook in Browser**: Make sure you are copying the entire URL from the terminal, including the token. If the terminal shows http://localhost:8888/, but you can’t connect, ensure that port 8888 is not being blocked by a firewall or other application.
- **Restart Jupyter Notebook**: If Jupyter Notebook is closed or the terminal is closed, simply restart it by running jupyter notebook again in the terminal.

## Cloning FabSim3 Jupyter and Running Jupyter Notebook

FabSim3 comes with a Jupyter Notebook repository, **FabSim3_Jupyter**, which provides interactive notebooks for running FabSim3 simulations. Follow the steps below to clone this repository and launch it using Jupyter Notebook in WSL.

### Step 1: Clone the FabSim3 Jupyter Repository

First, navigate to the directory where you want to clone the repository.

1. Change to the desired directory (e.g., projects):

```bash
cd ~/projects
```

### Step 2: Clone the FabSim3 Jupyter repository:

```bash
git clone https://github.com/mzrghorbani/FabSim3_Jupyter.git
```

Navigate to the cloned repository:

```bash
cd FabSim3_Jupyter
```

### Step 3: Launch Jupyter Notebook

Once the repository is cloned, launch Jupyter Notebook from the FabSim3_Jupyter directory:

```bash
jupyter notebook
```

### Step 4: Start Running FabSim3

Once the Jupyter Notebook interface is open in your browser, you can navigate through the FabSim3_Jupyter directory and start using the provided notebooks to run simulations with FabSim3.

- Simply click on any notebook (.ipynb file) in the directory to open it.
- From there, you can interact with FabSim3 by running the notebook cells, following the instructions in each notebook.

If you encountered any problem, please raise a GitHub issue. 
