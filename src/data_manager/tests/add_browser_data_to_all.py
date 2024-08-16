import io
import json
import os
import uuid

import constants
from data_manager.browser_builder import get_browser_data
from data_manager.json_extender import ExtendedJSONEncoder
from data_manager.utils import read_data_path

from data_manager.data_manager import ExperimentDataManager

data_path = read_data_path()

for date in os.listdir(data_path):
    if not date.startswith("_"):
        for experiment_name in os.listdir(os.path.join(data_path, date)):
            print(experiment_name)
            print(os.path.join(data_path, date, experiment_name))
            if constants.BROWSER_FOLDER not in os.listdir(
                os.path.join(data_path, date, experiment_name)
            ):
                edm = ExperimentDataManager.load_experiment_manager(
                    os.path.join(data_path, date, experiment_name)
                )
                edm.project = "fermionic cooling"
                if "plot" in edm.experiment_name:
                    tags = ["plotting"]
                else:
                    tags = None

                edm.create_browser_data(tags=tags)
            else:
                browser_data = get_browser_data(
                    os.path.join(data_path, date, experiment_name)
                )
                if "uuid" not in browser_data.keys():
                    browser_data["uuid"] = f"experiment_{uuid.uuid4()}"
                elif "uuid" in browser_data.keys():
                    if isinstance(browser_data["uuid"], (tuple, list)):
                        browser_data["uuid"] = f"experiment_{uuid.uuid4()}"
                    elif "project_" in browser_data["uuid"]:
                        browser_data["uuid"] = browser_data["uuid"].replace(
                            "project_", "experiment_"
                        )
                if browser_data["project"] == "fermionic_cooling":
                    browser_data["project"] = "fermionic cooling"
                if "display_name" not in browser_data.keys():
                    browser_data["display_name"] = (
                        ExperimentDataManager.format_for_display(experiment_name),
                    )
                fstream = io.open(
                    os.path.join(
                        os.path.join(data_path, date, experiment_name),
                        constants.BROWSER_FOLDER,
                        constants.LOGGING_DIR,
                        constants.MANIFEST_FILENAME + ".json",
                    ),
                    "w+",
                    encoding="utf8",
                )
                fstream.write(
                    json.dumps(
                        browser_data,
                        indent=4,
                        ensure_ascii=False,
                        cls=ExtendedJSONEncoder,
                    )
                )
                fstream.close()
