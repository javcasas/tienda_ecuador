$(document).ready(function (){
    $("div.panel-toggleable div.panel-heading").click(function () {
        $(this).parent().find('div.panel-body').toggle();
    });
    $("div.panel-toggleable.toggled-off div.panel-body").toggle();
})
