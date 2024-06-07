import atexit
import io
import json
import logging
import os
import pickle
import re
import sys
import uuid
from datetime import datetime

import constants
import matplotlib.pyplot as plt
import numpy as np
from browser.py.browser_builder import add_to_browser
from json_extender import ExtendedJSONDecoder
from utils import (
    dirname_has_substring,
    extended_dumps,
    get_figure_dict,
    get_project_list,
    name_builder,
    normalize_str,
    read_data_path,
    timestamp_dict,
)

import __main__


class ExperimentDataManager:
    def __init__(
        self,
        experiment_name: str = None,
        *,
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
        start_new_run: bool = True,
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
        if overwrite_experiment or self.dry_run:
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
            if self.use_runs and start_new_run:
                self.new_run(notes=notes)
            else:
                self.setup_logging(notes=notes)

        # create browser data for later ez browsing
        if not self.dry_run and self.save_logging_files:
            self.create_browser_data(tags)

        # rebuild browser automatically
        if not dry_run and self.add_to_browser:
            atexit.register(self.add_myself)

    @classmethod
    def format_for_display(cls, s: str):
        s2 = re.sub(r"_[0-9]{2}h[0-9]{2}", "", s)
        s2 = re.sub(r"_", " ", s2)
        return s2

    def create_browser_data(self, tags: str = None):
        browser_data_dir = os.path.join(self.experiment_path, constants.BROWSER_FOLDER)
        if not os.path.isdir(browser_data_dir):
            os.makedirs(browser_data_dir)

        jobj = {
            "display_name": self.format_for_display(self.experiment_name),
            "project": self.project,
            "uuid": f"project_{uuid.uuid4()}",
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
        try:
            if hasattr(sys, "last_value"):
                last_exception = sys.last_value
                exception_raised = isinstance(last_exception, Exception)
                if not exception_raised:
                    return add_to_browser(
                        self.experiment_date, self.experiment_name, self.experiment_path
                    )
                else:
                    raise RuntimeError(
                        f"Exception raised, not adding experiment {self.experiment_name} to the browser"
                    )
            else:
                return add_to_browser(
                    self.experiment_date, self.experiment_name, self.experiment_path
                )
        except Exception:
            pass

    def process_tags(self, tags: str):
        if isinstance(tags, (tuple, list)):
            return tags
        taglist = sorted(set(re.split(r"[,;\.] ?", tags)))
        return taglist

    def check_run_number(self, run_number: int):
        if not isinstance(run_number, int):
            raise TypeError(
                f"expected run_number to be an int, got: {type(run_number)}"
            )
        if run_number == -1:
            return self.run_number
        else:
            return run_number

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
                add_timestamp=False,
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

    def data_dir(self, run_number: int = -1):
        run_number = self.check_run_number(run_number)
        return os.path.join(self.saving_dirname(run_number), constants.DATA_DIR)

    @property
    def current_data_dir(self) -> str:
        return self.data_dir()

    @property
    def current_logging_dir(self) -> str:
        return os.path.join(self.current_saving_dirname, constants.LOGGING_DIR)

    @property
    def current_fig_dir(self) -> str:
        return os.path.join(self.current_saving_dirname, constants.FIG_DIR)

    def run_dir(self, run_number: int = -1) -> str:
        run_number = self.check_run_number(run_number)
        return constants.RUN_DIR + "_" + f"{run_number:0{self.zero_padding_len}}"

    @property
    def run_dirs(self) -> str:
        runs = []
        for run_number in range(0, self.run_number + 1):
            runs.append(
                constants.RUN_DIR + "_" + f"{run_number:0{self.zero_padding_len}}"
            )
        return runs

    @property
    def current_run_dir(self) -> str:
        if not self.use_runs:
            return ""
        return self.run_dir(self.run_number)

    def saved_dicts(self, run_number: int = -1) -> list:
        run_number = self.check_run_number(run_number)
        return os.listdir(
            os.path.join(self.saving_dirname(run_number), constants.DATA_DIR)
        )

    def saving_dirname(self, run_number: int = -1):
        run_number = self.check_run_number(run_number)
        if self.use_calendar:
            date_folder = self.experiment_date
        else:
            date_folder = ""
        return os.path.join(
            self.data_folder,
            date_folder,
            self.experiment_name,
            self.run_dir(run_number=run_number),
        )

    @property
    def current_saving_dirname(self) -> str:
        # this is where you save current stuff
        return self.saving_dirname(self.run_number)

    def load_saved_dict(self, dict_filename: str, run_number: int = -1) -> dict:
        run_number = self.check_run_number(run_number)
        fpath = os.path.join(self.data_dir(run_number), dict_filename)
        return json.load(io.open(fpath, mode="rb"), cls=ExtendedJSONDecoder)

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

    def change_filename_if_double(self, filename: str, dirname: str):
        if "." in filename:
            filename = filename.split(".")[0]
            extension = filename.split(".")[1]
            exisiting_files = [
                f.split(".")[0]
                for f in os.listdir(dirname)
                if f.split(".")[1] == extension
            ]
        else:
            extension = None
            exisiting_files = [f.split(".")[0] for f in os.listdir(dirname)]

        original_filename = filename
        trial_filename = filename
        n = 1
        n_tries = 0
        while trial_filename in exisiting_files:
            trial_filename = original_filename + "_" + f"{n:0{self.zero_padding_len}}"
            n += 1
            n_tries += 1
            # in case you know
            if n_tries > 1000:
                trial_filename = original_filename + name_builder(["animals.txt"])
                return trial_filename
        return trial_filename

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
                "experiment_name": self.experiment_name,
                "file_default_name": self.file_default_name,
                "redirect_print_output": self.redirect_print_output,
                "zero_padding_len": self.zero_padding_len,
                "experiment_date": self.experiment_date,
                "use_runs": self.use_runs,
                "use_calendar": self.use_calendar,
                "project": self.project,
                "notes": self.notes,
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

        # hacky stuff for legacy
        if "data_folder" in jobj["init"].keys():
            jobj["init"]["data_folder"] = read_data_path()
        if "overwrite_experiment" in jobj["init"].keys():
            del jobj["init"]["overwrite_experiment"]
        if "experiment_name" in jobj["init"].keys():
            del jobj["init"]["experiment_name"]
        edm = ExperimentDataManager(
            **jobj["init"],
            experiment_name=os.path.basename(experiment_dirname),
            save_logging_files=False,
            add_to_browser=False,
            overwrite_experiment=True,
            start_new_run=False,
        )
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
        overwrite: bool = False,
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

        # time stamp it
        if add_timestamp:
            filename = filename + "_" + self.now

        # check for similar filename and append 000x at end if true
        if not overwrite:
            filename = self.change_filename_if_double(
                filename=filename, dirname=dirname
            )

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
            subplot_row_scaling = True
            if michael_scaling:
                figsize = (figsize[0], figsize[1] * 1.5)
            if subplot_row_scaling:
                gridspec = fig.get_axes()[0].get_gridspec()
                figsize = (figsize[0], figsize[1] * gridspec.nrows / 2)
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
            elif fig_shape == "double-wide":
                figsize = (figsize[0] * 2, figsize[1] * 2)
            fig.set_size_inches(figsize[0], figsize[1])
            fig.savefig(
                figure_fpath, format="pdf", bbox_inches=bbox_inches, pad_inches=0.01
            )
            print("saved figure to {}".format(figure_fpath))
