# * encoding: utf-8 *
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


def verifier_number(c, coefficients, mul_op, modulus):
    pairs = zip(c, coefficients)
    muls = map(mul_op, pairs)
    sums = sum(muls)
    verif = sums % modulus
    if verif != 0:
        verif = modulus - verif
    return verif


def check_verifier_number(c, coefficients, mul_op, modulus, verifier_position):
    verif = verifier_number(c,
                            coefficients=coefficients,
                            mul_op=mul_op,
                            modulus=modulus)
    return verif == c[verifier_position]


def mul((x, y)):
    return x * y


def mul_merge((x, y)):
    r = x * y
    d, m = divmod(r, 10)
    return d + m


def valid_province_code(c):
    provincia = int(c[0:2])
    if provincia < 1 or provincia > 22:
        return False
    else:
        return True


def IsCedula(val):
    """
    Ensures the value is a valid cedula
    """
    num = map(int, val)

    if len(num) != 10:
        raise ValidationError("Invalid value length")

    if not valid_province_code(val):
        raise ValidationError("Codigo de provincia invalido")

    tipo = num[2]

    if tipo in [0, 1, 2, 3, 4, 5]:
        # Cedula
        if not check_verifier_number(
                num,
                coefficients=[2, 1, 2, 1, 2, 1, 2, 1, 2],
                mul_op=mul_merge,
                modulus=10,
                verifier_position=9):
            raise ValidationError("Invalid RUC invalid checksum")
    else:
        raise ValidationError("Tercer digito invalido")


def IsRuc(val):
    """
    Ensures the value is a valid RUC
    """
    if not val.endswith("001"):
        raise ValidationError("RUC no termina en 001")

    num = map(int, val)
    if len(num) != 13:
        raise ValidationError("Invalid value length")

    if val in ['9999999999999', '9999999999001']:
        return

    if not valid_province_code(val):
        raise ValidationError("Codigo de provincia invalido")

    tipo = num[2]

    if tipo in [0, 1, 2, 3, 4, 5]:
        # Cedula
        return IsCedula(val[0:10])
    elif tipo == 9:
        # Sociedad o extranjero no residente
        if not check_verifier_number(
                num,
                coefficients=[4, 3, 2, 7, 6, 5, 4, 3, 2],
                mul_op=mul,
                modulus=11,
                verifier_position=9):
            raise ValidationError("Invalid RUC invalid checksum")
    elif tipo == 6:
        # Empresa del estado
        if not check_verifier_number(
                num,
                coefficients=[3, 2, 7, 6, 5, 4, 3, 2],
                mul_op=mul,
                modulus=11,
                verifier_position=8):
            raise ValidationError("Invalid RUC invalid checksum")
    else:
        raise ValidationError("Tercer digito invalido")
