from flask import Flask, request
from flask import make_response
import os
from data_manager import read_data_path, ExtendedJSONEncoder

app = Flask(__name__)


def get_walk_as_json():
    data_path = read_data_path()
    return os.walk(data_path)


@app.route("/", methods=["POST"])
def result():
    print(request.form["foo"])  # should display 'bar'
    result = "return this"
    resp = make_response('{"response": ' + result + "}")
    resp.headers["Content-Type"] = "application/json"
    return resp


if __name__ == "__main__":
    app.run(debug=True)
