from data_manager import set_color_cycler
import matplotlib.pyplot as plt
import numpy as np


set_color_cycler()

fig, ax = plt.subplots()

for ind in range(15):
    ax.plot(np.linspace(0, 1, 100), np.sort(np.random.rand(100)))

plt.show()
