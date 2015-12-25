from django.test import TestCase
from django.core.exceptions import ValidationError 
from billing import validators


class OneOfTests(TestCase):
    """
    """
    def test_valid(self):
        v = validators.OneOf("a", "B", "cee")
        v("a")
        v("B")
        v("cee")

    def test_invalid(self):
        v = validators.OneOf("a", "B", "cee")
        with self.assertRaises(ValidationError):
            v("A")


class IsRucTests(TestCase):
    def setUp(self):
        self.v = validators.IsRuc

    def test_valid_ruc(self):
        self.v("1756760292001")

    def test_invalid_ruc_does_not_end_001(self):
        with self.assertRaises(ValidationError):
            self.v("1756760292002")

    def test_invalid_ruc_not_13_digits(self):
        with self.assertRaises(ValidationError):
            self.v("175676029201")

    def test_invalid_ruc_bad_verifier(self):
        with self.assertRaises(ValidationError):
            self.v("1756760293001")


class IsCedulaTests(TestCase):
    def setUp(self):
        self.v = validators.IsCedula

    def test_valid_cedula(self):
        self.v("1756760292")

    def test_invalid_cedula_invalid_length(self):
        with self.assertRaises(ValidationError):
            self.v("1738331533")

    def test_invalid_cedula_bad_verifier(self):
        with self.assertRaises(ValidationError):
            self.v("173831153")

    def test_invalid_cedula_bad_province(self):
        with self.assertRaises(ValidationError):
            self.v("313831153")

    def test_invalid_cedula_bad_third_digit(self):
        with self.assertRaises(ValidationError):
            self.v("178831153")
