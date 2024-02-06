async function run_script() {
    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (xhttp.readyState == XMLHttpRequest.DONE) {
            console.log("called the script")
            result = xhttp.responseText
            document.getElementById("main").innerHTML = result
        }
    };


    xhttp.open("POST", "./py/script.py", true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.overrideMimeType("application/json");
    data = { "foo": "bar" }
    xhttp.send(data);
}


async function main() {

};

document.addEventListener('DOMContentLoaded', (event) => {
    main()
});