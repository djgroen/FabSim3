# Installing WSL on Windows

## What is Windows Subsystem for Linux (WSL)?

**Windows Subsystem for Linux (WSL)** allows you to run a full Linux environment on Windows, enabling access to native Linux tools and utilities. It is a powerful tool for developers working on Unix-based systems who prefer to use Windows as their main operating system. With WSL, a lightweight virtual machine runs a Linux kernel, providing access to many Windows/Linux applications.

WSL is especially useful for running tools like **FabSim3**, which are designed for Unix-based systems. By installing WSL and a Linux distribution (e.g., Ubuntu), you can run FabSim3 on your Windows machine as though you were working on a native Linux system.

## Installing WSL on Windows

For the installation of WSL and a Linux distribution (e.g., Ubuntu-22.04), you can either clone and execute an automation script from [FabSim3_Jupyter](https://github.com/mzrghorbani/FabSim3_Jupyter) GitHub repository **or** visit the Official Microsoft Step-by-Step [Installation Guide](https://learn.microsoft.com/en-us/windows/wsl/install-manual).

<span style="color: red;">**Note**</span>: The automation script consolidates all commands from the Microsoft guide into a single executable.

<span style="color: red;">**Note**</span>: The automation script is intended for native Windows 11 installations. Running WSL2 inside VirtualBox or other virtual machine environments is not supported and may result in errors. If you like to install WSL in a virtual machine, please set WSL default version in the script to 1.

## Option 1: Clone GitHub Repository on Windows 

<span style="color: red;">**Important**</span>: If you are installing WSL for the first time, administrator privileges are required to enable the WSL optional feature.

### Step 1: Open PowerShell as Aministrator:

- In the search bar, type **PowerShell**. 
- **Right-click** on **Windows PowerShell** in the search results. 
- From the context menu that appears, select **Run as administrator**.
- If prompted with **Do you want to allow this app to make changes to your device?**, select **Yes**.

### Step 2: Navigate to the Directory Where You Want to Clone the Repository:

```PowerShell
cd C:\Users\<YourUsername>\Documents
```

### Step 3: Clone the GitHub Repository:

```PowerShell
git clone https://github.com/mzrghorbani/FabSim3_Jupyter.git
```

If you encountered any issues with `git : The term 'git' is not recognized` on Windows, please install git from here: [https://git-scm.com/downloads/win](https://git-scm.com/downloads/win). You may need to **restart PowerShell as an administrator** for the Git installation to take effect.

### Step 4: Change Directory to FabSim3_Jupyter:

```PowerShell
cd .\FabSim3_Jupyter
```

### Step 5: Execute Script in PowerShell (Admin) or Command Promp (Admin):

```PowerShell
.\install_wsl.bat
```

<span style="color: red;">**Note**</span>: Windows Defender may block the execution of `.bat` scripts as a security precaution. If you receive a security alert, review the details and choose to allow the script to run by selecting the appropriate option. Be sure that the script is from trusted source and safe before proceeding.

<span style="color: red;">**Important**</span>: Restarting is necessary to complete the WSL installation. It ensures that changes made during the installation are correctly applied. After the first restart, when you run the script again, you can safely answer **no** when prompted to restart. This allows the script to continue running the remaining steps without requiring another reboot.

<span style="color: red;">**Important**</span>: If the script execution hangs and remains idle for more than five minutes, press Enter to continue.

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

## Option 2: Installing WSL Manually

Visit official Microsoft [Manual Installation of WSL](https://learn.microsoft.com/en-us/windows/wsl/install-manual) guide for detailed instructions.

This guide provides more in-depth information about various installation methods, configuration options, and troubleshooting steps for WSL.

## Uninstall Linux Distribution in WSL

If you want to uninstall a Linux distribution from WSL (e.g., Ubuntu-22.04), follow the steps below:

### Step 1: List your Ubuntu distributions:

```PowerShell
wsl.exe -l
```

### Step 2: Unregister the Linux distribution:

```PowerShell
wsl --unregister <distribution_name>
```

## Open Ubuntu After Closing the Terminal

In the PowerShell or Command Prompt window (as user, no admin), type the following command to start your Ubuntu distribution:

```PowerShell
wsl.exe -d <distribution_name>
```

## Updating Your Linux System

After your user is created and the terminal is open, it's a good idea to update the system to ensure you have the latest software and security patches. This step also helps confirm that your user has administrative privileges (i.e., can run `sudo` commands).

Run the following command in the Ubuntu terminal:

```bash
sudo apt-get update && sudo apt-get upgrade
```

- The sudo command confirms that you have administrative privileges (you will be prompted for the password you just created).
- The apt-get update command fetches the latest package lists from the Ubuntu repositories.
- The apt-get upgrade command upgrades all installed packages to their latest versions.

## Install Python developemnt and pip

Following the update, you can install Python 3 essentials:

```bash
sudo apt-get install build-essential python3-dev python3-pip
```

## OpenSSH Server for SSH Connections

FabSim3 uses localhost for SSH connections. You can install and configure OpenSSH Server by running the following commands:

### Step 1: Install OpenSSH Server

```bash
sudo apt-get install openssh-server
```

### Step 2: Start the SSH Service

Once the OpenSSH server is installed, start the SSH service:

```bash
sudo service ssh start
```

### Step 3: Start the SSH Service

Enable SSH with the following command:

```bash
sudo systemctl enable ssh
```

### Step 4: Verify SSH Service Status

After starting the SSH service, verify that it's running properly:

```bash
sudo service ssh status
```

### Step 5: Test SSH Connection

Once SSH is running, you can test the connection by running:

```bash
ssh localhost
```

If everything is set up correctly, you should be logged in to localhost and exit without issues. Type exit to return to your original terminal. 

```bash
exit
```

## Installing MPI Packages in WSL Ubuntu

To use **mpi4py** and run parallel simulations with **FabSim3**, we need to install **OpenMPI** (or another MPI implementation). Since we are using Ubuntu in WSL, we can install these packages easily using the `apt-get` package manager.

```bash
sudo apt-get install openmpi-bin openmpi-common libopenmpi-dev
```

## Verify MPI Installation
After the installation is complete, you can verify that OpenMPI is installed correctly by running the following command:

```bash
mpirun --version
```

This should display the version of OpenMPI that is installed, confirming that it is ready to use.

## Installing Jupyter Notebook in WSL

Follow these steps to install and run Jupyter Notebook in your WSL environment:

### Step 1: Install Jupyter Notebook:
   
```bash
sudo apt-get install jupyter-notebook
```

### Step 2: Launch Jupyter Notebook:

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

### Troubleshooting
- **Can't Access Jupyter Notebook in Browser**: Make sure you are copying the entire URL from the terminal, including the token. If the terminal shows http://localhost:8888/, but you can’t connect, ensure that port 8888 is not being blocked by a firewall or other application.
- **Restart Jupyter Notebook**: If Jupyter Notebook is closed or the terminal is closed, simply restart it by running jupyter notebook again in the terminal.

You should now see the Jupyter Notebook interface in your browser. 

Please close the Jupyter Notebook and continue the instructions.

## Cloning and Running FabSim3 Jupyter 

**FabSim3_Jupyter** provides interactive notebook for running FabSim3 simulations. Follow the steps below to clone this repository and launch it using Jupyter Notebook in WSL.

### Step 1: Clone the FabSim3 Jupyter Repository

First, navigate to the directory where you want to clone the repository.

Change to the desired directory (e.g., home directory or tilde symbol):

```bash
cd ~
```

### Step 2: Clone the FabSim3 Jupyter repository

Clone GitHub repository containing the Jupyter Notebook:

```bash
git clone https://github.com/mzrghorbani/FabSim3_Jupyter.git
```

### Step 3: Navigate to the cloned repository:

```bash
cd FabSim3_Jupyter
```

### Step 4: Launch Jupyter Notebook

```bash
jupyter notebook
```

### Step 4: Start Running FabSim3

Once the Jupyter Notebook interface is open in your browser, you can navigate through the FabSim3_Jupyter directory and start using the provided notebook to run simulations with FabSim3.

- Simply click on any notebook (.ipynb file) in the directory to open it.
- From there, you can interact with FabSim3 by running the notebook cells and following the instructions in the notebook.

## Report Issues

If you encountered any problem, please raise a GitHub issue. 