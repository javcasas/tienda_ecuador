# * coding: utf-8 *
import pytz
from io import BytesIO
from contextlib import contextmanager
import StringIO
import xml.etree.ElementTree as ET

from elaphe.code128 import Code128

from django.templatetags import l10n

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Frame, Table, Image  # , Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors, utils

from sri.models import SRIStatus, AmbienteSRI
from util.templatetags.decimal_format import money_2d, decimals

tz = pytz.timezone('America/Guayaquil')


def gen_bill_ride(ob):
    print "Generating PDF"
    try:
        res = gen_bill_ride_stuff(ob)
        print "GENERATED"
        return res
    except:
        print "ERROR"
        import traceback
        print traceback.format_exc()
        raise


class RenderStack(object):
    context_stack = []

    def __init__(self, x0, y0, x1, y1, margin=(0, 0, 0, 0)):
        left, bottom, right, top = self._get_margin(margin)
        self._x0 = x0 + left
        self._y0 = y0 + bottom
        self._x1 = x1 - right
        self._y1 = y1 - top
        self.context_stack = []

    def _get_margin(self, margindata):
        try:
            left, bottom, right, top = margindata
            return left, bottom, right, top
        except TypeError:
            return margindata, margindata, margindata, margindata

    def _push_state(self):
        self.context_stack.append(
            [self._x0,
             self._y0,
             self._x1,
             self._y1,
             ])

    def _pop_state(self):
        old_context = self.context_stack.pop()
        self._x0, self._y0, self._x1, self._y1 = old_context

    def print_state(self):
        print self._x0, self._y0, self._x1, self._y1

    @contextmanager
    def section(self, x0, y0, x1, y1, margin=(0, 0, 0, 0)):
        self._push_state()
        left, bottom, right, top = self._get_margin(margin)
        new_x0 = self.x(x0) + left
        new_x1 = self.x(x1) - right
        new_y0 = self.y(y0) + bottom
        new_y1 = self.y(y1) - top
        self._x0 = new_x0
        self._y0 = new_y0
        self._x1 = new_x1
        self._y1 = new_y1
        yield
        self._pop_state()

    def x(self, x):
        return self._x0 + self.width(x)

    def y(self, y):
        return self._y0 + self.height(y)

    def width(self, x):
        return (self._x1 - self._x0) * x

    def height(self, y):
        return (self._y1 - self._y0) * y


def get_image(path, width=1*inch, height=1*inch):
    img = utils.ImageReader(path)
    iw, ih = img.getSize()
    aspect = ih / float(iw)
    if width * aspect > height:
        return Image(path, width=(height/aspect), height=height)
    else:
        return Image(path, width=width, height=(width * aspect))


def get_warning(ob):
    res = []
    invalid = False
    if ob.status == SRIStatus.options.Annulled:
        res.append("ANULADO")
        invalid = True
    elif ob.status == SRIStatus.options.Sent:
        res.append("PENDIENTE DE AUTORIZACIÓN")
    elif ob.status == SRIStatus.options.Accepted:
        pass
    else:
        res.append("PROFORMA")
        invalid = True
    if ob.ambiente_sri == AmbienteSRI.options.pruebas:
        res.append("AMBIENTE DE PRUEBAS")
        invalid = True
    if invalid:
        res.append("SIN VALIDEZ TRIBUTARIA")
    return res


def make_barcode(data):
    """
    Makes a GS1-128 barcode as an image
    @param data: the data to put in the barcode
    @return: file-like object with a png as content
    """
    out = StringIO.StringIO()
    image = Code128().render(data, scale=2, margin=0)
    for i in range(image.size[0] - 1, 0, -1):
        pix = image.getpixel((i, 0))
        if pix[0] == 0:
            image = image.crop((0, 0, i+1, image.size[1]))
            break
    image.save(out, "png")
    out.seek(0)
    return out


def get_bill_number_from_tree(tree):
    return u"{}-{}-{}".format(tree.find("./infoTributaria/estab").text,
                              tree.find("./infoTributaria/ptoEmi").text,
                              tree.find("./infoTributaria/secuencial").text)


def gen_bill_ride_stuff(ob):
    buffer_ = BytesIO()

    try:
        tree = ET.fromstring(ob.xml_content.encode('utf8'))
    except ET.ParseError:
        tree = None

    pagesize = A4
    margin = inch, inch, inch, inch

    canvas = Canvas(buffer_, pagesize=pagesize)

    c = RenderStack(0, 0, pagesize[0], pagesize[1], margin=margin)
    # p.roundRect(c.x(0), c.y(0), c.width(1), c.height(1), 3, stroke=1, fill=0)

    # Print warnings
    warnings = get_warning(ob)
    if warnings:
        canvas.saveState()
        grey = 0.3
        canvas.setFillColorCMYK(0, 0, 0, grey)
        canvas.setStrokeColorCMYK(0, 0, 0, grey)
        canvas.setFont("Helvetica", 50)

        total_height = 60 * len(warnings)
        canvas.translate(c.x(0.5), c.y(0.7))
        canvas.rotate(45)
        canvas.translate(0, total_height / 2)

        for item in warnings:
            canvas.drawCentredString(0, 0, item)
            canvas.translate(0, -60)

        canvas.restoreState()

    def add_items(items, showBoundary=False):
        f = Frame(c.x(0), c.y(0), c.width(1), c.height(1),
                  showBoundary=showBoundary,
                  leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0)
        f.addFromList(items, canvas)
        if items:
            raise Exception("Does not fit - items left")

    # Parameters
    column_height = 0.3
    column_width = 0.5
    footer_height = 0.14
    standard_separation = inch / 20

    # styles
    styles = getSampleStyleSheet()
    small = styles['Normal'].clone("Smaller", fontSize=8)
    normal = styles['Normal']
    bigheader = styles['h2']
    mediumheader = styles['h3']
    smallheader = styles['h4']

    with c.section(0, 1 - column_height, 1, 1):
        # columna izquierda
        with c.section(0, 0, column_width, 1,
                       margin=(0, 0, standard_separation, 0)):
            if ob.company.get_logo():
                with c.section(0, 0.5, 1, 1,
                               margin=standard_separation):
                    # logo
                    logo = ob.company.get_logo()
                    if logo:
                        add_items(
                            [get_image(logo.file.file.name, width=c.width(1), height=c.height(1))]
                        )
            with c.section(0, 0, 1, column_width,
                           margin=standard_separation):
                story = []
                if ob.company.nombre_comercial:
                    story.append(Paragraph(ob.company.nombre_comercial,
                                           bigheader))
                    story.append(Paragraph("Razon Social: {}".format(ob.company.razon_social),
                                           normal))
                else:
                    story.append(Paragraph("Razon Social: {}".format(ob.company.razon_social),
                                           bigheader))

                if ob.company.direccion_matriz != ob.punto_emision.establecimiento.direccion:
                    story.append(Paragraph(u"Dirección Matriz:",
                                           normal))
                    story.append(Paragraph(ob.company.direccion_matriz,
                                           small))
                    story.append(Paragraph(u"Dirección Sucursal:",
                                           normal))
                    story.append(Paragraph(ob.punto_emision.establecimiento.direccion,
                                           small))
                else:
                    story.append(Paragraph(u"Dirección:",
                                           normal))
                    story.append(Paragraph(ob.company.direccion_matriz,
                                           small))
                if ob.company.contribuyente_especial:
                    story.append(Paragraph("Contribuyente Especial: {}".format(ob.company.contribuyente_especial),
                                           normal))
                story.append(Paragraph("{} Obligado a llevar Contabilidad".format(
                                       "SI" if ob.company.obligado_contabilidad else "NO"),
                                       normal))
                add_items(story)

        # columna derecha
        with c.section(column_width, 0, 1, 1,
                       margin=standard_separation):
            story.append(Paragraph("RUC {}".format(ob.company.ruc),
                                   normal))
            subtipo = None
            if ob.status == SRIStatus.options.Accepted:
                tipo = "FACTURA"
                number = get_bill_number_from_tree(tree)
            elif ob.status == SRIStatus.options.Annulled:
                tipo = "FACTURA ANULADA"
                subtipo = "SIN VALIDEZ TRIBUTARIA"
                number = get_bill_number_from_tree(tree)
            elif ob.status == SRIStatus.options.Sent:
                tipo = "FACTURA ANULADA"
                subtipo = "PENDIENTE DE AUTORIZACIÓN"
                number = get_bill_number_from_tree(tree)
            else:
                tipo = "PROFORMA"
                subtipo = "SIN VALIDEZ TRIBUTARIA"
                number = ob.number
            story.append(Paragraph(tipo, smallheader))
            if subtipo:
                story.append(Paragraph(subtipo, normal))
            story.append(Paragraph(number, normal))
            canvas.setTitle("{} {}".format(tipo, number))

            if ob.clave_acceso:
                story.append(Paragraph("Clave de Acceso",
                                       mediumheader))
                story.append(Paragraph(ob.clave_acceso,
                                       small))
                story.append(Image(make_barcode(ob.clave_acceso), width=c.width(1), height=c.height(0.1)))
            if ob.numero_autorizacion:
                story.append(Paragraph(u"Autorización",
                                       mediumheader))
                story.append(Paragraph(ob.numero_autorizacion,
                                       small))
                story.append(Paragraph(l10n.localize(ob.fecha_autorizacion),
                                       small))
            story.append(Paragraph("Ambiente: {}".format(ob.ambiente_sri.upper()),
                                   normal))
            add_items(story)

    with c.section(0, 1 - column_height - 0.1, 1, 1 - column_height,
                   margin=(standard_separation, 0, standard_separation, 0)):
        story = []
        story.append(Paragraph("Cliente".format(ob.issued_to.razon_social),
                               mediumheader))
        story.append(Paragraph("Razon Social / Nombres y Apellidos: {}".format(ob.issued_to.razon_social),
                               normal))
        story.append(Paragraph("Identificacion: {} {}".format(ob.issued_to.tipo_identificacion,
                                                              ob.issued_to.identificacion),
                               normal))
        story.append(Paragraph("Fecha de Emision: {}".format(l10n.localize(ob.date)),
                               normal))
        # FIXME: Guia de remision
        add_items(story)

    with c.section(0, footer_height, 1, 1 - column_height - 0.1, margin=(0, 0, 0, standard_separation)):
        headers = [(u'Cod.\nPrincipal',  c.width(0.1)),
                   (u'Cod.\nAuxiliar',   c.width(0.1)),
                   (u'Cant.',            c.width(0.1)),
                   (u'Descripción',      c.width(0.4)),
                   (u'Precio\nUnitario', c.width(0.1)),
                   (u'Dcto.',            c.width(0.1)),
                   (u'Total',            c.width(0.1))]
        data, widths = zip(*headers)
        data = [data]
        for item in ob.items:
            linea = [
                item.code,
                '',
                str(decimals(item.qty, item.sku.batch.item.decimales_qty)),
                item.name,
                str(decimals(item.unit_price, 4)),
                str(decimals(item.discount, 2)),
                str(decimals(item.total_sin_impuestos, 2))
            ]
            data.append(linea)
        detail_table = Table(data,
                             style=[('GRID', (0, 0), (-1, -1), 0.5, colors.grey)],
                             colWidths=widths)
        detail_table.hAlign = 'LEFT'
        add_items([detail_table])

    with c.section(0, 0, 1, footer_height, margin=(0, 0, 0, standard_separation)):
        col_mid_point = 0.5
        with c.section(0, 0, col_mid_point, 1, margin=(0, 0, standard_separation, 0)):
            data = [
                ["DSSTI Facturas"],
            ]
            data.append(["Descarge su comprobante en:\n   http://facturas.dssti.com"])
            extrainfo_table = Table(data, style=[('GRID', (0, 0), (-1, -1), 0.5, colors.grey)], colWidths=[c.width(1)])
            extrainfo_table.hAlign = 'LEFT'
            add_items([extrainfo_table])
        with c.section(col_mid_point, 0, 1, 1, margin=(0, 0, 0, 0)):
            data = [
                ["Subtotal IVA 12%", money_2d(ob.subtotal[12])],
                ["Subtotal IVA 0%", money_2d(ob.subtotal[0])],
                ["IVA 12%", money_2d(ob.iva[12])],
                ['ICE', money_2d(ob.total_ice)],
                ["Total a Pagar", money_2d(ob.total)],
            ]
            totals_table = Table(data,
                                 style=[('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                                        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                                        ],
                                 colWidths=[c.width(0.5),
                                            c.width(0.5),
                                            ])
            totals_table.hAlign = 'RIGHT'
            add_items([totals_table])

    canvas.showPage()
    canvas.save()

    pdf = buffer_.getvalue()
    buffer_.close()
    return pdf
