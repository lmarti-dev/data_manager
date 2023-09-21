from data_manager import ExperimentDataManager
from json_extender import ExtendedJSONEncoder, ExtendedJSONDecoder

import json
import os
import numpy as np
import cirq
import openfermion as of
import matplotlib.pyplot as plt
import io

edm = ExperimentDataManager(
    data_folder="test_data_folder", notes="this is the test experiment"
)

vals = [3, 346, 1.435784]

edm.dump_some_variables(vals=vals)

numeric_data = np.random.rand(30, 30) + 1j * np.random.rand(30, 30)
word_data = ["word", "chocolate", "bike"]

cirq_qubits = cirq.LineQubit.range(10)
cirq_data = sum(cirq.X(q) for q in cirq_qubits)

of_data = of.FermionOperator("3^ 1^ 2 3 ") + of.FermionOperator("2^ 4^ 2 3 ")

mixed_list = [
    np.array([1, 2, 4]),
    1 + 3j,
    "hello",
]

edm.save_dict_to_experiment(
    jobj={
        "numeric_data": numeric_data,
        "word_data": word_data,
        "cirq_qubits": cirq_qubits,
        "of_data": of_data,
        "mixed_list": mixed_list,
    }
)

fig, ax = plt.subplots()

ax.plot(numeric_data.real, numeric_data.imag, "x")
ax.set_xlabel("real")
ax.set_ylabel("imag")

edm.save_figure(fig=fig)

dirname = edm.experiment_dirname
files = os.listdir(dirname)

filename = files[-1]

s = io.open(os.path.join(dirname, filename), "r", encoding="utf8").read()

dct = json.loads(s=s, cls=ExtendedJSONDecoder)

print(dct)
