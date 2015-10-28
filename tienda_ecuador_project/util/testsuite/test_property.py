from django.test import TestCase
from util.property import Property, ConvertedProperty, ProtectedSetattr


class PropertyTests(TestCase):
    """
    Tests for Property
    """
    class TestClass(object):
        good = Property(lambda x: True)
        bad = Property(lambda x: False)
        default = Property()

    def test_good(self):
        new = self.TestClass()
        new.good = 4
        self.assertEquals(new.good, 4)

    def test_bad(self):
        new = self.TestClass()
        with self.assertRaises(ValueError):
            new.bad = 6
        with self.assertRaises(AttributeError):
            new.bad

    def test_default(self):
        new = self.TestClass()
        new.default = 4
        self.assertEquals(new.default, 4)

    def test_multiple(self):
        new = self.TestClass()
        other = self.TestClass()
        new.good = 4
        self.assertEquals(new.good, 4)
        with self.assertRaises(AttributeError):
            other.good


class ConvertedPropertyTests(TestCase):
    """
    Tests for ConvertedProperty
    """
    class TestClass(object):
        v = ConvertedProperty(one=1, two=2, three=3)

    def test_set(self):
        new = self.TestClass()
        new.v = "one"
        self.assertEquals(new.v, "one")

    def test_invalid_set(self):
        new = self.TestClass()
        with self.assertRaises(ValueError):
            new.v = "nein"

    def test_code(self):
        new = self.TestClass()
        new.v = "one"
        self.assertEquals(new.v.code, 1)
        self.assertEquals(set(new.v.options), {'one', 'two', 'three'})

    def test_multiple(self):
        new = self.TestClass()
        other = self.TestClass()
        new.v = 'one'
        self.assertEquals(new.v, 'one')
        with self.assertRaises(AttributeError):
            other.v


class ProtectedSetattrTests(TestCase):
    """
    Tests for Property
    """
    class TestClass(ProtectedSetattr):
        good = Property(lambda x: True)

    def test_good(self):
        new = self.TestClass()
        new.good = 4
        self.assertEquals(new.good, 4)

    def test_not_found(self):
        new = self.TestClass()
        with self.assertRaises(AttributeError):
            new.b = 3
