# Example Test Case: FabDummy Installation

### Test ID: FABDUMMY-001

**Test Name:** FabDummy Plugin Installation Test

**Test Category:** Installation

**Priority:** High

**Author:** FabSim3 Team

**Date Created:** 2025-07-15

**Last Updated:** 2025-07-15

---

## Test Description

### Purpose

Verify that the FabDummy plugin can be successfully installed from the official repository and is ready for use in testing FabSim3 core functionality.

### Scope

This test covers:
- Plugin repository cloning
- Plugin requirements installation
- Basic plugin loading verification

### Dependencies

- **Prerequisites:** FabSim3 properly configured, internet connection, git installed
- **Related Tests:** None (this is a prerequisite for other FabDummy tests)

---

## Test Environment

### System Requirements

- **Operating System:** Linux, macOS, Windows (WSL)
- **Python Version:** 3.8+
- **FabSim3 Version:** Latest

### Setup Steps

1. Ensure FabSim3 is properly installed and configured
2. Ensure internet connectivity for git clone operations
3. Verify plugin directory exists: `$FABSIM3_HOME/plugins/`

```bash
# Verify FabSim3 setup
cd $FABSIM3_HOME
fabsim localhost -h
```

---

## Test Execution

### Test Command(s)

```bash
# Primary test command
fabsim localhost install_plugin:FabDummy
```

### Test Steps

1. Navigate to FabSim3 directory
2. Execute the install_plugin command
3. Verify plugin directory was created
4. Check that plugin appears in available plugins list

### Input Data

- **Test Files:** None required
- **Configuration:** Standard FabSim3 configuration
- **Parameters:** Plugin name: FabDummy

---

## Expected Results

### Success Criteria

- Command exits with code 0
- Output contains "FabDummy plugin installed successfully"
- Plugin directory created at `plugins/FabDummy/`
- Plugin appears in `fabsim localhost -l plugins` output

### Expected Output

```
Installing FabDummy plugin...
Cloning into 'plugins/FabDummy'...
FabDummy plugin installed successfully.
```

### Expected Files/Directories

```
plugins/
└── FabDummy/
    ├── FabDummy.py
    ├── README.md
    └── requirements.txt
```

---

## Test Results

### Status: PASS

### Actual Output

```
Installing FabDummy plugin...
Cloning into 'plugins/FabDummy'...
FabDummy plugin installed successfully.
```

### Actual vs Expected

| Aspect | Expected | Actual | Match |
|--------|----------|---------|-------|
| Exit code | 0 | 0 | ✅ |
| Output contains | "FabDummy plugin installed successfully" | "FabDummy plugin installed successfully" | ✅ |
| Directory created | plugins/FabDummy/ | plugins/FabDummy/ | ✅ |

### Verification Steps

- [x] Command executed successfully (exit code 0)
- [x] Expected output messages present
- [x] Plugin directory created
- [x] No error messages in logs
- [x] Plugin files present

---

## Issues & Notes

### Known Issues

- None currently known

### Workarounds

- If network issues occur, retry the command
- For corporate networks, may need proxy configuration

### Notes

- This test should be run first in any FabSim3 testing sequence
- Plugin installation requires write permissions to plugins directory

---

## Automated Test Integration

### pytest Implementation

```python
@pytest.mark.parametrize(
    "execute_cmd,search_for,cnt",
    [
        (
            "fabsim localhost install_plugin:FabDummy",
            "FabDummy plugin installed successfully",
            1,
        ),
    ],
    indirect=["execute_cmd"],
    ids=["FabDummy installation"],
)
def test_fabdummy_installation(execute_cmd, search_for, cnt):
    cmd_output = execute_cmd
    assert len(re.findall(search_for, cmd_output)) == cnt
```

### CI/CD Integration

- [x] Test runs in GitHub Actions
- [x] Test included in regression suite
- [ ] Performance benchmarks (not applicable)

---

## Maintenance

### Review Schedule

- **Next Review:** 2025-10-15
- **Review Frequency:** Quarterly

### Update History

| Date | Author | Changes |
|------|--------|---------|
| 2025-07-15 | FabSim3 Team | Initial test case creation |

---

## Related Documentation

- [FabSim3 Plugin Documentation](plugins.md)
- [FabDummy Plugin Guide](https://github.com/djgroen/FabDummy)
- [Installation Guide](installation.md)

---

## Test Artifacts

### Logs

- `fabdummy_install.log` - Installation execution log
- `plugin_verification.log` - Plugin loading verification

### Screenshots

- Not applicable for command-line installation

### Performance Data

- Typical installation time: 10-30 seconds
- Network bandwidth usage: ~1-5 MB

---

## Quick Reference

### One-Line Test Summary

```bash
# Test: Install FabDummy plugin
fabsim localhost install_plugin:FabDummy && echo "PASS" || echo "FAIL"
```

### Common Issues

1. **Issue:** "Permission denied" error
   **Solution:** Check write permissions to plugins directory

2. **Issue:** "Network connection failed"
   **Solution:** Verify internet connectivity and proxy settings

---

*Template Version: 1.0*
*Last Updated: 2025-07-15*
