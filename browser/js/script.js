async function run_script() {
    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (xhttp.readyState == XMLHttpRequest.DONE) {
            ini_file = this.responseText
            regex = /data_path = (.*)/
            match = ini_file.match(regex)
            console.log(match[1])
        }
    };


    xhttp.open("GET", "../settings.ini", true);
    xhttp.setRequestHeader("Content-type", "text/json");
    xhttp.overrideMimeType("text/json");
    xhttp.send();
}


function main() {
    load_files().then((e) => {



    });
};

document.addEventListener('DOMContentLoaded', (event) => {
    main()
});