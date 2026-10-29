# Semester Project — Question 4: Evaluate the final design

## Issue found in the improved project

**Component:** Receiving a pharmacy purchase order in
[`pharmacy/views/purchases.py`](../pharmacy/views/purchases.py).

The Question 2 refactor moved purchase-order creation into a service, but the
separate receiving view still changed the order status before it had processed
all received quantities. If a submitted quantity was malformed or a later
stock update failed, the view displayed an error after some database changes
had already been saved. The order could therefore say “received” while its
items or medicine stock reflected only part of the receipt. The HTML form's
minimum and maximum are helpful for normal users, but they are not server-side
validation.

**Course principle:** Transactional integrity and the contract of an operation.
A purchase receipt should have an all-or-nothing outcome: either every valid
item quantity, stock update, and order status change is saved, or none is.
Moving the operation into the pharmacy service also follows SRP by keeping
business-state changes out of the request/response view.

## Original relevant code

```python
@pharmacist_required
def receive_purchase(request, pk):
    """View for receiving purchase orders"""
    purchase = get_object_or_404(Purchase, pk=pk)

    if request.method == 'POST':
        if purchase.status != Purchase.PENDING:
            messages.error(request, 'This purchase order has already been processed.')
            return redirect('purchase_detail', pk=purchase.id)

        try:
            purchase.status = Purchase.RECEIVED
            purchase.save()

            for item in purchase.items.all():
                received_qty = int(request.POST.get(f'received_qty_{item.id}', 0))
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

            messages.success(request, 'Purchase order received successfully.')
            return redirect('purchase_detail', pk=purchase.id)

        except Exception as e:
            messages.error(request, f'Error receiving purchase order: {str(e)}')

    context = {
        'purchase': purchase,
        'items': purchase.items.all(),
        'active_tab': 'purchases'
    }

    return render(request, 'pharmacy/receive_purchase.html', context)
```

## Improvement

The view now collects the submitted values and delegates the state transition
to `receive_purchase_order`. It reports invalid input to the user and only
shows success after the service commits.

### Refactored view

```python
@pharmacist_required
def receive_purchase(request, pk):
    """View for receiving purchase orders"""
    purchase = get_object_or_404(Purchase, pk=pk)

    if request.method == 'POST':
        try:
            received_quantities = {
                item.id: request.POST.get(f'received_qty_{item.id}')
                for item in purchase.items.all()
            }
            services.receive_purchase_order(
                purchase_id=purchase.id,
                received_quantities=received_quantities,
            )
        except ValueError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, 'Purchase order received successfully.')
            return redirect('purchase_detail', pk=purchase.id)

    context = {
        'purchase': purchase,
        'items': purchase.items.all(),
        'active_tab': 'purchases'
    }

    return render(request, 'pharmacy/receive_purchase.html', context)
```

### Refactored business operation

```python
def receive_purchase_order(*, purchase_id, received_quantities):
    """Receive a pending purchase and update its medicine stock atomically.

    ``received_quantities`` maps purchase-item IDs to submitted quantities.
    Raises ValueError if the order is not pending or a quantity is invalid.
    """
    with transaction.atomic():
        purchase = Purchase.objects.select_for_update().get(pk=purchase_id)
        if purchase.status != Purchase.PENDING:
            raise ValueError("Only pending purchase orders can be received.")

        items = list(
            PurchaseItem.objects.filter(purchase=purchase).order_by('pk')
        )
        quantities = []
        for item in items:
            try:
                received_quantity = int(received_quantities[item.pk])
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(
                    f"Enter a whole-number received quantity for item {item.pk}."
                ) from error

            if not 0 <= received_quantity <= item.quantity:
                raise ValueError(
                    f"Received quantity for item {item.pk} must be between "
                    f"0 and {item.quantity}."
                )
            quantities.append((item, received_quantity))

        for item, received_quantity in quantities:
            item.received_quantity = received_quantity
            item.save(update_fields=['received_quantity'])

            if item.medicine_id:
                medicine = MedicineItem.objects.select_for_update().get(
                    pk=item.medicine_id
                )
                medicine.stock_quantity += received_quantity
                update_fields = ['stock_quantity', 'updated_at']
                if item.expiry_date:
                    medicine.expiry_date = item.expiry_date
                    update_fields.append('expiry_date')
                if item.batch_number:
                    medicine.batch_number = item.batch_number
                    update_fields.append('batch_number')
                medicine.save(update_fields=update_fields)

        purchase.status = Purchase.RECEIVED
        purchase.save(update_fields=['status', 'updated_at'])
        return purchase
```

## Effect and verification

- The service validates that an order is pending.
- Each submitted quantity must be a whole number between zero and the ordered
  quantity, inclusive. Invalid or missing quantities are rejected before any
  receipt data is changed.
- The order status, received quantities, and medicine stock updates run inside
  one database transaction. A failure during an update rolls back the whole
  receipt.
- The view shows an error for invalid quantities and displays success only
  after the service returns successfully.

**Tests added:** valid partial receipt updates the received quantity, stock,
batch, and expiry; malformed, negative, and over-ordered quantities are
rejected at the service and view; a simulated stock-update failure rolls
back item quantities, stock, and order status.

**Test result:** Six focused pharmacy purchase/receiving tests passed.
`manage.py check` also passed. The normal test command encounters the
project's pre-existing duplicate `ContactInquiry` migration; the focused test
run used a temporary, test-only `MIGRATION_MODULES={'website': None}` override
and did not modify project migrations.

## Remaining limitations and next improvement

The current receiving form and service support medicine purchase items. The
model also allows a purchase item to reference a non-medicine `InventoryItem`,
but this receiving path does not yet update that inventory's stock. The next
improvement should extend the receiving form and service to handle both item
types, with tests ensuring the correct inventory is updated atomically.
