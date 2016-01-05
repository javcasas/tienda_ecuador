from django import forms
from decimal import Decimal
from django.core import validators


class UpdatedDecimalField(forms.DecimalField):
    """
    Checks if decimal_places has been updated after form creation
    Ignores trailing zeroes
    """
    def to_python(self, value):
        self.validators.append(validators.DecimalValidator(self.max_digits, self.decimal_places))
        res = super(UpdatedDecimalField, self).to_python(value)
        converted = res.quantize(Decimal(1) / (Decimal(10) ** self.decimal_places))
        if converted == res:
            return converted
        else:
            return res
