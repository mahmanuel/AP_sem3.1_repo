# SonarQube for IDE Analysis Results

This document records the Question 3 automated review of the pharmacy
purchase view. SonarLint is the former name of the **SonarQube for IDE**
extension for VS Code.

## Analysis setup

- **Tool:** SonarQube for IDE (SonarLint) VS Code extension 6.2.0
- **Python analyzer:** SonarPython 5.32.0.37250
- **Analyzed file:** [`pharmacy/views/purchases.py`](../pharmacy/views/purchases.py)
- **Analysis mode:** Standalone, local analysis; no SonarQube Server or Cloud
  connection
- **Rules:** Default standalone rules
- **Telemetry:** Disabled

The analysis ran locally using the extension's bundled Python analyzer.
Project source was not sent to SonarQube Server or SonarQube Cloud.

## Findings before the fix

| Rule | Location | Finding | Decision |
|---|---|---|---|
| `python:S3457` | `pharmacy/views/purchases.py`, line 79 | An f-string has no replacement fields. | Fixed |
| `python:S3776` | `pharmacy/views/purchases.py`, line 114 | `receive_purchase` has cognitive complexity 18, exceeding the configured threshold of 15. | Deferred |

## Finding fixed: unnecessary f-string

The purchase-success message did not interpolate any values. The `f` prefix
was unnecessary.

### Before

```python
messages.success(request, f'Purchase order created successfully.')
```

### After

```python
messages.success(request, 'Purchase order created successfully.')
```

This change preserves the displayed message and removes the Sonar rule
violation.

## Finding deferred: complex receiving workflow

SonarQube for IDE also reported that `receive_purchase` is more complex than
the default threshold.

**Reported finding:** Cognitive complexity 18; allowed threshold 15.

This finding was assessed as valid but deferred. `receive_purchase` is the
separate workflow that receives a purchase order and updates medicine stock;
it was outside the purchase-creation change made for Question 2. A later
refactor should include tests for received quantities, stock updates,
invalid input, and rollback behavior before changing this workflow.

## Re-analysis

The same file was analyzed again after the fix:

- **Before:** 2 findings
- **After:** 1 finding
- `python:S3457`: resolved
- `python:S3776`: remains and is deferred

The Django system check and both focused pharmacy purchase-service tests
passed. The test run used the previously documented test-only migration
override because of a pre-existing duplicate-table migration issue; no
project migrations were changed.


