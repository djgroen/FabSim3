# FabSim3 Jupyter Notebook Setup Guide

## Overview

This guide addresses **Issue #295**: "Path variable not picked up when notebooks are run in VSCode or PyCharm". The issue occurs because IDEs like VSCode and PyCharm don't always inherit the full shell environment, causing PATH-related problems when using FabSim3 in Jupyter notebooks.

## The Problem

When running Jupyter notebooks in IDEs, you may encounter:

- `command not found: fabsim`
- Module import errors for FabSim3
- Configuration files not being found
- Environment variables not being set correctly

## The Solution

We've created a comprehensive notebook (`docs/notebooks/fabsim3_path_configure.ipynb`) that provides workarounds for these issues. This notebook demonstrates how to:

1. **Detect the IDE environment** - Identify whether you're running in VSCode, PyCharm, or another IDE
2. **Set explicit path variables** - Configure FabSim3 paths manually to bypass IDE limitations
3. **Create helper functions** - Provide utilities for path management and validation
4. **Test the configuration** - Verify that FabSim3 is working correctly

## Dependencies

Before using the notebook, ensure you have the core FabSim3 dependencies installed:

```bash
pip install rich beartype pyyaml fabric2
```

Or install from the FabSim3 requirements:

```bash
pip install -r requirements.txt
```

**Note**: Individual plugins may require additional dependencies (e.g., `numpy`, `matplotlib`, etc.). The notebook will identify missing plugin dependencies and provide guidance on installing them as needed.

## Quick Setup

For immediate use in any notebook, add this code cell at the beginning:

```python
# Quick FabSim3 setup for IDE environments
import os
import sys
from pathlib import Path

# MODIFY THIS PATH TO YOUR FABSIM3 INSTALLATION!
FABSIM_ROOT = Path("/path/to/your/FabSim3") # MODIFY THIS!

# Add to Python path
sys.path.insert(0, str(FABSIM_ROOT / "fabsim"))

# Set environment variables
os.environ['FABSIM_ROOT'] = str(FABSIM_ROOT)
os.environ['FABSIM_CONFIG_DIR'] = str(FABSIM_ROOT / "fabsim" / "deploy")
os.environ['PATH'] = f"{FABSIM_ROOT / 'fabsim' / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}"

# Test import
try:
    from fabsim.base.env import env
    print("FabSim3 ready!")
except ImportError as e:
    print(f"Setup failed: {e}")
```

## Using the Comprehensive Notebook

1. **Open the notebook**: `docs/notebooks/fabsim3_path_configure.ipynb`
2. **Run all cells**: This will automatically detect your environment and set up paths
3. **Modify the path**: In Section 4, update the `FABSIM_ROOT` path to your actual FabSim3 installation
4. **Verify setup**: The notebook will test that everything is working correctly

## IDE-Specific Notes

### VSCode

- Ensure you're using the correct Python kernel
- Check that the Jupyter extension is installed
- The notebook should auto-detect VSCode environment

### PyCharm

- Make sure you're using the correct Python interpreter
- Enable Jupyter support in PyCharm Professional
- The notebook should auto-detect PyCharm environment

### Other IDEs

- The notebook includes generic fallback methods
- You may need to manually set the `FABSIM_ROOT` path

## Troubleshooting

### Common Issues

1. **"FabSim3 executable not found"**
   - Check the path in the notebook and modify it to your actual installation
   - Ensure FabSim3 is properly installed

2. **"Module import errors"**
   - Verify the Python path is correctly set
   - Check you're using the correct Python environment

3. **"Configuration files not found"**
   - Ensure FabSim3 configuration file `machines_user.yml` exists in the deploy directory
   - Run `python3 configure_fabsim.py` if needed. Check startup files (e.g., ~/.bashrc) for added FabSim3 path.

4. **"Plugin dependency errors" (e.g., "No module named 'numpy'")**
   - This indicates a specific plugin requires additional packages
   - Check the plugin's `requirements.txt` file for dependencies
   - Install the missing package: `pip install numpy` (or the specific package mentioned)
   - Plugin dependency issues don't affect core FabSim3 functionality

### Testing Your Setup

After running the setup, test with:

```python
# Test Python API (core functionality)
from fabsim.base.env import env
from fabsim.base.utils import show_avail_plugins
show_avail_plugins()

# Test command execution (may require plugin dependencies)
!fabsim localhost -l tasks
```

**Note**: If command tests fail with "No module named" errors, this indicates plugin dependency issues, not core FabSim3 problems. Install the missing packages as needed.

## For Tutorial Authors

When creating FabSim3 tutorials that use Jupyter notebooks:

1. **Include the setup code** at the beginning of each notebook
2. **Reference this guide** for users experiencing path issues
3. **Test in multiple IDEs** to ensure compatibility
4. **Provide the explicit path** as a fallback option

## Integration with Documentation

This workaround should be referenced in:

- FabSim3 installation documentation
- Jupyter notebook tutorials
- VSCode/PyCharm setup guides
- Troubleshooting sections

## Files Created

- `docs/notebooks/fabsim3_path_workaround.ipynb` - Comprehensive setup notebook
- `docs/jupyter_notebook_setup.md` - This guide

## Future Improvements

Consider these enhancements for future versions:

- Auto-detection of FabSim3 installation paths
- Integration with FabSim3 configuration system
- Support for additional IDEs
- Automated testing of notebook compatibility
