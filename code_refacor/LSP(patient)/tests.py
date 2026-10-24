from django.test import SimpleTestCase

from patient.forms.admissions import (
    EmergencyAdmissionForm,
    PatientAdmissionForm,
    _AdmissionFormBehavior,
)


class AdmissionFormSubstitutionTests(SimpleTestCase):
    def test_emergency_form_is_not_a_regular_admission_form_subtype(self):
        self.assertFalse(issubclass(EmergencyAdmissionForm, PatientAdmissionForm))

    def test_forms_share_behavior_but_keep_distinct_fields(self):
        self.assertTrue(issubclass(PatientAdmissionForm, _AdmissionFormBehavior))
        self.assertTrue(issubclass(EmergencyAdmissionForm, _AdmissionFormBehavior))
        self.assertIn('admission_type', PatientAdmissionForm.base_fields)
        self.assertNotIn('admission_type', EmergencyAdmissionForm.base_fields)
        self.assertIn('notes', PatientAdmissionForm.base_fields)
        self.assertNotIn('notes', EmergencyAdmissionForm.base_fields)
