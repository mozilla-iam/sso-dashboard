$(document).ready(function(){
    'use strict';

    // Dismiss alert
    $('#dismiss-alert').click(function() {
        var alert_id = $('#dismiss-alert').data('alert-id');
        $.ajax({
            url: '/alert/' + alert_id,
            type: 'POST',
            dataType   : 'json',
            contentType: 'application/json; charset=UTF-8',
            data: JSON.stringify({ 'alert_action': 'acknowledge' })
        }).done(function() {
            window.location.reload();
        });
    });

    // Mark false positive
    $('#escalate-alert').click(function() {
        var alert_id = $('#dismiss-alert').data('alert-id');
        $.ajax({
            url: '/alert/' + alert_id,
            type: 'POST',
            dataType   : 'json',
            contentType: 'application/json; charset=UTF-8',
            data: JSON.stringify({ 'alert_action': 'escalate' })
        }).done(function() {
            window.location.reload();
        });
    });

    // Mark False Positive
    $('#false-positive-alert').click(function() {
        var alert_id = $('#dismiss-alert').data('alert-id');
        $.ajax({
            url: '/alert/' + alert_id,
            type: 'POST',
            dataType   : 'json',
            contentType: 'application/json; charset=UTF-8',
            data: JSON.stringify({ 'alert_action': 'false-positive' })
        }).done(function() {
            window.location.reload();
        });
    });
});
