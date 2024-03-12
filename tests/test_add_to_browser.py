from data_manager import ExperimentDataManager
import matplotlib.pyplot as plt
import numpy as np

edm = ExperimentDataManager(experiment_name="test_add_browser", add_to_browser=True)


edm.save_dict_to_experiment({"this data": "is useless"})

edm.dump_some_variables(hello="world", goodbye="heart")

fig, ax = plt.subplots()

ax.plot(np.sort(np.random.rand(100)), np.sort(np.random.rand(100)), label="random")

edm.save_figure(fig)
