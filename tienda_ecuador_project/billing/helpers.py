# nombre, xpath, funcion procesado

def noop(x):
    return x

# Info Tributaria
info_tributaria = [
    ('Ambiente', "./infoTributaria/ambiente", {'1': 'Pruebas', '2': 'Produccion'}.get),
    ('Tipo de Emisión', './infoTributaria/tipoEmision', {'1': 'Normal', '2': 'Indisponibilidad del Sistema'}.get),
    ('Razón Social', "./infoTributaria/razonSocial", noop),
    ("Nombre Comercial", "./infoTributaria/nombreComercial" noop),
    ('RUC', "./infoTributaria/ruc", noop),
    ('Clave de Acceso', "./infoTributaria/claveAcceso", noop)
    ("Código de Documento", "./infoTributaria/codDoc", {"01": "Factura"}.get),
    ("Código de Establecimiento", "./infoTributaria/estab", noop),
    ("Punto de Emisión", "./infoTributaria/ptoEmi", noop),
    ("Secuencial", "./infoTributaria/secuencial", noop),
    ("Dirección Matriz", "./infoTributaria/dirMatriz", noop),
]


info_factura = [
    ("Fecha de Emisión", "./infoFactura/fechaEmision", noop),
    ("Obligado a llevar Contabilidad", "./infoFactura/obligadoContabilidad", {"SI": True, "NO": False}.get),
    ("Tipo de Identificación del Comprador", "./infoFactura/tipoIdentificacionComprador", noop),  #FIXME
    ("Razón Social del Comprador", "./infoFactura/razonSocialComprador", noop),
    ("Identificación del Comprador", "./infoFactura/identificacionComprador", noop),
    ("Total sin Impuestos", "./infoFactura/totalSinImpuestos", Decimal),
    ("Descuento Total", "./infoFactura/totalDescuento", Decimal),
    ("Propina", "./infoFactura/propina", Decimal),
    ("Total con Impuestos", "./infoFactura/importeTotal", Decimal),
    ("Moneda", "./infoFactura/moneda", noop)
]

# Impuestos
desc_total_impuesto = [
    ("Código", "codigo", {"2": "IVA", '3': "ICE"}.get),  # FIXME
    ("Código de Porcentaje", "codigoPorcentaje", {}.get),  # FIXME
    ("Descuento Adicional", "descuentoAdicional", Decimal),
    ("Base Imponible", "baseImponible", Decimal),
    ("Valor", "valor", Decimal),
]

# Detalle
desc_detalle = [
    ("Descripción", "descripcion", noop),
    ("Cantidad", "cantidad", Decimal),
    ("Precio Unitario", "precioUnitario", Decimal),
    ("Descuento", "descuento", Decimal),
    ("Total Sin Impuestos", "precioTotalSinImpuesto", Decimal),
]

# IVA item 1
desc_detalle_impuesto = [
    ("Código", "codigo", {"2": "IVA"}.get),  # FIXME
    ("Código de Porcentaje", "codigoPorcentaje", {}.get),  # FIXME
    ("Tarifa", "tarifa", Decimal),
    ("Base Imponible", "baseImponible", Decimal),
    ("Valor", "valor", Decimal),
]
