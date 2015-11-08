$(document).ready(function () {
    $('a[data-valid-licence=False]').popover({
        html: true,
        content: 'Esta funcionalidad requiere una licencia superior a la que usted tiene.' +
                 '<a href="{% url "company_accounts:company_profile_select_plan" company.id %}"' +
                 ' class="btn btn-primary btn-block">Cambiar Licencia</a>',
        title: "Requiere Licencia"
    });
    $('a[data-valid-licence=True]').each(function (index){
        $(this).attr('href', $(this).attr("data-href"));
    });
});
