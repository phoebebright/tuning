//TODO: ON calendar optionally show archived bookings

function load_booking(eventid) {


    // get full details
    $.ajax({
        type:"get",
        url:API+"bookings_fat",
        data: {
            ref: eventid,
            limit:0},
        dataType : 'json',
        success:function(json){

            var data = tidy_data(json.objects[0]);
            populate_form(data, eventid);
            // holds on click events etc.
            add_form_events();
        }
    });
}


function populate_form(object, eventid) {

    /* put booking data into template form (in booking_editable_template.html) */

    // eventid and object.ref are expected to be the same
    //TODO: should pass in name of div to hold form as paramter - currently hard coded to #booking_edit

    
    // create new form in div
    $("#booking_edit").html(object.template);

    // save event id from calendar and ref of object
    // update: these are now the same eventid==ref
    $("#editform")
        .attr("data-eventid", eventid )
        .attr("data-eventref", object.ref );

    // add classes
    $("#booking_edit").attr("class", 'panel-body booking_status_'+object.status);

    if (object.editable) {


        // now put data into "fields" or ? if no data
        $("#modal_label").text("Add Booking for " + object.client.name);

        $("#field_client_name").text(object.client.name);
        $("#field_deadline_date").text(moment(object.deadline).format("dddd D MMM"));

        $("#field_activity").text(object.activity.name_verb);
        $("#field_activity_name").text(object.activity.name);
        $("#field_activity").attr("data-value", String(object.activity.id));

        if (object.instrument != null) {
            $("#field_instrument").text(object.instrument.name);
            $("#field_instrument").attr("data-value", String(object.instrument.id));
        } else {
            $("#field_instrument").text("?");
        }

        if (object.studio != null) {
            $("#field_studio").text(object.studio.name);
            $("#field_studio").attr("data-value", String(object.studio.id));
        } else {
            $("#field_studio").text("?");
        }

        if (object.client_ref != null) {
            $("#field_client_ref").text(object.client_ref);
            $("#field_client_ref").attr("data-value", String(object.client_ref));
        } else {
            $("#field_client_ref").text("?");
        }

        // the line belows turns .uct property from true to false!!!!!
        // var deadline = object.deadline;

        var dline = object.deadline;
        if (dline.isValid() && (dline.hour() > 0 || dline.minute() > 0)) {
            // output as local time here
            $("#field_deadline_time").text(dline.local().format("HH:mm"));
            // store as utc
            $("#field_deadline_time").attr("data-value", dline.toISOString());
        } else {
            $("#field_deadline_time").text("?");
        }


        var requested = object.requested_from;

        if (requested.isValid() && (requested.hour() > 0 || requested.minute() > 0)) {
            // convert as local time here
            $("#field_requested_time").text(requested.local().format("HH:mm"));
            //store as utc
            $("#field_requested_time").attr("data-value", requested.toISOString());
        } else {
            $("#field_requested_time").text("?");
        }

        if (object.booker != null) {
            $("#field_booker").text(object.booker.full_name);
            $("#field_booker").attr("data-value", String(object.booker.id));
        } else {
            $("#field_booker").text("?");
        }
        if (object.tuner != null) {
            $("#field_tuner").text(object.tuner.full_name);
            $("#field_tuner").attr("data-value", String(object.tuner.id));
        } else {
            $("#field_tuner").text("?");
        }


        if (object.price != null) {
            $("#field_price").text(object.price);
            $("#field_price").attr("data-value", String(object.price));
        } else {
            $("#field_price").text("?");
        }

        if (object.tuner_payment != null) {
            $("#field_fee").text(object.tuner_payment);
            $("#field_fee").attr("data-value", String(object.tuner_payment));
        } else {
            $("#field_fee").text("?");
        }


        $("#field_duration").text(object.duration.toFixed(2));
        $("#field_duration").attr("data-value", String(object.duration));

        // can only update bookings with status < complete


        // load lists of instruments, activities etc. to be used for editable fields
        load_data(object.client.id);
    } else {
        $("#editform").html(object.description);
    }

    // decide which buttons to show
    $("#booking_edit button").each(function() {
        $(this).hide();

        // show/hide buttons based on user type and status which are data attributes on buttons

        if ($(this).data('showUser').indexOf(USER_TYPE) > -1) {
            if ($(this).data('showStatus').indexOf(object.status) > -1) {
                $(this).show();
            }
        }
    });

    // now show the booking
    $("#booking_row").slideDown();

    // enable onclicks
    $("#editable_save").on("click", function() {
        // mark booking as created
        $.ajax({
            type:"post",
            url:API+"make_booking/",
            data: {pk: object.ref, value:"{{ request.user.id }}"},
            dataType : 'json',
            success:function(json){

                var data = tidy_data(json.booking);

                close_form();
                redraw_event(object.ref, data);


            }
        });

    });
    $("#editable_done").on("click", function() {
        // nothing to do as everything saved already

        close_form();

    });




            $("#editable_cancel").on("click", function() {

                var msg = "Are you sure you want to cancel this booking?";

                if (parseInt(object.status) == 0) {
                    msg = "Are you sure you don't want to save this booking? "
                }
                if (window.confirm(msg)) {

                    $.ajax({
                        type:"post",
                        url:API+"delete_booking/",
                        data: {pk: object.ref, value:"{{ request.user.id }}"},
                        dataType : 'json',
                        success:function(json){

                            close_form();
                            remove_event(object.ref);


                        }
                    });
                }

            });

        }



        function load_data(client_id) {
            // pass parameters like this:
            //init({{ object.client_id }}, NOW, MAX_DATE);

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
                        list.push({value: d.id, text: d.full_name});
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

        function add_form_events() {

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

            //TODO: check booking_provider_paid is the right call here
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

                    cancel(ref);
                }
            });

            $(".accept_booking").on("click", function(e) {
                // tried to have two on clicks and to stop propgation so would not have to do clunky lookup to see where it
                // came from.  Could not get propogation to stop however.
                if (window.confirm("Are you sure you want to accept this booking?")) {

                    accept_booking(this.dataset['pk']);

                }
            });



            $(".booking_provider_paid").on("click", function(e) {
                e.stopPropagation();
                if (window.confirm("Are you sure you want to mark this booking as paid?")) {

                    var ref = this.dataset['pk'];

                    provider_paid(ref);
                }
            });

            $(".booking_client_paid").on("click", function(e) {
                e.stopPropagation();
                if (window.confirm("Are you sure you want to mark this booking as paid?")) {

                    var ref = this.dataset['pk'];

                    client_paid(ref);
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
                        populate_form(data, ref);

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

        function accept_booking(ref) {


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

                    if( $('#calendar').length ) {
                        close_form();
                    }

                }

            });
        }
        function provider_paid(ref) {


            $.ajax({
                type:"post",
                url:API+"booking_provider_paid/",
                data: {
                    state: "true",
                    value: USER_ID,
                    ref: ref,
                    pk: ref},
                dataType : 'json',
                success:function(json){
                    redraw(ref, json.booking)
                }

            });
        }

        function client_paid(ref) {


            $.ajax({
                type:"post",
                url:API+"booking_client_paid/",
                data: {
                    state: "true",
                    ref:ref,
                    pk:ref},
                dataType : 'json',
                success:function(json){
                    redraw(ref, json.booking)
                }

            });
        }

        function cancel(ref) {


            $.ajax({
                type:"post",
                url:API+"booking_cancel/",
                data: {
                    pk:ref},
                dataType : 'json',
                success:function(json){
                    redraw(ref, json.booking)

                }

            });

        }
        function redraw(ref, json) {
            /* redraw form and event with updted data */
            console.log('redraw from tuning_update');
            var data = tidy_data(json);
            populate_form(data, ref);
            add_form_events();   // updates the on clicks etc.

            // if called from a page with calendar then update related event
            if( $('#calendar').length ) {
                redraw_event(ref, data);
                load_recent_comments($(".message-log"));
            }

        }

