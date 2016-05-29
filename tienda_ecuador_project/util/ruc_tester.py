def is_luhn_valid(cc): #Parametro ejemplo 4896889802135
    num = map(int, str(cc))
    return sum(num[::-2] + [sum(divmod(d * 2, 10)) for d in num[-2::-2]]) % 10 == 0

def is_luhn_valid2(cc): #Parametro ejemplo 4896889802135
    num = map(int, str(cc))
    curr_verif = num[-1]
    num = num[:-1]
    evens = num[1::2]
    odds = num[::2]
    odds = map(lambda x: x*2, odds)
    verif = (sum(evens + odds) * 9) % 10
    return curr_verif == verif

def is_valid_cedula(c):
    return is_luhn_valid(c)

def is_valid_ruc(c):
    num = map(int, str(c))
    provincia = int(c[0:2])
    if provincia < 1 or provincia > 22:
        return False
    tipo = num[2]
    curr_verif = num[9]
    if tipo in [0, 1, 2, 3, 4, 5]:
        coefs = [2, 1, 2, 1, 2, 1, 2, 1, 2]
        pairs = zip(num, coefs)
        def mul_merge((x, y)):
            r = x * y
            d, m = divmod(r, 10)
            return d + m
        muls = map(mul_merge, pairs) 
        sums = sum(muls)
        verif = 10 - (sums % 10)
        if verif == 10:
            verif = 0
        return verif == curr_verif
    elif tipo == 9:
        coefs = [4, 3, 2, 7, 6, 5, 4, 3, 2]
        pairs = zip(num, coefs)
        def mul_merge((x, y)):
            return x * y
        muls = map(mul_merge, pairs) 
        sums = sum(muls)
        verif = sums % 11
        if verif != 0:
            verif = 11 - verif
        return verif == curr_verif
    elif tipo == 6:
        curr_verif = num[8]
        coefs = [3, 2, 7, 6, 5, 4, 3, 2]
        pairs = zip(num, coefs)
        def mul_merge((x, y)):
            return x * y
        muls = map(mul_merge, pairs) 
        sums = sum(muls)
        verif = sums % 11
        if verif != 0:
            verif = 11 - verif
        return verif == curr_verif
    else:
        return False


assert is_valid_ruc("1710034065001")
assert is_valid_ruc("1756760292001")
assert is_valid_ruc("1791321634001")


with open("/home/javier/proyectos/SRI/RUCs/valid_rucs.txt") as f:
    rucs = f.readlines()
rucs = [r.strip() for r in rucs]
print "Total rucs:", len(rucs)

#cedulas = [c[1:] if c.startswith("0") else c for c in cedulas]



def calculate_luhn(cc):
    num = map(int, str(cc))
    check_digit = 10 - sum(num[-2::-2] + [sum(divmod(d * 2, 10)) for d in num[::-2]]) % 10
    return 0 if check_digit == 10 else check_digit

test1 = [(r, is_valid_ruc(r)) for r in rucs]
print "Valid RUCs:", sum([r[1] for r in test1])
print "Invalid RUCs:", [r[0] for r in test1 if not r[1]]
