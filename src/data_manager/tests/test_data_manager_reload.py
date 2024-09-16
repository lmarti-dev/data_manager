from data_manager.data_manager import ExperimentDataManager
import os


edm = ExperimentDataManager.load(
    experiment_dirname=os.path.dirname(__file__)
    + "/test_data_folder/2023_09_28/goldhaber_presinge_14h21",
)

print(edm.current_data_dir)
print(edm.current_fig_dir)
print(edm.current_run_dir)
