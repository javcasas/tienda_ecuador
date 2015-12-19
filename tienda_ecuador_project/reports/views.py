# -- coding: utf8 --
import pytz
from decimal import Decimal
from datetime import datetime, timedelta
from calendar import LocaleHTMLCalendar, monthrange
from datetime import date
from itertools import groupby

from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape as esc

from company_accounts.views import CompanyView, CompanySelected
from billing.models import Bill
from accounts_receivable.models import Payment

from templatetags.date_management import month_name

from sri.models import SRIStatus

tz = pytz.timezone('America/Guayaquil')


class ReportsIndexView(CompanyView,
                       CompanySelected,
                       DetailView):
    """
    View that shows a general index for a given company
    """
    template_name = 'reports/company_index.html'

    def get_context_data(self, **kwargs):
        context = super(ReportsIndexView, self).get_context_data(**kwargs)
        context['year'] = date.today().year
        context['month'] = date.today().month
        context['day'] = date.today().day
        return context


class DayItemsCalendar(LocaleHTMLCalendar):
    def __init__(self, items):
        """
            @param items: {day: [(url, name)]}
        """
        super(DayItemsCalendar, self).__init__()
        self.items = items

    def formatday(self, day, weekday):
        if day != 0:
            cssclass = self.cssclasses[weekday]
            cssclass += " col-xs-1 text-center"
            if date.today() == date(self.year, self.month, day):
                cssclass += ' warning text-warning'
            if day in self.items:
                cssclass += ' success'
                body = ['<ul style="padding-left: 0px">']
                for item in self.items[day]:
                    url, text = item
                    body.append('<li style="display: inline">')
                    body.append('<a href="%s">' % url)
                    body.append(esc(text))
                    body.append('</a></li>')
                body.append('</ul>')
                return self.day_cell(cssclass, '%d %s' % (day, ''.join(body)))
            return self.day_cell(cssclass, day)
        return self.day_cell('noday', '&nbsp;')

    def day_cell(self, cssclass, body):
        return (
            '<td class="day {cls}">{body}</td>'
            ).format(cls=cssclass, body=body)

    def formatweekheader(self):
        res = []
        for d, cls in [(u"Lunes", 'mon'),
                       (u"Martes", 'tue'),
                       (u"Miércoles", 'wed'),
                       (u"Jueves", 'thu'),
                       (u"Viernes", 'fri'),
                       (u"Sábado", 'sat'),
                       (u"Domingo", 'sun')]:
            css_class = cls + " text-center col-xs-1"
            res.append(u'<th class="{cls}">{name}</th>'
                       .format(cls=css_class, name=d))
        return u"".join(res)

    def formatmonthname(self, year, month, withyear=True):
        return (
            '<tr><th colspan="7" class="month">{month} {year}</th></tr>'
            ).format(year=year, month=month_name(month))

    def formatmonth(self, theyear, themonth, withyear=True):
        """
        Return a formatted month as a table.
        """
        self.year, self.month = theyear, themonth
        v = []
        a = v.append
        a('<table border="0" cellpadding="0" cellspacing="0"'
          'class="table table-bordered calendar">\n')
        a(self.formatmonthname(theyear, themonth, withyear=withyear))
        a('\n')
        a(self.formatweekheader())
        a('\n')
        for week in self.monthdays2calendar(theyear, themonth):
            a(self.formatweek(week))
            a('\n')
        a('</table>\n')
        return ''.join(v)


class DateListReport(CompanySelected, ListView):
    """
    Base class for reports on a date range
    """
    model = None
    context_object_name = None
    url_suffix = None
    ambiente_sri = 'produccion'

    @property
    def report_url_year(self):
        res = "report_yearly" + self.url_suffix
        if self.ambiente_sri == 'pruebas':
            res += '.pruebas'
        return res

    @property
    def report_url_month(self):
        res = "report_monthly" + self.url_suffix
        if self.ambiente_sri == 'pruebas':
            res += '.pruebas'
        return res

    @property
    def report_url_day(self):
        res = "report_daily" + self.url_suffix
        if self.ambiente_sri == 'pruebas':
            res += '.pruebas'
        return res

    @property
    def company_id(self):
        return self.kwargs['company_id']

    @property
    def year(self):
        return int(self.kwargs['year'])

    @property
    def month(self):
        return int(self.kwargs['month'])

    @property
    def day(self):
        return int(self.kwargs['day'])

    def get_context_data(self, **kwargs):
        context = super(DateListReport, self).get_context_data(**kwargs)

        context['year'] = self.year
        context['month'] = int(self.kwargs.get('month', 0)) or None
        context['day'] = int(self.kwargs.get('day', 0)) or None

        context['prev_date'] = self.get_context_prev_date()
        context['next_date'] = self.get_context_next_date()

        context['total'] = self.get_total(self.get_queryset())
        context['report_url_day'] = self.report_url_day
        context['report_url_month'] = self.report_url_month
        context['report_url_year'] = self.report_url_year

        context['ambiente_sri'] = self.ambiente_sri
        return context


class PaymentDateListReport(DateListReport):
    """
    Mixin for payment reports
    """
    model = Payment
    context_object_name = "payment_list"
    url_suffix = '_income'

    @property
    def report_url_year(self):
        res = "report_yearly" + self.url_suffix
        if self.ambiente_sri == 'pruebas':
            res += '.pruebas'
        return res

    @property
    def report_url_month(self):
        res = "report_monthly" + self.url_suffix
        if self.ambiente_sri == 'pruebas':
            res += '.pruebas'
        return res

    @property
    def report_url_day(self):
        res = "report_daily" + self.url_suffix
        if self.ambiente_sri == 'pruebas':
            res += '.pruebas'
        return res

    def get_queryset(self, start_date=None, end_date=None):
        if not start_date or not end_date:
            start_date, end_date = self.get_date_range()
        res = (self.model.objects
               .filter(receivable__bill__company=self.company)
               .filter(receivable__bill__ambiente_sri=self.ambiente_sri)
               .filter(date__gte=start_date)
               .filter(date__lte=end_date))
        return res

    def get_total(self, items):
        return sum([i.qty for i in items], Decimal(0))

    def format_text(self, item_list):
        if len(item_list) == 1:
            template = "{} cobro, ${:.2f}"
        else:
            template = "{} cobros, ${:.2f}"
        return template.format(len(item_list),
                               self.get_total(item_list))


class BillDateListReport(DateListReport):
    """
    Mixin for Bill reports
    """
    model = Bill
    context_object_name = "bill_list"
    report_url_year = "report_yearly_bills"
    report_url_month = "report_monthly_bills"
    report_url_day = "report_daily_bills"

    def get_queryset(self, start_date=None, end_date=None):
        if not start_date or not end_date:
            start_date, end_date = self.get_date_range()
        res = (self.model.objects
               .filter(company=self.company)
               .filter(status=SRIStatus.options.Accepted)
               .filter(ambiente_sri=self.ambiente_sri)
               .filter(date__gte=start_date)
               .filter(date__lte=end_date))
        return res

    def get_total(self, items):
        return sum([i.total_sin_iva for i in items], Decimal(0))

    def format_text(self, item_list):
        if len(item_list) == 1:
            template = "{} facturas, ${:.2f}"
        else:
            template = "{} facturas, ${:.2f}"
        return template.format(len(item_list),
                               self.get_total(item_list))


class YearListReport(object):
    """
    Mixin for yearly reports
    """
    def get_date_range(self):
        start_date = datetime(self.year, 1, 1)
        end_date = datetime(self.year, 12, 31, 23, 59, 59)
        return start_date, end_date

    def get_context_prev_date(self):
        return {
            'url': reverse(self.report_url_year,
                           args=(self.company.id, self.year - 1)),
            'text': "Año {}".format(self.year - 1),
        }

    def get_context_next_date(self):
        if date.today().year > self.year:
            return {
                'url': reverse(self.report_url_year,
                               args=(self.company.id, self.year + 1)),
                'text': "Año {}".format(self.year + 1),
            }

    def get_context_data(self, **kwargs):
        context = super(YearListReport, self).get_context_data(**kwargs)

        items = self.get_queryset()

        grouped_by_date = {month: list(i)
                           for month, i
                           in groupby(items, lambda x: x.date.month)}

        joined_by_date = [
            (month,
             reverse(self.report_url_month,
                     args=(self.company.id, self.year, month)),
             len(grouped_by_date.get(month, [])),
             self.get_total(grouped_by_date.get(month, []))
             )
            for month in range(1, 13)
        ]

        context['date_items'] = joined_by_date
        return context


class MonthListReport(object):
    """
    Mixin for month reports
    """

    def get_date_range(self):
        start_date = datetime(self.year, self.month, 1)
        last_day = monthrange(self.year, self.month)[1]
        end_date = datetime(self.year, self.month, last_day,
                            23, 59, 59)
        return start_date, end_date

    def get_context_prev_date(self):
        dt = (date(self.year, self.month, 1)
              - timedelta(days=1)).replace(day=1)
        return {
            'url': reverse(self.report_url_month,
                           args=(self.company.id, dt.year, dt.month)),
            'text': "{} / {}".format(month_name(dt.month), dt.year),
        }

    def get_context_next_date(self):
        dt = (date(self.year, self.month, 1)
              + timedelta(days=31)).replace(day=1)
        if date.today() >= dt:
            return {
                'url': reverse(self.report_url_month,
                               args=(self.company.id, dt.year, dt.month)),
                'text': "{} / {}".format(month_name(dt.month), dt.year),
            }

    def get_context_data(self, **kwargs):
        context = super(MonthListReport, self).get_context_data(**kwargs)

        items = self.get_queryset()

        grouped_by_date = [(day, list(i))
                           for day, i in groupby(items, lambda x: x.date.day)]

        joined_by_date = {
            day: [(reverse(self.report_url_day,
                           args=(self.company.id, self.year, self.month, day)),
                   self.format_text(item_list))]
            for day, item_list in grouped_by_date}

        context['calendar'] = mark_safe(
            DayItemsCalendar(joined_by_date)
            .formatmonth(self.year, self.month)
        )

        return context


class DayListReport(object):
    """
    Mixin for day reports
    """
    def get_date_range(self):
        start_date = datetime(self.year, self.month, self.day)
        end_date = datetime(self.year, self.month, self.day, 23, 59, 59)
        return start_date, end_date

    def get_context_prev_date(self):
        dt = date(self.year, self.month, self.day) - timedelta(days=1)
        return {
            'url': reverse(self.report_url_day,
                           args=(self.company.id, dt.year, dt.month, dt.day)),
            'text': "{} / {} / {}".format(
                dt.day, month_name(dt.month), dt.year),
        }

    def get_context_next_date(self):
        dt = date(self.year, self.month, self.day) + timedelta(days=1)
        if date.today() >= dt:
            return {
                'url': reverse(
                    self.report_url_day,
                    args=(self.company.id, dt.year, dt.month, dt.day)),
                'text': "{} / {} / {}".format(
                    dt.day, month_name(dt.month), dt.year),
            }

    def get_context_data(self, **kwargs):
        context = super(DayListReport, self).get_context_data(**kwargs)

        last_day = monthrange(self.year, self.month)[1]
        items = self.get_queryset(
            start_date=datetime(self.year, self.month, 1),
            end_date=datetime(self.year, self.month, last_day,
                              23, 59, 59)
        )

        grouped_by_date = [(day, list(i))
                           for day, i in groupby(items, lambda x: x.date.day)]

        joined_by_date = {
            day: [(reverse(self.report_url_day,
                           args=(self.company.id, self.year, self.month, day)),
                   self.format_text(item_list))]
            for day, item_list in grouped_by_date}

        context['calendar'] = mark_safe(
            DayItemsCalendar(joined_by_date)
            .formatmonth(self.year, self.month)
        )

        return context


class PaymentYearListReport(YearListReport, PaymentDateListReport):
    template_name = 'reports/sri/income_year.html'


class BillYearListReport(YearListReport, BillDateListReport):
    template_name = 'reports/sri/bills_year.html'


class PaymentMonthListReport(MonthListReport, PaymentDateListReport):
    template_name = 'reports/sri/income_month.html'


class BillMonthListReport(MonthListReport, BillDateListReport):
    template_name = 'reports/sri/bills_month.html'


class PaymentDayListReport(DayListReport, PaymentDateListReport):
    template_name = 'reports/sri/income_day.html'


class BillDayListReport(DayListReport, BillDateListReport):
    template_name = 'reports/sri/bills_day.html'
