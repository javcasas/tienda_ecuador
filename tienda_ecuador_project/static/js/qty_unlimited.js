$(document).ready(function () {
    function show_hide_qty () {
        if($("#id_qty_unlimited").prop("checked")) {
            $("#id_qty").parent().hide(400);
        } else {
            $("#id_qty").parent().show(400);
        }
    }
    $("#id_qty_unlimited").on("change", show_hide_qty);
    show_hide_qty();
});
