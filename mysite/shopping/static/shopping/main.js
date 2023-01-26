//loading soln

$(function () {
    if (localStorage.tempScrollTop) {
        $(window).scrollTop(localStorage.tempScrollTop);
        alert("loaded postion : " + localStorage.tempScrollTop);
    }
});


//saving soln 1
$(window).on("scroll", function () {
    localStorage.setItem("tempScrollTop", $(window).scrollTop());
});

//saving soln 2
window.onbeforeunload = function () {
    var tempScrollTop = $(window).scrollTop();
    localStorage.setItem("tempScrollTop", tempScrollTop);
    return "Saved scroll to localstorage!!";
};