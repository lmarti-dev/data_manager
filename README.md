# What is this?

This small library is a silly but lovable set of scripts/classes that help with my currently awful data management by saving a lot of contextual stuff, print logs, etc. and assigning random names.

Usage is simple:

```python
import matplotlib.pyplot as plt
from data_manager import ExperimentDataManager

# declare edm
edm = ExperimentDataManager(experiment_name="experiment")

# quick dump of variables
edm.var_dump(a=1,b="a")

# save json
json_object={"data":1}
edm.save_dict(json_object)

# save figure
fig,ax = plt.subplots()
ax.plot([1,2],[1,2])
edm.save_figure(fig)

```
