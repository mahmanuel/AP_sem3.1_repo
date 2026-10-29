
"""Question 3: SonarLint finding and the relevant before/after code only.

The production fix is in pharmacy/views/purchases.py. This file is a
presentation reference and is not imported by the application.
"""


RULE = "python:S3457"
FINDING = "The f-string has no replacement fields."
ANALYSIS_RESULT = (
    "Two findings before the change; one remained after the change."
)
REMAINING_FINDING = (
    "python:S3776: receive_purchase has cognitive complexity 18 "
    "(configured limit 15); deferred for a separate behavior-preserving refactor."
)

BEFORE = "messages.success(request, f'Purchase order created successfully.')"
AFTER = "messages.success(request, 'Purchase order created successfully.')"


if __name__ == "__main__":
    print(f"Rule: {RULE}")
    print(f"Finding: {FINDING}")
    print("\nBefore:")
    print(BEFORE)
    print("\nAfter:")
    print(AFTER)
    print(f"\nResult: {ANALYSIS_RESULT}")
    print(f"Remaining finding: {REMAINING_FINDING}")

#SonarLint rule python:S3457: remove the f-string prefix because there are no
# replacement fields.

# Before:
BEFORE = """messages.success(
    request, f'Purchase order created successfully.'
)"""

# After:
AFTER = """messages.success(
    request, 'Purchase order created successfully.'
)"""