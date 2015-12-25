from collections import namedtuple
from datetime import date
from decimal import Decimal

data = open("/home/javier/ComprobantesElectronicos/"
            "resources/impuesto_valor.sql").read()


def split_parts(s):
    res = []
    while(s):
        if s.startswith("'"):
            curr, rest = s[1:].split("'", 1)
            res.append(curr)
            s = rest[1:]
        else:
            parts = s.split(",", 1)
            if len(parts) == 1:
                res.append(s)
                s = ""
            else:
                curr, rest = parts
                res.append(curr.strip())
                s = rest
        s = s.strip()
    return res


def get_date(s):
    if s != "NULL":
        parts = s.split("-")
        parts = map(int, parts)
        return date(*parts)
    else:
        return None


def clean_desc(s):
    headers = ['ICE - ', 'ICE \xe2\x80\x93 ']
    for i in headers:
        if s.startswith(i):
            s = s[len(i):]
    middle_items = [
        ('  ', ' '),
        ('\xc2\xa0', ""),
        ('\xe2\x80\x93', '-'),
    ]
    for i, r in middle_items:
        s = s.replace(i, r)
    s = s.lower()
    replacements = [
        ('usd.', 'USD'),
        ('usd', 'USD'),
        ('pvp', 'PVP'),
        ('vehic ', 'vehiculos '),
    ]
    for i, r in replacements:
        s = s.replace(i, r)
    s = s[0].upper() + s[1:]
    return s


Ice = namedtuple("Ice", ['codigo', 'porcentaje', 'descripcion',
                         'fecha_inicio', 'fecha_fin', 'id'])
Iva = namedtuple("Iva", ['codigo', 'porcentaje', 'descripcion',
                         'fecha_inicio', 'fecha_fin', 'id'])
Retencion = namedtuple("Retencion", ['codigo', 'porcentaje', 'descripcion',
                                     'fecha_inicio', 'fecha_fin', 'id'])

ices = []
ivas = []
retenciones = []


def process():
    lines = data.splitlines()
    for line in lines:
        if line.startswith("DELETE"):
            continue
        if not line.strip():
            continue
        if line.startswith("COMMIT"):
            continue
        parts = line.split(" ", 3)
        data_line = parts[-1]
        key, value = data_line.split(" VALUES ")
        key = key[1:-1]
        value = value[1:-2]

        keys = split_parts(key)
        values = split_parts(value)

        res = dict(zip(keys, values))
        # convert_TIPO_IMPUESTO = {
        #     "I": "Ice",
        #     "R": "Retencion",
        #     "A": "Iva",
        #     "B": "Botellas",
        # }
        d = dict(codigo=res['CODIGO'],
                 porcentaje=Decimal(res['PORCENTAJE']),
                 descripcion=clean_desc(res['DESCRIPCION']),
                 fecha_inicio=get_date(res['FECHA_INICIO']),
                 fecha_fin=get_date(res['FECHA_FIN']),
                 id=None)
        if res['TIPO_IMPUESTO'] == 'I':
            d = Ice(**d)
            ices.append(d)
        elif res['TIPO_IMPUESTO'] == 'A':
            d = Iva(**d)
            ivas.append(d)
        elif res['TIPO_IMPUESTO'] == 'R':
            d = Retencion(**d)
            retenciones.append(d)  # FIXME: Incompleto

process()
# for ice in ices:
#     print ice
# for iva in ivas:
#     print iva
# for retencion in retenciones:
#     print retencion
res = []

ivas.append(Iva(codigo='0',
                descripcion="0%",
                porcentaje=Decimal(0),
                fecha_inicio=None,
                fecha_fin=None,
                id=2))

ivas.append(Iva(codigo='6',
                descripcion='No Objeto de Impuesto',
                porcentaje=Decimal('0'),
                fecha_inicio=None,
                fecha_fin=None,
                id=3))

ivas.append(Iva(codigo='7',
                descripcion='Exento de IVA',
                porcentaje=Decimal(0),
                fecha_inicio=None,
                fecha_fin=None,
                id=4))


res.append("# IVA")
curr_id = 1
for iva in ivas:
    template = """
- model: billing.iva
  fields:
    codigo: '{codigo}'
    descripcion: {descripcion}
    porcentaje: {porcentaje}
  pk: {pk}
"""
    if iva.id:
        curr_id = iva.id
    item = template.format(codigo=iva.codigo,
                           descripcion=iva.descripcion,
                           porcentaje=iva.porcentaje,
                           pk=curr_id)
    res.append(item)
    curr_id += 1

res.append("# ICE")
for i, ice in enumerate(ices, 101):
    template = """
- model: billing.ice
  fields:
    codigo: '{codigo}'
    descripcion: {descripcion}
    porcentaje: {porcentaje}
  pk: {pk}
"""
    item = template.format(codigo=ice.codigo,
                           descripcion=ice.descripcion,
                           porcentaje=ice.porcentaje,
                           pk=i)
    res.append(item)

print "".join(res)
