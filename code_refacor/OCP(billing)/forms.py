#Case 3 — OCP: Open/Closed Principle
#We’ve now covered DIP, SRP, and OCP. This example is from the billing payment form.

#Question 1 — Identify and explain a code issue
#Affected component: Payment-method validation in billing/forms.py.

#Principle: OCP. Code should be open to extension but closed to repeated changes in its existing behavior.

#Original relevant logic:

def clean(self):
    cleaned_data = super().clean()
    payment_method = cleaned_data.get('payment_method')
    is_insurance_payment = cleaned_data.get('is_insurance_payment')
    reference_number = cleaned_data.get('reference_number')
    card_last_digits = cleaned_data.get('card_last_digits')

    # Validate payment method specific fields
    if payment_method == Bill.CARD and not card_last_digits:
        self.add_error(
            'card_last_digits',
            'Last 4 digits are required for card payments'
        )

    if payment_method in [
        Bill.CARD,
        Bill.BANK_TRANSFER,
        Bill.MOBILE_PAYMENT
    ] and not reference_number:
        self.add_error(
            'reference_number',
            f'Reference number is required for '
            f'{dict(Bill.PAYMENT_METHOD_CHOICES)[payment_method]} payments'
        )

    if is_insurance_payment:
        insurance_company = cleaned_data.get('insurance_company')
        insurance_approval_code = cleaned_data.get('insurance_approval_code')

        if not insurance_company:
            self.add_error(
                'insurance_company',
                'Insurance company is required for insurance payments'
            )

        if not insurance_approval_code:
            self.add_error(
                'insurance_approval_code',
                'Approval code is required for insurance payments'
            )

    return cleaned_data


#When adding a payment method with its own required fields, developers would need to edit this existing validation logic and add more conditions. 
# That makes the method harder to extend without changing its existing control flow.







#Question 2 — Refactor while preserving behavior

#Refactored configuration: Payment-method requirements are declared as data on PaymentForm. 
# For a new payment type, its required fields can be added to this mapping while leaving the validation loop unchanged.


METHOD_REQUIRED_FIELDS = {
    Bill.CARD: {
        'card_last_digits': 'Last 4 digits are required for card payments',
        'reference_number': None,
    },
    Bill.BANK_TRANSFER: {
        'reference_number': None,
    },
    Bill.MOBILE_PAYMENT: {
        'reference_number': None,
    },
}




#Refactored validation logic:


def clean(self):
    cleaned_data = super().clean()
    payment_method = cleaned_data.get('payment_method')
    is_insurance_payment = cleaned_data.get('is_insurance_payment')

    method_label = dict(Bill.PAYMENT_METHOD_CHOICES).get(
        payment_method,
        payment_method
    )
    required_fields = self.METHOD_REQUIRED_FIELDS.get(payment_method, {})

    for field_name, error_message in required_fields.items():
        if not cleaned_data.get(field_name):
            self.add_error(
                field_name,
                error_message
                or f'Reference number is required for {method_label} payments'
            )

    if is_insurance_payment:
        insurance_company = cleaned_data.get('insurance_company')
        insurance_approval_code = cleaned_data.get('insurance_approval_code')

        if not insurance_company:
            self.add_error(
                'insurance_company',
                'Insurance company is required for insurance payments'
            )

        if not insurance_approval_code:
            self.add_error(
                'insurance_approval_code',
                'Approval code is required for insurance payments'
            )

    return cleaned_data



#What changed: The repeated method-specific conditions became a configuration mapping plus one reusable validation loop. 
# Existing requirements remain: card payments require the last four digits and a reference number; bank transfers and mobile payments require a reference number. 
# Cash payments remain unaffected, and the existing insurance-checkbox validation is unchanged.

