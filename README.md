# What is this?

This small library is a silly but lovable set of scripts/classes that help with my currently awful data management by saving a lot of contextual stuff, print logs, etc. and assigning random names.

## Installation

Clone this repository to a desired location, `cd` in the `data_manager` folder, then `pip install .` (or `pip install data_manager/` if you are just a level above and in a hurry)

## Setup

You need to manually setup the package before being able to use it. After the installation, call `python -m data_manager` and follow the instructions. You will be prompted to input paths for the general data folder and the browser, as well as project names to get started. This will create a `settings.ini` file, which can be modified later.

## Usage

```python
import matplotlib.pyplot as plt
from data_manager import ExperimentDataManager

# declare edm
edm = ExperimentDataManager(experiment_name="experiment",project="project name")

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

The code also generates an .html page to conveniently browse results.