# What is this?

This small library is a silly but lovable set of scripts/classes that help with my currently awful data management by saving a lot of contextual stuff, print logs, etc. and assigning random names.

Usage is simple:

```
from data_manager import ExperimentDataManager

edm = ExperimentDataManager(experiment_name="experiment")

json_object={"data":1}

edm.save_dict(json_object)

```
