//TODO: ON calendar optionally show archived bookings

function load_data(client_id, start_date, end_date) {
    // pass parameters like this:
    //init({{ object.client_id }}, "{{ NOW|date:"d/m/Y" }}","{{ MAX_DATE|date:"d/m/Y" }}");

    // when page is first loaded



    // get list of activity and setup editable
    $.ajax({
        type:"get",
        url:API+"activities",
        dataType : 'json',
        success:function(data){

            var objects = data.objects;
            var list = [];
            $.each(objects, function(i,d) {
                list.push({value: d.id, text: d.name});
            });

            $('.activities').editable({
                type: 'select',
                mode: 'inline',
                source: list,
                sourceCache: true,
                url: API + 'set_activity_booking/?format=json&limit=0',

                success: function(response, newValue) {

                                        // reload form and event
                    redraw(response.booking.ref, response.booking);
                }

            });


        }
    });



    // get list of tuners and setup editable
    $.ajax({
        type:"get",
        url:API+"tuners",
        dataType : 'json',
        success:function(data){

            var objects = data.objects;
            var list = [];
            $.each(objects, function(i,d) {
                list.push({value: d.id, text: d.name});
            });

            $('.tuners').editable({
                type: 'select',
                mode: 'inline',
                source: list,
                sourceCache: true,
                url: API + 'set_tuner_booking/?format=json&limit=0',

                success: function(response, newValue) {

                    // reload form and event
                    redraw(response.booking.ref, response.booking);


                }

            });


        }
    });



    // get list of instruments and setup editable
    $.ajax({
        type:"get",
        url:API+"instruments",
        dataType : 'json',
        data: {client_id: client_id},
        success:function(data){

            var objects = data.objects;
            var list = [];
            $.each(objects, function(i,d) {
                list.push({value: d.id, text: d.name});
            });

            $('.instruments').editable({
                type: 'select',
                mode: 'inline',
                source: list,
                sourceCache: true,
                url: API + 'set_instrument_booking/?format=json&limit=0',

                success: function(response, newValue) {
                    // reload form and event
                    redraw(response.booking.ref, response.booking);
                }

            });


        }
    });

    // get list of studios and setup editable
    $.ajax({
        type:"get",
        url:API+"studios",
        dataType : 'json',
        data: {client_id: client_id },
        success:function(data){

            var objects = data.objects;
            var list = [];
            $.each(objects, function(i,d) {
                list.push({value: d.id, text: d.name});
            });

            $('.studios').editable({
                type: 'select',
                mode: 'inline',
                source: list,
                sourceCache: true,
                url: API + 'set_studio_booking/?format=json&limit=0',

                success: function(response, newValue) {
                    // reload form and event
                    redraw(response.booking.ref, response.booking);
                }
            });


        }
    });

    // get list of bookers and setup editable
    $.ajax({
        type:"get",
        url:API+"bookers",
        dataType : 'json',
        data: {client_id: client_id},
        success:function(data){

            var objects = data.objects;
            var list = [];
            $.each(objects, function(i,d) {
                list.push({value: d.id, text: d.full_name});
            });

            $('.booker').editable({
                type: 'select',
                mode: 'inline',
                source: list,
                sourceCache: true,
                url: API + 'set_booker_booking/?format=json&limit=0',

                success: function(response, newValue) {
                    // reload form and event
                    redraw(response.booking.ref, response.booking);
                }

            });


        }
    });
    // edit date

//            {#            $('.deadline_date').editable({#}
//            {#                type: 'combodate',#}
//            {#                mode: 'inline',#}
//            {#                url: API + 'set_deadline_booking/?format=json&limit=0',#}
//            {##}
//            {#                success: function(response, newValue) {#}
//            {#                    if(response.status == 'error') return response.msg; //msg will be shown in editable form#}
//            {#                }#}
//            {#            });#}

    //TODO: not working - shows calendar before clicking
//           $(".when_date").datepicker({
//                format: "dd/mm",
//                startDate: start_date,
//                endDate: end_date,
//                todayHighlight: true
//            });

    $('#field_requested_time').clockin($("#field_requested_time").text(), time_update);
    $('#field_deadline_time').clockin($("#field_deadline_time").text(), time_update);


// session ref
    $('.clientref').editable({
        type: 'text',
        mode: 'inline',
        defaultValue: '',
        url: API + 'set_clientref_booking/?format=json&limit=0',

        success: function(response, newValue) {
        // nothing to do
        }
    });

    $('.duration').editable({
        type: 'text',
        mode: 'inline',
        url: API + 'set_duration_booking/?format=json&limit=0',

        success: function(response, newValue) {
                       redraw(response.ref, response.booking);
        }
    });


    if ($(".price").hasClass("editable")) {
        $('.price').editable({
            type: 'text',
            mode: 'inline',
            url: API + 'set_price_booking/?format=json&limit=0',

            success: function(response, newValue) {
               // nothing to do
            }
        });
    }




}

function update_events() {

    /*  COMPLETE */

    // for marking complete - can be marked and unmarked

    $(".switch").bootstrapSwitch();  // make checkboxes in table into switches

    // save state when switch toggled
    $(".switch_complete").on("switch-change", function(e) {
        e.stopPropagation();

        // checked means not tuned and vv.
        var state = !(this.checked);
        var ref = this.dataset['pk'];

        complete_booking(ref, USER_ID, state);

    });

    // complete button pressed
    $(".complete_booking").on("click", function(e) {
        e.stopPropagation();
        if (window.confirm("Are you sure you want to mark this booking as complete?")) {

            var ref = this.dataset['pk'];

            complete_booking(ref, USER_ID, "true");

        }
    });

    $(".switch_tuner").on("switch-change", function(e) {
        e.stopPropagation();

        // checked means not tuned and vv.
        var state = !(this.checked);
        var ref = this.dataset['pk'];

        $.ajax({
            type:"post",
            url:API+"booking_provider_paid/",
            data: {
                ref:ref,
                state: state},
            dataType : 'json',
            success:function(json){
                            redraw(ref, json.booking);
            }

        });
    });

    $(".switch_client").on("switch-change", function(e) {
        e.stopPropagation();

        // checked means not tuned and vv.
        var state = !(this.checked);
        var ref = this.dataset['pk'];

        $.ajax({
            type:"post",
            url:API+"booking_client_paid/",
            data: {
                ref:ref,
                state: state},
            dataType : 'json',
            success:function(json){
                 redraw(ref, json.booking)
            }

        });
    });

    $(".cancel_booking").on("click", function(e) {
        e.stopPropagation();
        if (window.confirm("Are you sure you want to cancel this booking?")) {

            var ref = this.dataset['pk'];

            $.ajax({
                type:"post",
                url:API+"booking_cancel/",
                data: {
                    ref:ref},
                dataType : 'json',
                success:function(json){
                        redraw(ref, json.booking)

                }

            });
        }
    });

    $(".accept_booking").on("click", function(e) {
        e.stopPropagation();
        if (window.confirm("Are you sure you want to accept this booking?")) {


            var ref = this.dataset['pk'];

            $.ajax({
                type:"post",
                url:API+"accept_booking/",
                data: {
                    value: USER_ID,
                    pk: ref,
                    ref:ref},
                dataType : 'json',
                success:function(json){
            redraw(ref, json.booking)
                }

            });
        }
    });



    $(".booking_provider_paid").on("click", function(e) {
        e.stopPropagation();
        if (window.confirm("Are you sure you want to mark this booking as paid?")) {

            var ref = this.dataset['pk'];

            $.ajax({
                type:"post",
                url:API+"booking_provider_paid/",
                data: {
                    value: USER_ID,
                    state: "true",
                    ref:ref},
                dataType : 'json',
                success:function(json){
                     redraw(ref, json.booking)
                }

            });
        }
    });

      $(".booking_client_paid").on("click", function(e) {
        e.stopPropagation();
        if (window.confirm("Are you sure you want to mark this booking as paid?")) {

            var ref = this.dataset['pk'];

            $.ajax({
                type:"post",
                url:API+"booking_client_paid/",
                data: {
                    value: USER_ID,
                    state: "true",
                    ref:ref},
                dataType : 'json',
                success:function(json){
                     redraw(ref, json.booking)
                }

            });
        }
    });


}

function tidy_data(json) {
    // convert dates and setup for calendar

    // dates come in as utc
    json['deadline'] = moment(moment.utc(json['deadline']).toDate());
    json['start'] = moment(moment.utc(json['start']).toDate());
    json['end'] = moment(moment.utc(json['end']).toDate());
    json['requested_from'] = moment(moment.utc(json['requested_from']).toDate());
    json['requested_to'] = moment(moment.utc(json['requested_to']).toDate());
    json['when'] = moment(moment.utc(json['when']).toDate());
    json['price'] = parseFloat(json['price']).toFixed(2);

    // stuff for calendar
    json['id'] = json.ref;
    json['className'] = "booking_status_"+json['status'];
    return json;
}

function time_update(selection, time) {
    // note that time is being sent back in utc

    var duration = parseInt($("#field_duration").text());
    var ref = selection[0].dataset['pk'];

    // Deadline
    if (selection[0].id == "field_deadline_time") {


        // combine deadline date with new time
        var deadline = moment($("#field_deadline_time").data("date") + " " + time);

        // note conversion to utc
        $.ajax({
            type:"post",
            url:API+"set_deadline_booking/",
            data: {
                pk:ref, value:deadline.utc().format()},
            dataType : 'json',
            success:function(json){

                // reload as other values may have changed
                var data = tidy_data(json.booking);
                populate_form(data, eventid);

            }

        });

    }

    // Requested time
    if (selection[0].id == "field_requested_time") {


        // combine deadline date with new time
        var tm = moment($("#field_requested_time").data("date") + " " + time);
        update_start(ref, tm.utc().format());



    }
}

function update_duration(ref, duration) {
    $.ajax({
        type:"post",
        url:API+ 'set_duration_booking/?format=json&limit=0',
        data: {
            pk:ref, value:duration },
        dataType : 'json',
        success:function(json){
            redraw(ref, json.booking)
        }

    });
}

function update_start(ref, start) {
    // this api call does not change other times
    $.ajax({
        type:"post",
        url:API+"set_requested_start_booking/",
        data: {
            pk:ref, value:start},
        dataType : 'json',
        success:function(json){

            redraw(ref, json.booking)

        }

    });
}

function update_end(ref, end) {
    $.ajax({
        type:"post",
        url:API+"set_requested_end_booking/",
        data: {
            pk:ref, value:end},
        dataType : 'json',
        success:function(json){

            redraw(ref, json.booking)
        }

    });
}


function update_time(ref, time_type,  end) {
    $.ajax({
        type:"post",
        url:API+"set_booking_times/",
        data: {
            pk:ref, value:end, time_type: time_type},
        dataType : 'json',
        success:function(json){

            redraw(ref, json.booking)

        }

    });
}

function complete_booking(ref, user_id, state) {

    $.ajax({
        type:"post",
        url:API+"booking_complete/",
        data: {
            value: user_id,
            state: state,
            pk:ref},
        dataType : 'json',
        success:function(json){
            // reload form and event
            redraw(ref, json.booking);

        }

    });

}

function redraw(ref, json) {
    /* redraw form and event with updted data */

    var data = tidy_data(json);
    populate_form(data, ref);
    update_events();   // updates the on clicks etc.

    // if called from a page with calendar then update related event
    if( $('#calendar').length ) {
        redraw_event(ref, data);
    }

}