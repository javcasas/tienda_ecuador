import billing.sri

tabla_19 = billing.sri.tabla_19


def print_item(i, n):
    print "- model: billing.ice"
    print "  fields:"
    print "    codigo:", i.codigo
    print "    grupo:", i.grupo
    print "    descripcion:", i.nombre
    print "    porcentaje: 0"
    print "  pk:", n+1
    print


for n, i in enumerate(tabla_19):
    print_item(i, n)
