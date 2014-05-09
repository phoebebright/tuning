function show_comments(id) {
    /* load comments from log and display them in #comment_list
     TOOD: pass selection AND/OR only load if comment_list exists
     */

    var html = '';

    $.ajax({
        type:"get",
        url:API+"log",
        data: {
            limit:100,
            booking_id: id},
        dataType : 'json',
        success:function(json){
            var data =json.objects;
            $.each(data, function(i, d) {

                var when = moment(d.created).format('ddd Do MMM - HH:mm')
                var since = moment(d.created).fromNow()

                html += "<li>" + d['comment'] + ' - ' + d['created_by']['full_name'] + ' - ' + when +'</li>';
            })

            $("#comment_list").html(html);

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


    var template = $('#log_list_template').html();
    Mustache.parse(template);

    var limit = parseInt(selection[0].dataset['limit']);
    if (limit < 1) { limit=1; }


    $.ajax({
        type:"get",
        url:API+"log",
        data: {
            limit:10},
        dataType : 'json',
        success:function(json){
            var html = '';
            $.each(json.objects, function(i, d) {

                html += comment_html(d, template);
            });

            selection.html(html);

        }
    });
}


function load_comment_count(pk, selection, template) {

    $.ajax({
        type:"get",
        url:API+"log",
        data: {
            limit:100,
            ref:pk},
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

    $.ajax({
        type:"get",
        url:API+"log",
        data: {
            limit:0,
            ref:pk},
        dataType : 'json',
        success:function(json){
            var html = '';
            $.each(json.objects, function(i, d) {
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
        time: moment(d['created']).fromNow(),
        booking_ref: d['booking_ref'],
        booking_url: d['booking_url'],
        long_heading: d['long_heading'],
        text: d['comment']});
}
