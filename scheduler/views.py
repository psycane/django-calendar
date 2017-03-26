from .models import Event
import calendar
import datetime
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.template.loader import render_to_string
from django.template.defaulttags import register
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
import json
import pytz

calendar.setfirstweekday(calendar.SUNDAY)
year_from, year_to = 1950, 2050
calendar_context = {
    'months': ['January',
               'February',
               'March',
               'April',
               'May',
               'June',
               'July',
               'August',
               'September',
               'October',
               'November',
               'December'],
    'years': range(year_from, year_to + 1),
    'weekdays': ['Sunday',
                 'Monday',
                 'Tuesday',
                 'Wednesday',
                 'Thursday',
                 'Friday',
                 'Saturday'],
}


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


def generateCalendarData(current_month, current_year):
    # Handling current month's dates
    calendar_data = calendar.monthcalendar(current_year,
                                           current_month)
    for row in range(len(calendar_data)):
        for day in range(7):
            if calendar_data[row][day]:
                calendar_data[row][day] = (calendar_data[row][day],
                                           current_month,
                                           current_year,
                                           'current')
    # Handling previous month's dates
    previous_zeroes = calendar_data[0].count(0)
    first_day = datetime.datetime(current_year,
                                  current_month,
                                  1)
    previous_day = first_day - datetime.timedelta(days=1)
    previous_month, previous_year = previous_day.month, previous_day.year
    previous_month_last_day = calendar.monthrange(previous_year,
                                                  previous_month)[1]
    for day in range(previous_zeroes):
        calendar_data[0][day] = (previous_month_last_day - previous_zeroes + day + 1,
                                 previous_month,
                                 previous_year,
                                 'previous')

    # Handling next month's dates
    next_zeroes = calendar_data[-1].count(0)
    current_month_last_day = calendar.monthrange(current_year,
                                                 current_month)[1]
    last_day = datetime.datetime(current_year,
                                 current_month,
                                 current_month_last_day)
    next_day = last_day + datetime.timedelta(days=1)
    next_month, next_year = next_day.month, next_day.year
    for day in range(next_zeroes):
        calendar_data[-1][7 - next_zeroes + day] = (day + 1,
                                                    next_month,
                                                    next_year,
                                                    'next')

    return calendar_data


def generateEventsData(events, calendar_data, current_month, current_year):
    rows, cols = len(calendar_data), 7
    events_data = {}
    start = {}
    end = {}
    for event in events:
        event_id = event.id
        event_name = event.event_name
        start_date = timezone.localtime(event.start_date)
        end_date = timezone.localtime(event.end_date)
        st, en = None, None
        for row in range(rows):
            for col in range(cols):
                date_tuple = calendar_data[row][col]
                cur_date = timezone.make_aware(datetime.datetime(date_tuple[2],
                                                                 date_tuple[1],
                                                                 date_tuple[0],
                                                                 start_date.hour,
                                                                 start_date.minute,
                                                                 start_date.second),
                                               pytz.timezone(settings.TIME_ZONE))
                if start_date <= cur_date <= end_date:
                    if not st:
                        st = date_tuple
                    en = date_tuple
                    if events_data.get(date_tuple):
                        events_data[date_tuple].append((event_id, event_name))
                    else:
                        events_data[date_tuple] = [(event_id, event_name)]

        start[st] = event_id
        end[en] = event_id
    return (start, end, events_data)


def validateEventDetails(req):
    response = True
    error = None
    event_name = req.get('event_name')
    event_location = req.get('event_location')
    event_start_date = req.get('event_start_date')
    event_start_time = req.get('event_start_time')
    event_end_date = req.get('event_end_date')
    event_end_time = req.get('event_end_time')
    event_description = req.get('event_description')
    if event_name and event_location and event_start_date and event_start_time and event_end_date and event_end_time and event_description:
        if len(event_name) <= Event._meta.get_field('event_name').max_length:
            if len(event_location) <= Event._meta.get_field('location').max_length:
                if len(event_description) <= Event._meta.get_field('description').max_length:
                    try:
                        start_date = datetime.datetime.strptime(event_start_date + ' ' + event_start_time,
                                                                '%Y-%m-%d %H:%M')
                        end_date = datetime.datetime.strptime(event_end_date + ' ' + event_end_time,
                                                              '%Y-%m-%d %H:%M')
                        if end_date >= start_date:
                            pass
                        else:
                            response = False
                            error = 'Start date cannot be greater than end date!'
                    except:
                        response = False
                        error = 'Invalid date or time format!'
                else:
                    response = False
                    error = 'Description too long!'
            else:
                response = False
                error = 'Location too long!'
        else:
            response = False
            error = 'Event name too long!'
    else:
        response = False
        error = 'Empty values not allowed!'

    return(response, error)


@ensure_csrf_cookie
def home(request):
    error = None
    if request.method == 'POST':
        req = request.POST
        if req:
            current_month = req.get('month')
            current_year = req.get('year')
            if current_month and current_year:
                current_month = int(current_month)
                current_year = int(current_year)
                if 1 <= current_month <= 12 and year_from <= current_year <= year_to:
                    calendar_context['current_month'] = current_month
                    calendar_context['current_year'] = current_year
                    calendar_data = generateCalendarData(current_month,
                                                         current_year)
                    calendar_context['calendar_data'] = calendar_data
                    print(calendar_data)
                    events = Event.objects.all()
                    start, end, events_data = generateEventsData(events,
                                                                 calendar_data,
                                                                 current_month,
                                                                 current_year)
                    calendar_context['events_data'] = events_data
                    calendar_context['event_start'] = start
                    calendar_context['event_end'] = end
                    print(events_data, start, end)

                else:
                    error = 'Out of bounds!'
            else:
                error = 'Invalid month or year!'
        else:
            error = 'Data not received!'

        if error:
            return HttpResponseBadRequest(error)
        else:
            calendar_html = render_to_string('calendar.html',
                                             context=calendar_context)
            return HttpResponse(json.dumps({'html': calendar_html}))

    now = datetime.datetime.now()
    current_month = now.month
    current_year = now.year
    current_day = now.day
    calendar_context['current_month'] = current_month
    calendar_context['current_year'] = current_year
    calendar_context['current_day'] = current_day
    calendar_data = generateCalendarData(current_month,
                                         current_year)
    calendar_context['calendar_data'] = calendar_data
    events = Event.objects.all()
    start, end, events_data = generateEventsData(events,
                                                 calendar_data,
                                                 current_month,
                                                 current_year)
    calendar_context['events_data'] = events_data
    calendar_context['event_start'] = start
    calendar_context['event_end'] = end
    return render(request, 'index.html', context=calendar_context)


@ensure_csrf_cookie
def create_event(request):
    error = None
    if request.method == 'POST':
        req = request.POST
        if req:
            response, error = validateEventDetails(req)
            if response:
                event_name = req.get('event_name')
                event_location = req.get('event_location')
                event_start_date = req.get('event_start_date')
                event_start_time = req.get('event_start_time')
                event_end_date = req.get('event_end_date')
                event_end_time = req.get('event_end_time')
                event_description = req.get('event_description')
                start_date = datetime.datetime.strptime(event_start_date + ' ' + event_start_time,
                                                        '%Y-%m-%d %H:%M')
                end_date = datetime.datetime.strptime(event_end_date + ' ' + event_end_time,
                                                      '%Y-%m-%d %H:%M')
                event = Event.objects.create(event_name=event_name,
                                             location=event_location,
                                             start_date=start_date,
                                             end_date=end_date,
                                             description=event_description)
                calendar_data = generateCalendarData(start_date.month,
                                                     start_date.year)

        else:
            error = 'Data not received!'

        if error:
            return HttpResponseBadRequest(error)
        else:
            return HttpResponse(json.dumps({'message': 'Event created successfully!'}))
    raise Http404
