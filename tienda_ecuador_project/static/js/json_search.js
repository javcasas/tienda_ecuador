// <input id='selector' type="text" class="dropdown-toggle form-control col-xs-12"
//        placeholder='Añadir Artículo'
//        value=''
//        autofocus />
// <ul class="dropdown-menu col-xs-12"></ul>

function prepare_search_box(
    selector,           // JQuery selector
    gen_name_fn,        // Generates a name from the items being searched
    callback_fn,        // onclick for each item selected
    data_url,           // URL to get a JSON of all the items to search
    fields_to_search,   // List of fields to search
    no_match_msg,       // Message to show when no items match the search
    error_loading_msg   // Message to show when there was a problem loading the list
) {
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
                    add_link(res, item);
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
