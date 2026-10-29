"""Question 3 — SonarQube for IDE (SonarLint) code review.

# Question 3 — SonarQube for IDE (SonarLint) code review

## Review scope

The broader pharmacy review covered these three first-party files:

1. `pharmacy/views/purchases.py`
2. `pharmacy/views/sales.py`
3. `pharmacy/views/inventory.py`

The recorded standalone SonarPython analysis was run against
`pharmacy/views/purchases.py`. The other two files were inspected as related
pharmacy code, but no separate Sonar diagnostic output for them was recorded.
Therefore this report does not claim that SonarLint returned zero findings
for `sales.py` or `inventory.py`.

**Tool:** SonarQube for IDE for VS Code 6.2.0  
**Python analyzer:** SonarPython 5.32.0.37250  
**Mode:** Standalone local analysis; no SonarQube Server or Cloud connection

## Finding 1 — Unnecessary f-string

**File:** `pharmacy/views/purchases.py`  
**Rule:** `python:S3457`  
**Explanation:** The success message contains no replacement fields, so the
`f` prefix is unnecessary. Removing it keeps the displayed message exactly
the same.

### Original relevant code

```python
messages.success(request, f'Purchase order created successfully.')
```

### Refactored relevant code

```python
messages.success(request, 'Purchase order created successfully.')
```

**Result:** Fixed. The recorded follow-up analysis no longer reported
`python:S3457`.

## Finding 2 — Cognitive complexity in receiving workflow

**File:** `pharmacy/views/purchases.py`  
**Rule:** `python:S3776`  
**Reported result:** `receive_purchase` has cognitive complexity 18, above the
configured threshold of 15.

This finding is documented but not refactored here. The receiving workflow
changes purchase status, received quantities, and medicine stock. A safe
refactor needs focused tests for invalid quantities, stock updates, and
failure/rollback behavior. Showing invented “after” code without those tests
would be misleading.

### Original relevant code

```python
@pharmacist_required
def receive_purchase(request, pk):
    """View for receiving purchase orders"""
    purchase = get_object_or_404(Purchase, pk=pk)

    if request.method == 'POST':
        if purchase.status != Purchase.PENDING:
            messages.error(
                request,
                'This purchase order has already been processed.'
            )
            return redirect('purchase_detail', pk=purchase.id)

        try:
            purchase.status = Purchase.RECEIVED
            purchase.save()

            for item in purchase.items.all():
                received_qty = int(
                    request.POST.get(f'received_qty_{item.id}', 0)
                )
                item.received_quantity = received_qty
                item.save()

                if item.medicine:
                    medicine = item.medicine
                    medicine.stock_quantity += received_qty

                    if item.expiry_date:
                        medicine.expiry_date = item.expiry_date
                    if item.batch_number:
                        medicine.batch_number = item.batch_number

                    medicine.save()

            messages.success(
                request,
                'Purchase order received successfully.'
            )
            return redirect('purchase_detail', pk=purchase.id)

        except Exception as e:
            messages.error(
                request,
                f'Error receiving purchase order: {str(e)}'
            )

    context = {
        'purchase': purchase,
        'items': purchase.items.all(),
        'active_tab': 'purchases'
    }

    return render(request, 'pharmacy/receive_purchase.html', context)
```

### Refactored relevant code

No refactored code is presented for this finding because it was deferred for
behavior-preserving tests. This is intentionally different from the fixed
`python:S3457` finding above.

## Findings and review coverage

| File | Review status | Result recorded |
|---|---|---|
| `pharmacy/views/purchases.py` | Analyzed with standalone SonarPython | Two findings before the fix; one remains after it |
| `pharmacy/views/sales.py` | Included in broader source inspection | No separate Sonar diagnostic output is recorded in this report |
| `pharmacy/views/inventory.py` | Included in broader source inspection | No separate Sonar diagnostic output is recorded in this report |

The file-level analysis result is not a claim that the entire hospital
system is defect-free. It records the files and findings actually reviewed.
'''


## Inventory file review — interpolated messages

**File:** `pharmacy/views/inventory.py`

The inventory view was inspected for the same unnecessary-f-string issue.
These messages interpolate `item_code` or `item.name`, so their `f` prefixes
are required to produce the intended messages. No Sonar diagnostic for this
file was recorded, and these lines are shown as reviewed code, not as a fix.

### Original relevant code

```python
if dup.exists():
    return f'Item code "{item_code}" is already in use.'

item.save()
messages.success(request, f'Added "{item.name}" to the hospital inventory.')
```

### Refactored relevant code

```python
if dup.exists():
    return f'Item code "{item_code}" is already in use.'

item.save()
messages.success(request, f'Added "{item.name}" to the hospital inventory.')
```

**Result:** No change. Both f-strings contain replacement fields and are
needed. This comparison documents why these inventory messages should not
receive the same edit as the purchase-success message.

## Findings and review coverage

| File | Review status | Result recorded |
|---|---|---|
| `pharmacy/views/purchases.py` | Analyzed with standalone SonarPython | Two findings before the fix; one remains after it |
| `pharmacy/views/sales.py` | Included in broader source inspection | No separate Sonar diagnostic output is recorded in this report |
| `pharmacy/views/inventory.py` | Source-inspected; relevant f-strings compared before and after | No separate Sonar diagnostic output is recorded; interpolated f-strings were retained |

The file-level analysis result is not a claim that the entire hospital
system is defect-free. It records the files and findings actually reviewed.
'''
