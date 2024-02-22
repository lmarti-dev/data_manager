import configparser
import io
import json
import os
from datetime import datetime

import __main__
import matplotlib.pyplot as plt
import numpy as np
from constants import *
from fau_colors import colors_dark
from json_extender import ExtendedJSONDecoder
from matplotlib import cycler


def set_color_cycler():
    plt.rcParams["axes.prop_cycle"] = cycler(color=list(colors_dark))


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
    return random_word_from_list(os.path.join(wordlists_dir(), list_name))


def name_builder(wordlists: list, *args):
    words = [name_from_list(wordlist) for wordlist in wordlists]
    return "_".join(words + list(args))


def is_date(date):
    try:
        datetime.strptime(date, DATE_FORMAT)
        return True
    except ValueError:
        return False


def get_experiments_without_data(data_folder: str):
    experiments_without_data = {}
    days = os.listdir(data_folder)
    experiments_without_data = {d: [] for d in days}
    for day in days:
        if is_date(day):
            experiments = os.listdir(os.path.join(data_folder, day))
            if experiments == []:
                experiments_without_data[day] = day
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
    # shutil.rmtree


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


def read_data_path():
    fpath = os.path.join(os.path.dirname(__file__), SETTINGS_FILENAME)
    if os.path.isfile(fpath):
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), SETTINGS_FILENAME))
        return config["paths"]["data_path"]
    else:
        raise FileNotFoundError("settings.ini doesn't exist")
