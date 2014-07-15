function show_comments(id) {
    /* load comments from log and display them in #comment_list
     TOOD: pass selection AND/OR only load if comment_list exists
     */

    var html = '';
    var selection = $("#comment_list");

    var data = {
            limit:100,
            booking_id: id}

    if (selection.data('type') ) {
        data['log_type'] = selection.data('type');
    }

    $.ajax({
        type:"get",
        url:API+"log",
        data: data,
        dataType : 'json',
        success:function(json){


            var data =tidy_comment_data(json.objects);

            $.each(data, function(i, d) {

                html += "<li>" + d['comment'] + ' - ' + d['created_by']['full_name'] + ' - ' + d['when'] +'</li>';
            })

            selection.html(html);

        }
    });

}

function add_comment_editable() {
    $('.comment').editable({
        type: 'textarea',
        sourceCache: true,
        url: API + 'log/?format=json',

        success: function (response, newValue) {
            if (response.status == 'error') return response.msg; //msg will be shown in editable form

            // refresh list of comments
            var pk = this.dataset['pk'];
            var sel = $('.comment_list[data-pk="' + pk + '"]');
            update_comment_list(sel, pk)

            // show comment list
            sel.show('slow');


        },
        title: 'add comment',
        display: false
    });

}

function add_comment_list() {
    /* the comment badge is the little circle with the number of comments in it.
    Clicking on the badge reveals the comments.  In order to get this behaviour,
    first load all comments for each booking - update_comment_list - this includes creating
    badge.  Now update each badge with the count of comments.  Now can setup the onclick.
    see Q docs - https://github.com/kriskowal/q
     */


    $(".comment_list").each(function(i,d) {

        update_comment_list($(this), d.dataset['pk']);

    });

    var template = $('#comment_badge_template').html();
    Mustache.parse(template);
    var promises = [];


    $(".comment_badge").each(function(i,d) {
        var selection = $(this);
        promises.push(load_comment_count(d.dataset['pk'], selection, template));

    });

    Q.all(promises).then(function() {

        // once all comments loaded

        $(".comment_badge").on("click", function(e) {
            $(".comment_list[data-pk="+this.dataset['pk']+"]").toggle('slow');
        })
    });


}


function load_recent_comments(selection, filter) {

    var data = {};

    // comments that can be viewed depends on user type
    if (USER_TYPE == "admin") {
        data['filter'] = '';
    } else if (USER_TYPE == "booker") {
        data['filter'] = {client_id: CLIENT_ID};
    } else if (USER_TYPE == "tuner") {
        data['filter'] = {user_id: USER_ID};
    }


    var template = $('#log_list_template').html();
    Mustache.parse(template);

    var limit = parseInt(selection[0].dataset['items']);
    if (limit < 1) { limit=1; }

    data['limit'] = limit;

    // limit comments to just one type - usually "user" comments
    if (selection.data('type') ) {
        data['log_type'] = selection.data('type');
    }


    $.ajax({
        type:"get",
        url:API+"log",
        data: data,
        dataType : 'json',
        success:function(json){
            var html = '';
            var data =tidy_comment_data(json.objects);
            $.each(data, function(i, d) {

                html += comment_html(d, template);
            });

            selection.html(html);

        }
    });
}


function load_comment_count(pk, selection, template) {

       var data = {
            limit:100,
            ref: pk};

        // limit comments to just one type - usually "user" comments
    if (selection.data('type') ) {
        data['log_type'] = selection.data('type');
    }

    $.ajax({
        type:"get",
        url:API+"log",
        data: data,
        dataType : 'json',
        success:function(json){
            var num = json.meta['total_count'];
            if (num > 0) {
                selection.html(Mustache.render(template, {num: num}));
            }


        }
    });
}

function update_comment_list(selection, pk) {

    var template = $('#comment_list_template').html();
    Mustache.parse(template);

       var data = {
            limit:0,
            ref: pk};

        // limit comments to just one type - usually "user" comments
    if (selection.data('type') ) {
        data['log_type'] = selection.data('type');
    }

    $.ajax({
        type:"get",
        url:API+"log",
        data: data,
        dataType : 'json',
        success:function(json){
            var html = '';
            var data =tidy_comment_data(json.objects);
            
            $.each(data, function(i, d) {
                html += comment_html(d, template);
            });

            selection.html(html);

            // update badge
            var badge = $('.comment_badge[data-pk='+pk+']');
            if (badge.length) {
                badge.children('span').html(json.meta['total_count']);
            }

        }
    });
}

function comment_html(d, template) {

    if (typeof template == "undefined") {
        var template = $('#comment_list_template').html();
        Mustache.parse(template);
    }

    return Mustache.render(template, {
        user: d['user'],
        since: d['since'],
        booking_ref: d['booking_ref'],
        booking_url: d['booking_url'],
        long_heading: d['long_heading'],
        status: d['status'],
        text: d['comment']});
}

function tidy_comment_data(data) {
    /* convert utc dates to local */

    var is_list = (typeof data.id === 'undefined');

    // if passing in one object, make it a list
    if (!is_list) {
        data = [data];
    }

    $.each(data, function(i, d) {
                d['created'] = moment(moment.utc(d.created).toDate());
                d['when'] = moment(d['created']).format('ddd Do MMM - HH:mm');
                d['since'] = moment(d['created']).fromNow();
            });

    if (!is_list) {
        data = data[0];
    }

    return data
}