from .models import Event
import calendar
import datetime
from django.conf import settings
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.template.defaulttags import register
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
import json
import pytz

# Calendar settings
calendar.setfirstweekday(calendar.SUNDAY)
year_from, year_to = 1950, 2050


def stringToDateTime(date, time, _format='%Y-%m-%d %H:%M'):
    """ Combine date and time from string to datetime object """
    return datetime.datetime.strptime(' '.join([date, time]),
                                      _format)


def datetimeToString(date, _format):
    """ Converts datetime object to a string """
    return date.strftime(_format)


def generateCalendarData(current_month, current_year):
    """ Returns a list containing all the dates to view on the web page for current month and current year """

    current_month = int(current_month)
    current_year = int(current_year)

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
    """ Reads events and calendar data and returns data about the events to display on the web page """

    rows, cols = len(calendar_data), 7
    events_data = {}

    for event in events:
        event_id = event.id
        event_name = event.event_name

        # Converting naive datetime to active
        start_date = timezone.localtime(event.start_date)
        end_date = timezone.localtime(event.end_date)

        for row in range(rows):
            for col in range(cols):
                date_tuple = calendar_data[row][col]

                # Converting naive datetime to active
                cur_date = timezone.make_aware(datetime.datetime(date_tuple[2],
                                                                 date_tuple[1],
                                                                 date_tuple[0],
                                                                 start_date.hour,
                                                                 start_date.minute,
                                                                 start_date.second),
                                               pytz.timezone(settings.TIME_ZONE))

                if start_date <= cur_date <= end_date:

                    # If an event exists append else create a new list
                    if events_data.get(date_tuple):
                        events_data[date_tuple].append((event_id, event_name))
                    else:
                        events_data[date_tuple] = [(event_id, event_name)]

    return events_data


def processContext(current_month, current_year, event_query, data=None):
    error = None

    # Initialize calendar context
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
        'current_month': current_month,
        'current_year': current_year
    }

    # To highlight today's date if present in the calendar view
    now = datetime.datetime.now()
    current_day = now.day if current_month == now.month and current_year == now.year else None
    calendar_context['current_day'] = current_day

    # Receives the calendar's data based on current month and current year
    calendar_data = generateCalendarData(current_month,
                                         current_year)

    # Stores the first date of the view
    first_date = datetime.datetime(calendar_data[0][0][2],
                                   calendar_data[0][0][1],
                                   calendar_data[0][0][0],
                                   0,
                                   0,
                                   0)

    # Stores the last date of the view
    last_date = datetime.datetime(calendar_data[-1][-1][2],
                                  calendar_data[-1][-1][1],
                                  calendar_data[-1][-1][0],
                                  23,
                                  59,
                                  59)

    calendar_context['calendar_data'] = calendar_data

    # Handle all the queries with the database
    if event_query == 'show':
        # Pass to fetch the details of all the events from first_date to
        # last_date
        pass

    elif event_query == 'create':
        # Creates a new entry in the database

        # Get all information from the variable data
        event_name = data.get('event_name')
        event_location = data.get('event_location')
        event_start_date = data.get('event_start_date')
        event_start_time = data.get('event_start_time')
        event_end_date = data.get('event_end_date')
        event_end_time = data.get('event_end_time')
        event_description = data.get('event_description')

        # Combine date and time from string to datetime object
        start_date = stringToDateTime(event_start_date,
                                      event_start_time)
        end_date = stringToDateTime(event_end_date,
                                    event_end_time)

        # Create an object with all the values
        event = Event.objects.create(event_name=event_name,
                                     location=event_location,
                                     start_date=start_date,
                                     end_date=end_date,
                                     description=event_description)

    elif event_query == 'edit':
        # Edits a previously stored event in the database

        event_id = data.get("event_id")
        if event_id:
            event = Event.objects.get(id=event_id)
            if event:

                # Get all information fromt the variable data
                event_name = data.get('event_name')
                event_location = data.get('event_location')
                event_start_date = data.get('event_start_date')
                event_start_time = data.get('event_start_time')
                event_end_date = data.get('event_end_date')
                event_end_time = data.get('event_end_time')
                event_description = data.get('event_description')

                # Combine date and time from string to datetime object
                start_date = stringToDateTime(event_start_date,
                                              event_start_time)
                end_date = stringToDateTime(event_end_date,
                                            event_end_time)

                # Update the values
                event.event_name = event_name
                event.location = event_location
                event.start_date = start_date
                event.end_date = end_date
                event.description = event_description

                # Save event
                event.save()
            else:
                error = 'No record found for this event id!'
        else:
            error = 'Blank id received for editing event!'

    elif event_query == 'delete':
        # Deletes an event from the database

        event_id = data.get('event_id')
        if event_id:
            event = Event.objects.filter(id=event_id)
            if event:
                # Delete event
                event.delete()
            else:
                error = 'No data found for this event id!'
        else:
            error = 'Blank event id not allowed!'
    else:
        error = 'Unknown query!'

    # Fetch only those events that we have to display based on first date and
    # last date of the calendar view
    events = Event.objects.filter(Q(start_date__range=[first_date, last_date]) | Q(
        end_date__range=[first_date, last_date]))

    # Use the events to generate events data to display
    events_data = generateEventsData(events,
                                     calendar_data,
                                     current_month,
                                     current_year)

    calendar_context['events_data'] = events_data
    return (error, calendar_context)


def validateEventDetails(req):
    response = True
    error = None

    # Get all the information about event
    event_name = req.get('event_name')
    event_location = req.get('event_location')
    event_start_date = req.get('event_start_date')
    event_start_time = req.get('event_start_time')
    event_end_date = req.get('event_end_date')
    event_end_time = req.get('event_end_time')
    event_description = req.get('event_description')

    # Validate based on the model
    if event_name and event_location and event_start_date and event_start_time and event_end_date and event_end_time and event_description:
        if len(event_name) <= Event._meta.get_field('event_name').max_length:
            if len(event_location) <= Event._meta.get_field('location').max_length:
                if len(event_description) <= Event._meta.get_field('description').max_length:
                    try:

                        # Combine date and time from string to datetime object
                        start_date = stringToDateTime(event_start_date,
                                                      event_start_time)
                        end_date = stringToDateTime(event_end_date,
                                                    event_end_time)

                        # Event start time should be <= event end time
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

    return (response, error)


@ensure_csrf_cookie
def home(request):
    """ Loads the calendar for current month and year if request == GET else the calendar for month and year mentioned in the POST request """
    error = None
    if request.method == 'POST':
        req = request.POST
        if req:
            current_month = req.get('month')
            current_year = req.get('year')
            if current_month and current_year:
                current_month = int(current_month)
                current_year = int(current_year)

                # Validate current month and current year
                if 1 <= current_month <= 12 and year_from <= current_year <= year_to:
                    error, calendar_context = processContext(current_month,
                                                             current_year,
                                                             'show')
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

    # Load the calendar for current month and current year
    now = datetime.datetime.now()
    current_month = now.month
    current_year = now.year

    error, calendar_context = processContext(current_month,
                                             current_year,
                                             'show')

    if error:
        return HttpResponseBadRequest(error)
    else:
        return render(request, 'index.html', context=calendar_context)


@ensure_csrf_cookie
def create_event(request):
    """ Receives data from POST request and creates a new event or edits an existing event based on the query type """
    error = None
    if request.method == 'POST':
        req = request.POST
        if req:
            response, error = validateEventDetails(req)
            # If validates go ahead else do nothing
            if response:
                current_month = req.get("current_month")
                current_year = req.get("current_year")
                if current_month and current_year:
                    current_month = int(current_month)
                    current_year = int(current_year)

                    # Validate current month and current year
                    if 1 <= current_month <= 12 and year_from <= current_year <= year_to:

                        if req.get('editing'):
                            # Editing query
                            error, calendar_context = processContext(current_month,
                                                                     current_year,
                                                                     'edit',
                                                                     data=req)
                        else:
                            # Create query
                            error, calendar_context = processContext(current_month,
                                                                     current_year,
                                                                     'create',
                                                                     data=req)
                    else:
                        error = 'Out of bounds!'
                else:
                    error = "Invalid month or year!"
            else:
                pass
        else:
            error = 'Data not received!'

        if error:
            return HttpResponseBadRequest(error)
        else:
            calendar_html = render_to_string('calendar.html',
                                             context=calendar_context)
            if req.get('editing'):
                return HttpResponse(json.dumps({'message': 'Event edited successfully!', 'html': calendar_html}))
            else:
                return HttpResponse(json.dumps({'message': 'Event created successfully!', 'html': calendar_html}))

    raise Http404  # GET request not allowed


@ensure_csrf_cookie
def query_event(request):
    """ Returns event data based on the event id """
    error = None
    if request.method == 'POST':
        req = request.POST
        if req:
            event_id = req.get('event_id')
            if event_id:
                event = Event.objects.filter(id=event_id)
                if event:
                    # Fetch all the details from the database
                    name = event[0].event_name
                    location = event[0].location
                    description = event[0].description
                    start_date_datetime = timezone.localtime(
                        event[0].start_date)
                    end_date_datetime = timezone.localtime(event[0].end_date)

                    # Convert datetime to string object
                    start_date = datetimeToString(start_date_datetime,
                                                  '%-I:%M %p, %A, %b %-d')
                    start_time_24hr = datetimeToString(start_date_datetime,
                                                       '%H:%M')
                    end_date = datetimeToString(end_date_datetime,
                                                '%-I:%M %p, %A, %b %-d')
                    end_time_24hr = datetimeToString(end_date_datetime,
                                                     '%H:%M')

                    start_day = start_date_datetime.day
                    start_month = start_date_datetime.month
                    start_year = start_date_datetime.year
                    end_day = end_date_datetime.day
                    end_month = end_date_datetime.month
                    end_year = end_date_datetime.year

                    # Hash all the data
                    event_data = {
                        'name': name,
                        'location': location,
                        'start_date': start_date,
                        'end_date': end_date,
                        'description': description,
                        'start_time_24hr': start_time_24hr,
                        'end_time_24hr': end_time_24hr,
                        'start_day': start_day,
                        'start_month': start_month,
                        'start_year': start_year,
                        'end_day': end_day,
                        'end_month': end_month,
                        'end_year': end_year,
                    }

                else:
                    error = 'No data found for this event id!'
            else:
                error = 'Blank event id not allowed!'
        else:
            error = 'Data not received!'

        if error:
            return HttpResponseBadRequest(error)
        else:
            return HttpResponse(json.dumps(event_data))

    raise Http404  # GET request not allowed


@ensure_csrf_cookie
def delete_event(request):
    """ Deletes the event based on the event id """
    error = None
    if request.method == 'POST':
        req = request.POST
        if req:
            current_month = req.get("current_month")
            current_year = req.get("current_year")
            if current_month and current_year:
                current_month = int(current_month)
                current_year = int(current_year)

                # Validate current month and current year
                if 1 <= current_month <= 12 and year_from <= current_year <= year_to:
                    # Delete query
                    error, calendar_context = processContext(current_month,
                                                             current_year,
                                                             'delete',
                                                             data=req)
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
            return HttpResponse(json.dumps({'message': 'Event deleted successfully!', 'html': calendar_html}))

    raise Http404  # GET request not allowed
