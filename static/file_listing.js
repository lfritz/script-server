$(function() {
    // Create Folder form
    $("#mkdir-name").hide();
    $("#mkdir-submit").hide();
    $("#mkdir-activate").click(function(event) {
        event.preventDefault();
        $("#mkdir-activate").hide();
        $("#mkdir-name").show();
        $("#mkdir-submit").show();
    });

    // Upload form
    $("#upload-file").hide();
    $("#upload-submit").hide();
    $("#upload-activate").click(function(event) {
        event.preventDefault();
        $("#upload-file").show();
        $("#upload-submit").show();
        $("#upload-activate").hide();
        console.log("upload!");
    });
});
