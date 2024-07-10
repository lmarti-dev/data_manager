from data_manager.data_manager import ExperimentDataManager
from data_manager.utils import name_from_list
import matplotlib.pyplot as plt
import numpy as np


for project in ("testing", None, "fermionic cooling"):
    edm = ExperimentDataManager(
        experiment_name=f"browser_data_test_{project}",
        tags=[name_from_list("animals.txt") for a in range(10)],
        project=project,
    )

    edm.var_dump(xy=100, nonzero="a")
    edm.save_dict({"a": 100, "hello": "goodbye"})

    edm.save_dict([10000, 1000, 1001])

    fig, ax = plt.subplots()

    ax.plot(sorted(np.random.rand(100)), sorted(np.random.rand(100)))

    edm.save_figure(fig)
