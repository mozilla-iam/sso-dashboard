$(document).ready(function(){

  $("[data-toggle~=collapse]").click(function(){
    $(".opacity").toggle();

  });
});

$(document).ready(function () {
    $("#search").focus();
});


//This is the js that powers the search box
$(':input[name=filter]').on('input',function() {

  //get value just typed into textbox -- see .toLowerCase()
  var val = this.value.toLowerCase();

  //find all .user-profile divs
  $('#app-grid').find('.app-tile')

  //find those that should be visible
  .filter(function() {
    return $(this).data('id').toLowerCase().indexOf( val ) > -1;
  })

  //make them visible
  .show()

  //now go back and get only the visible ones
  .end().filter(':visible')

  //filter only those for which typed value 'val' does not match the `data-id` value
  .filter(function() {
    return $(this).data('id').toLowerCase().indexOf( val ) === -1;
  })

  //fade those out
  .fadeOut();

});
