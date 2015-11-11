# -- coding: utf8 --
import tempfile
import os
import base64
import pytz
from decimal import Decimal
from datetime import datetime, timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.forms.models import model_to_dict

from company_accounts.views import CompanyView, CompanySelected
from billing.views import BillView
from accounts_receivable.models import Payment

tz = pytz.timezone('America/Guayaquil')


class ReportsIndexView(CompanyView,
                       CompanySelected,
                       DetailView):
    """
    View that shows a general index for a given company
    """
    template_name = 'reports/company_index.html'




from calendar import LocaleHTMLCalendar
from datetime import date
from itertools import groupby

from django.utils.html import conditional_escape as esc


class DayItemsCalendar(LocaleHTMLCalendar):
    def __init__(self, items):
        """
            @param items: [(day:int, [(url, name)])]
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
                print self.items
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
        return '<td class="%s" style="height:5em; vertical-align: top">%s</td>' % (cssclass, body)

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
            res.append(u'<th class="{cls}">{name}</th>'.format(cls=css_class, name=d))
        return u"".join(res)

    def formatmonth(self, theyear, themonth, withyear=True):
        """
        Return a formatted month as a table.
        """
        self.year, self.month = theyear, themonth
        v = []
        a = v.append
        a('<table border="0" cellpadding="0" cellspacing="0" class="table table-bordered">')
        a('\n')
        a(self.formatmonthname(theyear, themonth, withyear=withyear))
        a('\n')
        a(self.formatweekheader())
        a('\n')
        for week in self.monthdays2calendar(theyear, themonth):
            a(self.formatweek(week))
            a('\n')
        a('</table>')
        a('\n')
        return ''.join(v)


from django.utils.safestring import mark_safe

class PaymentDateListReport(CompanySelected, ListView):
    model = Payment
    context_object_name = "payment_list"
    template_name = 'reports/sri/income.html'

    def get_date_range(self):
        import calendar
        p_month = int(self.kwargs.get('month', 0))
        p_day = int(self.kwargs.get('day', 0))

        year = int(self.kwargs['year'])
        month = [1, 12]
        day = [1, 31]

        if p_month:
            month = [p_month, p_month]
            day = [1, calendar.monthrange(year, p_month)[1]]
            if p_day:
                day = [p_day, p_day]
        start_date = datetime(year, month[0], day[0])
        end_date = datetime(year, month[1], day[1], 23, 59, 59)
        return start_date, end_date

    def get_queryset(self):
        start_date, end_date = self.get_date_range()
        res = (self.model.objects
                .filter(receivable__bill__company=self.company)
                .filter(date__gte=start_date)
                .filter(date__lte=end_date))
        return res

    @property
    def company_id(self):
        return self.kwargs['company_id']

    def get_context_data(self, **kwargs):
        context = super(PaymentDateListReport, self).get_context_data(**kwargs)

        theyear = context['year'] = self.kwargs.get('year')
        themonth = context['month'] = self.kwargs.get('month')
        theday = context['day'] = self.kwargs.get('day')

        context['prev_month'] = (date(int(theyear), int(themonth), 1) - timedelta(days=1)).replace(day=1)
        context['next_month'] = (date(int(theyear), int(themonth), 1) + timedelta(days=31)).replace(day=1)

        items = self.get_queryset()
        grouped_by_days = [(day, list(i)) for day, i in groupby(items, lambda x: x.date.day)]
        def format_text(item_list):
            if len(item_list) == 1:
                template = "{} cobro, ${:.2f}"
            else:
                template = "{} cobros, ${:.2f}"
            return template.format(len(item_list), sum([c.qty for c in item_list]))
            
        joined_by_days = dict([
            (day,
             [(reverse("report_daily_income", args=(self.company.id, theyear, themonth, day)),
               format_text(item_list))
             ]
            )
            for day, item_list in grouped_by_days])

        context['calendar'] = mark_safe(
            DayItemsCalendar(joined_by_days)
            .formatmonth(int(context['year']), int(context['month']))
        )
        context['total'] = sum([i.qty for i in items], Decimal(0))
        return context
