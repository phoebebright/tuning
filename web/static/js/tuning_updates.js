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
                if (window.confirm("Are you sure?")) {


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
 }