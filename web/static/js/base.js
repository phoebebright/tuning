
$('.notification-pie-chart').easyPieChart({
    onStep: function (from, to, percent) {
        //TODO: harding coding sla as 60 mins here, should refer back to settings.SLA
        $(this.el).find('.percent').text(Math.round(percent));
    },
    barColor: "#39b6ac",
    lineWidth: 3,
    size: 50,
    trackColor: "#efefef",
    scaleColor: "#cccccc"

});

function base() {


    /*==Left Navigation Accordion ==*/
    if ($.fn.dcAccordion) {
        $('#nav-accordion').dcAccordion({
            eventType: 'click',
            autoClose: true,
            saveState: true,
            disableLink: true,
            speed: 'slow',
            showCount: false,
            autoExpand: true,
            classExpand: 'dcjq-current-parent'
        });
    }
    /*==Slim Scroll ==*/
    if ($.fn.slimScroll) {
        $('.event-list').slimscroll({
            height: '305px',
            wheelStep: 20
        });
        $('.conversation-list').slimscroll({
            height: '360px',
            wheelStep: 35
        });
        $('.to-do-list').slimscroll({
            height: '300px',
            wheelStep: 35
        });
    }
    /*==Nice Scroll ==*/
    if ($.fn.niceScroll) {


        $(".leftside-navigation").niceScroll({
            cursorcolor: "#1FB5AD",
            cursorborder: "0px solid #fff",
            cursorborderradius: "0px",
            cursorwidth: "3px"
        });

        $(".leftside-navigation").getNiceScroll().resize();
        if ($('#sidebar').hasClass('hide-left-bar')) {
            $(".leftside-navigation").getNiceScroll().hide();
        }
        $(".leftside-navigation").getNiceScroll().show();

        $(".right-stat-bar").niceScroll({
            cursorcolor: "#1FB5AD",
            cursorborder: "0px solid #fff",
            cursorborderradius: "0px",
            cursorwidth: "3px"
        });

    }


    /*==Collapsible==*/
    $('.widget-head').click(function (e) {
        var widgetElem = $(this).children('.widget-collapse').children('i');

        $(this)
            .next('.widget-container')
            .slideToggle('slow');
        if ($(widgetElem).hasClass('ico-minus')) {
            $(widgetElem).removeClass('ico-minus');
            $(widgetElem).addClass('ico-plus');
        } else {
            $(widgetElem).removeClass('ico-plus');
            $(widgetElem).addClass('ico-minus');
        }
        e.preventDefault();
    });




    /*==Sidebar Toggle==*/

    $(".leftside-navigation .sub-menu > a").click(function () {
        var o = ($(this).offset());
        var diff = 80 - o.top;
        if (diff > 0)
            $(".leftside-navigation").scrollTo("-=" + Math.abs(diff), 500);
        else
            $(".leftside-navigation").scrollTo("+=" + Math.abs(diff), 500);
    });



    $('.sidebar-toggle-box .fa-bars').click(function (e) {

        $(".leftside-navigation").niceScroll({
            cursorcolor: "#1FB5AD",
            cursorborder: "0px solid #fff",
            cursorborderradius: "0px",
            cursorwidth: "3px"
        });

        $('#sidebar').toggleClass('hide-left-bar');
        if ($('#sidebar').hasClass('hide-left-bar')) {
            $(".leftside-navigation").getNiceScroll().hide();
        }
        $(".leftside-navigation").getNiceScroll().show();
        $('#main-content').toggleClass('merge-left');
        e.stopPropagation();
        if ($('#container').hasClass('open-right-panel')) {
            $('#container').removeClass('open-right-panel')
        }
        if ($('.right-sidebar').hasClass('open-right-bar')) {
            $('.right-sidebar').removeClass('open-right-bar')
        }

        if ($('.header').hasClass('merge-header')) {
            $('.header').removeClass('merge-header')
        }


    });
    $('.toggle-right-box .fa-bars').click(function (e) {
        $('#container').toggleClass('open-right-panel');
        $('.right-sidebar').toggleClass('open-right-bar');
        $('.header').toggleClass('merge-header');

        e.stopPropagation();
    });

    $('.header,#main-content,#sidebar').click(function () {
        if ($('#container').hasClass('open-right-panel')) {
            $('#container').removeClass('open-right-panel')
        }
        if ($('.right-sidebar').hasClass('open-right-bar')) {
            $('.right-sidebar').removeClass('open-right-bar')
        }

        if ($('.header').hasClass('merge-header')) {
            $('.header').removeClass('merge-header')
        }


    });


    $('.panel .tools .fa').click(function () {
        var el = $(this).parents(".panel").children(".panel-body");
        if ($(this).hasClass("fa-chevron-down")) {
            $(this).removeClass("fa-chevron-down").addClass("fa-chevron-up");
            el.slideUp(200);
        } else {
            $(this).removeClass("fa-chevron-up").addClass("fa-chevron-down");
            el.slideDown(200); }
    });



    $('.panel .tools .fa-times').click(function () {
        $(this).parents(".panel").parent().remove();
    });



    $('.search').on("change", function(e) {
        // search for booking ref

        var ref = this.value;

        $.ajax({
            type:"get",
            url:API+"bookings",
            data: {
                limit:2,
                ref:ref},
            dataType : 'json',
            success:function(json){

                if (json.meta['total_count'] == 1) {
                    document.location.href = "/booking/" + ref;

                }

            }
        });


    });


}