from data_manager import ExperimentDataManager
from json_extender import ExtendedJSONDecoder

import json
import os
import numpy as np
import cirq
import openfermion as of
import matplotlib.pyplot as plt
import io

# declare manager class
edm = ExperimentDataManager(
    data_folder=os.path.dirname(__file__) + "/test_data_folder",
    notes="this is the test experiment",
)

# dump some variables quickly
vals = [3, 346, 1.435784]

edm.dump_some_variables(vals=vals)

# create important data
numeric_data = np.random.rand(4, 4) + 1j * np.random.rand(4, 4)
word_data = ["word", "chocolate", "bike"]

cirq_qubits = cirq.LineQubit.range(10)
cirq_data = sum(cirq.X(q) for q in cirq_qubits)

of_data = of.FermionOperator("3^ 1^ 2 3 ") + of.FermionOperator("2^ 4^ 2 3 ")

mixed_list = [
    np.array([1 + 3j, 0 + 0j, 2929 + 5858j]),
    1 + 3j,
    "hello",
]

# save the data
edm.save_dict_to_experiment(
    jobj={
        "numeric_data": numeric_data,
        "word_data": word_data,
        "cirq_qubits": cirq_qubits,
        "of_data": of_data,
        "mixed_list": mixed_list,
    }
)


# save a plot
fig, ax = plt.subplots(nrows=2)

ax[0].plot(numeric_data.real**0.1, numeric_data.imag**0.1, "x")
ax[1].plot(numeric_data.real**2, numeric_data.imag**2, "o")
ax[0].set_xlabel("real")
ax[1].set_ylabel("imag")

edm.save_figure(fig=fig)


# load everything back again
# data folder == general folder where all data is
dirname = edm.current_data_dir
files = os.listdir(
    dirname,
)

filename = files[-1]

s = io.open(os.path.join(dirname, filename), "r", encoding="utf8").read()

dct = json.loads(s=s, cls=ExtendedJSONDecoder)

print(dct)

plt.show()
