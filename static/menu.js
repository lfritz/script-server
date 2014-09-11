$(function() {
    // open/close menu when the username is clicked
    var showingUserArea = false;
    $("#user").click(function() {
        if (showingUserArea) {
            $("#user-area").hide();
            showingUserArea = false;
        } else {
            $("#user-area").show();
            showingUserArea = true;
        }
    })
});
