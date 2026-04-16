import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple
from mpl_toolkits.mplot3d.axes3d import Axes3D


def setup_figure_3D() -> Tuple[plt.Figure, Axes3D]:
    fig = plt.figure(figsize=(20, 20))
    ax = fig.add_subplot(111, projection='3d')
    return fig, ax


def scatter_plot(data: pd.DataFrame, fig: plt.Figure, ax: Axes3D, color: str, column_names: dict[str, str]):
    # ax = fig.add_subplot(111, projection='3d')
    ax.scatter(data[column_names['thrust']], data[column_names['voltage']],
               data[column_names['throttle']], label='Data from multirotor experiments', color=color)

    ax.set_xlabel(column_names['thrust'], fontsize=18, labelpad=16)
    ax.set_ylabel(column_names['voltage'], fontsize=18, labelpad=16)
    ax.set_zlabel(column_names['throttle'], fontsize=18, labelpad=19)

    ax.set_xlim(min(data[column_names['thrust']]), max(data[column_names['thrust']]))
    ax.set_ylim(min(data[column_names['voltage']]), max(data[column_names['voltage']]))
    ax.set_zlim(min(data[column_names['throttle']]), max(data[column_names['throttle']]))


def surface_plot(data: pd.DataFrame, fig, ax, func, popt, color, column_names: dict[str, str]):
    x = np.linspace(min(data[column_names['thrust']]), max(data[column_names['thrust']]), 100)
    y = np.linspace(min(data[column_names['voltage']]), max(data[column_names['voltage']]), 100)
    x, y = np.meshgrid(x, y)
    z = func((x, y), *popt)
    ax.plot_surface(x, y, z, alpha=0.5, color=color)
