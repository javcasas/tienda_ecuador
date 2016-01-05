// <input id='selector' type="text" class="dropdown-toggle form-control col-xs-12"
//        placeholder='Añadir Artículo'
//        value=''
//        autofocus />
// <ul class="dropdown-menu col-xs-12"></ul>

function prepare_search_box(ob)
{
    if (!(ob !== null && typeof ob === 'object')) {
        console.log("Invalid parameter for prepare search box");
        return;
    }
    // Parameters
    // JQuery selector
    var selector = ob.selector || console.log("No selector provided");
    // Generates a name from the items being searched
    var gen_name_fn = ob.gen_name_fn || console.log("No gen_name_fn provided");
    // Post-processes the name of the item
    var gen_name_post_process_fn = ob.gen_name_post_process_fn || function (x) { return x; };
    // onclick for each item selected
    var callback_fn = ob.callback_fn || console.log("No callback_fn provided");
    // URL to get a JSON of all the items to search
    var data_url = ob.data_url || console.log("No data_url provided");
    // List of fields to search
    var fields_to_search = ob.fields_to_search || console.log("No fields to search provided");
    // Message to show when no items match the search
    var no_match_msg = ob.no_match_msg || "<span style='color: #777'>No se encontró ningún artículo</span>";
    // Message to show when there was a problem loading the list
    var error_loading_msg = ob.error_loading_msg || "Error cargando lista";

    // Helper for loading the JSON data
    var data = null;
    var retries = 0;
    function load_items() {
        if(retries > 3){
            return;
        }
        $.getJSON(data_url)
        .done(function (dt) {
            data = dt;
        }).error(function () {
        });
    }
    // Start loading everything up
    load_items();

    // Helpers for adding, showing, hiding and removing entries from the list
    var control = $(selector + " + ul");
    function add_link(name, item) {
        control.append(
            $("<li></li>").append(
                $("<a></a>")
                    .attr("href", "#")
                    .click(function () {callback_fn(item); return false;})
                    .html(name)));
    }
    function clear_all_links() {
        control.html("");
    }
    function add_text_only_link(text) {
        control.append(
            $("<li></li>").append(
                $("<a></a>")
                    .html(text)));
    }

    function split(text, delimiter) {
        var lowertext = text.toLowerCase();
        var lowerdelimiter = delimiter.toLowerCase();
        var index = lowertext.indexOf(lowerdelimiter);
        if(index == -1) {
            return [text]
        }
        var current_bit = text.substr(0, index);
        var current_delimiter = text.substr(index, delimiter.length);
        var rest = text.substr(index + delimiter.length, 1000);
        var res = [current_bit, current_delimiter].concat(split(rest, delimiter));
        return res
    }

    // Callback for each keystroke
    function callback() {
        var current_text = $(selector).val().toLowerCase();
        control.hide();
        clear_all_links();

        if(current_text.length < 1) {
            return;
        }

        if(data == null) {
            add_text_only_link(error_loading_msg);
            load_items();
            control.show();
            return;
        } else {
            var to_show = [];
            function select_item(item){
                if(to_show.indexOf(item) == -1) {
                    to_show.push(item);
                }
            }

            // Search full name
            $.each(data, function (i, item) {
                if(gen_name_fn(item).toLowerCase() == current_text) {
                    select_item(item);
                }
            });

            // Search all the fields
            $.each(fields_to_search, function (i, field) {
                $.each(data, function (i, item) {
                    if(item[field].toLowerCase().contains(current_text)) {
                        select_item(item);
                    }
                });
            });

            // Show all the found items
            if(to_show.length > 0) {
                $.each(to_show, function (i, item) {
                    var text_to_add = gen_name_fn(item);
                    // bold the found text
                    var parts = split(text_to_add, current_text);
                    $.each(parts, function (index, part) {
                        if(index % 2 == 1) {
                            parts[index] = "<b>" + part + "</b>";
                        }
                    });
                    var res = parts.join("");
                    add_link(gen_name_post_process_fn(item, res), item);
                });
            } else {
                add_text_only_link(no_match_msg);
            }
        }
        control.show();
    }
    $(selector).focus(callback);
    $(selector).keyup(callback);
    $(selector).blur(function() {
        control.hide(400);
    });
}
