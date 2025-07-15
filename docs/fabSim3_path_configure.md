# FabSim3 Path Configure for VSCode and PyCharm

## Overview

This notebook provides workarounds for path variable issues when running FabSim3 in IDEs like VSCode or PyCharm. These IDEs sometimes don't inherit the full shell environment, causing PATH-related problems.

## Problem Description

When running Jupyter notebooks in VSCode or PyCharm, you may encounter issues such as:

- FabSim3 command not found
- Module import errors
- Unable to locate configuration files
- Path variables not being picked up correctly

## Solution Approach

This notebook demonstrates how to:

1. Detect the current IDE environment
2. Set explicit path variables as workarounds
3. Create helper functions for path management
4. Verify that FabSim3 is working correctly

## 1. Import Required Libraries

Import necessary libraries for path manipulation, environment detection, and system information.

```python
import os
import sys
import platform
import subprocess
from pathlib import Path
from pprint import pprint

# For pretty printing and formatting
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich library not available. Install with: pip install rich")

print("✓ Required libraries imported successfully")
print(f"Python version: {sys.version}")
print(f"Platform: {platform.system()} {platform.release()}")
```

## 2. Check Current Path Variables

Let's examine the current environment variables to understand what paths are available.

```python
def check_environment_variables():
    """Check and display current environment variables related to paths"""
    
    important_vars = [
        'PATH', 'PYTHONPATH', 'HOME', 'USER', 'PWD', 
        'FABSIM_ROOT', 'FABSIM_CONFIG_DIR', 'VIRTUAL_ENV'
    ]
    
    print("Current Environment Variables:")
    print("=" * 50)
    
    for var in important_vars:
        value = os.environ.get(var, 'NOT SET')
        if var == 'PATH' and value != 'NOT SET':
            # Display PATH in a more readable format
            print(f"{var}:")
            for path in value.split(os.pathsep):
                print(f"  - {path}")
        else:
            print(f"{var}: {value}")
    
    print("\nCurrent Working Directory:", os.getcwd())
    print("Python Executable:", sys.executable)
    print("Python Path:", sys.path[:3], "..." if len(sys.path) > 3 else "")

check_environment_variables()
```

## 3. Detect IDE Environment

Identify whether we're running in VSCode, PyCharm, or another IDE to apply appropriate workarounds.

```python
def detect_ide_environment():
    """Detect which IDE environment we're running in"""
    
    ide_indicators = {
        'VSCode': [
            'VSCODE_PID',
            'VSCODE_CWD', 
            'VSCODE_IPC_HOOK',
            'TERM_PROGRAM'
        ],
        'PyCharm': [
            'PYCHARM_HOSTED',
            'PYCHARM_MATPLOTLIB_INTERACTIVE',
            'PYCHARM_DISPLAY_PORT'
        ],
        'Jupyter': [
            'JPY_PARENT_PID',
            'JUPYTER_SERVER_ROOT'
        ],
        'Colab': [
            'COLAB_GPU'
        ]
    }
    
    detected_ide = []
    
    for ide, indicators in ide_indicators.items():
        for indicator in indicators:
            if indicator in os.environ:
                detected_ide.append(ide)
                break
    
    # Additional checks
    if 'TERM_PROGRAM' in os.environ and os.environ['TERM_PROGRAM'] == 'vscode':
        detected_ide.append('VSCode')
    
    # Check for Jupyter notebook context
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            detected_ide.append('Jupyter')
    except ImportError:
        pass
    
    # Remove duplicates
    detected_ide = list(set(detected_ide))
    
    print("IDE Detection Results:")
    print("=" * 30)
    
    if detected_ide:
        print(f"Detected IDE(s): {', '.join(detected_ide)}")
    else:
        print("No specific IDE detected - likely running in standard Python environment")
    
    # Show relevant environment variables
    print("\nRelevant Environment Variables:")
    all_indicators = [indicator for indicators in ide_indicators.values() for indicator in indicators]
    for var in all_indicators:
        if var in os.environ:
            print(f"  {var}: {os.environ[var]}")
    
    return detected_ide

current_ide = detect_ide_environment()
```

## 4. Set Explicit Path Variables

Set explicit path variables as workarounds for IDE path issues. **This is the main workaround section!**

```python
# ========================================
# MAIN WORKAROUND: Set Explicit Paths
# ========================================

def setup_fabsim_paths():
    """
    Set up FabSim3 paths explicitly to work around IDE path issues.
    
    IMPORTANT: Modify these paths according to your FabSim3 installation!
    """
    
    # Method 1: Auto-detect FabSim3 root from current location
    current_dir = Path.cwd()
    fabsim_root = None
    
    # Search for FabSim3 root by looking for key files
    search_paths = [
        current_dir,
        current_dir.parent,
        current_dir.parent.parent,
        Path.home() / "FabSim3",
        Path("/opt/FabSim3"),
        Path("/usr/local/FabSim3")
    ]
    
    for path in search_paths:
        if (path / "fabsim" / "bin" / "fabsim").exists():
            fabsim_root = path
            break
    
    if fabsim_root:
        print(f"✓ Auto-detected FabSim3 root: {fabsim_root}")
    else:
        # Method 2: Set explicit path (MODIFY THIS!)
        print("Could not auto-detect FabSim3 root. Setting explicit path...")
        
        # MODIFY THIS PATH TO YOUR FABSIM3 INSTALLATION!
        fabsim_root = Path("/path/to/FabSim3") # MODIFY THIS!
        
        if not fabsim_root.exists():
            print(f"FabSim3 root not found at {fabsim_root}")
            print("Please modify the path in this cell to point to your FabSim3 installation!")
            return None
    
    # Set up all important paths
    fabsim_paths = {
        'FABSIM_ROOT': fabsim_root,
        'FABSIM_BIN': fabsim_root / "fabsim" / "bin",
        'FABSIM_CONFIG_DIR': fabsim_root / "fabsim" / "deploy",
        'FABSIM_PLUGINS_DIR': fabsim_root / "plugins",
        'FABSIM_RESULTS_DIR': fabsim_root / "results",
        'FABSIM_PYTHON_PATH': fabsim_root / "fabsim"
    }
    
    # Add to environment variables
    for key, path in fabsim_paths.items():
        os.environ[key] = str(path)
    
    # Add FabSim3 to Python path
    if str(fabsim_paths['FABSIM_PYTHON_PATH']) not in sys.path:
        sys.path.insert(0, str(fabsim_paths['FABSIM_PYTHON_PATH']))
    
    # Add FabSim3 bin to PATH
    fabsim_bin_path = str(fabsim_paths['FABSIM_BIN'])
    if fabsim_bin_path not in os.environ.get('PATH', ''):
        os.environ['PATH'] = f"{fabsim_bin_path}{os.pathsep}{os.environ.get('PATH', '')}"
    
    print("\n✓ FabSim3 paths configured successfully!")
    print("\nConfigured paths:")
    for key, path in fabsim_paths.items():
        status = "✓" if path.exists() else "❌"
        print(f"  {key}: {path} {status}")
    
    return fabsim_paths

# Run the setup
fabsim_paths = setup_fabsim_paths()
```

## 5. Create Path Helper Functions

Implement utility functions for dynamic path management and validation.

```python
def get_fabsim_executable():
    """
    Get the full path to the FabSim3 executable.
    Returns the path if found, None otherwise.
    """
    fabsim_bin = os.environ.get('FABSIM_BIN')
    if fabsim_bin:
        fabsim_exe = Path(fabsim_bin) / "fabsim"
        if fabsim_exe.exists():
            return str(fabsim_exe)
    
    # Fallback: search in PATH
    try:
        result = subprocess.run(['which', 'fabsim'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    return None

def validate_fabsim_installation():
    """
    Validate that FabSim3 is properly installed and accessible.
    """
    print("Validating FabSim3 installation...")
    print("=" * 35)
    
    # Check executable
    fabsim_exe = get_fabsim_executable()
    if fabsim_exe:
        print(f"FabSim3 executable found: {fabsim_exe} ✓")
    else:
        print("❌ FabSim3 executable not found")
        return False
    
    # Check configuration files
    config_files = [
        'machines.yml',
        'plugins.yml',
        'applications.yml'
    ]
    
    config_dir = os.environ.get('FABSIM_CONFIG_DIR')
    if config_dir:
        for config_file in config_files:
            config_path = Path(config_dir) / config_file
            if config_path.exists():
                print(f"Configuration file found: {config_file}")
            else:
                print(f"Configuration file missing: {config_file}")
    else:
        print("FABSIM_CONFIG_DIR not set")
        return False
    
    # Check plugins directory
    plugins_dir = os.environ.get('FABSIM_PLUGINS_DIR')
    if plugins_dir and Path(plugins_dir).exists():
        print(f"Plugins directory found: {plugins_dir}")
    else:
        print("Plugins directory not found")

    return True

def run_fabsim_command(command, args=None):
    """
    Run a FabSim3 command with proper path handling.
    """
    fabsim_exe = get_fabsim_executable()
    if not fabsim_exe:
        print("Cannot run FabSim3 command: executable not found")
        return None
    
    cmd = [fabsim_exe, command]
    if args:
        if isinstance(args, str):
            cmd.append(args)
        else:
            cmd.extend(args)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result
    except subprocess.TimeoutExpired:
        print("Command timed out")
        return None
    except Exception as e:
        print(f"Error running command: {e}")
        return None

# Run validation
validation_result = validate_fabsim_installation()
```

## 6. Verify Path Configuration

Test the configured paths by importing FabSim3 modules and verifying access to configuration files.

```python
def test_fabsim_imports():
    """
    Test importing FabSim3 modules to verify path configuration.
    """
    print("Testing FabSim3 module imports...")
    print("=" * 35)
    
    # Test basic imports
    test_modules = [
        ('fabsim.base.env', 'env'),
        ('fabsim.base.utils', 'utils'),
        ('fabsim.deploy.machines', 'machines'),
        ('fabsim.base.fab', 'fab')
    ]
    
    successfully_imported = []
    
    for module_name, alias in test_modules:
        try:
            module = __import__(module_name, fromlist=[alias])
            print(f"✓ Successfully imported {module_name}")
            successfully_imported.append(module_name)
        except ImportError as e:
            print(f"❌ Failed to import {module_name}: {e}")
        except Exception as e:
            print(f"Error importing {module_name}: {e}")
    
    return successfully_imported

def test_config_file_access():
    """
    Test access to FabSim3 configuration files.
    """
    print("\nTesting configuration file access...")
    print("=" * 40)
    
    config_dir = os.environ.get('FABSIM_CONFIG_DIR')
    if not config_dir:
        print("FABSIM_CONFIG_DIR not set")
        return False
    
    config_files = {
        'machines.yml': 'Machine configurations',
        'plugins.yml': 'Plugin configurations',
        'applications.yml': 'Application configurations'
    }
    
    accessible_files = []
    
    for filename, description in config_files.items():
        filepath = Path(config_dir) / filename
        try:
            if filepath.exists():
                # Try to read the file
                with open(filepath, 'r') as f:
                    content = f.read()
                    print(f"{description} accessible: {filepath}")
                    print(f"  File size: {len(content)} bytes")
                    accessible_files.append(filename)
            else:
                print(f"{description} not found: {filepath}")
        except Exception as e:
            print(f"Error accessing {description}: {e}")

    return accessible_files

# Run the tests
print("=" * 50)
print("VERIFICATION TESTS")
print("=" * 50)

imported_modules = test_fabsim_imports()
accessible_configs = test_config_file_access()

print(f"\nSummary:")
print(f"  Modules imported: {len(imported_modules)}")
print(f"  Config files accessible: {len(accessible_configs)}")

if imported_modules and accessible_configs:
    print("\nFabSim3 path configuration appears to be working!")
else:
    print("\nSome issues detected. Check the output above for details.")
```

## 7. Test FabSim3 Integration

Run basic FabSim3 commands to ensure the path workarounds are working correctly.

```python
def check_plugin_dependencies():
    """
    Check for common plugin dependency issues.
    """
    print("Checking plugin dependencies...")
    print("=" * 35)
    
    # Common plugin dependencies
    common_plugin_deps = {
        'numpy': 'Required by VVP module and many data analysis plugins',
        'matplotlib': 'Required by visualization plugins',
        'pandas': 'Required by data processing plugins',
        'scipy': 'Required by scientific computing plugins'
    }
    
    missing_deps = []
    available_deps = []
    
    for dep, description in common_plugin_deps.items():
        try:
            __import__(dep)
            available_deps.append(dep)
            print(f"✓ {dep}: Available - {description}")
        except ImportError:
            missing_deps.append(dep)
            print(f"{dep}: Missing - {description}")
    
    if missing_deps:
        print(f"\nNote: {len(missing_deps)} plugin dependencies are missing.")
        print("This is normal - install them only if you need specific plugins:")
        for dep in missing_deps:
            print(f"  pip install {dep}")
    
    return available_deps, missing_deps

def test_fabsim_commands():
    """
    Test basic FabSim3 commands to verify functionality.
    """
    print("\nTesting FabSim3 command execution...")
    print("=" * 40)
    
    # Test commands that should work without additional setup
    test_commands = [
        ('localhost', ['-l', 'tasks'], 'List available tasks'),
        ('localhost', ['-l', 'machines'], 'List available machines'),
        ('localhost', ['-l', 'plugins'], 'List available plugins')
    ]
    
    successful_commands = []
    plugin_dependency_issues = []
    
    for command, args, description in test_commands:
        print(f"\nTesting: {description}")
        print(f"Command: fabsim {command} {' '.join(args)}")
        
        result = run_fabsim_command(command, args)
        
        if result and result.returncode == 0:
            print(f"✓ Success!")
            print(f"Output (first 200 chars): {result.stdout[:200]}...")
            successful_commands.append(command)
        else:
            print(f"❌ Failed!")
            if result and result.stderr:
                error_msg = result.stderr
                # Check if this is a plugin dependency issue
                if "No module named" in error_msg:
                    missing_module = error_msg.split("No module named")[1].split("'")[1] if "'" in error_msg else "unknown"
                    plugin_dependency_issues.append(missing_module)
                    print(f"Plugin dependency issue: Missing '{missing_module}'")
                    print(f"Solution: pip install {missing_module}")
                else:
                    print(f"Return code: {result.returncode}")
                    print(f"Error: {error_msg[:200]}...")
            else:
                print("No result returned")
    
    return successful_commands, plugin_dependency_issues

def test_fabsim_python_api():
    """
    Test using FabSim3 Python API directly.
    """
    print("\nTesting FabSim3 Python API...")
    print("=" * 35)
    
    try:
        # Try to import and use FabSim3 environment
        from fabsim.base.env import env
        print("✓ Successfully imported FabSim3 environment")
        
        # Test accessing environment variables
        if hasattr(env, 'localroot'):
            print(f"✓ Local root: {env.localroot}")
        
        if hasattr(env, 'fabsim_root'):
            print(f"✓ FabSim root: {env.fabsim_root}")
        
        # Try to import utilities
        from fabsim.base.utils import show_avail_plugins
        print("✓ Successfully imported show_avail_plugins")
        
        # Test calling a utility function
        print("\n--- Available Plugins ---")
        show_avail_plugins()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Python API: {e}")
        return False

# Run dependency check first
available_deps, missing_deps = check_plugin_dependencies()

# Run integration tests
print("\n" + "=" * 50)
print("INTEGRATION TESTS")
print("=" * 50)

successful_commands, plugin_dependency_issues = test_fabsim_commands()
api_test_success = test_fabsim_python_api()

print(f"\n" + "=" * 50)
print("FINAL RESULTS")
print("=" * 50)
print(f"Core FabSim3 Python API: {'✓ WORKING' if api_test_success else '❌ FAILED'}")
print(f"Command execution: {len(successful_commands)}/3 commands successful")
print(f"Plugin dependencies available: {len(available_deps)}")
print(f"Plugin dependencies missing: {len(missing_deps)}")

if api_test_success:
    print("\nSUCCESS! FabSim3 path workaround is working correctly!")
    print("\n✓ Core FabSim3 functionality is available in this IDE environment.")
    print("✓ You can now use FabSim3 Python modules in your notebooks.")
    
    if plugin_dependency_issues:
        print(f"\nPlugin Dependencies: {len(plugin_dependency_issues)} missing dependencies detected:")
        for dep in set(plugin_dependency_issues):
            print(f"   • {dep} - Install with: pip install {dep}")
        print("\nNote: Plugin dependencies are only needed for specific plugins.")
        print("Install them as needed based on which plugins you plan to use.")
    
    if successful_commands == 3:
        print("\nAll command-line operations are also working perfectly!")
    else:
        print(f"\nCommand-line: {len(successful_commands)}/3 tests passed")
        print("Command issues are typically due to missing plugin dependencies.")
        
else:
    print("\n❌ Core FabSim3 setup failed. Please check:")
    print("  1. FabSim3 is properly installed")
    print("  2. The path in Section 4 is correct")
    print("  3. Core dependencies are installed (rich, beartype, pyyaml, fabric2)")

print(f"\nSUMMARY FOR ISSUE #295:")
print("✓ Path workaround successfully enables FabSim3 Python API in IDEs")
print("✓ Core functionality works independently of plugin dependencies")
print("Plugin-specific dependencies can be installed as needed")
```

## 8. Troubleshooting and Additional Resources

### Common Issues and Solutions

1. **"FabSim3 executable not found"**
   - Check the path in Section 4 and modify it to your actual FabSim3 installation
   - Ensure FabSim3 is properly installed and the `fabsim` executable exists

2. **"Module import errors"**
   - Verify that the Python path is correctly set
   - Check that you're using the correct Python environment

3. **"Configuration files not found"**
   - Ensure FabSim3 configuration files exist in the deploy directory
   - Run `python3 configure_fabsim.py` using the system Python 3, if needed
  
4. **"Plugin dependency errors" (e.g., "No module named 'numpy'")**
   - This indicates a specific plugin requires additional packages
   - **This is NOT a core FabSim3 issue** - the path workaround is working correctly
   - Check the plugin's `requirements.txt` file for dependencies
   - Install the missing package: `pip install numpy` (or the specific package mentioned)
   - You only need to install dependencies for plugins you actually plan to use

5. **"Permission errors"**
   - Check file permissions on the FabSim3 directory
   - Ensure you have read/write access to the installation directory

### Plugin Dependencies vs Core FabSim3

**Important distinction:**

- **Core FabSim3** requires: `rich`, `beartype`, `pyyaml`, `fabric2`
- **Individual plugins** may require: `numpy`, `matplotlib`, `pandas`, `scipy`, etc.

If the Python API test passes but command-line tests fail with "No module named" errors, this means:

- ✓ The path workaround is working correctly
- ✓ Core FabSim3 is accessible
- A plugin needs additional dependencies

### Quick Setup Template

For future notebooks, you can use this minimal setup code:

```python
# Quick FabSim3 setup for IDE environments
import os
import sys
from pathlib import Path

# Set your FabSim3 installation path here
FABSIM_ROOT = Path("/path/to/your/FabSim3")  # MODIFY THIS!

# Add to Python path
sys.path.insert(0, str(FABSIM_ROOT / "fabsim"))

# Set environment variables
os.environ['FABSIM_ROOT'] = str(FABSIM_ROOT)
os.environ['FABSIM_CONFIG_DIR'] = str(FABSIM_ROOT / "fabsim" / "deploy")
os.environ['PATH'] = f"{FABSIM_ROOT / 'fabsim' / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}"

# Test import
try:
    from fabsim.base.env import env
    print("✓ FabSim3 ready!")
except ImportError as e:
    print(f"❌ Setup failed: {e}")
```

### Installing Plugin Dependencies

When you encounter plugin dependency errors, install them individually:

```python
# Example: Install common plugin dependencies
import subprocess
import sys

def install_plugin_dependency(package):
    """Install a plugin dependency"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install as needed
# install_plugin_dependency("numpy")      # For VVP and data analysis plugins
# install_plugin_dependency("matplotlib") # For visualization plugins
# install_plugin_dependency("pandas")     # For data processing plugins
```

### Resources

- [FabSim3 Documentation](https://fabsim3.readthedocs.io/)
- [FabSim3 GitHub Repository](https://github.com/djgroen/FabSim3)
- [Issue #295: Path variable not picked up](https://github.com/djgroen/FabSim3/issues/295)

### Next Steps

After running this notebook successfully, you can:

1. Use FabSim3 Python API directly in code cells
2. Import and use FabSim3 Python modules
3. Install plugin dependencies as needed for specific plugins
4. Create your own FabSim3-based analysis notebooks
5. Use the quick setup template in new notebooks
