function populate_booking_template(obj) {

// TUNER

// may not know tuner yet
    if (obj.status >=0 && obj.status <3 && USER_TYPE == "admin") {
        // admin can edit
        var template = $('#tuner_edit').html();
    } else {

        if (obj.tuner != null) {
            // viewable
            var template = $('#tuner_view').html();
        }
    }
    Mustache.parse(template);
    $("#tuner_box").html(Mustache.render(template, obj));


// ACTIVITY

    if (obj.status >=0 && obj.status <3 && (USER_TYPE == "admin" || USER_TYPE == "booker")) {
        // admin can edit
        var template = $('#activity_edit').html();

    } else {

        if (parseInt(obj.activity_id) > 0) {
            // viewable
            var template = $('#activity_view').html();

        }
    }

    Mustache.parse(template);
    $("#activity_box").html(Mustache.render(template, obj));



// INSTRUMENT

    if (obj.status >=0 && obj.status <3 && (USER_TYPE == "admin" || USER_TYPE == "booker")) {
        // admin can edit
        var template = $('#instrument_edit').html();

    } else {

        if (parseInt(obj.instrument_id) > 0) {
            // viewable
            var template = $('#instrument_view').html();

        }
    }

    Mustache.parse(template);
    $("#instrument_box").html(Mustache.render(template, obj));


// STUDIO

    if (obj.status >=0 && obj.status <3 && (USER_TYPE == "admin" || USER_TYPE == "booker")) {
        // admin can edit
        var template = $('#studio_edit').html();

    } else {

        if (parseInt(obj.studio_id) > 0) {
            // viewable
            var template = $('#studio_view').html();

        }
    }

    Mustache.parse(template);
    $("#studio_box").html(Mustache.render(template, obj));



// DEADLINE

    if (obj.status >=0 && obj.status <3 && (USER_TYPE == "admin" || USER_TYPE == "booker")) {
        var template = $('#deadline_edit').html();

    } else {

        if (parseInt(obj.deadline) > 0) {
            // viewable
            var template = $('#deadline_view').html();

        }
    }

    Mustache.parse(template);
    $("#deadline_box").html(Mustache.render(template, obj));


    // add data-pk to all editable objects
    $('.editable').each(function() {
        this.dataset['pk'] = obj.ref;
    });


    }
