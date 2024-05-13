from data_manager import ExperimentDataManager
import os

data_folder = os.path.dirname(__file__) + "/test_data_folder"
edm = ExperimentDataManager(data_folder=data_folder, experiment_name="test_file_exists")


edm.var_dump(a=1, b=2)
edm.var_dump(a=10, b=20, c="mdr")


edm.save_dict({"kez": 1, "mez": 100}, filename="will_overwrite")
edm.save_dict({"droopy": "good", "gloopy": "strong"}, filename="will_overwrite")
