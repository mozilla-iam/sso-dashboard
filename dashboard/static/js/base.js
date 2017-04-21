$(document).ready(function(){
    'use strict';

    $('[data-toggle~=collapse]').click(function(){
        $('.opacity').toggle();
    });

    $('#search').focus();

    // This is the js that powers the search box
    $(':input[name=filter]').on('input', function() {
        // Get value just typed into textbox -- see .toLowerCase()
        var val = this.value.toLowerCase();

        // Find all .user-profile divs
        $('#app-grid').find('.app-tile')
        // Find those that should be visible
        .filter(function() {
            return $(this).data('id').toLowerCase().indexOf( val ) > -1;
        })
        // Make them visible
        .show()
        // Now go back and get only the visible ones
        .end().filter(':visible')
        // Filter only those for which typed value 'val' does not match the `data-id` value
        .filter(function() {
            return $(this).data('id').toLowerCase().indexOf( val ) === -1;
        })
        // Fade those out
        .fadeOut();
    });

    // Highlight elements
    $(':input[name=filter]').focusin(function() {
        $('.filter .mui-textfield').addClass('yellow-border');
        $('.filter img').addClass('yellow-border');
    });
    $(':input[name=filter]').focusout(function() {
        $('.filter .mui-textfield').removeClass('yellow-border');
        $('.filter img').removeClass('yellow-border');
    });
    $('a.app-tile').hover(
        function() {
            $(this).find('.app-logo').addClass('yellow-border');
        },
        function() {
            $(this).find('.app-logo').removeClass('yellow-border');
        }
    );

    // Mobile search toggle
    $('.search-button a').click(function() {
        $('.search-mobile').fadeToggle();
        $('.search-button').toggleClass('invert');
    });
});
