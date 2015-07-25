# * encoding: utf8 *
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class OneOf(object):
    """
    Ensures the value is one of the valid ones
    """
    def __init__(self, *values):
        self.values = values

    def __call__(self, val):
        if val not in self.values:
            raise ValidationError("Invalid value {}, not in {}".format(
                val, self.values))


def IsCedula(val):
    """
    Ensures the value is a valid cedula
    """
    codigo_provincia = int(val[0:2])
    if codigo_provincia < 1 or codigo_provincia > 24:
        raise ValidationError("Codigo de provincia invalido")
    tipo_cedula = int(val[2])
    if tipo_cedula < 1 or tipo_cedula > 6:
        raise ValidationError("Tercer digito invalido")
    if len(val) != 10:
        raise ValidationError("Invalid value length")
    verificador = int(val[-1])
    checksum_multiplier = "21212121212"

    def digit_sum(digit, multiplier):
        digit = int(digit)
        multiplier = int(multiplier)
        res = digit * multiplier
        div, mod = divmod(res, 10)
        return div + mod

    checksum = sum([digit_sum(*params) for params
                    in zip(val[0:9], checksum_multiplier[0:9])])
    _, checksum = divmod(checksum, 10)
    checksum = 10 - checksum
    _, checksum = divmod(checksum, 10)
    if checksum != verificador:
        raise ValidationError("Invalid RUC invalid checksum")


def IsRuc(val):
    """
    Ensures the value is a valid RUC
    """
    if not len(val) == 13:
        raise ValidationError("RUC no tiene 13 digitos")
    if not val.endswith("001"):
        raise ValidationError("RUC no termina en 001")
    IsCedula(val[0:10])
