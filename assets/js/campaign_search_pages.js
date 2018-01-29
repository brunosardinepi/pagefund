function search() {
    var q = $('#q').val();

    $.ajax({
        url : "/create/campaign/search/",
        type : "POST",
        traditional: true,
        data : {
            q : q,
        },
        success : function(json) {
            $("#results").empty();
            for (var key in json) {
                $("#results").append(json[key]);
            }
        }
    });
};

$(document).on('keyup', '#q', function() {
    search();
});

$(document).on('keypress', '#q', function(event) {
    if (event.keyCode == 13) {
        event.preventDefault();
        return false;
    }
});

$(document).on("submit", "form", function(event) {
    if (!$("input[type='radio']:checked").length) {
        event.preventDefault();
        $("#results").append("<div class='col-md-8 offset-md-2 mt-1 mb-4'><div class='alert alert-danger' role='alert'>Please select a Page.</div></div>");
    };
});

