async function run_script() {
    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (xhttp.readyState == XMLHttpRequest.DONE) {
            console.log("called the script")
        }
    };


    xhttp.open("POST", "./py/script.py", true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.overrideMimeType("application/json");
    xhttp.send();
}


function main() {
    run_script().then((e) => {
        console.log(e)
    });
};

document.addEventListener('DOMContentLoaded', (event) => {
    main()
});