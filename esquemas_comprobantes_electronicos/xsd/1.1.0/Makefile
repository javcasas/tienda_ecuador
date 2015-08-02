all: factura_1_1_0.py guia_remision_1_1_0.py nota_credito_1_1_0.py

factura_1_1_0.py: factura_v1.1.0.xsd
	pyxbgen --module factura_1_1_0 factura_v1.1.0.xsd

guia_remision_1_1_0.py: guiaRemision_v1.1.0.xsd
	pyxbgen --module guia_remision_1_1_0 guiaRemision_v1.1.0.xsd

nota_credito_1_1_0.py: notaCredito_v1.1.0.xsd
	pyxbgen --module nota_credito_1_1_0 notaCredito_v1.1.0.xsd

.PHONY: all
