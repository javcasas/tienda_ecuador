# * encoding: utf-8 *
from datetime import date, timedelta
from calendar import LocaleHTMLCalendar, monthrange
from django.utils.html import conditional_escape as esc

from reports.templatetags.date_management import month_name


def first_day_of_month(dt):
    return dt.replace(day=1)


def last_day_of_month(dt):
    last_day = monthrange(dt.year, dt.month)[1]
    return dt.replace(day=last_day)


def first_day_of_prev_month(dt):
    first_day = first_day_of_month(dt)
    prev_month = first_day - timedelta(days=1)
    return first_day_of_month(prev_month)


def first_day_of_next_month(dt):
    last_day = last_day_of_month(dt)
    next_month = last_day + timedelta(days=1)
    return next_month


def first_day_of_year(dt):
    return dt.replace(month=1, day=1)


def last_day_of_year(dt):
    return last_day_of_month(dt.replace(month=12))


class DayItemsCalendar(LocaleHTMLCalendar):
    def get_items_for_date(self, date):
        """
        Returns pairs of (url, text)items
        """
        return []

    def get_prev_date(self):
        """
        Returns pair of (url, text) or None
        """
        return None

    def get_next_date(self):
        """
        Returns pair of (url, text) or None
        """
        return None

    def formatday(self, day, weekday):
        if day != 0:
            cssclass = self.cssclasses[weekday]
            cssclass += " col-xs-1 text-center"
            curr_date = date(self.year, self.month, day)
            if date.today() == curr_date:
                cssclass += ' warning text-warning'
            items = self.get_items_for_date(curr_date)
            if items:
                cssclass += ' success'
                body = ['<ul style="padding-left: 0px">']
                for url, text in items:
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
        if prev_date:
            a("""<a href='{}'
                    class='pull-left btn btn-default'>
                    <span class='glyphicon glyphicon-chevron-left'></span>
                        {}</a>
              """.format(prev_date[0], prev_date[1]))

        next_date = self.get_next_date()
        if next_date:
            a("""<a href='{}'
                    class='pull-right btn btn-default'>
                    {}
                    <span class='glyphicon glyphicon-chevron-right'></span></a>"""
              .format(next_date[0], next_date[1]))
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

        prev_date = self.get_prev_date()
        return ''.join(v)
