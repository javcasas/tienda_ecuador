def verifier_number(c, coefficients, mul_op, modulus):
    coefs = [2, 1, 2, 1, 2, 1, 2, 1, 2]
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

def is_valid_cedula(c):
    num = map(int, str(c))

    provincia = int(c[0:2])
    if provincia < 1 or provincia > 22:
        return False

    tipo = num[2]

    if tipo in [0, 1, 2, 3, 4, 5]:
        # Cedula
        return check_verifier_number(
            num, 
            coefficients=[2, 1, 2, 1, 2, 1, 2, 1, 2],
            mul_op=mul_merge,
            modulus=10,
            verifier_position=9)
    else:
        return False

def is_valid_ruc(c):
    num = map(int, str(c))

    if c in ['9999999999999', '9999999999001']:
        return True

    provincia = int(c[0:2])
    if provincia < 1 or provincia > 22:
        return False

    tipo = num[2]

    if tipo in [0, 1, 2, 3, 4, 5]:
        # Cedula
        return check_verifier_number(
            num, 
            coefficients=[2, 1, 2, 1, 2, 1, 2, 1, 2],
            mul_op=mul_merge,
            modulus=10,
            verifier_position=9)
    elif tipo == 9:
        # Sociedad o extranjero no residente
        return check_verifier_number(
            num, 
            coefficients=[4, 3, 2, 7, 6, 5, 4, 3, 2],
            mul_op=mul,
            modulus=11,
            verifier_position=9)
    elif tipo == 6:
        # Empresa del estado
        return check_verifier_number(
            num, 
            coefficients=[3, 2, 7, 6, 5, 4, 3, 2],
            mul_op=mul,
            modulus=11,
            verifier_position=8)
    else:
        return False


def test():
    assert is_valid_ruc("1710034065001")
    assert is_valid_ruc("1756760292001")
    assert is_valid_ruc("1791321634001")
    assert is_valid_cedula("1710034065")
    assert is_valid_cedula("1756760292")
    assert not is_valid_cedula("1791321634")

    with open("/home/javier/proyectos/SRI/RUCs/valid_rucs.txt") as f:
        rucs = f.readlines()
    rucs = [r.strip() for r in rucs]
    print "Total rucs:", len(rucs)

    test1 = [(r, is_valid_ruc(r)) for r in rucs]
    print "Valid RUCs:", sum([r[1] for r in test1])
    print "Invalid RUCs:", [r[0] for r in test1 if not r[1]]

if __name__ == '__main__':
    test()
