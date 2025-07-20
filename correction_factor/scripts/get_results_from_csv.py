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

""" Get the results with all he data of one strategy"""

__authors__ = 'Carmen De Rojas Pita-Romero'
__copyright__ = 'Copyright (c) 2025 Universidad Politécnica de Madrid'
__license__ = 'BSD-3-Clause'


from compute_results import ResultsComputer
import plot_utils as pl
import csv_utils as csv
from pathlib import Path


class GetResultsFromCSV:
    def __init__(self, filename: str, tm_paramerters: list[float] = None, cf_parameters: list[float] = None, t_max: float = None, mass: float = 1.0):
        self.csv_results = csv.CSVResults()
        self.compute = ResultsComputer()
        self.plot = pl.Plotter()
        data = self.csv_results.read_csv(f'{filename}.csv')
        self.thrust_sended = data["Thrust sended (N)"]
        self.thrust_measured = data["Thrust measured (N)"]
        self.voltage = data["Voltage (V)"]
        self.acc = data["Acc (m/s²)"]
        self.m = ["m (Kg)"]

        self.voltage_throttle = self.csv_results.get_vector_from_csv(
            data["Voltage (V)"], data["Throttle (%)"])
        self.thrust_throttle = self.csv_results.get_vector_from_csv(
            data["Thrust measured (N)"], data["Throttle (%)"])
        self.throttle_thrust_commanded = self.csv_results.get_vector_from_csv(
            data["Throttle (%)"], data["Thrust sended (N)"])
        self.throttle_thrust_meassured = self.csv_results.get_vector_from_csv(
            data["Throttle (%)"], data["Thrust measured (N)"])
        self.voltage_voltage = self.csv_results.get_vector_from_csv(
            data["Voltage (V)"], data["Voltage (V)"])
        self.tm_parameters = tm_paramerters
        self.cf_parameters = cf_parameters
        self.t_max = t_max
        self.mass = mass

    def linear_aproximation(self):
        self.throttle = self.compute.compute_throttle(
            self.throttle_thrust_meassured, self.voltage_voltage, self.cf_parameters, True, None)
        self.voltage_vs_throttle = self.compute.data1_vs_data2(
            self.throttle, self.voltage_voltage)

    def thrustmap_without_correction_factor(self) -> list:
        correction_factor = self.compute.run_correction_factor(
            self.throttle_thrust_commanded, self.throttle_thrust_meassured, self.voltage_voltage, self.mass)
        self.cf_parameters = self.compute.get_parameters(correction_factor, 2)
        print(
            f'The ecuation for the correction factor is : {self.cf_parameters[2]} * x^2 + {self.cf_parameters[1]} * x + {self.cf_parameters[0]}')
        self.throttle = self.compute.compute_throttle(
            self.throttle_thrust_meassured, self.voltage_voltage, self.cf_parameters, False, self.tm_parameters)
        self.voltage_vs_throttle = self.compute.data1_vs_data2(
            self.throttle, self.voltage_voltage)
        self.plot.plot_fitted_curve(
            correction_factor, self.compute.func_2nd_order, self.cf_parameters)

    def thrustmap_with_correction_factor(self):
        print(
            f'The ecuation for the correction factor is : {self.cf_parameters[2]} * x^2 + {self.cf_parameters[1]} * x + {self.cf_parameters[0]}')
        self.throttle = self.compute.compute_throttle(
            self.throttle_thrust_meassured, self.voltage_voltage, self.cf_parameters, True, self.tm_parameters)
        self.voltage_vs_throttle = self.compute.data1_vs_data2(
            self.throttle, self.voltage_voltage)

    def compute_error(self, filename: str,):
        print('Error between thrust commanded and measured')
        self.error_thrust = self.compute.compute_error(
            self.throttle_thrust_commanded, self.throttle_thrust_meassured)
        print('Error throttle vs voltage')
        self.error_throttle_vs_voltage = self.compute.compute_error(
            self.voltage_vs_throttle, self.voltage_throttle)
        self.error_throttle_vs_thrust = self.compute.data1_vs_data2(
            self.error_throttle_vs_voltage, self.throttle_thrust_meassured)

        (V, _) = zip(*self.voltage_vs_throttle)
        (_, T) = zip(*self.throttle_thrust_meassured)
        (_, ET_V) = zip(*self.error_throttle_vs_voltage)
        (_, ET_T) = zip(*self.error_throttle_vs_thrust)
        (_, E_Thrust) = zip(*self.error_thrust)
        self.csv_results.save_data([V, ET_V, T, ET_T, E_Thrust], [
            'V (V)', 'ET_V (%)', 'T (N)', 'ET_T (%)', 'E_Thrust (%)'], f'{filename}_errors.csv', 'data/errors')

    def computed_thrust_expected(self, filenames: list, cf_parameters: list[float] = None):
        if cf_parameters is not None:
            self.cf_parameters = cf_parameters
        for file in filenames:
            data = self.csv_results.read_csv(f'{file}')
            throttle_thrust_commanded = self.csv_results.get_vector_from_csv(
                data["Throttle (%)"], data["Thrust sended (N)"])
            voltage_voltage = self.csv_results.get_vector_from_csv(
                data["Voltage (V)"], data["Voltage (V)"])
            throttle_thrust_meassured = self.csv_results.get_vector_from_csv(
                data["Throttle (%)"], data["Thrust measured (N)"])
            thrust_expected = self.compute.compute_thrust(
                throttle_thrust_commanded, voltage_voltage, self.cf_parameters, False)
            self.plot.plot([thrust_expected, throttle_thrust_meassured, throttle_thrust_commanded], [
                'Thrust expected', 'Thrust measured', 'Thrust commanded'], 'Compare Thrust from experiment of ' + Path(file).stem, 'Time (s)', 'Thrust (N)')
