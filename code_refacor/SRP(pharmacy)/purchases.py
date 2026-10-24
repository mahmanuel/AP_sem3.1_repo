#Case 2 — SRP: Single Responsibility Principle
#For this example, we’ll look at creating a pharmacy purchase order. The view used to both handle the web request and create database records. The refactor separates those jobs: the view handles HTTP and form data; a service handles the purchase-order workflow.

#Question 1 — Identify and explain a code issue
#Affected component: add_purchase in pharmacy/views/purchases.py.

#Principle: SRP. The function had two reasons to change: changes to the web form or response, and changes to how purchase orders and their items are saved.

#Original relevant logic:

@pharmacist_required
def add_purchase(request):
    """View for creating a new purchase order"""
    if request.method == 'POST':
        # Process main purchase data
        supplier_id = request.POST.get('supplier')
        purchase_date = request.POST.get('purchase_date')
        notes = request.POST.get('notes')

        try:
            supplier = Supplier.objects.get(id=supplier_id)

            # Create purchase
            purchase = Purchase(
                supplier=supplier,
                purchase_date=purchase_date,
                status=Purchase.PENDING,
                payment_status='Unpaid',
                notes=notes,
                created_by=request.user
            )
            purchase.save()

            # Process purchase items
            medicine_ids = request.POST.getlist('medicine_id')
            quantities = request.POST.getlist('quantity')
            unit_prices = request.POST.getlist('unit_price')
            expiry_dates = request.POST.getlist('expiry_date')
            batch_numbers = request.POST.getlist('batch_number')

            for i in range(len(medicine_ids)):
                if medicine_ids[i] and quantities[i] and unit_prices[i]:
                    medicine = MedicineItem.objects.get(id=medicine_ids[i])

                    item = PurchaseItem(
                        purchase=purchase,
                        medicine=medicine,
                        quantity=quantities[i],
                        unit_price=unit_prices[i],
                        batch_number=batch_numbers[i] if batch_numbers[i] else None
                    )

                    if expiry_dates[i]:
                        item.expiry_date = expiry_dates[i]

                    item.save()

            messages.success(request, 'Purchase order created successfully.')
            return redirect('purchase_detail', pk=purchase.id)

        except Exception as e:
            messages.error(request, f'Error creating purchase order: {str(e)}')

    # Get suppliers and medicines for the form
    suppliers = Supplier.objects.filter(is_active=True)
    medicines = MedicineItem.objects.filter(is_active=True)

    context = {
        'suppliers': suppliers,
        'medicines': medicines,
        'active_tab': 'purchases'
    }

    return render(request, 'pharmacy/add_purchase.html', context)

#Why it matters: Form handling and database persistence change for different reasons. Combining them makes the view harder to maintain and the purchase workflow harder to test separately. 
# Also, if creating an item failed partway through, the original code could leave a purchase order with only some of its items saved.







#Question 2 — Refactor while preserving behavior
#Refactored view: It still reads the submitted form, displays messages, redirects on success, and renders the form. 
# It now delegates purchase creation to the service.


@pharmacist_required
def add_purchase(request):
    """View for creating a new purchase order"""
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        purchase_date = request.POST.get('purchase_date')
        notes = request.POST.get('notes')

        try:
            medicine_ids = request.POST.getlist('medicine_id')
            quantities = request.POST.getlist('quantity')
            unit_prices = request.POST.getlist('unit_price')
            expiry_dates = request.POST.getlist('expiry_date')
            batch_numbers = request.POST.getlist('batch_number')

            items = []
            for i in range(len(medicine_ids)):
                if medicine_ids[i] and quantities[i] and unit_prices[i]:
                    items.append({
                        'medicine_id': medicine_ids[i],
                        'quantity': quantities[i],
                        'unit_price': unit_prices[i],
                        'batch_number': batch_numbers[i] if batch_numbers[i] else None,
                        'expiry_date': expiry_dates[i],
                    })

            purchase = services.create_purchase_order(
                supplier_id=supplier_id,
                purchase_date=purchase_date,
                notes=notes,
                created_by=request.user,
                items=items,
            )
            messages.success(request, 'Purchase order created successfully.')
            return redirect('purchase_detail', pk=purchase.id)

        except Exception as e:
            messages.error(request, f'Error creating purchase order: {str(e)}')

    suppliers = Supplier.objects.filter(is_active=True)
    medicines = MedicineItem.objects.filter(is_active=True)

    context = {
        'suppliers': suppliers,
        'medicines': medicines,
        'active_tab': 'purchases'
    }

    return render(request, 'pharmacy/add_purchase.html', context)






#New service: This function owns the database workflow. 
# It creates the order and items within one transaction, then updates the purchase total after its items have been saved. It’s in pharmacy/services.py.


def create_purchase_order(*, supplier_id, purchase_date, notes, created_by, items):
    """Create a purchase order and its medicine items atomically."""
    with transaction.atomic():
        supplier = Supplier.objects.get(pk=supplier_id)
        purchase = Purchase.objects.create(
            supplier=supplier,
            purchase_date=purchase_date,
            status=Purchase.PENDING,
            payment_status='Unpaid',
            notes=notes,
            created_by=created_by,
        )

        for item in items:
            medicine = MedicineItem.objects.get(pk=item['medicine_id'])
            PurchaseItem.objects.create(
                purchase=purchase,
                medicine=medicine,
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                batch_number=item['batch_number'],
                expiry_date=item['expiry_date'] or None,
            )

        purchase.save(update_fields=['total_amount', 'updated_at'])
        return purchase