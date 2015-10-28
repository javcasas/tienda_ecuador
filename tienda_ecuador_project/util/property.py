class Property(object):
    """
    Property for a class with a validator.
    Ensures the validator returns True on the value passed
    before accepting it
    """
    def __init__(self, validator=None):
        def always_valid(x):
            return True
        self.validator = validator or always_valid

    def __get__(self, a, b):
        return getattr(a, self.name)

    def __set__(self, a, newval):
        if not self.validator(newval):
            raise ValueError("Invalid value :{}".format(newval))
        setattr(a, self.name, newval)

    @property
    def name(self):
        return "__property__{}__".format(hash(self))


class ConvertedProperty(object):
    """
    Property for a class with a dict that converts values.
    Ensures the value passed is part of the keys of the dict.
    """
    def __init__(self, **conversion):
        self.conversion = conversion

    def __get__(self, a, b):
        """
        Returns a clone of the value with a hidden field
        called "code"
        """
        val = getattr(a, self.name)

        class b(type(val)):
            code = self.conversion[val]
            options = self.conversion.keys()
        return b(val)

    def __set__(self, a, newval):
        if newval not in self.conversion.keys():
            raise ValueError("Invalid value :{}".format(newval))
        setattr(a, self.name, newval)

    @property
    def name(self):
        return "__property__{}__".format(hash(self))


class ProtectedSetattr(object):
    def __setattr__(self, key, val):
        attrs = dir(self)
        if key in attrs or key.startswith("__property__"):
            return super(ProtectedSetattr, self).__setattr__(key, val)
        else:
            raise AttributeError("Attribute {} not found".format(key))
