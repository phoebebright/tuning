(function ( $ ) {
    /* this code is adapted from this d3 clock: http://bl.ocks.org/tomgp/6475678
     use this to input a time.
     // currently requires that the selection is an id, ie. $("#gettime").clockin()
     NOT $(".gettime").clockin();

     Only works once per page
     Assumes there is not another instance of #clock on the page

     Requires d3, jquery and moment.js
     <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.0/jquery.min.js"></script>
     <script src="http://d3js.org/d3.v3.min.js"></script>
     <script src="//cdnjs.cloudflare.com/ajax/libs/moment.js/2.5.1/moment.min.js"></script>


     */
    $.fn.clockin = function( default_time, callback ) {

        var clock_id = $(this).attr('id');

        this.bind("click", function (e) {


            var selected = $(this);

            // ignore clicks on the clock face or if clock face already showing
            if (e.target.id == clock_id && !$("#clock").is(":visible")) {


                e.preventDefault();
                e.stopPropagation();

                $('#clock').fadeIn();

                $(document).on('click', function(e){
                    if($('#clock').has(e.target).length === 0){

                        // if clicked outside clock
                        // remove clock and put value in selection
                        $('#clock').fadeOut();
                        selected.text(get_time());  
                        $(document).unbind("click");

                        if (typeof callback != "undefined") {
                            callback(selected, get_time());
                        }
                    }
                    e.preventDefault();
                    e.stopPropagation();
                });


                drawClock();
                updateData(time_now.hour(), time_now.minute());
                moveHands();

            }

        });


        var radians = 0.0174532925,
            clockRadius = 200,
            margin = 50,
            width = (clockRadius+margin)*2,
            height = (clockRadius+margin)*2,
            hourHandLength = 2*clockRadius/3,
            minuteHandLength = clockRadius,

            secondHandLength = clockRadius-12,
            secondHandBalance = 30,
            secondTickStart = clockRadius;

        secondTickLength = -10,
            hourTickStart = clockRadius,
            hourTickLength = -18
        secondLabelRadius = clockRadius + 16;
        secondLabelYOffset = 5
        hourLabelRadius = clockRadius - 40
        pmhourLabelRadius = clockRadius - 70
        hourLabelYOffset = 7;

        var working_hours = d3.range(9,19,1);

        var hourScale = d3.scale.linear()
            .range([0,330])
            .domain([0,11]);

        var minuteScale = secondScale = d3.scale.linear()
            .range([0,354])
            .domain([0,59]);

        var handData = [
            {
                type:'hour',
                value:0,
                length:-hourHandLength,
                scale:hourScale
            },
            {
                type:'minute',
                value:0,
                length:-minuteHandLength,
                scale:minuteScale
            }
        ];

        var time_now = moment(),   // global variable that matches clock face
            time_format = "H:mm",  // format of time to display on clock face
            return_moment = false;  // if moment is passed in return a moemnt, otherwise a string




        /* if no default_time passed
         defaults to current time and returns a string eg. 12:30
         if string in format h:m passed in
         returns a string
         if a moment is passed in
         returns a moment
         */

        // convert to moment
        if (typeof default_time == typeof "12:00") {
            time_now.hour(default_time.slice(0,2));
            time_now.minute(default_time.slice(3,5));
        }

        if (typeof default_time == typeof time_now) {
            time_now = default_time;
            return_moment = true;
        }





        function drawClock(){

            var selection = d3.select("#"+clock_id);

            var svg = selection.append("svg")
                .attr("id", "clock")
                .attr("viewBox", "0 0 "+width+" "+height)
                .attr("preserveAspectRatio", "xMinYMin meet")
                .attr("class", "clock-svg");

            var face = svg.append('g')
                .attr('id','clock-face')
                .attr('transform','translate(' + (clockRadius + margin) + ',' + (clockRadius + margin) + ')');


            //and labels

            face.selectAll('.second-label')
                .data(d3.range(5,61,5))
                .enter()
                .append('text')
                .attr('class', 'second-label')
                .attr('text-anchor','middle')
                .attr('x',function(d){
                    return secondLabelRadius*Math.sin(secondScale(d)*radians);
                })
                .attr('y',function(d){
                    return -secondLabelRadius*Math.cos(secondScale(d)*radians) + secondLabelYOffset;
                })
                .on("click", function(d) {
                    updateData(0, d);
                })
                .text(function(d){
                    return d;
                });

            //... and hours
            face.selectAll('.hour-tick')
                .data(d3.range(0,12)).enter()
                .append('line')
                .attr('class', 'hour-tick')
                .attr('x1',0)
                .attr('x2',0)
                .attr('y1',hourTickStart)
                .attr('y2',hourTickStart + hourTickLength)
                .attr('transform',function(d){
                    return 'rotate(' + hourScale(d) + ')';
                });

            face.selectAll('.hour-label')
                .data(d3.range(1,25,1))
                .enter()
                .append('text')
                .attr('class', function(d, i) {
                    if (working_hours.indexOf(d) > -1) {
                        return 'hour-label working';
                    } else {
                        return 'hour-label';
                    }
                })
                .attr('text-anchor','middle')
                .attr('x',function(d){
                    var radius = hourLabelRadius;
                    if (d > 12) radius -= 30;
                    return radius*Math.sin(hourScale(d)*radians);
                })
                .attr('y',function(d){
                    var radius = hourLabelRadius;
                    if (d > 12) radius -= 30;
                    return -radius*Math.cos(hourScale(d)*radians) + hourLabelYOffset;
                })
                .on("click", function(d) {
                    updateData(d, 0);
                })
                .text(function(d){
                    return d;
                });

            face.append('text')
                .attr('id', 'timeis')
                .attr('y', 25)
                .attr('x', 0)
                .attr('text-anchor', 'middle')
                .text(time_now.format(time_format));

            var hands = face.append('g').attr('id','clock-hands');

            face.append('g').attr('id','face-overlay')
                .append('circle').attr('class','hands-cover')
                .attr('x',0)
                .attr('y',0)
                .attr('r',clockRadius/20);


            hands.selectAll('line')
                .data(handData)
                .enter()
                .append('line')
                .attr('class', function(d){
                    return d.type + '-hand';
                })
                .attr('x1',0)
                .attr('y1',function(d){
                    return d.balance ? d.balance : 0;
                })
                .attr('x2',0)
                .attr('y2',function(d){
                    return d.length;
                })
                .attr('transform',function(d){
                    return 'rotate('+ d.scale(d.value) +')';
                });
        }

        function moveHands(){
            d3.select('#clock-hands').selectAll('line')
                .data(handData)
                .transition()
                .attr('transform',function(d){
                    return 'rotate('+ d.scale(d.value) +')';
                });

            d3.select("#timeis")
                .text(time_now.format(time_format));
        }

        function updateData(h, m){

            // update moment global variable and hand dat

            // value for hour depends on the minutes
            if (h > 0) {
                time_now.hour(h)

            }
            if (m > 0) {
                time_now.minute(m)
                handData[1].value = m;
            }
            // hour has to be refreshed as depends on both
            // value of hours and minutes
            handData[0].value = (time_now.hour() % 12) + time_now.minute()/60 ;


            moveHands();
        }

        function get_time() {

            if (return_moment) {
                return time_now;
            } else {
                return time_now.format(time_now.format("H:mm"));
            }
        }

    };

}( jQuery ));