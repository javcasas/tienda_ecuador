# * coding: utf-8 *
import pytz
from io import BytesIO
from contextlib import contextmanager

import PIL.Image

from django.core.urlresolvers import reverse

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, Frame, Table, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from util.sri_models import SRIStatus

tz = pytz.timezone('America/Guayaquil')


def gen_bill_ride(ob):
    print "Generating PDF"
    try:
        res = gen_bill_ride_stuff(ob)
        print "GENERATED"
        return res
    except Exception, e:
        print "ERROR"
        print e
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


def gen_bill_ride_stuff(ob):
    buffer_ = BytesIO()


    styles = getSampleStyleSheet()

    p = canvas.Canvas(buffer_, pagesize=A4)
    pagesize = A4
    margin = inch, inch, inch, inch
    standard_separation = inch / 20


    c = RenderStack(0, 0, pagesize[0], pagesize[1], margin=margin)
    #p.roundRect(c.x(0), c.y(0), c.width(1), c.height(1), 3, stroke=1, fill=0)

    def get_warning():
        if ob.status == SRIStatus.options.Annulled:
            return "ANULADO", "SIN VALIDEZ TRIBUTARIA"
        elif ob.status == SRIStatus.options.Sent:
            return "PENDIENTE DE AUTORIZACIÓN", ""
        else:
            return "PROFORMA", "SIN VALIDEZ TRIBUTARIA"

    warning = get_warning()
    if warning:
        p.saveState()
        p.setFillColorCMYK(0, 0, 0, 0.4)
        p.setStrokeColorCMYK(0, 0, 0, 0.4)
        p.setFont("Helvetica", 50)

        items = len(warning)
        total_height = 60 * items
        p.translate(c.x(0.5), c.y(0.7))
        p.rotate(45)
        p.translate(0, total_height / 2)
        for item in warning:
            p.drawCentredString(0, 0, item)
            p.translate(0, -60)

        p.restoreState()

    def add_items(items):
        f = Frame(c.x(0), c.y(0), c.width(1), c.height(1),
                  showBoundary=0,
                  leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0)
        f.addFromList(items, p)
        if items:
            raise Exception("Does not fit - items left")

    from reportlab.lib import utils

    def get_image(path, width=1*inch, height=1*inch):
        img = utils.ImageReader(path)
        iw, ih = img.getSize()
        aspect = ih / float(iw)
        if width * aspect > height:
            return Image(path, width=(height/aspect), height=height)
        else:
            return Image(path, width=width, height=(width * aspect))

    column_height = 0.3
    with c.section(0, 1 - column_height, 1, 1):
        column_width = 0.5
        # columna izquierda
        with c.section(0, 0, column_width, 1, margin=(0, 0, standard_separation, 0)):
            if ob.company.get_logo():
                with c.section(0, 0.5, 1, 1, margin=standard_separation):
                    # logo
                    fn = ob.company.get_logo()
                    add_items(
                        [get_image(fn, width=c.width(1), height=c.height(1))]
                    )
            with c.section(0, 0, 1, column_width, margin=standard_separation):
                story = []
                if ob.company.nombre_comercial:
                    story.append(Paragraph(ob.company.nombre_comercial, styles['Normal']))
                story.append(Paragraph("Razon Social: {}".format(ob.company.razon_social), styles['Normal']))
                story.append(Paragraph("Direccion Matriz: {}".format(ob.company.direccion_matriz), styles['Normal']))
                story.append(Paragraph("Direccion Sucursal: {}".format(ob.punto_emision.establecimiento.direccion), styles['Normal']))
                if ob.company.contribuyente_especial:
                    story.append(Paragraph("Contribuyente Especial: {}".format(ob.company.contribuyente_especial), styles['Normal']))
                if ob.company.obligado_contabilidad:
                    story.append(Paragraph("SI Obligado a llevar Contabilidad", styles['Normal']))
                else:
                    story.append(Paragraph("NO Obligado a llevar Contabilidad", styles['Normal']))
                add_items(story)
            
        # columna derecha
        with c.section(column_width, 0, 1, 1, margin=standard_separation):
            story.append(Paragraph("RUC {}".format(ob.company.ruc), styles['Normal']))
            if ob.status == SRIStatus.options.Accepted:
                story.append(Paragraph("FACTURA", styles['Normal']))
            elif ob.status == SRIStatus.options.Annulled:
                story.append(Paragraph("FACTURA ANULADA", styles['Normal']))
                story.append(Paragraph("SIN VALIDEZ TRIBUTARIA", styles['Normal']))  # FIXME: poner en grande
            elif ob.status == SRIStatus.options.Sent:
                story.append(Paragraph("FACTURA", styles['Normal']))
                story.append(Paragraph("PENDIENTE DE AUTORIZACIÓN", styles['Normal'])) # FIXME: poner en grande
            else:
                story.append(Paragraph("PROFORMA", styles['Normal']))
                story.append(Paragraph("SIN VALIDEZ TRIBUTARIA", styles['Normal'])) # FIXME: poner en grande
            story.append(Paragraph("{}".format(ob.number), styles['Normal']))
            if ob.clave_acceso:
                story.append(Paragraph("Clave de Acceso", styles['Normal']))
                story.append(Paragraph(ob.clave_acceso, styles['Normal']))
            if ob.numero_autorizacion:
                story.append(Paragraph(u"Autorización", styles['Normal']))
                story.append(Paragraph(ob.numero_autorizacion, styles['Normal']))
                story.append(Paragraph(str(ob.fecha_autorizacion), styles['Normal']))
            story.append(Paragraph("Ambiente: {}".format(ob.ambiente_sri.upper()), styles['Normal']))
            # if ambiente == 'pruebas': FIXME poner en grande
            add_items(story)

    with c.section(0, 1 - column_height - 0.1, 1, 1 - column_height, margin=(standard_separation, 0, standard_separation, 0)):
        story = []
        story.append(Paragraph("Razon Social / Nombres y Apellidos: {}".format(ob.issued_to.razon_social), styles['Normal']))
        story.append(Paragraph("Identificacion: {} {}".format(ob.issued_to.tipo_identificacion, ob.issued_to.identificacion), styles['Normal']))
        story.append(Paragraph("Fecha de Emision {}".format(ob.date), styles['Normal']))
        # FIXME: Guia de remision
        # story.append(Paragraph("Guia de Remision 001-001-00000003", styles['Normal']))
        add_items(story)

    footer_height = 0.25
    with c.section(0, footer_height, 1, 1 - column_height - 0.1, margin=(0, 0, 0, standard_separation)):
        #linea = ['001', '001', '3', 'Cosa', '20', '0', '60']
        data = [['Cod.\nPrincipal', 'Cod.\nAuxiliar', 'Cant.', 'Descripcion', 'Precio\nUnitario', 'Dcto.', 'Total']]
        for item in ob.items:
            linea = [
                item.sku,
                '',
                str(item.qty),
                item.name,
                str(item.unit_price),
                str(item.descuento),
                str(item.total_sin_impuestos)
            ]
            data.append(linea)
        detail_table = Table(data,
                             style=[('GRID', (0, 0), (-1, -1), 0.5, colors.grey)],
                             colWidths=[c.width(0.1),
                                        c.width(0.1),
                                        None,
                                        None,
                                        c.width(0.1),
                                        c.width(0.1),
                                        c.width(0.1),
                                       ])
        detail_table.hAlign = 'LEFT'
        add_items([detail_table])

    with c.section(0, 0, 1, footer_height, margin=(0, 0, 0, standard_separation)):
        col_mid_point = 0.5
        with c.section(0, 0, col_mid_point, 1, margin=(0, 0, standard_separation, 0)):
            data = [
                ["DSSTI Facturas"],
            ]
            data.append(["Descarge su comprobante en:\n   http://facturas.dssti.com"])
            extrainfo_table = Table(data, style=[('GRID', (0, 0), (-1, -1), 0.5, colors.grey)])
            extrainfo_table.hAlign = 'LEFT'
            add_items([extrainfo_table])
        with c.section(col_mid_point, 0, 1, 1, margin=(0, 0, 0, 0)):
            data = [
                ["Subtotal IVA 12%", ob.subtotal[12]],
                ["Subtotal IVA 0%", ob.subtotal[0]],
                ["IVA 12%", ob.iva[12]],
                ["Total a Pagar", ob.total],
            ]
            totals_table = Table(data,
                                 style=[('GRID', (0, 0), (-1, -1), 0.5, colors.grey)],
                                 colWidths=[c.width(0.5),
                                            c.width(0.5),
                                           ])
            totals_table.hAlign = 'RIGHT'
            add_items([totals_table])

    p.showPage()
    p.save()

    pdf = buffer_.getvalue()
    buffer_.close()
    return pdf
