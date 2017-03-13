$(document).ready(function(){$("[data-toggle~=collapse]").click(function(){$(".opacity").toggle();});});$(':input[name=filter]').on('input',function(){var val=this.value.toLowerCase();$('#app-grid').find('.app-tile')
.filter(function(){return $(this).data('id').toLowerCase().indexOf(val)>-1;})
.show()
.end().filter(':visible')
.filter(function(){return $(this).data('id').toLowerCase().indexOf(val)===-1;})
.fadeOut();});