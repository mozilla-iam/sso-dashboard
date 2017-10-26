$(document).ready(function(){
    'use strict';

    // Dismiss alert
    $('#dismiss-alert').click(function() {
        var alert_id = $('#dismiss-alert').data('alert-id');
        $.ajax({
            type: 'POST',
            url: '/alert/' + alert_id
        }).done(function() {
            window.location.reload();
        });
    });
});
