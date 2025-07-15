# FabSim3 Testing Documentation Guide

This guide explains how to use the FabSim3 testing template to create standardized test documentation.

## Overview

The FabSim3 testing template provides a consistent structure for documenting tests, making it easier to:

- **Maintain Test Quality:** Ensure all tests follow the same documentation standards
- **Improve Test Coverage:** Identify gaps in testing through systematic documentation
- **Facilitate Reviews:** Standardized format makes code reviews more efficient
- **Onboard Contributors:** Clear template helps new contributors document tests properly

## Using the Template

### 1. Choose the Right Template

- **Main Template:** Use `testing_template.md` for comprehensive test documentation
- **Quick Tests:** For simple verification tests, you can use abbreviated sections
- **Example Reference:** See `fabdummy_installation_test.md` for a complete example

### 2. Fill Out Required Sections

#### Essential Sections (Always Required)

- **Test ID:** Unique identifier (e.g., CORE-001, PLUGIN-FABDUMMY-001)
- **Test Name:** Clear, descriptive name
- **Test Description:** What the test verifies
- **Test Command(s):** Exact commands to run
- **Expected Results:** What should happen
- **Test Results:** Actual outcome

#### Optional Sections (Use When Applicable)

- **Test Environment:** For environment-specific tests
- **Setup Steps:** For tests requiring special setup
- **Issues & Notes:** For known limitations or special considerations
- **Automated Test Integration:** For tests that should be automated

### 3. Test ID Conventions

Use the following format: `[CATEGORY]-[COMPONENT]-[NUMBER]`

Examples:

- `CORE-001` - Core functionality test #1
- `PLUGIN-FABDUMMY-001` - FabDummy plugin test #1
- `INSTALL-001` - Installation test #1
- `PERF-001` - Performance test #1

### 4. Test Categories

- **CORE:** Core FabSim3 functionality
- **PLUGIN:** Plugin-specific tests
- **INSTALL:** Installation and setup tests
- **CONFIG:** Configuration tests
- **PERF:** Performance tests
- **INTEGRATION:** Integration tests
- **REGRESSION:** Regression tests

## Creating Test Documentation

### Step 1: Copy the Template

```bash
# Create a new test document
cp testing_template.md docs/test_cases/my_new_test.md
```

### Step 2: Fill in the Details

1. **Start with the header information:**
   - Assign a unique Test ID
   - Give it a descriptive name
   - Set the appropriate category and priority

2. **Write the test description:**
   - Clearly explain what the test verifies
   - Define the scope and any dependencies

3. **Document the test execution:**
   - Provide exact commands
   - List all required steps
   - Specify expected outputs

4. **Record the results:**
   - Document actual vs expected outcomes
   - Mark as PASS/FAIL/SKIP
   - Note any issues or observations

### Step 3: Integration with Automated Tests

For tests that can be automated, add pytest code:

```python
@pytest.mark.parametrize(
    "execute_cmd,search_for,cnt",
    [
        (
            "fabsim localhost your_command",
            "expected_output_string",
            1,
        ),
    ],
    indirect=["execute_cmd"],
    ids=["your_test_id"],
)
def test_your_function(execute_cmd, search_for, cnt):
    cmd_output = execute_cmd
    assert len(re.findall(search_for, cmd_output)) == cnt
```

## Best Practices

### Documentation Standards

1. **Be Specific:** Use exact command syntax and expected outputs
2. **Be Complete:** Include all necessary setup and teardown steps
3. **Be Consistent:** Follow the template structure
4. **Be Clear:** Write for someone who's never seen the test before

### Test Design Principles

1. **Single Responsibility:** Each test should verify one specific aspect
2. **Repeatable:** Tests should produce consistent results
3. **Independent:** Tests shouldn't depend on the order of execution
4. **Fast:** Keep tests as quick as possible while being thorough

### Maintenance

1. **Regular Reviews:** Update tests when functionality changes
2. **Version Control:** Track changes to test documentation
3. **Deprecation:** Mark obsolete tests clearly
4. **Coverage:** Ensure critical paths are tested

## File Organization

```bash
docs/
├── testing_template.md          # Main template
├── testing_guide.md            # This guide
├── test_cases/                 # Individual test documentation
│   ├── core_functionality/
│   ├── plugin_tests/
│   ├── installation_tests/
│   └── performance_tests/
└── test_examples/              # Example test cases
    └── fabdummy_installation_test.md
```

## Integration with CI/CD

### GitHub Actions Integration

Tests documented with this template should be integrated into the CI/CD pipeline:

1. **Automated Execution:** Critical tests should run automatically
2. **Regression Testing:** All tests should run on major releases
3. **Performance Monitoring:** Performance tests should track metrics over time

### Test Reporting

Use the standardized format to generate test reports:

```bash
# Generate test report
pytest --html=test_report.html tests/
```

## Common Scenarios

### Scenario 1: Testing a New Feature

1. Create test documentation using the template
2. Implement the test in pytest
3. Add to CI/CD pipeline
4. Document in the main testing guide

### Scenario 2: Documenting Existing Tests

1. Review existing test code
2. Create documentation using the template
3. Fill in results from previous test runs
4. Identify gaps and improve coverage

### Scenario 3: Bug Verification

1. Create a specific test for the bug
2. Document the failing case
3. Fix the bug
4. Update documentation with passing results
5. Add to regression test suite

## Getting Help

- **Template Questions:** Review the example test cases
- **Test Implementation:** Check existing tests in `tests/`
- **CI/CD Integration:** See `.github/workflows/`
- **Documentation Issues:** Create an issue in the FabSim3 repository

---

*Guide Version: 1.0*
*Last Updated: 2025-07-15*
