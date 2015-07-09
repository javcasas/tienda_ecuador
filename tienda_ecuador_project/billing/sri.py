# * encoding: utf8 *
from collections import namedtuple
from functools import wraps

unknown = None

# Tarifa del IVA
TarifaIva = namedtuple("TarifaIva", "nombre porcentaje codigo")
tabla_18 = [
    # nombre porcentaje codigo
    TarifaIva("0%", 0, 0),
    TarifaIva("12%", 12, 2),
    TarifaIva("No objeto de impuesto", 0, 6),
    TarifaIva("Exento de IVA", 0, 7),
]

dict_tabla_18 = {v.nombre: v for v in tabla_18}

TarifaIce = namedtuple("TarifaIce", "grupo nombre porcentaje codigo")
# Tarifa ICE
tabla_19 = [
    # nombre porcentaje codigo
    # Grupo 1
    TarifaIce(1, "Productos del tabaco y sucedáneos del tabaco (abarcan los "
                 "productos preparados totalmente o en parte utilizando "
                 "como materia prima hojas de tabaco y destinados a ser "
                 "fumados, chupados, inhalados, mascados o utilizados "
                 "como rapé).", unknown, 3023),
    TarifaIce(1, "Bebidas gaseosas.", unknown, 3051),
    TarifaIce(1, "Perfumes y aguas de tocador", unknown, 3610),
    TarifaIce(1, "Videojuegos", unknown, 3620),
    TarifaIce(1, "Armas de fuego, armas deportivas y municiones excepto "
                 "aquellas adquiridas por la fuerza pública", unknown, 3630),
    TarifaIce(1, "Focos incandescentes excepto aquellos utilizados como "
                 "insumos automotrices", unknown, 3640),
    TarifaIce(1, "Cocinas, calefones y otros de uso doméstico a gas SRI",
              unknown, 3670),
    TarifaIce(1, "Cocinas, calefones y otros de uso doméstico a gas SENAE",
              unknown, 3770),

    # Grupo 2:
    # 1. Vehículos motorizados de transporte terrestre
    # de hasta 3.5 toneladas de carga, conforme el siguiente detalle:
    TarifaIce(2, "Vehículos motorizados cuyo precio de venta al público "
                 "sea de hasta USD 20.000", unknown, 3073),
    TarifaIce(2, "Camionetas, furgonetas, camiones, y vehículos de rescate "
                 "cuyo precio de venta al público sea de hasta USD 30.000",
                 unknown, 3072),
    TarifaIce(2, "Vehículos motorizados, excepto camionetas, furgonetas, "
                 "camiones y vehículos de rescate, cuyo precio de venta "
                 "al público sea superior a USD 20.000 y de hasta USD 30.000",
                 unknown, 3074),
    TarifaIce(2, "Vehículos motorizados, cuyo precio de venta al público sea "
                 "superior a USD 30.000 y de hasta USD 40.000", unknown, 3075),
    TarifaIce(2, "Vehículos motorizados, cuyo precio de venta al público sea "
                 "superior a USD 40.000 y de hasta USD 50.000", unknown, 3077),
    TarifaIce(2, "Vehículos motorizados, cuyo precio de venta al público sea "
                 "superior a USD 50.000 y de hasta USD 60.000", unknown, 3078),
    TarifaIce(2, "Vehículos motorizados, cuyo precio de venta al público sea "
                 "superior a USD 60.000 y de hasta  USD 70.000",
                 unknown, 3079),
    TarifaIce(2, "Vehículos motorizados, cuyo precio de venta al público sea "
                 "superior a USD 70.000", unknown, 3080),
    # 2. Vehículos motorizados híbridos o eléctricos de transporte terrestre
    # de hasta 3.5 toneladas de carga, conforme el siguiente detalle:
    TarifaIce(2, "Vehículos híbridos o eléctricos cuyo precio de venta al "
                 "público sea de hasta USD 35.000", unknown, 3171),
    TarifaIce(2, "Vehículos híbridos o eléctricos cuyo precio de venta al "
                 "público sea superior a USD 35.000 y de hasta USD 40.000",
                 unknown, 3172),
    TarifaIce(2, "Vehículos híbridos o eléctricos cuyo precio de venta al "
                 "público sea superior a USD 40.000 y de hasta USD 50.000",
                 unknown, 3173),
    TarifaIce(2, "Vehículos híbridos o eléctricos cuyo precio de venta al "
                 "público sea superior a USD 50.000 y de hasta USD 60.000",
                 unknown, 3174),
    TarifaIce(2, "Vehículos híbridos o eléctricos cuyo precio de venta al "
                 "público sea superior a USD 60.000 y de hasta USD 70.000",
                 unknown, 3175),
    TarifaIce(2, "Vehículos híbridos o eléctricos cuyo precio de venta al "
                 "público sea superior a USD 70.000", unknown, 3176),
    TarifaIce(2, "3. Aviones, avionetas y helicópteros excepto aquellas "
                 "destinadas al transporte comercial de pasajeros, carga y "
                 "servicios; motos acuáticas, tricares, cuadrones, yates y "
                 "barcos de recreo", unknown, 3081),

    # Grupo 3
    TarifaIce(3, "Servicios de television pagada", unknown, 3092),
    TarifaIce(3, "Servicios de casinos, salas de juego (bingo - mecanicos) "
                 "y otros juegos de azar", unknown, 3650),

    # Grupo 4
    TarifaIce(4, "Las cuotas, membresías, afiliaciones, acciones y "
                 "similares que cobren a sus miembros y usuarios los "
                 "Clubes Sociales, para prestar sus servicios, cuyo monto "
                 "en su conjunto supere los US $ 1.500 anuales",
                 unknown, 3660),

    # Grupo 5
    TarifaIce(5, "Cigarrillos rubio", unknown, 3011),
    TarifaIce(5, "Cigarrillos negros", unknown, 3021),
    TarifaIce(5, "Bebidas alcohólicas, distintas a la cerveza", unknown, 3031),
    TarifaIce(5, "Cerveza", unknown, 3041),
]
dict_tabla_19 = {v.nombre: v for v in tabla_19}

tabla_20 = [
    # Impuesto a retener
    ("RENTA", 1),
    ("IVA", 2),
    ("ISD", 6),
]

tabla_21 = [
    # Retencion de iva
    ("10%", 10, 9),
    ("20%", 20, 10),
    ("30%", 30, 1),
    ("70%", 70, 2),
    ("100%", 100, 3),
    ("Retencion en cero", 0, 7),
    ("No procede retencion", 0, 8),
]


class CheckValue(object):
    def __init__(self, accepted_values):
        self.accepted_values = accepted_values

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(value):
            if value not in self.accepted_values:
                raise ValueError("Invalid value: {}".format(value))
            else:
                return fn(value)


class ConvertedProperty(object):
    def __init__(self, **conversion):
        self.conversion = conversion

    def __get__(self, a, b):
        class b(type(self.val)):
            code = self.code
            options = self.conversion.keys()
        return b(self.val)

    def __set__(self, a, newval):
        if newval not in self.conversion.keys():
            raise ValueError("Invalid value :{}".format(newval))
        self.val = newval

    @property
    def code(self):
        return self.conversion[self.val]


class ConvertedPropertyFollowing(object):
    def __init__(self, key, **conversion):
        self.key = key
        self.conversion = conversion

    def conversion_dict(self):
        current_key = self.key.__get__(None, None)
        valid_values = self.conversion[current_key]
        return valid_values

    def __get__(self, a, b):
        class b(type(self.val)):
            code = self.code.codigo
            name = self.code.nombre
            value = self.code.porcentaje
            options = self.conversion_dict().keys()
        return b(self.val)

    def __set__(self, a, newval):
        valid_values = self.conversion_dict()
        if newval not in valid_values.keys():
            raise ValueError("Invalid value :{}".format(newval))
        self.val = newval

    @property
    def code(self):
        return self.conversion_dict()[self.val]


class IdentificacionComprador(object):
    def __init__(self, tipo_identificacion_comprador):
        self.tipo_identificacion = tipo_identificacion_comprador

    def __get__(self, a, b):
        class b(type(self.val)):
            pass
        return b(self.val)

    def __set__(self, a, newval):
        def error(texto):
            texto = texto + ": {}"
            raise ValueError(texto.format(newval))

        def tests_cedula(val):
            codigo_provincia = int(val[0:2])
            if codigo_provincia < 1 or codigo_provincia > 24:
                error("Codigo de provincia invalido")
            tipo_cedula = int(val[2])
            if tipo_cedula < 1 or tipo_cedula > 6:
                error("Tercer digito invalido")
            if "-" not in val:
                error("Cedula does not contain dash")
            if len(val) != 11:
                error("Invalid value length")
            verificador = int(val[-1])
            checksum_multiplier = "21" * 5

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
                error("Invalid RUC invalid checksum")

        tipo = self.tipo_identificacion.__get__(None, None)
        if tipo == 'ruc':
            if len(newval) != 13:
                error("Invalid value length")
            if not newval.endswith("001"):
                error("Invalid RUC doesn't end with 001")
            if 1 <= int(newval[3]) <= 5:
                cedula = newval[0:9] + '-' + newval[9]
                tests_cedula(cedula)
        elif tipo == 'cedula':
            tests_cedula(newval)
        elif tipo == 'pasaporte':
            pass
        elif tipo == 'consumidor_final':
            if newval != '999999999':
                error("Invalid value")
        self.val = newval


class FormattedProperty(object):
    def __init__(self, type_check):
        self.type_check = type_check

    def __get__(self, a, b):
        class b(type(self.val)):
            code = self.code
        return b(self.val)

    def __set__(self, a, newval):
        if type(newval) != self.type_check:
            raise ValueError("Invalid value :{}".format(newval))
        self.val = newval

    @property
    def code(self):
        return self.val


class BillXmlData(object):
    class InfoTributaria(object):
        __slots__ = [
            'ambiente', 'tipo_emision', 'razon_social', 'nombre_comercial',
            'ruc', 'clave_acceso', 'cod_doc', 'establecimiento',
            'punto_emision', 'secuencial', 'direccion_matriz',
        ]

        ambiente = ConvertedProperty(pruebas=1, produccion=2)
        tipo_emision = ConvertedProperty(normal=1, indisponibilidad_sistema=2)
        cod_doc = ConvertedProperty(factura=1, nota_credito=4, nota_debito=5,
                                    guia_remision=6, comprobante_retencion=7)

    class InfoFactura(object):
        __slots__ = [
            'fecha_emision', 'direccion_establecimiento',
            'contribuyente_especial', 'obligado_contabilidad',
            'tipo_identificacion_comprador', 'razon_social_comprador',
            'identificacion_comprador', 'total_sin_impuestos',
            'total_descuento', 'impuestos', 'propina', 'importe_total',
            'moneda',
        ]
        tipo_identificacion_comprador = ConvertedProperty(
            ruc=4, cedula=5, pasaporte=6, consumidor_final=7,
            identificacion_exterior=8, placa=9)

        identificacion_comprador = IdentificacionComprador(tipo_identificacion_comprador)

        class TotalImpuestos(object):
            __slots__ = [
                'codigo', 'codigo_porcentaje', 'descuento_adicional'
                'base_imponible', 'valor'
            ]

    class Detalle(object):
        __slots__ = [
            'codigo_principal', 'codigo_auxiliar', 'descripcion',
            'unidad_medida', 'cantidad', 'precio_unitario', 'descuento',
            'total_sin_impuesto',
        ]

        class Impuesto(object):
            __slots__ = [
                'codigo', 'codigo_porcentaje', 'tarifa', 'base_imponible',
                'valor',
            ]
            codigo = ConvertedProperty(iva=2, ice=3, irbpnr=5)  # Tabla 17
            codigo_porcentaje = ConvertedPropertyFollowing(
                codigo,
                iva=dict_tabla_18,
                ice=dict_tabla_19)

    class Retencion(object):
        __slots__ = [
            'codigo', 'codigo_porcentaje', 'tarifa', 'valor'
        ]
        codigo = ConvertedProperty(renta=1, iva=2, isd=6)
        codigo_porcentaje = ConvertedProperty(
            iva_10=9, iva_20=10, iva_30=1, iva_70=2, iva_100=3, iva_0=7,
            iva_no_procede=8, isd_5=4580)
