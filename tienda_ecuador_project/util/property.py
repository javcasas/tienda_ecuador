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
        return self.val

    def __set__(self, a, newval):
        if not self.validator(newval):
            raise ValueError("Invalid value :{}".format(newval))
        self.val = newval


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
        class b(type(self.val)):
            code = self.conversion[self.val]
            options = self.conversion.keys()
        return b(self.val)

    def __set__(self, a, newval):
        if newval not in self.conversion.keys():
            raise ValueError("Invalid value :{}".format(newval))
        self.val = newval
