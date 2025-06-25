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

""" Preparate the data from a rosbag file, compute the results, save them and plot them."""

__authors__ = 'Carmen De Rojas Pita-Romero'
__copyright__ = 'Copyright (c) 2025 Universidad Politécnica de Madrid'
__license__ = 'BSD-3-Clause'

from pathlib import Path
import plot_utils as pl
import csv_utils as csvr
import compute_results as cr
import yaml
import os


# from bag_reader import read_rosbag, deserialize_msgs
from bag_reader import LogData
import argparse


class ProcessRosbag:
    def __init__(self, log_file: str):
        self.compute_results = cr.ResultsComputer()
        self.csv_results = csvr.CSVResults()
        if Path(log_file).is_dir():
            log_files = list(Path(log_file).iterdir())
            for child in Path(log_file).iterdir():
                if child.is_file() and child.suffix == ".db3":
                    log_files = [Path(log_file)]
                    break
        elif Path(log_file).is_file():
            print('else')
            raise NotADirectoryError(f"{log_file} is not a directory")

        for log in log_files:
            self.data = LogData.from_rosbag(log)

    def run_preprocesing(self):

        # Get the data from the log
        imu = self.compute_results.get_data(self.data.imu)
        thrust = self.compute_results.get_data(self.data.thrust)
        battery = self.compute_results.get_data(self.data.battery)
        status_info = self.compute_results.get_data(self.data.platform_info)
        throttle = self.compute_results.get_data(self.data.rc_command)
        position = self.compute_results.get_data(self.data.position)

        # Synchronize the data to the same time limits and fz: 1 Hz
        status_info_time = self.compute_results.interval_flying(status_info)
        position_time = self.compute_results.adjust_time_limits(status_info_time, position)
        throttle_commanded_time = self.compute_results.adjust_time_limits(
            status_info_time, throttle)
        imu_time = self.compute_results.adjust_time_limits(status_info_time, imu)
        battery_time = self.compute_results.adjust_time_limits(status_info_time, battery)
        thrust_commanded_time = self.compute_results.adjust_time_limits(status_info_time, thrust)
        self.position_sampled = self.compute_results.fz_sample(position_time, 1.0)
        self.imu_sampled = self.compute_results.fz_sample(imu_time, 1.0)
        self.thrust_commanded = self.compute_results.fz_sample(thrust_commanded_time, 1.0)
        self.battery_sampled = self.compute_results.fz_sample(battery_time, 1.0)
        self.throttle_commanded = self.compute_results.fz_sample(throttle_commanded_time, 1.0)

        # Compute thrust measured and correction factor. CHANGE DRONE'S MASS
        # thrust_measured = compute_results.run_param_reference(imu_sampled, 0.96)
        self.thrust_measured = self.compute_results.run_thrust_reference(self.imu_sampled, 0.972)

    def save_results(self, filename: str, folder_name: str):
        """
        Save the results to csv files
        """

        time, thrust_commanded = zip(*self.thrust_commanded)
        time, thrust_measured = zip(*self.thrust_measured)
        time, throttle = zip(*self.throttle_commanded)
        time, battery = zip(*self.battery_sampled)
        time, a_z = zip(*self.imu_sampled)
        time, position = zip(*self.position_sampled)
        m = [0.96] * len(battery)
        self.csv_results.save_data([thrust_commanded, thrust_measured, battery, a_z, m, throttle, position, time], [
            'Thrust sended (N)', 'Thrust measured (N)', 'Voltage (V)', 'Acc (m/s²)', 'm (Kg)', 'Throttle (%)', 'Position_z (m)', 'Time (s)'], f"{filename}.csv", f"data/{folder_name}/")

    def run_file_computing(self):
        """ 
        Run the computing of the data of one flight
        """
        # Compute correction factor γ(B)
        self.correction_factor = self.compute_results.run_correction_factor(
            self.thrust_commanded, self.thrust_measured, self.battery_sampled)
        # Estimated the parameters
        self.parameters = self.compute_results.get_parameters(self.correction_factor, 2)

        # Throttle if the input to the trustmap is the thrust measured with γ(B)
        self.throttle_with_cf = self.compute_results.compute_throttle(
            self.thrust_measured, self.battery_sampled, self.parameters, True, 1)

        # Throttle if the input to the trustmap is the thrust measured without γ(B)
        self.throttle_without_cf = self.compute_results.compute_throttle(
            self.thrust_measured, self.battery_sampled, self.parameters, False, 1)

        # Thrust commanded with correction factor γ(B) (to see errors, only for rosbags record without correction factor)
        self.thrust_commanded_with_cf = self.compute_results.compute_thrust(
            self.thrust_commanded, self.battery_sampled, self.parameters, False)

        # Thrust measured with correction factor γ(B)
        thrust_measured_with_cf = self.compute_results.compute_thrust(
            self.thrust_measured, self.battery_sampled, self.parameters, True)

        # Errors in thrust
        # For flight without correction factor γ(B). To evaluate if the thrust will outperform the thrust stand
        self.thrust_error_without_cf_record = self.compute_results.compute_error(
            self.thrust_measured, self.thrust_commanded_with_cf)

        # For evaluate the difference between thrust measured and thrust commanded in the flight
        self.thrust_error = self.compute_results.compute_error(
            self.thrust_measured, self.thrust_commanded)

        # Erros in throttle
        # Error between throttle record and throttle without correction factor γ(B)

        self.throttle_error_without_cf = self.compute_results.compute_error(
            self.throttle_commanded, self.compute_results.adjust_time_limits(
                self.throttle_commanded, self.throttle_without_cf))
        # Error between throttle record and throttle with correction factor γ(B)
        self.throttle_error_with_cf = self.compute_results.compute_error(
            self.throttle_commanded, self.compute_results.adjust_time_limits(
                self.throttle_commanded, self.throttle_with_cf))

    def plot_results(self):
        plot = pl.Plotter()
        plot.plot_fitted_curve(self.correction_factor,
                               self.compute_results.func_2nd_order, self.parameters)
        # Put the data vs battery for plotting
        battery_thrust_commanded = self.compute_results.data1_vs_data2(
            self.thrust_commanded, self.battery_sampled)
        battery_thrust_measured = self.compute_results.data1_vs_data2(
            self.thrust_measured, self.battery_sampled)
        battery_throttle_error_without_cf = self.compute_results.data1_vs_data2(
            self.throttle_error_without_cf, self.battery_sampled)
        battery_throttle_error_with_cf = self.compute_results.data1_vs_data2(
            self.throttle_error_with_cf, self.battery_sampled)
        battery_throttle_with_cf = self.compute_results.data1_vs_data2(
            self.throttle_with_cf, self.battery_sampled)
        battery_throttle_without_cf = self.compute_results.data1_vs_data2(
            self.throttle_without_cf, self.battery_sampled)
        battery_throttle = self.compute_results.data1_vs_data2(
            self.throttle_commanded, self.battery_sampled)

        # Thrust_meassured VS Thrust_commanded
        plot.plot([battery_thrust_commanded, battery_thrust_measured],
                  ['Thrust commanded (N)', 'Thrust measured (N)'],
                  'Thrust commanded vs Thrust measured',
                  'Battery (V)', 'Thrust (N)')
        plot.plot([battery_throttle_error_with_cf, battery_throttle_error_without_cf],
                  ['Throttle error with γ(B)', 'Throttle error without γ(B)'],
                  'Throttle error vs Battery',
                  'Battery (V)', 'Throttle error (%)')
        plot.plot([battery_throttle_with_cf, battery_throttle_without_cf, battery_throttle],
                  ['Throttle with γ(B)', 'Throttle without γ(B)', 'Throttle commanded'],
                  'Throttle vs Battery',
                  'Battery (V)', 'Throttle (%)')

        plot.show()


def main(namespace: str, filename: str, log_file: str, folder_name: str):
    ros = ProcessRosbag(namespace, log_file)
    ros.run_preprocesing()
    # ros.run_file_computing()
    ros.save_results(filename, folder_name)
    # ros.plot_results()


if __name__ == "__main__":
    # Example usage

    parser = argparse.ArgumentParser()
    parser.add_argument('--config',
                        type=str,
                        default='config/config_default.yaml',
                        help="Config file path")
    args = parser.parse_args()
    filename_config = args.config
    # Leer y cargar archivo YAML
    if not os.path.exists(filename_config):
        raise FileNotFoundError(f"Config file does not exist: {filename_config}")

    with open(filename_config, 'r') as file:
        config = yaml.safe_load(file)
    rosbags = config.get("rosbags", {})
    folder_name = config.get("folder")
    for filename, path in rosbags.items():
        main(filename, path, folder_name)
