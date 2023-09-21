from data_manager import ExperimentDataManager
import numpy as np

edm = ExperimentDataManager(
    data_folder="test_data_folder", notes="this is the test experiment"
)

numeric_data = np.random.rand(30, 30)
word_data = ["word", "chocolate", "bike"]
