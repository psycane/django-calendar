$(document).ready(function() {
    /* AJAX SETUP FOR DJANGO */
    var csrftoken = $.cookie('csrftoken');

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            }
        }
    });

    function formatDate(year, month, day) {
        year = year.toString();
        month = month.toString();
        day = day.toString();
        if (month.length < 2) month = '0' + month;
        if (day.length < 2) day = '0' + day;
        console.log(day, month, year)
        return [year, month, day].join('-');
    }

    months = {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August',
        9: 'September',
        10: 'October',
        11: 'November',
        12: 'December'
    }

    weekdays = {
        0: 'Sunday',
        1: 'Monday',
        2: 'Tuesday',
        3: 'Wednesday',
        4: 'Thursday',
        5: 'Friday',
        6: 'Saturday'
    }

    $(document).on('click', '#refresh_icon', function(e) {
        e.preventDefault();
        window.location.reload();
    });

    $(document).on('mouseover', '#calendar_body .days li', function(e) {
        e.stopPropagation();
        $(this).find('.date').css('color', '#f8f8f8');
        $(this).find('.event').css('background-color', '#f8f8f8');
        $(this).find('.event').css('color', '#2bc493');
    });

    $(document).on('mouseout', '#calendar_body .days li', function(e) {
        $(this).find('.date').css('color', '#b3b3b3');
        $(this).find('.event').css('background-color', 'white');
        $(this).find('.event').css('color', '#2bc493');
    });


    $(document).on('change', '#select_month, #select_year', function(e) {
        e.preventDefault();
        $('#greybox').show();
        var month = $('#select_month').find('option:selected').data('month_code');
        var year = $('#select_year').find('option:selected').attr('value');
        var data = {
            month: month,
            year: year
        }
        $.ajax({
            url: '/',
            type: 'POST',
            dataType: 'json',
            data: data,
            success: function(result) {
                $('#wrap_calendar').html(result.html);
                $('#greybox').hide();
            },
            error: function(result) {
                console.error(result.responseText);
                $('#greybox').hide();
            }
        });
    });

    $(document).on('click', '.date_block', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log("YYY");
        $('#greybox').show();
        var date_div = $(this).find('.date');
        day = date_div.data('day');
        month = date_div.data('month');
        year = date_div.data('year');
        weekday = date_div.data('weekday');
        var title_date = weekdays[weekday] + ', ' + day + ' ' + months[month] + ' ' + year;
        console.log(title_date);
        $('#event_start_date').val(formatDate(year, month, day));
        $('#create_event_dialog').dialog({
            draggable: false,
            resizable: false,
            modal: false,
            title: title_date,
            dialogClass: 'create_event_dialog'
        });

    });

    $(document).on('dialogclose', '#create_event_dialog', function(e) {
        $('#greybox').hide();
    });

    $(document).on('click', '#event_cancel', function(e) {
        e.preventDefault();
        $('#create_event_dialog').dialog('close');
    })

    $(document).on('submit', '#create_event_form', function(e) {
        e.preventDefault();
        $('#create_event_dialog').dialog('close');
        $('#greybox').show();
        console.log('processing...');
        var month = $('#select_month').find('option:selected').data('month_code');
        var year = $('#select_year').find('option:selected').attr('value');
        console.log(month, year);
        var data = $(this).serializeArray();
        data.push({
            name: "current_month",
            value: month
        });
        data.push({
            name: "current_year",
            value: year
        });
        console.log(data);
        $.ajax({
            url: 'create_event/',
            type: 'POST',
            dataType: 'json',
            data: data,
            success: function(result) {
                console.log(result);
                alert(result.message);
                $('#wrap_calendar').html(result.html);
                $('#greybox').hide();
            },
            error: function(result) {
                console.error(result.responseText);
                alert(result.responseText);
                $('#greybox').hide();
            }
        });
    });

    $(document).on('click', '.event', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log("TTT");
        $('#greybox').show();
        var event_id = $(this).data("id");
        var event_name = $(this).data("name");
        var data = {
            event_id: event_id
        }
        $.ajax({
            url: 'query_event/',
            type: 'POST',
            dataType: 'json',
            data: data,
            success: function(result) {
                console.log(result);
                $('#show_event_dialog #event_location').html(result["location"]);
                $('#show_event_dialog #event_time').html("Starts: " + result["start_date"] + "<br>" + "Ends: " + result["end_date"]);
                $('#show_event_dialog #event_description').html(result["description"]);
                $('#show_event_dialog #event_id').data("id", event_id);
                $('#show_event_dialog').dialog({
                    draggable: false,
                    resizable: false,
                    modal: false,
                    title: event_name,
                    dialogClass: 'show_event_dialog'
                });
            },
            error: function(result) {
                console.error(result.responseText);
                $('#greybox').hide();
            }
        });
    });

    $(document).on('dialogclose', '#show_event_dialog', function(e) {
        $('#greybox').hide();
    });

    $(document).on('click', '#show_event_dialog #event_delete', function(e) {
        e.preventDefault();
        if (confirm("Are you sure?")) {
            var event_id = $(this).parent().data("id");
            console.log(event_id);
            var month = $('#select_month').find('option:selected').data('month_code');
            var year = $('#select_year').find('option:selected').attr('value');
            var data = {
                event_id: event_id,
                current_month: month,
                current_year: year
            }
            $.ajax({
                url: 'delete_event/',
                type: 'POST',
                dataType: 'json',
                data: data,
                success: function(result) {
                    console.log(result);
                    alert(result.message);
                    $('#wrap_calendar').html(result.html);
                    $('#show_event_dialog').dialog('close');
                    $('#greybox').hide();
                },
                error: function(result) {
                    console.error(result.responseText);
                    $('#greybox').hide();
                }
            });
        }
    });
});
