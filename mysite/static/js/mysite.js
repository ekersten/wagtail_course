var yOff = 300;
var xOff = -100;
var giphys = $('a[href$=".gif"]');

giphys.each(function (e) {
    $(this).hover(function (e) {
        $("body").append("<p id='giphy-image'><img src='" + $(this).attr('href') + "'/></p>");
        $("#giphy-image").css("position", "absolute");
        if ($(window).width() > 768) {
            $("#giphy-image")
                .css("top", (e.pageY - yOff) + "px")
                .css("left", (e.pageX + xOff) + "px");
        } else if ($(window).width() < 767) {
            $("#giphy-image")
                .css("top", (e.pageY - 130) + "px")
                .css("left", (e.pageX + -100) + "px");
        }
        $("#giphy-image img").delay(400).animate({ opacity: 1 }, 100);
    },
        function () {
            $("#giphy-image").remove();
        }
    );

});

giphys.on('click', function(e) {
    e.preventDefault();
});