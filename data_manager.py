import atexit
import io
import json
import logging
import os
import pickle
import re
import sys
from datetime import datetime

import constants
import matplotlib.pyplot as plt
import numpy as np
from browser.py.browser_builder import add_to_browser
from json_extender import ExtendedJSONDecoder
from utils import (
    dirname_has_substring,
    get_figure_dict,
    name_builder,
    read_data_path,
    extended_dumps,
    get_project_list,
    normalize_str,
    timestamp_dict,
)

import __main__


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
        add_timestamp: bool = False,
        save_logging_files: bool = True,
        dry_run: bool = False,
        use_runs: bool = True,
        use_calendar: bool = True,
        add_to_browser: bool = True,  # might change this to false
        tags: str = None,
        project: str = None,
    ) -> None:
        # get everything to save for later
        self.registered_projects = get_project_list()
        if project is not None:
            if project not in self.registered_projects:
                raise ValueError(
                    f"{project} is not in your registered projects: {self.registered_projects}"
                )
            else:
                self.project = project
        else:
            self.project = constants.OTHER_PROJECT
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
        self.add_to_browser = add_to_browser

        # in case we restore, we set the original date back
        if experiment_date is None:
            self.experiment_date = datetime.today().strftime(constants.DATE_FORMAT)
        else:
            self.experiment_date = experiment_date
        if not self.dry_run:
            if self.use_calendar:
                self.create_date_folder()
            elif isinstance(self.use_calendar, str):
                # TODO: build custom datefolders
                pass
            else:
                pass

        # create new name if none is given
        if experiment_name is None:
            experiment_name = name_builder(["scientists.txt", "ge_villes.txt"])
        if add_timestamp:
            experiment_name = "_".join((experiment_name, self.clock))

        # if we allow the experiment to continue over the original folder
        # why the dry run? can't remember
        experiment_name = normalize_str(experiment_name)
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

        if not self.dry_run:
            self.create_browser_data(tags)

        # rebuild browser automatically
        if not dry_run and self.add_to_browser:
            atexit.register(self.add_myself)

    def format_for_display(self, s: str):
        s2 = re.sub(r"_[0-9]{2}h[0-9]{2}", "", s)
        s2 = re.sub(r"_", " ", s2)
        return s2

    def create_browser_data(self, tags: str = None):
        browser_data_dir = os.path.join(self.experiment_path, constants.BROWSER_FOLDER)
        os.makedirs(browser_data_dir)

        jobj = {
            "display_name": self.format_for_display(self.experiment_name),
            "project": self.project,
        }
        if tags is not None:
            jobj["tag_list"] = self.process_tags(tags)
        else:
            jobj["tag_list"] = []

        self.save_dict(
            jobj,
            filename=constants.MANIFEST_FILENAME,
            category=constants.LOGGING_DIR,
            dirname=browser_data_dir,
            add_timestamp=False,
        )

    @property
    def experiment_path(self):
        return os.path.join(
            self.data_folder, self.experiment_date, self.experiment_name
        )

    def add_myself(self):
        return add_to_browser(
            self.experiment_date, self.experiment_name, self.experiment_path
        )

    def process_tags(self, tags: str):
        if isinstance(tags, (tuple, list)):
            return tags
        taglist = sorted(set(re.split(r"[,;\.] ?", tags)))
        return taglist

    def setup_logging(self, notes: str):
        if self.save_logging_files and not self.dry_run:
            self.save_manifest(notes=notes)
            self.save_experiment_manager()
            if self.redirect_print_output:
                self.redirect_print()

    def create_date_folder(self):
        dirname = os.path.join(self.data_folder, self.experiment_date)
        if not self.dry_run and not os.path.exists(dirname):
            os.makedirs(dirname)
            print("created {}".format(dirname))

    def redirect_print(self):
        if not self.dry_run:
            print_output_fpath = self.get_savepath(
                filename="print_output",
                extension=".log",
                subfolder=constants.LOGGING_DIR,
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
        manifest = {"main_file": __main__.__file__}
        # add notes to manifest
        if notes is not None:
            manifest["notes"] = notes
        self.save_dict(
            jobj=manifest,
            filename=constants.MANIFEST_FILENAME,
            category=constants.LOGGING_DIR,
            add_timestamp=False,
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
        return os.path.join(self.current_saving_dirname, constants.DATA_DIR)

    @property
    def current_logging_dir(self) -> str:
        return os.path.join(self.current_saving_dirname, constants.LOGGING_DIR)

    @property
    def current_fig_dir(self) -> str:
        return os.path.join(self.current_saving_dirname, constants.FIG_DIR)

    @property
    def current_run_dir(self) -> str:
        if not self.use_runs:
            return ""
        return constants.RUN_DIR + "_" + f"{self.run_number:0{self.zero_padding_len}}"

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
        run_data_folder = os.path.join(self.current_saving_dirname, constants.DATA_DIR)
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
        return datetime.today().strftime(constants.DATETIME_FORMAT)

    @property
    def clock(self):
        return datetime.today().strftime(constants.CLOCK_FORMAT)

    def change_filename_if_double(self, filename, dirname):
        folders = os.listdir(dirname)
        if filename in folders:
            n_experiments = sum([1 if filename == x else 0 for x in folders])
            filename += "_" + f"{n_experiments:0{self.zero_padding_len}}"
        return filename

    def ensure_experiment_name(self, experiment_name):
        if self.use_calendar:
            dirname = os.path.join(self.data_folder, self.experiment_date)
        else:
            dirname = self.data_folder
        experiment_name = self.change_filename_if_double(
            filename=experiment_name, dirname=dirname
        )
        return experiment_name

    def save_experiment_manager(self):
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
        self.save_dict(
            jobj=jobj,
            filename=constants.RESTORE_FILENAME,
            category=constants.LOGGING_DIR,
        )

    @classmethod
    def load_experiment_manager(cls, experiment_dirname: str):
        # This allows you to pick up where you stopped,
        # and eventually also save figures in the corresponding folder
        # so that your data and figures are in the same place

        # check there is a edm_save file
        last_run = dirname_has_substring(experiment_dirname, constants.RUN_DIR)
        current_run_dir = os.path.join(experiment_dirname, last_run)
        last_log = dirname_has_substring(current_run_dir, constants.LOGGING_DIR)
        current_log_dir = os.path.join(current_run_dir, last_log)
        restore_fn = dirname_has_substring(current_log_dir, constants.RESTORE_FILENAME)

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

    def get_savepath(
        self,
        filename: os.PathLike = None,
        dirname: os.PathLike = None,
        extension: str = ".json",
        subfolder: os.PathLike = None,
        add_timestamp: bool = True,
    ):
        # get automatic full path to save file
        # check for subfolder
        if dirname is None:
            if subfolder is not None:
                dirname = os.path.join(self.current_saving_dirname, subfolder)
            else:
                dirname = self.current_saving_dirname
        else:
            if subfolder is not None:
                dirname = os.path.join(dirname, subfolder)
            else:
                pass

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

        # check for similar filename and append 000x at end if true
        filename = self.change_filename_if_double(filename=filename, dirname=dirname)

        # time stamp it
        if add_timestamp:
            filename = filename + "_" + self.now

        # put everything together
        current_run_savepath = os.path.join(dirname, filename + extension)
        return current_run_savepath

    def save_dict(
        self,
        jobj: dict,
        filename: str = None,
        category: str = constants.DATA_DIR,
        add_timestamp: bool = False,
        return_fpath: bool = False,
        dirname: str = None,
    ):
        if not self.dry_run:
            fpath = self.get_savepath(
                dirname=dirname,
                filename=filename,
                extension=".json",
                subfolder=category,
                add_timestamp=add_timestamp,
            )
            # if list, turn into dict to timestamp
            if not isinstance(jobj, dict):
                jobj = {"__content": jobj}
            timestamp_dict(jobj)

            print("saving object called {}".format(os.path.basename(fpath)))
            jobj_str = extended_dumps(jobj)
            fstream = io.open(fpath, "w+")
            fstream.write(jobj_str)
            print("wrote json to {}".format(fpath))
            fstream.close()
            if return_fpath:
                return fpath

    def var_dump(
        self,
        large_array_threshold: int = -1,
        filename: str = "var_dump",
        **kwargs,
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

        self.save_dict(
            kwargs,
            category=constants.LOGGING_DIR,
            filename=filename,
            add_timestamp=False,
        )

    def save_figure(
        self,
        fig: plt.Figure,
        filename: str = None,
        add_timestamp: bool = True,
        save_data: str = "pickle",
        expand_figure: bool = True,
        fig_shape: str = "regular",
    ):
        if not self.dry_run:
            if filename is None:
                filename = name_builder(["foods.txt"])
            figure_fpath = self.get_savepath(
                filename,
                extension=".pdf",
                subfolder=constants.FIG_DIR,
                add_timestamp=add_timestamp,
            )
            if save_data == "json":
                # WARNING! this method saves only a fraction of the plot data
                # use pickle if possible
                fig_data = get_figure_dict(fig=fig)
                self.save_dict(
                    filename=filename + "_data",
                    jobj=fig_data,
                    category=constants.FIG_DIR,
                )
            elif save_data == "pickle":
                experiment_fpath = self.get_savepath(
                    filename + "_data",
                    extension=".pickle",
                    subfolder=constants.FIG_DIR,
                    add_timestamp=add_timestamp,
                )
                pkl = pickle.dumps(obj=fig)
                out_file = io.open(experiment_fpath, "wb+")
                out_file.write(pkl)
            # saving the figure
            # the figure needs to be saved after the data as sometimes
            # one gets a TypeError from a faulty cache
            # since you can't pickle a _io.BufferedWriter
            bbox_inches = None
            figsize = plt.rcParams["figure.figsize"]
            if expand_figure:
                bbox_inches = "tight"

            # a full figure fits snugly in a revtex column
            michael_scaling = True
            if michael_scaling:
                figsize = (figsize[0], figsize[1] * 1.5)
            if fig_shape == "regular":
                pass
            elif fig_shape == "half-y":
                figsize = (figsize[0], figsize[1] / 2)
            elif fig_shape == "half-x":
                figsize = (figsize[0] / 2, figsize[1])
            elif fig_shape == "half-size":
                figsize = (figsize[0] / 2, figsize[1] / 2)
            elif fig_shape == "page-wide":
                figsize = (figsize[0] * 2, figsize[1])
            fig.set_size_inches(figsize[0], figsize[1])
            fig.savefig(
                figure_fpath, format="pdf", bbox_inches=bbox_inches, pad_inches=0.01
            )
            print("saved figure to {}".format(figure_fpath))
