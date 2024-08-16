import configparser
import io
import json
import os
import re
from datetime import datetime

import __main__
import matplotlib.pyplot as plt
import numpy as np
import data_manager.constants as constants
from data_manager.json_extender import ExtendedJSONDecoder, ExtendedJSONEncoder
import shutil
from typing import Iterable

DELETE_DAY_COMMAND = "__DELETE_DAY"
HOME = os.path.dirname(__file__)
BROWSER_DATA_PATH = os.path.join(HOME, "browser")


def setup_browser_folder():
    browser_path = read_browser_path()

    print(f"Setting up {browser_path}")
    if not os.path.isdir(browser_path):
        os.makedirs(browser_path)


def init_settings(
    data_dirname: str, html_browser_dirname: str, initial_projects: list[str]
):
    HOME = os.path.dirname(__file__)

    config = get_settings_file("settings_example.ini")
    config["paths"]["data_path"] = os.path.join(data_dirname, "data")
    config["paths"]["html_browser_path"] = os.path.join(
        html_browser_dirname, "data_browser/"
    )
    config["projects"]["project_list"] = initial_projects

    filepath = os.path.join(HOME, "settings.ini")
    settings_file = io.open(filepath, "w+", encoding="utf8")
    config.write(settings_file)
    settings_file.close()
    print(f"Wrote initial config to f{filepath}")


def get_most_recent_timestamped_files(files: list):
    timestamps = []
    for f in files:
        jobj = json.loads(
            io.open(f, "r", encoding="utf8").read(), cls=ExtendedJSONDecoder
        )
        if constants.TIMESTAMP_KEY in jobj.keys():
            timestamps.append(jobj[constants.TIMESTAMP_KEY])
        else:
            raise KeyError(f"{f} is not timestamped, cannot compare files")

    ind = np.argmax(
        [datetime.strptime(x, constants.DATETIME_FORMAT) for x in timestamps]
    )
    return files[ind]


def timestamp_dict(d: dict):
    d[constants.TIMESTAMP_KEY] = datetime.today().strftime(constants.DATETIME_FORMAT)


def normalize_str(s: str):
    s2 = re.sub(" ", "_", s)
    return re.sub("[^A-Za-z0-9_]+", "", s2)


def extended_dumps(jobj: dict) -> str:
    return json.dumps(jobj, indent=4, ensure_ascii=False, cls=ExtendedJSONEncoder)


def home() -> str:
    return os.path.dirname(__file__)


def wordlists_dir() -> str:
    return os.path.join(home(), "wordlists")


def random_word_from_list(fpath):
    lines = io.open(fpath, "r", encoding="utf8").read().splitlines()
    return np.random.choice(lines)


def get_figure_dict(fig: plt.Figure):
    fig_data = {}
    axes = fig.get_axes()
    fig_data["axes"] = {}
    for ax_ind, ax in enumerate(axes):
        ax_k = f"ax_{ax_ind}"
        if ax_k not in fig_data:
            fig_data["axes"][ax_k] = {}
            fig_data["axes"][ax_k]["lines"] = {}
            fig_data["axes"][ax_k]["labels"] = {}
        for line_ind, line in enumerate(ax.lines):
            x_data = line._x
            y_data = line._y
            line_label = line.get_label()
            line_data = {"x_data": x_data, "y_data": y_data, "label": line_label}
            line_k = f"line_{line_ind}"
            fig_data["axes"][ax_k]["lines"][line_k] = line_data
        x_label = ax.xaxis.label.get_text()
        y_label = ax.yaxis.label.get_text()
        fig_data["axes"][ax_k]["labels"]["x_label"] = x_label
        fig_data["axes"][ax_k]["labels"]["y_label"] = y_label
    fig_data["creator"] = __main__.__file__
    specs = axes[0].get_gridspec()
    fig_data["specs"] = (specs.nrows, specs.ncols)
    return fig_data


def load_figure_data(figure_fpath: os.PathLike):
    jobj = json.loads(
        io.open(figure_fpath, "r", encoding="utf8").read(),
        cls=ExtendedJSONDecoder,
    )
    keys = list(jobj.keys())
    if "axes" in keys:
        axes_data = jobj["axes"]
    else:
        axes_data = [jobj[key] for key in keys if "ax" in key]
    if "specs" in keys:
        (nrows, ncols) = jobj["specs"]
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols)
    else:
        n_subplots = sum([1 if "ax" in key else 0 for key in keys])
        fig, axes = plt.subplots(nrows=n_subplots, ncols=1)

    for ind, ax in enumerate(axes_data):
        if "labels" not in ax.keys():
            x_label = ax["x_label"]
            y_label = ax["y_label"]
        else:
            x_label = ax["labels"]["x_label"]
            y_label = ax["labels"]["y_label"]
        if "lines" not in ax.keys():
            lines = {key: ax[key] for key in ax.keys() if "line_" in key}
        else:
            lines = ax["lines"]
        for line_ind in lines.keys():
            label = None
            if "label" in lines[line_ind].keys():
                label = lines[line_ind]["label"]
            axes[ind].plot(
                lines[line_ind]["x_data"],
                lines[line_ind]["y_data"],
                label=label,
            )
            axes[ind].set_xlabel(x_label)
            axes[ind].set_ylabel(y_label)
    return fig


def get_time_of_day() -> str:
    if datetime.now().hour <= 8:
        return "early_morning"
    elif datetime.now().hour <= 10:
        return "morning"
    elif datetime.now().hour < 12:
        return "late_morning"
    elif datetime.now().hour == 12:
        return "noon"
    elif datetime.now().hour <= 16:
        return "afternoon"
    elif datetime.now().hour <= 20:
        return "evening"
    elif datetime.now().hour < 24:
        return "late_evening"
    elif datetime.now().hour == 24:
        return "cursed_midnight"


def name_from_list(list_name: str) -> str:
    return normalize_str(
        random_word_from_list(os.path.join(wordlists_dir(), list_name))
    )


def name_builder(wordlists: list, *args):
    words = [name_from_list(wordlist) for wordlist in wordlists]
    return "_".join(words + list(args))


def is_date(date):
    try:
        datetime.strptime(date, constants.DATE_FORMAT)
        return True
    except ValueError:
        return False


def get_all_experiment_paths() -> Iterable:
    data_path = read_data_path()
    paths = []
    for date in os.listdir(data_path):
        if is_date(date):
            for experiment_name in os.listdir(os.path.join(data_path, date)):
                paths.append(os.path.join(data_path, date, experiment_name))
    return paths


def get_experiments_without_data(data_folder: str):
    experiments_without_data = {}
    days = os.listdir(data_folder)
    experiments_without_data = {d: [] for d in days}
    for day in days:
        if is_date(day):
            experiments = os.listdir(os.path.join(data_folder, day))
            if experiments == []:
                experiments_without_data[day] = [DELETE_DAY_COMMAND]
            else:
                for experiment in experiments:
                    has_data = False
                    for _, dirnames, _ in os.walk(
                        os.path.join(data_folder, day, experiment)
                    ):
                        if "data" in dirnames or "figures" in dirnames:
                            has_data = True
                            break
                    if not has_data:
                        experiments_without_data[day].append(experiment)
    return experiments_without_data


def print_experiments_without_data(data_folder: str):
    experiments_without_data = get_experiments_without_data(data_folder=data_folder)
    for day in experiments_without_data.keys():
        print(day)
        print("\n".join(experiments_without_data[day]))


def delete_experiments_without_data(data_folder: str):
    ewd = get_experiments_without_data(data_folder)
    print("This would delete the following folders:")
    decision = ""
    if all([len(list(ewd[k])) == 0 for k in ewd.keys()]):
        print("No folders to delete")
        return
    for k in ewd.keys():
        for item in ewd[k]:
            print(k, item)
    while decision != "Y" and decision != "n":
        print("Are you sure you want to continue? [Y/n]?")
        decision = input()
    if decision == "n":
        print("Aborting")
    if decision == "Y":
        print("Deleting")
        for k in ewd.keys():
            for item in ewd[k]:
                if item == DELETE_DAY_COMMAND:
                    fpath = os.path.join(data_folder, k)
                else:
                    fpath = os.path.join(data_folder, k, item)
                print(f"Deleting: {fpath}")
                shutil.rmtree(fpath)


def dirname_has_substring(dirname: str, substr: str, return_last: bool = True):
    tentative_items = os.listdir(os.path.join(dirname))
    items = [item for item in tentative_items if substr in item]
    if items:
        if return_last:
            return items[-1]
        else:
            return items
    else:
        raise ValueError(f"{substr} not in {dirname}")


def get_settings_file(filename: str):
    fpath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.isfile(fpath):
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), filename))
        return config
    else:
        raise FileNotFoundError(f"{filename} doesn't exist")


def get_settings():
    return get_settings_file(filename=constants.SETTINGS_FILENAME)


def get_project_list():
    config = get_settings()
    project_list = config["projects"]["project_list"]
    # absolute mad stuff by json
    project_list = project_list.replace("'", '"')
    return json.loads(project_list)


def read_data_path():
    config = get_settings()
    return config["paths"]["data_path"]


def read_browser_path():
    config = get_settings()
    return config["paths"]["html_browser_path"]
