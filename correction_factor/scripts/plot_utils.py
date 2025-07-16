#!/usr/bin/env python3

# Copyright 2025 Universidad Politécnica de Madrid
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the Universidad Politécnica de Madrid nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

""" Plotting utility for results. """

__authors__ = 'Carmen De Rojas Pita-Romero'
__copyright__ = 'Copyright (c) 2025 Universidad Politécnica de Madrid'
__license__ = 'BSD-3-Clause'

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import csv_utils as csv
from pathlib import Path


class Plotter:
    def __init__(self):
        self.csv_results = csv.CSVResults()

    def synchronize_time(self, data):
        data = np.array(data, dtype=float)
        time = data - data[0]
        return time

    def plot(self, data_list, label_list, title, xlabel, ylabel, xlim=None, ylim=None):
        """Plot data"""
        fig, ax = plt.subplots()
        for data, label in zip(data_list, label_list):
            ts, xs = zip(*data)
            ax.plot(ts, xs, marker='.', linestyle='', label=label)
        ax.set_yscale('linear')
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        # ax.invert_xaxis()
        ax.grid()
        ax.legend()
        fig.savefig(f"/tmp/{title}.png")
        return fig

    def plot_line_only(self, m, b, x_min, x_max, title):
        x = np.linspace(x_min, x_max, 100)
        y = m * x + b
        fig, ax = plt.subplots()

        ax.plot(x, y, 'r-', label=f"$y = {m:.4f}x + {b:.2f}$")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Value")
        ax.set_title(title)
        ax.grid(True)
        ax.legend()
        fig.savefig(f"/tmp/{title}.png")
        return fig

    def plot_fitted_curve(self, data: pd.DataFrame, func, popt):
        """
        Plot results of a fit function against experimental data.

        :param data: DataFrame containing 'voltage' and 'value' columns.
        :param func: Function to fit the data.
        :param popt: Optimal parameters from the fit.
        """
        battery, value = zip(*data)
        plt.scatter(battery, value, label='Experimental data', s=10)
        x_fit = np.linspace(min(battery), max(battery), 300)
        y_fit = func(x_fit, *popt)
        if len(popt) == 2:
            plt.plot(x_fit, y_fit,
                     label=f'$\gamma$ (B) = {popt[1]:.4f}B + {popt[0]:.4f}', color='orange')
            plt.title('Correction Factor Fitted to a First-Degree Polynomial Curve')
        elif len(popt) == 3:
            plt.plot(
                x_fit, y_fit, label=f'$\gamma$ (B) = {popt[2]:.4f}B^2 + {popt[1]:.4f}B + {popt[0]:.4f}', color='orange')
            plt.title('Correction Factor Fitted to a Second-Degree Polynomial Curve')
        elif len(popt) == 4:
            plt.plot(
                x_fit, y_fit, label=f'$\gamma$ (B) = {popt[3]:.4f}B^3 + {popt[2]:.4f}B^2 + {popt[1]:.4f}B + {popt[0]:.4f}',
                color='orange')
            plt.title('Correction Factor Fitted to a Third-Degree Polynomial Curve')
        plt.xlabel('Battery (V)')
        plt.ylabel('$\gamma$ ')
        plt.gca().invert_xaxis()
        plt.legend()
        plt.grid(True)

    def plot_errors(self, file_paths: list):

        data = []
        errors_V = []
        errors_T = []
        errors_V_thrust = []
        legends = []
        for file_path in file_paths:
            d = self.csv_results.read_csv(file_path)
            data.append(d)
            errors_V.append(self.csv_results.get_vector_from_csv(d["V (V)"], d["ET_V (%)"]))
            errors_T.append(self.csv_results.get_vector_from_csv(d["T (N)"], d["ET_T (%)"]))
            errors_V_thrust.append(self.csv_results.get_vector_from_csv(
                d["V (V)"], d["E_Thrust (%)"]))
            legends.append(Path(file_path).stem)
        self.plot(errors_V, legends, 'Errors (% )', 'Battery (V)', 'Throttle error (%)')
        self.plot(errors_T, legends, 'Errors (% )', 'Thrust (N)', 'Throttle error (%)')
        self.plot(errors_V_thrust, legends, 'Errors (% )', 'Battery (V)', 'Thrust error (%)')

    def plot_position_z(self, file_paths: list, ref_value: float = 3.0):

        time_synced = []
        z_data = []

        for file_path in file_paths:
            data = self.csv_results.read_csv(file_path)
            time = self.synchronize_time(data["Time (s)"])
            z = self.csv_results.get_vector_from_csv(time, data["Position_z (m)"])
            time_synced.append(time)
            z_data.append(z)

        if time_synced:
            ref = [ref_value] * len(time_synced[0])
            ref_vec = self.csv_results.get_vector_from_csv(time_synced[0], ref)
            z_data.append(ref_vec)
            labels = [f"Curve {i+1}" for i in range(len(z_data) - 1)] + ["Reference"]
        self.plot(z_data, labels, 'Hover stability', 'Time (s)', 'z (m)', (0, 200))

    def plot_bat_vs_time(self, file_paths: list, labels: list = None):
        voltage_data = []
        data_time = self.csv_results.read_csv(file_paths[0])
        time = self.synchronize_time(data_time["Time (s)"])
        for file_path in file_paths:
            data = self.csv_results.read_csv(file_path)
            voltage = self.csv_results.get_vector_from_csv(time, data["Voltage (V)"])
            voltage_data.append(voltage)
        labels = [f"Curve {i+1}" for i in range(len(voltage_data))]

        self.plot(voltage_data, labels, 'Battery vs Time', 'Time (s)', 'Battery (V)')

    def show(self):
        """Show all plots"""
        plt.show()
