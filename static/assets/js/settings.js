(function ($) {
    "use strict";
    $(function () {
        $(".nav-settings").on("click", function () {
            $("#right-sidebar").toggleClass("open");
        });
        $(".settings-close").on("click", function () {
            $("#right-sidebar,#theme-settings").removeClass("open");
        });

        $("#settings-trigger").on("click", function () {
            $("#theme-settings").toggleClass("open");
        });

        //background constants
        var navbar_classes =
            "navbar-danger navbar-success navbar-warning navbar-dark navbar-light navbar-primary navbar-info navbar-pink";
        var sidebar_classes = "sidebar-light sidebar-dark";
        var $body = $("body");

        //sidebar backgrounds
        $("#sidebar-light-theme").on("click", function () {
            $body.removeClass(sidebar_classes);
            $body.addClass("sidebar-light");
            $(".sidebar-bg-options").removeClass("selected");
            $(this).addClass("selected");
        });
        $("#sidebar-dark-theme").on("click", function () {
            $body.removeClass(sidebar_classes);
            $body.addClass("sidebar-dark");
            $(".sidebar-bg-options").removeClass("selected");
            $(this).addClass("selected");
        });

        //Navbar Backgrounds
        $(".tiles.primary").on("click", function () {
            $(".navbar").removeClass(navbar_classes);
            $(".navbar").addClass("navbar-primary");
            $(".tiles").removeClass("selected");
            $(this).addClass("selected");
        });
        $(".tiles.success").on("click", function () {
            $(".navbar").removeClass(navbar_classes);
            $(".navbar").addClass("navbar-success");
            $(".tiles").removeClass("selected");
            $(this).addClass("selected");
        });
        $(".tiles.warning").on("click", function () {
            $(".navbar").removeClass(navbar_classes);
            $(".navbar").addClass("navbar-warning");
            $(".tiles").removeClass("selected");
            $(this).addClass("selected");
        });
        $(".tiles.danger").on("click", function () {
            $(".navbar").removeClass(navbar_classes);
            $(".navbar").addClass("navbar-danger");
            $(".tiles").removeClass("selected");
            $(this).addClass("selected");
        });
        $(".tiles.light").on("click", function () {
            $(".navbar").removeClass(navbar_classes);
            $(".navbar").addClass("navbar-light");
            $(".tiles").removeClass("selected");
            $(this).addClass("selected");
        });
        $(".tiles.info").on("click", function () {
            $(".navbar").removeClass(navbar_classes);
            $(".navbar").addClass("navbar-info");
            $(".tiles").removeClass("selected");
            $(this).addClass("selected");
        });
        $(".tiles.dark").on("click", function () {
            $(".navbar").removeClass(navbar_classes);
            $(".navbar").addClass("navbar-dark");
            $(".tiles").removeClass("selected");
            $(this).addClass("selected");
        });
        $(".tiles.default").on("click", function () {
            $(".navbar").removeClass(navbar_classes);
            $(".tiles").removeClass("selected");
            $(this).addClass("selected");
        });
        $(".tiles.default").on("click", function () {
            $(".navbar").removeClass(navbar_classes);
            $(".tiles").removeClass("selected");
            $(this).addClass("selected");
        });

        $(".color-theme.default").click(function () {
            $(".color-theme.default").attr({
                href: "https://www.bootstrapdash.com/demo/star-admin2-pro/template/demo/vertical-default-light/index.html",
                title: "Light",
            });
        });
        $(".color-theme.dark").click(function () {
            $(".color-theme.dark").attr({
                href: "https://www.bootstrapdash.com/demo/star-admin2-pro/template/demo/vertical-default-dark/index.html",
                title: "Dark",
            });
        });
        $(".color-theme.brown").click(function () {
            $(".color-theme.brown").attr({
                href: "https://www.bootstrapdash.com/demo/star-admin2-pro/template/demo/vertical-default-brown/index.html",
                title: "Brown",
            });
        });
    });
})(jQuery);



// This file is part of the Requisition App project.
// It is used to manage the settings page, specifically for adding and removing hierarchy levels.
document.addEventListener("DOMContentLoaded", function () {
    const addBtn = document.getElementById("add-hierarchy");
    const list = document.getElementById("hierarchy-list");

    addBtn.addEventListener("click", function () {
        const row = document.createElement("div");
        row.className = "row mb-2 hierarchy-row";
        row.innerHTML = `
            <div class="col-8">
                <input type="text" class="form-control" name="positions[]" placeholder="Position (e.g. Manager)" required>
            </div>
            <div class="col-3">
                <input type="number" class="form-control" name="levels[]" min="1" placeholder="Level" required>
            </div>
            <div class="col-1 d-flex align-items-center">
                <button type="button" class="btn btn-danger btn-sm remove-hierarchy">&times;</button>
            </div>
        `;
        list.appendChild(row);
        updateRemoveButtons();
    });

    function updateRemoveButtons() {
        const removeBtns = document.querySelectorAll(".remove-hierarchy");
        removeBtns.forEach((btn) => {
            btn.style.display = removeBtns.length > 1 ? "inline-block" : "none";
            btn.onclick = function () {
                btn.closest(".hierarchy-row").remove();
                updateRemoveButtons();
            };
        });
    }
    updateRemoveButtons();
});
