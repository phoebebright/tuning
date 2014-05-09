(function($) {
    function reloadMessages() {
        $('div.ajaxmessages').each(function(){

            var queryParams = '';
            $('div.ajaxmessage').each(function(){
                var identity = $(this).attr('data-identity');
                if (queryParams.length) {
                    queryParams += ',';
                } else {
                    queryParams = '?filter=';
                }
                queryParams += identity;
            });
            // Perform the reload.
            var refreshUrl = $(this).attr('data-refresh');
            if (refreshUrl) {
                $(this).load(refreshUrl + queryParams);
            }
        });
    }

    $(document).ready(function() {
        window.setInterval(reloadMessages, 2000);
    });
})(jQuery);
