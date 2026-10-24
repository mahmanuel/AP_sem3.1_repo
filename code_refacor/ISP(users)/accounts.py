#Case 5 — ISP: Interface Segregation Principle
#This completes one example for each of the five SOLID principles: SRP, OCP, LSP, ISP, and DIP.

#For this ISP example, the staff profile form is the interface a staff member uses to update their profile. It included fields for several different roles, even though each person should only need fields relevant to their own role.

#Question 1 — Identify and explain a code issue
#Affected component: UserUpdateForm in users/forms/accounts.py.

#Principle: ISP. Clients should not have to depend on an interface containing fields they do not use. The profile form included doctor, nurse, and pharmacist fields for every user, then hid the irrelevant fields in the interface.

#Original relevant logic:


class UserUpdateForm(forms.ModelForm):
    """Form for updating user profile"""

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'phone_number', 'address', 'profile_picture',
            'qualification', 'years_of_experience',
            # Doctor fields
            'specialization', 'doctor_license_number', 'is_available',
            # Nurse fields
            'nurse_license_number', 'nursing_specialty',
            # Pharmacist fields
            'pharmacist_license_number', 'pharmacy_certification',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Other shared widget setup...

        if self.instance and self.instance.pk:
            if self.instance.role != User.DOCTOR:
                doctor_fields = [
                    'specialization',
                    'doctor_license_number',
                    'is_available',
                ]
                for field_name in doctor_fields:
                    self.fields[field_name].widget = forms.HiddenInput()

            if self.instance.role != User.NURSE:
                nurse_fields = [
                    'nurse_license_number',
                    'nursing_specialty',
                ]
                for field_name in nurse_fields:
                    self.fields[field_name].widget = forms.HiddenInput()

            if self.instance.role != User.PHARMACIST:
                pharmacist_fields = [
                    'pharmacist_license_number',
                    'pharmacy_certification',
                ]
                for field_name in pharmacist_fields:
                    self.fields[field_name].widget = forms.HiddenInput()



#Each user’s form object still contained every role’s fields; hiding a widget only changes how a field is displayed. 
# That makes the form’s interface broader than the needs of the person using it.





#Question 2 — Refactor while preserving behavior

#Refactored approach: Keep shared profile fields for everyone and include only the professional fields relevant to the user’s role. 
# The role-to-field mapping is defined in the form; irrelevant fields are removed instead of hidden.



class UserUpdateForm(forms.ModelForm):
    """Form for updating user profile"""

    ROLE_SPECIFIC_FIELDS = {
        User.DOCTOR: {
            'specialization',
            'doctor_license_number',
            'is_available',
        },
        User.NURSE: {
            'nurse_license_number',
            'nursing_specialty',
        },
        User.PHARMACIST: {
            'pharmacist_license_number',
            'pharmacy_certification',
        },
    }

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'phone_number', 'address', 'profile_picture',
            'qualification', 'years_of_experience',
            'specialization', 'doctor_license_number', 'is_available',
            'nurse_license_number', 'nursing_specialty',
            'pharmacist_license_number', 'pharmacy_certification',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Other shared widget setup...

        if self.instance and self.instance.pk:
            allowed_fields = self.ROLE_SPECIFIC_FIELDS.get(
                self.instance.role,
                set(),
            )
            for role_fields in self.ROLE_SPECIFIC_FIELDS.values():
                for field_name in role_fields - allowed_fields:
                    self.fields.pop(field_name)




#The actual update is in users/forms/accounts.py. 
# Admin account-management forms are unchanged: admins need to edit details for multiple staff roles, unlike a staff member editing their own profile.

