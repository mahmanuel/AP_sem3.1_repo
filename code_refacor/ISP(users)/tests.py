from django.test import SimpleTestCase

from users.forms.accounts import UserUpdateForm
from users.models import User


class UserUpdateFormInterfaceTests(SimpleTestCase):
    def get_form(self, role):
        return UserUpdateForm(instance=User(pk=1, role=role))

    def test_doctor_form_contains_only_doctor_specific_fields(self):
        form = self.get_form(User.DOCTOR)

        self.assertIn('specialization', form.fields)
        self.assertIn('doctor_license_number', form.fields)
        self.assertIn('is_available', form.fields)
        self.assertNotIn('nurse_license_number', form.fields)
        self.assertNotIn('pharmacist_license_number', form.fields)

    def test_nurse_form_contains_only_nurse_specific_fields(self):
        form = self.get_form(User.NURSE)

        self.assertIn('nurse_license_number', form.fields)
        self.assertIn('nursing_specialty', form.fields)
        self.assertNotIn('specialization', form.fields)
        self.assertNotIn('pharmacist_license_number', form.fields)

    def test_pharmacist_form_contains_only_pharmacist_specific_fields(self):
        form = self.get_form(User.PHARMACIST)

        self.assertIn('pharmacist_license_number', form.fields)
        self.assertIn('pharmacy_certification', form.fields)
        self.assertNotIn('specialization', form.fields)
        self.assertNotIn('nurse_license_number', form.fields)

    def test_other_roles_do_not_get_professional_role_fields(self):
        for role in (User.ADMIN, User.RECEPTIONIST):
            with self.subTest(role=role):
                form = self.get_form(role)

                for role_fields in UserUpdateForm.ROLE_SPECIFIC_FIELDS.values():
                    self.assertTrue(role_fields.isdisjoint(form.fields))

    def test_common_profile_fields_remain_available(self):
        form = self.get_form(User.NURSE)

        for field_name in ('username', 'first_name', 'last_name', 'email', 'phone_number'):
            self.assertIn(field_name, form.fields)
