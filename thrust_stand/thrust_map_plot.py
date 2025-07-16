import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple
from mpl_toolkits.mplot3d.axes3d import Axes3D


def setup_figure_3D() -> Tuple[plt.Figure, Axes3D]:
    fig = plt.figure(figsize=(20, 20))
    ax = fig.add_subplot(111, projection='3d')
    return fig, ax


def scatter_plot(data: pd.DataFrame, fig: plt.Figure, ax: Axes3D, color: str):
    # ax = fig.add_subplot(111, projection='3d')
    ax.scatter(data['Thrust (N)'], data['Voltage (V)'],
               data['ESC signal (µs)'], label='Data from multirotor experiments', color=color)

    ax.set_xlabel('Thrust (N)', fontsize=18, labelpad=16)
    ax.set_ylabel('Voltage (V)', fontsize=18, labelpad=16)
    ax.set_zlabel('ESC signal (µs)', fontsize=18, labelpad=19)

    ax.set_xlim(min(data['Thrust (N)']), max(data['Thrust (N)']))
    ax.set_ylim(min(data['Voltage (V)']), max(data['Voltage (V)']))
    ax.set_zlim(min(data['ESC signal (µs)']), max(data['ESC signal (µs)']))


def surface_plot(data: pd.DataFrame, fig, ax, func, popt, color):
    x = np.linspace(min(data['Thrust (N)']), max(data['Thrust (N)']), 100)
    y = np.linspace(min(data['Voltage (V)']), max(data['Voltage (V)']), 100)
    x, y = np.meshgrid(x, y)
    z = func((x, y), *popt)
    ax.plot_surface(x, y, z, alpha=0.5, color=color)
