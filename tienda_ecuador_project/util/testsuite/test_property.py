from django.test import TestCase
from util.property import Property, ConvertedProperty


class PropertyTests(TestCase):
    """
    Tests for Property
    """
    good = Property(lambda x: True)
    bad = Property(lambda x: False)
    default = Property()

    def test_good(self):
        self.good = 4
        self.assertEquals(self.good, 4)

    def test_bad(self):
        with self.assertRaises(ValueError):
            self.bad = 6
        with self.assertRaises(AttributeError):
            self.bad

    def test_default(self):
        self.default = 4
        self.assertEquals(self.default, 4)


class ConvertedPropertyTests(TestCase):
    """
    Tests for ConvertedProperty
    """
    v = ConvertedProperty(one=1, two=2, three=3)

    def test_set(self):
        self.v = "one"
        self.assertEquals(self.v, "one")

    def test_invalid_set(self):
        with self.assertRaises(ValueError):
            self.v = "nein"

    def test_code(self):
        self.v = "one"
        self.assertEquals(self.v.code, 1)
        self.assertEquals(set(self.v.options), {'one', 'two', 'three'})
