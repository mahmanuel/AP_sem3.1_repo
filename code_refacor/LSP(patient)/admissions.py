#Case 4 — LSP: Liskov Substitution Principle
#LSP says a subtype should be usable wherever its parent type is expected without breaking the parent’s contract.

#Question 1 — Identify and explain a code issue
#Affected component: The relationship between the regular and emergency admission forms in patient/forms/admissions.py.

#Principle: LSP. EmergencyAdmissionForm inherits from PatientAdmissionForm, but deliberately removes fields that the regular form provides. That makes the emergency form a different interface, even though the inheritance says it is a kind of regular admission form.

#Original relevant logic:

class PatientAdmissionForm(forms.ModelForm):
    class Meta:
        model = PatientAdmission
        fields = [
            'patient',
            'admitting_doctor',
            'bed',
            'admission_type',
            'primary_diagnosis',
            'notes',
            'is_critical',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Shared patient, doctor, and bed setup...


class EmergencyAdmissionForm(PatientAdmissionForm):
    class Meta(PatientAdmissionForm.Meta):
        fields = [
            'patient',
            'admitting_doctor',
            'bed',
            'primary_diagnosis',
            'is_critical',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_critical'].initial = True
        # Emergency-specific doctor and bed setup...



#The emergency form omits admission_type and notes, which the regular form includes. 
# The emergency view uses this specialized form directly, so this is a substitutability/design risk rather than a currently demonstrated runtime failure: 
# if generic code expects a PatientAdmissionForm, the emergency subtype does not provide the same fields.








#Question 2 — Refactor while preserving behavior

#Refactored approach: Both forms now share setup and validation through _AdmissionFormBehavior, a mixin. 
# They are separate ModelForm classes rather than one form inheriting from the other. This keeps their distinct field lists while sharing common behavior.


class _AdmissionFormBehavior:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Shared patient, doctor, and bed setup...

    def clean(self):
        cleaned_data = super().clean()
        # Shared admission validation...
        return cleaned_data


class PatientAdmissionForm(_AdmissionFormBehavior, forms.ModelForm):
    class Meta:
        model = PatientAdmission
        fields = [
            'patient',
            'admitting_doctor',
            'bed',
            'admission_type',
            'primary_diagnosis',
            'notes',
            'is_critical',
        ]


class EmergencyAdmissionForm(_AdmissionFormBehavior, forms.ModelForm):
    class Meta(PatientAdmissionForm.Meta):
        fields = [
            'patient',
            'admitting_doctor',
            'bed',
            'primary_diagnosis',
            'is_critical',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_critical'].initial = True
        # Emergency-specific doctor and bed setup...




#The shared setup and validation remain in patient/forms/admissions.py. 
# The emergency view still receives its simplified form, and the regular form retains its original fields.     