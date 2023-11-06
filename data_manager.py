import os
from datetime import datetime
import io
import numpy as np
import __main__
import logging
import sys
import matplotlib.pyplot as plt
from json_extender import ExtendedJSONEncoder, ExtendedJSONDecoder
import json


DATA_DIR = "data"
FIG_DIR = "figures"
LOGGING_DIR = "logging"
RUN_DIR = "run"
RESTORE_FILENAME = "edm_data"
DATE_FORMAT = "%Y_%m_%d"


def home() -> str:
    return os.path.dirname(__file__)


def wordlists_dir() -> str:
    return os.path.join(home(), "wordlists")


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


def print_experiments_without_data(data_folder: str):
    days = os.listdir(data_folder)
    for day in days:
        if is_date(day):
            print(day)
            experiments = os.listdir(os.path.join(data_folder, day))
            for experiment in experiments:
                has_data = False
                for _, dirnames, _ in os.walk(
                    os.path.join(data_folder, day, experiment)
                ):
                    if "data" in dirnames:
                        has_data = True
                        break
                if not has_data:
                    print(experiment)


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


class ExperimentDataManager:
    def __init__(
        self,
        data_folder: os.PathLike,
        *,
        experiment_name: str = None,
        file_default_name: str = None,
        overwrite_experiment: bool = False,
        redirect_print_output: bool = True,
        notes: str = None,
        zero_padding_len: int = 5,
        experiment_date: str = None,
        start_new_run: bool = True,
        dry_run: bool = False,
    ) -> None:
        # get everything to save for later
        self.overwrite_experiment = overwrite_experiment
        self.redirect_print_output = redirect_print_output
        self.notes = notes
        self.data_folder = data_folder
        self.zero_padding_len = zero_padding_len
        self.dry_run = dry_run

        # default filename
        if file_default_name is None:
            self.file_default_name = name_builder(["foods.txt"])
        else:
            self.file_default_name = file_default_name

        # set run number to none, figure it out later
        self.run_number = None

        # in case we restore, we set the original date back
        if experiment_date is None:
            self.experiment_date = datetime.today().strftime(DATE_FORMAT)
        else:
            self.experiment_date = experiment_date

        # create new name if none is given
        if experiment_name is None:
            experiment_name = name_builder(["scientists.txt", "ge_villes.txt"])
        experiment_name = "_".join((experiment_name, self.clock))

        # if we allow the experiment to continue over the original folder
        if self.overwrite_experiment:
            self.experiment_name = experiment_name
        else:
            self.experiment_name = self.ensure_experiment_name(experiment_name)

        # save only if not dry run
        if not self.dry_run:
            print(
                "Experiment name: {} created {}. Clock reads {}".format(
                    self.experiment_name, self.experiment_date, self.now
                )
            )

        if start_new_run:
            self.new_run(notes=notes)

    def redirect_print(self):
        if not self.dry_run:
            print_output_fpath = self.get_experiment_fpath(
                filename="print_output", extension=".log", subfolder=LOGGING_DIR
            )
            targets = logging.StreamHandler(sys.stdout), logging.FileHandler(
                print_output_fpath
            )
            logging.basicConfig(
                format="%(message)s", level=logging.INFO, handlers=targets
            )
            __main__.print = logging.info
            print(
                "Redirect print of {} to {}".format(
                    __main__.__file__, print_output_fpath
                )
            )

    def new_run(self, notes: str = None):
        if self.run_number is None:
            self.run_number = 0
        else:
            self.run_number += 1
        print("New run: starting run {}".format(self.run_number))

        manifest = {"main_file": __main__.__file__, "timestamp": self.now}
        # add notes to manifest
        if notes is not None:
            manifest["notes"] = notes
        self.save_dict_to_experiment(
            jobj=manifest,
            filename="manifest",
            category=LOGGING_DIR,
        )
        if not self.dry_run:
            print("Run saving in folder: {}".format(self.current_run_dir))
            print("Saved manifest: {}".format(manifest))

        self.store()

    @property
    def current_data_dir(self) -> str:
        return os.path.join(self.current_saving_dirname, DATA_DIR)

    @property
    def current_logging_dir(self) -> str:
        return os.path.join(self.current_saving_dirname, LOGGING_DIR)

    @property
    def current_fig_dir(self) -> str:
        return os.path.join(self.current_saving_dirname, FIG_DIR)

    @property
    def current_run_dir(self) -> str:
        return RUN_DIR + "_" + f"{self.run_number:0{self.zero_padding_len}}"

    @property
    def current_saving_dirname(self):
        # this is where you save current stuff
        return os.path.join(
            self.data_folder,
            self.experiment_date,
            self.experiment_name,
            self.current_run_dir,
        )

    @property
    def load_last_saved_data_file(self) -> str:
        run_data_folder = os.path.join(self.current_saving_dirname, DATA_DIR)
        filenames = os.listdir(run_data_folder)
        fpath = os.path.join(run_data_folder, max(filenames))
        jobj = json.loads(
            io.open(fpath, "r", encoding="utf8").read(),
            cls=ExtendedJSONDecoder,
        )
        print(f"Loaded file: {fpath}")
        return jobj

    @property
    def now(self):
        return datetime.today().strftime("%Y_%m_%d_%H_%M_%S")

    @property
    def clock(self):
        return datetime.today().strftime("%Hh%M")

    def ensure_experiment_name(self, experiment_name):
        folders = os.listdir(os.path.join(self.data_folder, self.experiment_date))
        n_experiments = len([experiment_name == x for x in folders])
        if experiment_name in folders:
            experiment_name += "_" + f"{n_experiments:0{self.zero_padding_len}}"
        return experiment_name

    def store(self):
        # save self data for later use
        jobj = {
            "init": {
                "data_folder": self.data_folder,
                "experiment_name": self.experiment_name,
                "file_default_name": self.file_default_name,
                "overwrite_experiment": self.overwrite_experiment,
                "redirect_print_output": self.redirect_print_output,
                "zero_padding_len": self.zero_padding_len,
                "experiment_date": self.experiment_date,
            },
            "run_number": self.run_number,
            "current_run_dir": self.current_run_dir,
        }
        self.save_dict_to_experiment(
            jobj=jobj, filename=RESTORE_FILENAME, category=LOGGING_DIR
        )

    @classmethod
    def restore(cls, experiment_dirname: str):
        # This allows you to pick up where you stopped,
        # and eventually also save figures in the corresponding folder
        # so that your data and figures are in the same place

        # check there is a edm_save file
        last_run = dirname_has_substring(experiment_dirname, RUN_DIR)
        current_run_dir = os.path.join(experiment_dirname, last_run)
        last_log = dirname_has_substring(current_run_dir, LOGGING_DIR)
        current_log_dir = os.path.join(current_run_dir, last_log)
        restore_fn = dirname_has_substring(current_log_dir, RESTORE_FILENAME)

        # restore it
        restore_file = io.open(
            os.path.join(current_log_dir, restore_fn), "r", encoding="utf8"
        ).read()

        # load jobj and restore without new run
        jobj = json.loads(restore_file, cls=ExtendedJSONDecoder)
        edm = ExperimentDataManager(**jobj["init"], start_new_run=False)
        edm.run_number = jobj["run_number"]
        print("Experiment restored: {}".format(edm.current_saving_dirname))
        return edm

    def get_experiment_fpath(
        self,
        filename: os.PathLike = None,
        extension: str = ".json",
        subfolder: os.PathLike = None,
        add_timestamp: bool = True,
    ):
        # get automatic full path to save file
        # check for subfolder
        if subfolder:
            dirname = os.path.join(self.current_saving_dirname, subfolder)
        else:
            dirname = self.current_saving_dirname

        # create required path
        if not self.dry_run and not os.path.exists(dirname):
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
                filename = (
                    self.file_default_name + "_" + f"{0:0{self.zero_padding_len}}"
                )

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
        if not self.dry_run:
            experiment_fpath = self.get_experiment_fpath(
                filename,
                extension=".json",
                subfolder=category,
                add_timestamp=add_timestamp,
            )
            print("saving object called {}".format(os.path.basename(experiment_fpath)))
            jobj_str = json.dumps(
                jobj, indent=4, ensure_ascii=False, cls=ExtendedJSONEncoder
            )
            fstream = io.open(experiment_fpath, "w+")
            fstream.write(jobj_str)
            print("wrote json to {}".format(experiment_fpath))
            fstream.close()

    def dump_some_variables(
        self, large_array_threshold: int = -1, filename: str = "var_dump", **kwargs
    ):
        if not self.dry_run:
            print("dumping variables {}".format(kwargs.keys()))
        # this function is for quick dumping of variable to identify
        # a folder. For readability, we can hide big arrays
        if large_array_threshold > 0:
            for k in kwargs.keys():
                item = kwargs[k]
                try:
                    if (
                        isinstance(item, (tuple, list, np.ndarray))
                        and len(item) > large_array_threshold
                    ):
                        kwargs[
                            k
                        ] = f"{item.__class__.__name__} array of len {len(item)}"
                except:
                    pass

        kwargs.update({"__timestamp": self.now})
        self.save_dict_to_experiment(kwargs, category=LOGGING_DIR, filename=filename)

    def save_figure(
        self,
        fig: plt.Figure,
        filename: str = None,
        add_timestamp: bool = True,
        save_data: bool = True,
    ):
        if filename is None:
            filename = name_builder(["foods.txt"])
        figure_fpath = self.get_experiment_fpath(
            filename,
            extension=".pdf",
            subfolder=FIG_DIR,
            add_timestamp=add_timestamp,
        )
        if not self.dry_run:
            fig.savefig(figure_fpath, format="pdf")
            print("saved figure to {}".format(figure_fpath))
        if save_data:
            fig_data = get_figure_dict(fig=fig)
            self.save_dict_to_experiment(
                filename=filename + "_data", jobj=fig_data, category=FIG_DIR
            )
