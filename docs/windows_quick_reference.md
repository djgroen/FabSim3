# FabSim3 + EasyVVUQ Windows Quick Reference

## Installation Method Comparison

| Feature | WSL (Recommended) | Git Bash (Simpler) |
|---------|-------------------|-------------------|
| **Setup Complexity** | Moderate (requires admin) | Easy (standard install) |
| **Linux Compatibility** | Full Linux environment | Limited compatibility |
| **SSH Support** | Full SSH server | Limited/None |
| **EasyVVUQ Integration** | ✓ Full support | ❌ Limited |
| **FabSim3 Basic Features** | ✓ All features | ✓ Basic features |
| **Remote Machine Access** | ✓ Full support | ❌ Limited |
| **Performance** | Good | Good |
| **Best For** | Production use, full features | Testing, simple workflows |

**Recommendation:** Use WSL for full FabSim3 + EasyVVUQ functionality. Use Git Bash for simple testing or when WSL installation is not possible.

## One-Time Setup Commands

### Method 1: WSL Installation (Recommended)

```powershell
# In PowerShell (Admin)
git clone https://github.com/mzrghorbani/FabSim3_Jupyter.git
cd FabSim3_Jupyter
.\install_wsl.bat
```

### Method 2: Git Bash Alternative (Simpler Setup)

**Install Git Bash:**

1. Download Git for Windows from: https://git-scm.com/download/win
2. Install with default settings (includes Git Bash)
3. Open Git Bash terminal

**Setup in Git Bash:**

```bash
# Install Python (if not already installed)
# Download from: https://www.python.org/downloads/

# Verify Python installation
python --version
pip --version

# Install FabSim3 dependencies
pip install ruamel.yaml rich fabric2 pyyaml pytest beartype

# Clone FabSim3
git clone https://github.com/djgroen/FabSim3.git
cd FabSim3

# Configure FabSim3
python configure_fabsim.py

# Add to PATH (add to ~/.bashrc for persistence)
export PATH="$PWD/bin:$PATH"
```

**Note:** Git Bash provides a Linux-like terminal experience on Windows, making it easier to run FabSim3 commands without the complexity of WSL setup.

### Ubuntu Environment Setup

```bash
# In Ubuntu terminal
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential python3-dev python3-pip git curl wget openssh-server
```

### FabSim3 Installation

```bash
# Install dependencies
pip3 install ruamel.yaml rich

# Clone and install FabSim3
git clone https://github.com/djgroen/FabSim3.git
cd FabSim3
python3 configure_fabsim.py
echo 'export PATH="$HOME/FabSim3/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### EasyVVUQ Installation

```bash
pip3 install easyvvuq numpy pandas matplotlib scipy jupyter
```

### SSH Configuration

```bash
sudo service ssh start
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

## Common Commands

### FabSim3 Testing (WSL/Git Bash)

```bash
# Install test plugin
fabsim localhost install_plugin:FabDummy

# Run basic test
fabsim localhost dummy:dummy_test

# Fetch results
fabsim localhost fetch_results
```

### EasyVVUQ + FabSim3 Workflow (WSL Only)

**Note:** Full EasyVVUQ integration requires WSL due to SSH dependencies.

```bash
# Install dynamics plugin
fabsim localhost install_plugin:FabDynamics

# Clone test application
git clone https://github.com/arindamsaha1507/dynamics.git
cd dynamics
pip3 install -r requirements.txt

# Convert EasyVVUQ campaign to FabSim3 format
fabsim localhost campaign2ensemble:config_name,/path/to/campaign

# Run ensemble
fabsim localhost dynamics_ensemble:config_name
```

### Daily Use Commands

**WSL:**

```bash
# Start SSH service (if stopped)
sudo service ssh start

# Activate virtual environment (if used)
source ~/FabSim3/VirtualEnv/bin/activate

# Check FabSim3 version
fabsim localhost dummy:localhost_test
```

**Git Bash:**

```bash
# Navigate to FabSim3 directory
cd /c/path/to/FabSim3

# Ensure PATH is set
export PATH="$PWD/bin:$PATH"

# Run basic commands (limited functionality)
fabsim localhost dummy:localhost_test
```

## Quick Troubleshooting

### Fix PATH Issues

**WSL:**

```bash
echo 'export PATH="$HOME/FabSim3/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Git Bash:**

```bash
# Add to ~/.bashrc for persistence
echo 'export PATH="/c/path/to/FabSim3/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Fix SSH Issues (WSL Only)

```bash
sudo service ssh restart
ssh localhost  # Test connection
```

### Fix Python Issues

**WSL:**

```bash
python3 -c "import sys; print(sys.path)"
pip3 install --upgrade easyvvuq
```

**Git Bash:**

```bash
python -c "import sys; print(sys.path)"
pip install --upgrade easyvvuq
```

### Git Bash Specific Issues

**Problem:** Commands not found in Git Bash
**Solution:**

```bash
# Ensure Python is in PATH
export PATH="/c/Python39:$PATH"  # Adjust Python path as needed

# Use Windows-style paths when necessary
cd /c/Users/YourUsername/FabSim3
```

**Problem:** Permission issues in Git Bash
**Solution:**

```bash
# Run Git Bash as Administrator if needed
# Or use Windows file permissions through Properties
```

## Configuration Files

### Machine Configuration (`fabsim/deploy/machines_user.yml`)

```yaml
localhost:
  remote: localhost
  username: fabuser
  home_path_template: /home/$username
  cores: 4
  corespernode: 4
  virtual_env_path: /path/to/FabSim3/VirtualEnv
  venv: true  # Enable virtual environment
  nb_process: 8  # Parallel processes
```

## Links

- **Full Guide**: `windows_installation_guide.md`
- **FabSim3 Docs**: https://fabsim3.readthedocs.io
- **EasyVVUQ Docs**: https://easyvvuq.readthedocs.io
- **WSL Docs**: https://docs.microsoft.com/en-us/windows/wsl/
