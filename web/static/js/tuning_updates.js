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
                    //TODO: Error checking
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
                    //TODO: Error checking
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
                    //TODO: Error checking
                }

            });


        }
    });

    // get list of instruments and setup editable
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
                    //TODO: Error checking
                }
            });


        }
    });

    // get list of instruments and setup editable
    $.ajax({
        type:"get",
        url:API+"bookers",
        dataType : 'json',
        data: {client_id: client_id},
        success:function(data){

            var objects = data.objects;
            var list = [];
            $.each(objects, function(i,d) {
                list.push({value: d.id, text: d.name});
            });

            $('.booker').editable({
                type: 'select',
                mode: 'inline',
                source: list,
                sourceCache: true,
                url: API + 'set_booker_booking/?format=json&limit=0',

                success: function(response, newValue) {
                    //TODO: Error checking
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
        url: API + 'set_clientref_booking/?format=json&limit=0',

        success: function(response, newValue) {
            var x=1;
            //TODO: Error checking
        }
    });

    $('.duration').editable({
        type: 'text',
        mode: 'inline',
        url: API + 'set_duration_booking/?format=json&limit=0',

        success: function(response, newValue) {
            //TODO: Error checking
            // reload as other values may have changed
            load_booking(this.dataset['pk']);
        }
    });


    if ($(".price").hasClass("editable")) {
        $('.price').editable({
            type: 'text',
            mode: 'inline',
            url: API + 'set_price_booking/?format=json&limit=0',

            success: function(response, newValue) {
                //TODO: Error checking
            }
        });
    }


    // get list of tuners
    $.ajax({
        type:"get",
        url:API+"tuners",
        dataType : 'json',
        success:function(data){

            var tuners = data.objects;
            var tuners_list = [];
            $.each(tuners, function(i,d) {
                tuners_list.push({value: d.id, text: d.name});
            });

            $('.tuners').editable({
                type: 'select',
                source: tuners_list,
                sourceCache: true,
                url: API + 'accept_booking/?format=json&limit=0',

                success: function(response, newValue) {
                    //TODO: Error checking
                },
                title: 'Select Tuner'
            });


        }
    });


}

function update_events() {


    // for marking complete

    $(".switch").bootstrapSwitch();  // make checkboxes in table into switches

    // save state when switch toggled
    $(".switch_complete").on("switch-change", function(e) {
        e.stopPropagation();

        // checked means not tuned and vv.
        var state = !(this.checked);
        var ref = this.dataset['pk'];

        $.ajax({
            type:"post",
            url:API+"booking_complete/",
            data: {
                ref:ref,
                state: state},
            dataType : 'json',
            success:function(json){
                x=json;
            }

        });
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
                x=json;
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
                x=json;
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
                    location.reload();

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

                    location.reload();
                }

            });
        }
    });

    $(".complete_booking").on("click", function(e) {
        e.stopPropagation();
        if (window.confirm("Are you sure you want to mark this booking as complete?")) {

            var ref = this.dataset['pk'];

            $.ajax({
                type:"post",
                url:API+"booking_complete/",
                data: {
                    value: USER_ID,
                    state: "true",
                    ref:ref},
                dataType : 'json',
                success:function(json){
                    location.reload();
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
                    location.reload();
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
                load_booking(ref);

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

function update_duration(eventid, duration) {
      $.ajax({
            type:"post",
            url:API+ 'set_duration_booking/?format=json&limit=0',
            data: {
                pk:eventid, value:duration },
            dataType : 'json',
            success:function(json){
                 // reload as other values may have changed
                load_booking(eventid);
            }

        });
}

function update_start(eventid, start) {
     $.ajax({
            type:"post",
            url:API+"set_requested_booking/",
            data: {
                pk:eventid, value:start},
            dataType : 'json',
            success:function(json){

                // reload as other values may have changed
                load_booking(eventid);

            }

        });
}