/* global _dntEnabled */

$(document).ready(function(){
    'use strict';

    if (!_dntEnabled()) {
        var youtube = $('.youtube');
        var yid = youtube.data('id');
        var iframe_url = 'https://www.youtube.com/embed/' + yid + '?autoplay=1&autohide=1';
        var iframe = $('<iframe/>', {'frameborder': '0', 'src': iframe_url, 'width': $(youtube).width(), 'height': $(youtube).height() });
        $(youtube).replaceWith(iframe);
    }
});
