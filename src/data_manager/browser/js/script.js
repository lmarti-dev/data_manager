
function bind_click(object) {
    object.addEventListener("click", (e) => {
        let active_text = document.getElementById("project-select-active-text")
        active_text.innerHTML = object.innerHTML
        let project_id = object.getAttribute("id")
        let project_class = "part-of-" + project_id
        let scroll_items = document.getElementsByClassName("list-group-item")
        for (var scroll_ind = 0; scroll_ind < scroll_items.length; scroll_ind++) {
            if (scroll_items[scroll_ind].classList.contains(project_class) || "project-all-projects" === project_id) {
                scroll_items[scroll_ind].removeAttribute("style")
            } else {
                scroll_items[scroll_ind].setAttribute("style", "display:none;")
            }
        }

    });
}

async function main() {
    let project_drop_down = document.getElementById("project-select-dropdown")
    let projects = project_drop_down.getElementsByClassName("dropdown-item")

    for (var ind_proj = 0; ind_proj < projects.length; ind_proj++) {
        bind_click(projects[ind_proj])
    }



};


function ellipse_long_content() {

    var max_length = 1000;
    var i;
    var divs = document.querySelectorAll('*:not(:has(*))');
    for (i = 0; i < divs.length; i++) {
        console.log(divs[i])
        if (divs[i].innerHTML.length > max_length) {

            divs[i].innerHTML = divs[i].innerHTML.substring(0, max_length) + "...";
        }
    }
}

document.addEventListener('DOMContentLoaded', (event) => {
    ellipse_long_content()
    main()
});