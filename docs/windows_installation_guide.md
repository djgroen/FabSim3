# FabSim3 + E### Overview of Installation Methods

There are three primary ways to run FabSim3 + EasyVVUQ on Windows:

1. **Windows Subsystem for Linux (WSL)** - **Recommended**
   - Full Linux environment with complete FabSim3 + EasyVVUQ functionality
   - Supports SSH, remote machines, and advanced features
   - Requires admin privileges for initial setup

2. **Git Bash** - **Alternative for Simple Use**
   - Linux-like terminal experience on Windows
   - Good for basic FabSim3 testing and simple workflows
   - Limited SSH and EasyVVUQ integration capabilities

3. **Docker Desktop** - **Containerized Approach**
   - Containerized environment (documentation available separately)
   - Good for isolated testing environments

This guide covers **Methods 1 and 2** in detail, as they provide the most practical approaches for different use cases.nstallation and Usage Guide for Windows

This guide provides comprehensive instructions for installing and using FabSim3 together with EasyVVUQ on Windows systems. FabSim3 is an automation toolkit for scientific simulation workflows, while EasyVVUQ is a Python library for Verification, Validation, and Uncertainty Quantification.

## Prerequisites

### System Requirements

- Windows 10 version 2004 or later, or Windows 11
- Administrative privileges (required for initial WSL installation)
- At least 4GB available disk space
- Internet connection for downloading packages

### Overview of Installation Methods

There are three primary ways to run FabSim3 + EasyVVUQ on Windows:

1. **Windows Subsystem for Linux (WSL)** - **Recommended**
2. **Docker Desktop** - Alternative containerized approach
3. **Native Windows with Git Bash** - Limited functionality

This guide focuses on the **WSL approach** as it provides the most seamless Linux-like experience.

## Method 1: Installation via Windows Subsystem for Linux (WSL)

### Step 1: Install WSL and Ubuntu

#### Option A: Automated Installation Script (Recommended)

1. **Open PowerShell as Administrator**:
   - Press `Win + X` and select "Windows PowerShell (Admin)"
   - Or search "PowerShell" → Right-click → "Run as administrator"

2. **Clone the FabSim3 Windows Installation Repository**:

   ```powershell
   cd C:\Users\$env:USERNAME\Documents
   git clone https://github.com/mzrghorbani/FabSim3_Jupyter.git
   cd FabSim3_Jupyter
   ```

3. **Run the Installation Script**:

   ```powershell
   .\install_wsl.bat
   ```

   **Important Notes**:
   - Windows Defender may block the script - review and allow it to run
   - The script will require a restart after WSL installation
   - After restart, run the script again and answer "no" to the restart prompt

#### Option B: Manual WSL Installation

If you prefer manual installation, follow the [official Microsoft WSL installation guide](https://learn.microsoft.com/en-us/windows/wsl/install-manual).

### Step 2: Configure Ubuntu Environment

1. **Create Ubuntu User Account**:

   ```bash
   # You'll be prompted to create a username and password
   # Choose something simple like 'fabuser' and '123456'
   Enter new UNIX username: fabuser
   New password: [type password - won't show on screen]
   Retype new password: [type password again]
   ```

2. **Update the System**:

   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

3. **Install Development Tools**:

   ```bash
   sudo apt install -y build-essential python3-dev python3-pip git curl wget
   ```

### Step 3: Install FabSim3

1. **Install FabSim3 Dependencies**:

   ```bash
   pip3 install ruamel.yaml rich
   ```

2. **Clone FabSim3 Repository**:

   ```bash
   cd ~
   git clone https://github.com/djgroen/FabSim3.git
   cd FabSim3
   ```

3. **Install FabSim3**:

   ```bash
   python3 configure_fabsim.py
   ```

4. **Add FabSim3 to PATH**:

   ```bash
   echo 'export PATH="$HOME/FabSim3/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

### Step 4: Install EasyVVUQ

1. **Install EasyVVUQ and Dependencies**:

   ```bash
   pip3 install easyvvuq
   ```

2. **Install Additional Scientific Computing Libraries**:

   ```bash
   pip3 install numpy pandas matplotlib scipy jupyter
   ```

3. **Verify EasyVVUQ Installation**:

   ```bash
   python3 -c "import easyvvuq; print('EasyVVUQ version:', easyvvuq.__version__)"
   ```

### Step 5: Configure SSH for Local Testing

FabSim3 uses SSH for communication, even with localhost:

1. **Install OpenSSH Server**:

   ```bash
   sudo apt install -y openssh-server
   ```

2. **Start SSH Service**:

   ```bash
   sudo service ssh start
   ```

3. **Generate SSH Key Pair**:

   ```bash
   ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
   # Press Enter for all prompts to use defaults
   ```

4. **Add Key to Authorized Keys**:

   ```bash
   cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

5. **Test SSH Connection**:

   ```bash
   ssh localhost
   # Type 'yes' when prompted, then exit
   ```

### Step 6: Configure FabSim3 Machine Settings

1. **Copy Machine Configuration**:

   ```bash
   cd ~/FabSim3
   cp fabsim/deploy/machines_user_example.yml fabsim/deploy/machines_user.yml
   ```

2. **Edit Machine Configuration**:

   ```bash
   nano fabsim/deploy/machines_user.yml
   ```

   Add or modify the localhost configuration:

   ```yaml
   localhost:
     remote: localhost
     username: fabuser  # Your Ubuntu username
     home_path_template: /path/to/$username
     virtual_env_path: /path/to/VirtualEnv
   ```

## Method 2: Installation via Git Bash (Alternative)

**Note:** This method provides basic FabSim3 functionality but has limitations with SSH-based features and full EasyVVUQ integration. Recommended for simple testing or when WSL installation is not possible.

### Step 1: Install Git for Windows

1. **Download Git for Windows**:
   - Visit [https://git-scm.com/download/win](https://git-scm.com/download/win)
   - Download the latest version for your system (64-bit recommended)

2. **Install Git with Default Settings**:
   - Run the installer as Administrator
   - Accept all default options (includes Git Bash)
   - Git Bash provides a Linux-like terminal experience

### Step 2: Install Python (if not already installed)

1. **Download Python**:
   - Visit [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - Download Python 3.9 or later

2. **Install Python**:
   - Run installer as Administrator
   - **Important**: Check "Add Python to PATH" during installation
   - Verify installation in Git Bash:

   ```bash
   python --version
   pip --version
   ```

### Step 3: Install FabSim3 Dependencies

1. **Open Git Bash**:
   - Right-click on desktop/folder → "Git Bash Here"
   - Or search "Git Bash" in Start menu

2. **Install Required Python Packages**:

   ```bash
   pip install ruamel.yaml rich fabric2 pyyaml pytest beartype numpy
   ```

### Step 4: Install FabSim3

1. **Clone FabSim3 Repository**:

   ```bash
   # Navigate to desired directory (e.g., Documents)
   cd /c/Users/$USERNAME/Documents
   
   # Clone FabSim3
   git clone https://github.com/djgroen/FabSim3.git
   cd FabSim3
   ```

2. **Configure FabSim3**:

   ```bash
   python configure_fabsim.py
   ```

3. **Add FabSim3 to PATH**:

   ```bash
   # For current session
   export PATH="$PWD/bin:$PATH"
   
   # For persistent PATH (add to ~/.bashrc)
   echo 'export PATH="/c/Users/$USERNAME/Documents/FabSim3/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

### Step 5: Configure Machine Settings

1. **Copy Machine Configuration**:

   ```bash
   cp fabsim/deploy/machines_user_example.yml fabsim/deploy/machines_user.yml
   ```

2. **Edit Configuration for Git Bash**:

   ```bash
   # Edit with notepad or preferred editor
   notepad fabsim/deploy/machines_user.yml
   ```

   Configure localhost for Git Bash:

   ```yaml
   localhost:
     remote: localhost
     username: $USERNAME  # Your Windows username
     manual_ssh: false
     batch_header: bash_header
     home_path_template: /c/Users/$username
     cores: 4
     corespernode: 4
     # Note: SSH features limited in Git Bash
   ```

### Step 6: Basic Testing

1. **Test FabSim3 Installation**:

   ```bash
   # Install test plugin
   fabsim localhost install_plugin:FabDummy
   
   # Run basic test (limited functionality)
   fabsim localhost dummy:localhost_test
   ```

### Limitations of Git Bash Method

**What Works:**

- ✓ Basic FabSim3 commands
- ✓ Plugin installation
- ✓ Local job execution (limited)
- ✓ Configuration management

**What Doesn't Work:**

- ❌ SSH-based remote machine access
- ❌ Full EasyVVUQ integration
- ❌ Advanced job scheduling features
- ❌ Network-based file transfers

**Recommendation:** Use Git Bash for initial testing and basic workflows. For production use with EasyVVUQ, switch to WSL (Method 1).

## Testing the Installation

### Test 1: Basic FabSim3 Functionality

1. **Install FabDummy Plugin**:

   ```bash
   fabsim localhost install_plugin:FabDummy
   ```

2. **Run a Simple Test**:

   ```bash
   fabsim localhost dummy:localhost_test
   ```

3. **Check Results**:

   ```bash
   fabsim localhost fetch_results:localhost_test_1
   ls ~/FabSim3/results/
   ```

### Test 2: EasyVVUQ Integration Test

1. **Install FabDynamics Plugin** (for EasyVVUQ tutorials):

   ```bash
   fabsim localhost install_plugin:FabDynamics
   ```

2. **Clone Dynamics Test Application**:

   ```bash
   cd ~
   git clone https://github.com/arindamsaha1507/dynamics.git
   cd dynamics
   pip3 install -r requirements.txt
   ```

3. **Test Dynamics Application**:

   ```bash
   python3 run.py
   ls -la timeseries.csv  # Should exist if successful
   ```

## Usage Examples

### Example 1: Basic Sensitivity Analysis with EasyVVUQ

Create a simple sensitivity analysis script:

```python
# sensitivity_example.py
import easyvvuq as uq
import numpy as np
import os

# Define parameter space
params = {
    "a": {"type": "real", "min": 0.5, "max": 2.0, "default": 1.0},
    "b": {"type": "real", "min": 0.1, "max": 1.0, "default": 0.5},
    "c": {"type": "real", "min": 0.1, "max": 1.0, "default": 0.5},
}

# Create EasyVVUQ campaign
campaign = uq.Campaign(name='dynamics_sensitivity')
campaign.add_app(name="dynamics", params=params)

# Use Sobol sampler for sensitivity analysis
sampler = uq.sampling.SobolSampler(
    vary=params,
    n_samples=100
)
campaign.set_sampler(sampler)

# Generate parameter sets
campaign.draw_samples()

print(f"Generated {campaign.get_active_sampler().n_samples} parameter sets")
print("Campaign created successfully!")
```

Run the script:

```bash
python3 sensitivity_example.py
```

### Example 2: Running EasyVVUQ Campaigns with FabSim3

1. **Create Campaign Directory**:

   ```bash
   mkdir -p ~/campaigns/dynamics_uq
   cd ~/campaigns/dynamics_uq
   ```

2. **Generate EasyVVUQ Campaign**:

   ```python
   # generate_campaign.py
   import easyvvuq as uq
   import os
   
   # Create campaign for FabSim3 integration
   campaign = uq.Campaign(name='dynamics_fabsim')
   
   params = {
       "a": {"type": "real", "min": 0.5, "max": 2.0, "default": 1.0},
       "b": {"type": "real", "min": 0.1, "max": 1.0, "default": 0.5},
       "c": {"type": "real", "min": 0.1, "max": 1.0, "default": 0.5},
   }
   
   campaign.add_app(name="dynamics", params=params)
   
   # Create sampler
   sampler = uq.sampling.SobolSampler(vary=params, n_samples=50)
   campaign.set_sampler(sampler)
   campaign.draw_samples()
   
   # Save campaign
   campaign.save_state("campaign_state.json")
   print("Campaign saved successfully!")
   ```

3. **Convert EasyVVUQ Campaign to FabSim3 Format**:

   ```bash
   cd ~/FabSim3
   fabsim localhost campaign2ensemble:dynamics_uq,~/campaigns/dynamics_uq
   ```

4. **Run Ensemble with FabSim3**:

   ```bash
   fabsim localhost dynamics_ensemble:dynamics_uq
   ```

## Advanced Configuration

### Using Virtual Environments

For better package management, you can use Python virtual environments:

1. **Create Virtual Environment**:

   ```bash
   python3 -m venv /path/to/FabSim3/VirtualEnv  # MODIFY THIS!
   source /path/to//FabSim3/VirtualEnv/bin/activate  # MODIFY THIS!
   ```

2. **Install Packages in Virtual Environment**:

   ```bash
   pip install easyvvuq numpy pandas matplotlib
   ```

3. **Configure FabSim3 to Use Virtual Environment**:

   Edit `fabsim/deploy/machines_user.yml`:

   ```yaml
   localhost:
     venv: true
     virtual_env_path: /path/to/FabSim3/VirtualEnv  # MODIFY THIS!
   ```

### Jupyter Notebook Integration

1. **Install Jupyter**:

   ```bash
   pip3 install jupyter ipykernel
   ```

2. **Start Jupyter Notebook**:

   ```bash
   jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser
   ```

3. **Access from Windows**:
   - Open browser and go to `http://localhost:8888`
   - Use the token shown in the terminal

### Performance Optimization

1. **Increase Process Count**:

   ```yaml
   localhost:
     nb_process: 8  # Adjust based on your CPU cores
   ```

2. **Enable Template Caching**:

   ```yaml
   localhost:
     enable_template_cache: true
     template_cache_size: 5000
   ```

## Troubleshooting

### Common Issues and Solutions

#### WSL Installation Issues

**Problem**: WSL installation fails with "Feature not available"

**Solution**:

```powershell
# Enable WSL features manually
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
# Restart computer and try again
```

#### SSH Connection Issues

**Problem**: SSH connection refused

**Solution**:

```bash
# Restart SSH service
sudo service ssh restart
# Check SSH status
sudo service ssh status
```

#### FabSim3 Command Not Found

**Problem**: `fabsim` command not recognized

**Solution**:

```bash
# Add to PATH permanently
echo 'export PATH="$HOME/FabSim3/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

#### EasyVVUQ Import Errors

**Problem**: `ImportError: No module named 'easyvvuq'`

**Solution**:

```bash
# Check Python path
python3 -c "import sys; print(sys.path)"
# Reinstall EasyVVUQ
pip3 install --upgrade easyvvuq
```

#### Permission Denied Errors

**Problem**: Permission denied when running scripts

**Solution**:

```bash
# Fix file permissions
chmod +x /path/to/FabSim3/bin/fabsim  # MODIFY THIS!
# Or run with python3
/path/to/FabSim3/bin/fabsim localhost dummy:dummy_test  # MODIFY THIS!
```

### Performance Issues

**Problem**: Slow execution on Windows

**Solutions**:

1. **Exclude WSL from Windows Defender**:
   - Open Windows Security → Virus & threat protection → Exclusions
   - Add folder: `C:\Users\%USERNAME%\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu*`

2. **Move FabSim3 to Linux filesystem**:

   ```bash
   # Access from WSL, not Windows filesystem
   cd /home/fabuser/FabSim3  # Not /mnt/c/Users/...
   ```

3. **Use WSL 2** (recommended):

   ```powershell
   wsl --set-default-version 2
   ```

### Getting Help

1. **FabSim3 Documentation**: [https://fabsim3.readthedocs.io](https://fabsim3.readthedocs.io)
2. **EasyVVUQ Documentation**: [https://easyvvuq.readthedocs.io](https://easyvvuq.readthedocs.io)
3. **FabSim3 GitHub Issues**: [https://github.com/djgroen/FabSim3/issues](https://github.com/djgroen/FabSim3/issues)
4. **WSL Documentation**: [https://docs.microsoft.com/en-us/windows/wsl/](https://docs.microsoft.com/en-us/windows/wsl/)

## Next Steps

After successful installation, you can:

1. **Explore FabSim3 Plugins**: Install additional plugins from the [plugin repository](https://github.com/djgroen/FabSim3/tree/master/plugins)
2. **Learn EasyVVUQ**: Follow the [EasyVVUQ tutorials](https://easyvvuq.readthedocs.io/en/latest/tutorials.html)
3. **Set up Remote Machines**: Configure FabSim3 to run on HPC systems
4. **Develop Custom Workflows**: Create your own FabSim3 plugins for specific applications
