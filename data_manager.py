import os
from datetime import datetime
import io
import numpy as np
import __main__
import logging
import sys
import matplotlib.pyplot as plt
from json_extender import ExtendedJSONEncoder
import json


DATA_DIR = "data"
FIG_DIR = "figures"
LOGGING_DIR = "logging"


def random_word_from_list(fpath):
    lines = io.open(fpath, "r", encoding="utf8").read().splitlines()
    return np.random.choice(lines)


def get_figure_dict(fig: plt.Figure) -> dict:
    fig_data = {}
    axes = fig.get_axes()
    for ax_ind, ax in enumerate(axes):
        ax_k = f"ax_{ax_ind}"
        if ax_k not in fig_data:
            fig_data[ax_k] = {}
        for line_ind, line in enumerate(ax.lines):
            x_data = line._x
            y_data = line._y
            line_data = {"x_data": x_data, "y_data": y_data}
            line_k = f"line_{line_ind}"
            fig_data[ax_k][line_k] = line_data
        x_label = ax.xaxis.label.get_text()
        y_label = ax.yaxis.label.get_text()
        fig_data[ax_k]["x_label"] = x_label
        fig_data[ax_k]["y_label"] = y_label
    fig_data["creator"] = __main__.__file__
    return fig_data


def get_time_of_day():
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


class ExperimentDataManager:
    def __init__(
        self,
        data_folder: os.PathLike,
        experiment_name: str = None,
        file_default_name: str = None,
        overwrite_experiment: bool = False,
        redirect_print_output: bool = True,
        notes: str = None,
        zero_padding_len: int = 5,
    ) -> None:
        self.data_folder = data_folder
        self.run_number = None
        self.zero_padding_len = zero_padding_len
        if file_default_name is None:
            self.file_default_name = self.random_filename()
        else:
            self.file_default_name = file_default_name
        if experiment_name is None:
            experiment_name = (
                self.random_experiment_name()
                + "_"
                + get_time_of_day()
                + "_"
                + self.clock
            )
        if overwrite_experiment:
            self.experiment_name = experiment_name
        else:
            self.experiment_name = self.ensure_experiment_name(experiment_name)
        self.today = datetime.today().strftime("%Y_%m_%d")

        self.new_run()
        print("Run saving in folder: {}".format(self.current_run_dir))
        if redirect_print_output:
            self.redirect_print()

        print("created experiment {}. Today is {}".format(experiment_name, self.today))
        manifest = {"main_file": __main__.__file__, "timestamp": self.now}
        # add notes to manifest
        if notes is not None:
            manifest["notes"] = notes
        self.save_dict_to_experiment(
            jobj=manifest,
            filename="manifest",
            category=LOGGING_DIR,
        )
        print("saved manifest: {}".format(manifest))

    def redirect_print(self):
        print_output_fpath = self.get_experiment_fpath(
            filename="print_output", extension=".log", subfolder=LOGGING_DIR
        )
        targets = logging.StreamHandler(sys.stdout), logging.FileHandler(
            print_output_fpath
        )
        logging.basicConfig(format="%(message)s", level=logging.INFO, handlers=targets)
        __main__.print = logging.info
        print(
            "redirect print of {} to {}".format(__main__.__file__, print_output_fpath)
        )

    def new_run(self):
        if self.run_number is None:
            self.run_number = 0
        else:
            self.run_number += 1
        print("new run: starting run {}".format(self.run_number))

    @property
    def current_data_dir(self):
        return os.path.join(self.experiment_dirname, DATA_DIR)

    @property
    def current_logging_dir(self):
        return os.path.join(self.experiment_dirname, LOGGING_DIR)

    @property
    def current_fig_dir(self):
        return os.path.join(self.experiment_dirname, FIG_DIR)

    @property
    def current_run_dir(self):
        return "run_" + str(self.run_number)

    @property
    def home(self):
        return os.path.dirname(__file__)

    @property
    def experiment_dirname(self):
        return os.path.join(
            self.data_folder, self.today, self.experiment_name, self.current_run_dir
        )

    @property
    def now(self):
        return datetime.today().strftime("%Y_%m_%d_%H_%M_%S")

    @property
    def clock(self):
        return datetime.today().strftime("%H%M")

    def ensure_experiment_name(self, experiment_name):
        folders = os.listdir(self.data_folder)
        n_experiments = len([experiment_name == x for x in folders])
        if experiment_name in folders:
            experiment_name += "_" + f"{n_experiments:0{self.zero_padding_len}}"
        return experiment_name

    def get_experiment_fpath(
        self,
        filename: os.PathLike = None,
        extension: str = ".json",
        subfolder: os.PathLike = None,
        add_timestamp: bool = True,
    ):
        # check for subfolder
        if subfolder:
            dirname = os.path.join(self.experiment_dirname, subfolder)
        else:
            dirname = self.experiment_dirname

        # create required path
        if not os.path.exists(dirname):
            os.makedirs(dirname)
            print("created {}".format(dirname))

        # if no filename, pick one from the list and append number
        if filename is None:
            if os.path.exists(dirname):
                files = os.listdir(dirname)
                n_files = len(files)
                filename = (
                    self.file_default_name + "_" + f"{n_files:0{self.zero_padding_len}}"
                )
            else:
                filename = self.file_default_name + "_0"

        # remove duplicate extension if necessary
        else:
            if "." in filename:
                filename = os.path.splitext(os.path.basename(filename))[0]

        # time stamp it
        if add_timestamp:
            filename = filename + "_" + self.now

        # put everything together
        experiment_fpath = os.path.join(dirname, filename + extension)
        return experiment_fpath

    def save_dict_to_experiment(
        self,
        jobj: dict,
        filename: str = None,
        category: str = DATA_DIR,
        add_timestamp: bool = True,
    ):
        experiment_fpath = self.get_experiment_fpath(
            filename, extension=".json", subfolder=category, add_timestamp=add_timestamp
        )
        print("saving object called {}".format(os.path.basename(experiment_fpath)))
        jobj_str = json.dumps(
            jobj, indent=4, ensure_ascii=False, cls=ExtendedJSONEncoder
        )
        fstream = io.open(experiment_fpath, "w+")
        fstream.write(jobj_str)
        print("wrote json to {}".format(experiment_fpath))
        fstream.close()

    def dump_some_variables(self, **kwargs):
        print("dumping variables {}".format(kwargs.keys()))
        kwargs.update({"now": self.now})
        self.save_dict_to_experiment(kwargs, category=LOGGING_DIR, filename="var_dump")

    def random_experiment_name(self):
        return random_word_from_list(
            os.path.join(self.home, "wordlists", "experiment_wordlist.txt")
        )

    def random_filename(self):
        return random_word_from_list(
            os.path.join(
                self.home,
                "wordlists",
                "run_default_wordlist_3.txt",
            )
        )

    def save_figure(
        self, fig: plt.Figure, filename: str = None, add_timestamp: bool = True
    ):
        if filename is None:
            filename = self.random_filename()
        figure_fpath = self.get_experiment_fpath(
            filename,
            extension=".pdf",
            subfolder=FIG_DIR,
            add_timestamp=add_timestamp,
        )
        fig.savefig(figure_fpath, format="pdf")
        print("saved figure to {}".format(figure_fpath))
        fig_data = get_figure_dict(fig=fig)
        self.save_dict_to_experiment(
            filename=filename + "_data", jobj=fig_data, category=FIG_DIR
        )
