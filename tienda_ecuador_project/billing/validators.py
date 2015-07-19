# * encoding: utf8 *
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class OneOf(object):
    def __init__(self, *values):
        self.values = values

    def __call__(self, val):
        if val not in self.values:
            raise ValidationError("Invalid value {}, not in {}".format(
                val, self.values))
