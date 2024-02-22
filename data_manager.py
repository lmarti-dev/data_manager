import io
import json
import logging
import os
import pickle
import sys
from datetime import datetime

import __main__
import matplotlib.pyplot as plt
import numpy as np
from constants import *
from json_extender import ExtendedJSONDecoder, ExtendedJSONEncoder
from utils import dirname_has_substring, get_figure_dict, name_builder, read_data_path


class ExperimentDataManager:
    def __init__(
        self,
        *,
        experiment_name: str = None,
        data_folder: os.PathLike = None,
        file_default_name: str = None,
        overwrite_experiment: bool = False,
        redirect_print_output: bool = True,
        notes: str = None,
        zero_padding_len: int = 5,
        experiment_date: str = None,
        add_timestamp: bool = True,
        save_logging_files: bool = True,
        dry_run: bool = False,
        use_runs: bool = True,
        use_calendar: bool = True,
    ) -> None:
        # get everything to save for later
        self.overwrite_experiment = overwrite_experiment
        self.redirect_print_output = redirect_print_output
        self.notes = notes
        if data_folder is None:
            self.data_folder = read_data_path()
        else:
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
        self.use_runs = use_runs
        self.save_logging_files = save_logging_files
        self.use_calendar = use_calendar

        # in case we restore, we set the original date back
        if experiment_date is None:
            self.experiment_date = datetime.today().strftime(DATE_FORMAT)
        else:
            self.experiment_date = experiment_date
        if not self.dry_run and self.use_calendar:
            self.create_date_folder()

        # create new name if none is given
        if experiment_name is None:
            experiment_name = name_builder(["scientists.txt", "ge_villes.txt"])
        if add_timestamp:
            experiment_name = "_".join((experiment_name, self.clock))

        # if we allow the experiment to continue over the original folder
        if self.overwrite_experiment or self.dry_run:
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

        if not dry_run:
            if self.use_runs:
                self.new_run(notes=notes)
            else:
                self.setup_logging(notes=notes)

    def setup_logging(self, notes: str):
        if self.save_logging_files and not self.dry_run:
            self.save_manifest(notes=notes)
            self.store()
            if self.redirect_print_output:
                self.redirect_print()

    def create_date_folder(self):
        dirname = os.path.join(self.data_folder, self.experiment_date)
        if not self.dry_run and not os.path.exists(dirname):
            os.makedirs(dirname)
            print("created {}".format(dirname))

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

    def save_manifest(self, notes: str):
        manifest = {"main_file": __main__.__file__, "timestamp": self.now}
        # add notes to manifest
        if notes is not None:
            manifest["notes"] = notes
        self.save_dict_to_experiment(
            jobj=manifest,
            filename="manifest",
            category=LOGGING_DIR,
        )
        print("Saved manifest: {}".format(manifest))

    def new_run(self, notes: str = None):
        if not self.use_runs:
            raise ValueError("Starting a new run when use_runs is False is not allowed")
        if self.run_number is None:
            self.run_number = 0
        else:
            self.run_number += 1
        if not self.dry_run:
            print("Starting run {}".format(self.run_number))
            self.setup_logging(notes=notes)
            print("Run saving in folder: {}".format(self.current_run_dir))

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
        if not self.use_runs:
            return ""
        return RUN_DIR + "_" + f"{self.run_number:0{self.zero_padding_len}}"

    @property
    def current_saving_dirname(self):
        # this is where you save current stuff
        if self.use_calendar:
            date_folder = self.experiment_date
        else:
            date_folder = ""
        return os.path.join(
            self.data_folder,
            date_folder,
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
        if self.use_calendar:
            dirname = os.path.join(self.data_folder, self.experiment_date)
        else:
            dirname = self.data_folder
            folders = os.listdir(dirname)
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
                "use_runs": self.use_runs,
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
        edm = ExperimentDataManager(**jobj["init"], save_logging_files=False)
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
        return_fpath: bool = False,
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
            if return_fpath:
                return experiment_fpath

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
                        kwargs[k] = (
                            f"{item.__class__.__name__} array of len {len(item)}"
                        )
                except Exception:
                    pass

        kwargs.update({"__timestamp": self.now})
        self.save_dict_to_experiment(kwargs, category=LOGGING_DIR, filename=filename)

    def save_figure(
        self,
        fig: plt.Figure,
        filename: str = None,
        add_timestamp: bool = True,
        save_data: str = "pickle",
        expand_figure: bool = True,
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
            bbox_inches = None
            if expand_figure:
                bbox_inches = "tight"
            fig.savefig(figure_fpath, format="pdf", bbox_inches=bbox_inches)
            print("saved figure to {}".format(figure_fpath))
            if save_data == "json":
                fig_data = get_figure_dict(fig=fig)
                self.save_dict_to_experiment(
                    filename=filename + "_data", jobj=fig_data, category=FIG_DIR
                )
            elif save_data == "pickle":
                experiment_fpath = self.get_experiment_fpath(
                    filename + "_data",
                    extension=".pickle",
                    subfolder=FIG_DIR,
                    add_timestamp=add_timestamp,
                )
                out_file = io.open(experiment_fpath, "wb+")
                pickle.dump(fig, out_file)
