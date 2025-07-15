# FabSim3 Testing Template

This document provides a standardized template for documenting tests in FabSim3. Use this template to ensure consistent, clear, and comprehensive test documentation.

## Test Documentation Template

### Test ID: [UNIQUE_TEST_ID]

**Test Name:** [Brief descriptive name of the test]

**Test Category:** [e.g., Installation, Core Functionality, Plugin, Integration, Performance]

**Priority:** [High/Medium/Low]

**Author:** [Your name]

**Date Created:** [YYYY-MM-DD]

**Last Updated:** [YYYY-MM-DD]

---

## Test Description

### Purpose

[Clear explanation of what this test is designed to verify]

### Scope

[What aspects of FabSim3 does this test cover?]

### Dependencies

- **Prerequisites:** [List any required setup, plugins, or configurations]
- **Related Tests:** [Reference to other tests that should pass first]

---

## Test Environment

### System Requirements

- **Operating System:** [e.g., Linux, macOS, Windows]
- **Python Version:** [e.g., 3.8+]
- **FabSim3 Version:** [e.g., latest, v3.x.x]

### Setup Steps

1. [Step-by-step setup instructions]
2. [Include any configuration changes needed]
3. [List any test data or files required]

```bash
# Example setup commands (MODIFY PATH!)
cd /path/to/FabSim3
python configure_fabsim.py
# Additional setup commands...
```

---

## Test Execution

### Test Command(s)

```bash
# Primary test command
fabsim localhost [command]:[config_dir]

# Additional commands if needed
fabsim localhost [command]:[config_dir],[additional_command]
```

### Test Steps

1. [Detailed step-by-step execution]
2. [Include any manual verification steps]
3. [Note any timing considerations]

### Input Data

- **Test Files:** [List any required test files]
- **Configuration:** [Any specific settings needed]
- **Parameters:** [Command-line parameters or config values]

### Fetch Results

```bash
fabsim localhost fetch_results
```

## Expected Results

### Success Criteria

- [Specific output strings to look for]
- [Files that should be created]
- [System state changes expected]

### Expected Output

```bash
[Example of expected terminal output]
```

### Example of Expected Files/Directories

```bash
localhost_exe/FabSim/
├── config_files
│   └── dummy_test
│       ├── SWEEP
│       │   ├── d1
│       │   │   └── dummy.txt
│       │   ├── d2
│       │   │   └── dummy.txt
│       │   └── d3
│       │       └── dummy.txt
│       └── dummy.txt
├── results
│   ├── _localhost_1
│   │   ├── _localhost_1.sh
│   │   ├── dummy_test
│   │   │   └── dummy.txt
│   │   ├── env.log
│   │   ├── env.yml
│   │   └── out.txt
│   └── dummy_test_localhost_1
│       ├── dummy.txt
│       ├── dummy_test_localhost_1.sh
│       ├── env.log
│       ├── env.yml
│       └── out.txt
└── scripts
    ├── _localhost_1.sh
    └── dummy_test_localhost_1.sh
```

## Test Results

### Status: [PASS/FAIL/SKIP/PENDING]

### Actual Output

```bash
[Copy actual terminal output here]
```

### Actual vs Expected

| Aspect | Expected | Actual | Match |
|--------|----------|---------|-------|
| Exit code | 0 | 0 | ✓ |
| Output contains | "test completed" | "test completed" | ✓ |
| Files created | 3 files | 3 files | ✓ |

### Verification Steps

- [ ] Command executed successfully (exit code 0)
- [ ] Expected output messages present
- [ ] Required files created
- [ ] No error messages in logs
- [ ] System state as expected

---

## Issues & Notes

### Known Issues

- [List any known problems or limitations]

### Workarounds

- [Any temporary fixes or alternative approaches]

### Notes

- [Additional observations or context]

---

## Automated Test Integration

---

## Related Documentation

- [Link to relevant user guides]
- [Link to developer documentation]
- [Link to issue tracker entries]

---

## Quick Reference

### One-Line Test Summary

```bash
# Test: [brief description]
fabsim localhost [command]:[config_dir] && echo "PASS" || echo "FAIL"
```

### Common Issues

1. **Issue:** [Common problem]
   **Solution:** [Quick fix]

2. **Issue:** [Another common problem]
   **Solution:** [Quick fix]

---

*Template Version: 1.0*
*Last Updated: 2025-07-15*
