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

__authors__ = 'Carmen De Rojas Pita-Romero'
__copyright__ = 'Copyright (c) 2025 Universidad Politécnica de Madrid'
__license__ = 'BSD-3-Clause'

import numpy as np
import pandas as pd
from std_msgs.msg import Header, UInt16MultiArray
from typing import Any
from sensor_msgs.msg import Imu, BatteryState
from as2_msgs.msg import Thrust, PlatformInfo, UInt16MultiArrayStamped
from geometry_msgs.msg import PoseStamped
from disturbance_estimation import DisturbanceEstimation
from scipy.optimize import curve_fit


def timestamp_to_float(header: Header) -> float:
    """
    Parse timestamp from header and convert float
    """
    return header.stamp.sec + header.stamp.nanosec * 1e-9


def time_to_index(time: float, msgs_stamped: list[Any]) -> int:
    """
    Get index from time
    """
    for i, msg in enumerate(msgs_stamped):
        if msg[0] >= time:
            return i
    return -1


class ResultsComputer:
    def __init__(self):
        pass

    def get_data(self, data):
        """
        Get data from the input

        :param data: Input data
        :return: Data
        """
        if isinstance(data, list) and all(isinstance(item, Thrust) for item in data):
            return self.get_thrust_data(data)
        elif isinstance(data, list) and all(isinstance(item, BatteryState) for item in data):
            return self.get_battery_data(data)
        elif isinstance(data, list) and all(isinstance(item, Imu) for item in data):
            return self.get_imu_data(data)
        elif isinstance(data, list) and all(isinstance(item, PlatformInfo) for item in data):
            return self.get_platform_info(data)
        elif isinstance(data, list) and all(isinstance(item, UInt16MultiArrayStamped) for item in data):
            return self.get_throttle_data(data)
        elif isinstance(data, list) and all(isinstance(item, PoseStamped) for item in data):
            return self.get_position_data(data)
        else:
            raise TypeError("Unsupported data type for resampling.")

    def get_imu_data(self, data: list[Imu]):
        imu_list = []
        for imu in data:
            time = timestamp_to_float(imu.header)
            acceleration_z = imu.linear_acceleration.z
            imu_list.append((time, acceleration_z))
        return imu_list

    def get_thrust_data(self, data: list[Thrust]):
        thrust_list = []
        for thrust in data:
            time = timestamp_to_float(thrust.header)
            thrust_value = thrust.thrust
            thrust_list.append((time, thrust_value))
        return thrust_list

    def get_battery_data(self, data: list[BatteryState]):
        battery_list = []
        for battery in data:
            time = timestamp_to_float(battery.header)
            voltage = battery.voltage
            battery_list.append((time, voltage))
        return battery_list

    def get_platform_info(self, data: list[PlatformInfo]):
        control_status_list = []
        for info in data:
            time = timestamp_to_float(info.header)
            status = info.status.state
            control_status_list.append((time, status))
        return control_status_list

    def get_throttle_data(self, data: list[UInt16MultiArrayStamped]):  # new
        throttle_list = []
        for throttle in data:
            time = throttle.stamp.sec
            values = throttle.data[2]
            throttle_list.append((time, values))
        return throttle_list

    def get_position_data(self, data: list[PoseStamped]):
        position_list = []
        for position in data:
            time = timestamp_to_float(position.header)
            position = position.pose.position.z
            position_list.append((time, position))
        return position_list

    def get_rc_command_data(self, data: list[UInt16MultiArray], data_time):
        throttle_list = []
        for (throttle), (time, _) in zip(data, data_time):
            values = throttle.data[2]
            throttle_list.append((time, values))
        return throttle_list

    def interval_flying(self, data):
        """
        Filter time intervals where the platform is flying.

        :param data: List of (time, status)
        :return: List of (time, status) where the platform is flying
        """
        flying_data = []
        for (t, value) in data:
            if value == 3:
                flying_data.append((t, value))
        return flying_data

    def adjust_time_limits(self, limiting_data, data):
        t_0 = time_to_index(limiting_data[0][0], data)
        t_f = time_to_index(limiting_data[-1][0], data)

        return data[t_0:t_f]

    def synchronize_two_data(self, data1, data2):
        """
        Sample data1 based on time intervals defined by data2 in order to synchronize them.
        Use this when there are more data points in data1 than in data2 within the same interval.

        :param data1: List of (time,value)
        :param data2: List of (time,value)
        :return: data1 resample
        """
        sample_data = []
        data1_iter = iter(data1)
        current = next(data1_iter, None)

        for (t_start, _), (t_end, _) in zip(data2, data2[1:]):
            window_values = []

            while current is not None:
                t_data1, value = current

                if t_data1 < t_start:
                    current = next(data1_iter, None)
                elif t_start <= t_data1 < t_end:
                    window_values.append(value)
                    current = next(data1_iter, None)
                else:
                    break

            if window_values:
                mean_val = np.mean(window_values)
                sample_data.append((t_start, mean_val))

        return sample_data

    def fz_sample(self, data, freq_hz):
        """
         Sample to a uniform frequency.

         :param data:  List of (time,value)
         :param freq_hz: Desired frequency in Hz
         :return: sample data
         """
        times, values = zip(*data)
        df = pd.DataFrame({'value': values}, index=pd.to_datetime(times, unit='s'))
        period_ms = int(1000 / freq_hz)
        df_resampled = df.resample(f'{period_ms}ms').mean().interpolate()
        new_times = df_resampled.index.astype('int64') / 1e9
        new_values = df_resampled['value'].tolist()
        sample_data = list(zip(new_times, new_values))
        return sample_data

    def resize_data(self, long_data, short_data):
        """
        Resize data when you have less data in one of the lists to match the longer one.

        :param long_data: List of (time,value)
        :param short_data: List of (time,value)
        :return: short_data sample
        """

        if len(long_data) > len(short_data):
            base = long_data
            source = short_data
        else:
            base = short_data
            source = long_data

        sample_data = []
        idx = 0
        last_value = source[0][1]

        for t_base, _ in base:
            while idx < len(source) and source[idx][0] <= t_base:
                last_value = source[idx][1]
                idx += 1
            sample_data.append((t_base, last_value))

        return sample_data

    def func_1st_order(self, x, a1, a2):
        """ 
        Curve fit a fuction with 1st degree polynomial

        """
        return a1 + a2 * x

    def func_2nd_order(self, x, a1, a2, a3):
        """ 
        Curve fit function with 2nd degree polynomial

        """
        return a1 + a2 * x + a3 * x**2

    def func_3rd_order(self, x, a1, a2, a3, a4):
        """ 
        Curve fit function with 3rd degree polynomial

        """
        return a1 + a2 * x + a3 * x**2 + a4 * x**3

    def fit_curve(self, data, func):
        """
        Fit a curve to the data using the specified function.

        :param data: List of (x, y) data points
        :param func: Function to fit the data
        :return: Fitted parameters
        """
        xdata, ydata = zip(*data)
        popt, pcov = curve_fit(func, xdata, ydata)
        return popt

    def get_parameters(self, data, grade):
        if grade == 1:
            return self.fit_curve(data, self.func_1st_order)
        elif grade == 2:
            return self.fit_curve(data, self.func_2nd_order)
        elif grade == 3:
            return self.fit_curve(data, self.func_3rd_order)

    def run_correction_factor(self, send_thrust, measured_thrust, battery, mass) -> list[tuple[float, float]]:
        """
        Run correction factor for thrust map vs time

        :param send_thrust: Thrust from the actuator
        :param measured_thrust: Measured thrust
        :return: List(time, correction_factor)
        """

        DE = DisturbanceEstimation(mass)
        correction_factor_list = []
        for (t_send, value_send), (_, value_measured), (_, voltage) in zip(send_thrust, measured_thrust, battery):

            factor = DE.compute_correction_factor_thrust(
                value_send, value_measured)
            correction_factor_list.append((voltage, factor))

        return correction_factor_list

    def run_thrust_reference(self, param1, real_mass):
        """
        Compute the thrust reference based on the real mass and the IMU (a_z) 

        :param param1: acelerration_z from IMU (time, value)
        :param real_mass: Dependent parameter
        :return: List[(time, thrust_value)]
        """
        DE = DisturbanceEstimation(real_mass)

        thrust_measure = []
        for value in param1:
            if np.isnan(value[1]):
                pass
            else:
                value_measure = DE.compute_thrust(real_mass, value[1])
                thrust_measure.append((value[0], value_measure))
        return thrust_measure

    def data1_vs_data2(self, data1: list[(float, float)], data2: list[(float, float)]) -> list[(float, float)]:
        """
        Short the data to voltage
        :param data1: List(time, value1)
        :param data2:  List(time, value2)
        :return: List(value2,value1)
        """
        dataVSvoltage = []
        for (_, value1), (_, value2) in zip(data1, data2):
            dataVSvoltage.append((value2, value1))
        return dataVSvoltage

    def compute_thrust(self, thrust, battery, parameters, flag):
        """
        Correct the thrust input to the thrust map using a polynomial correction factor

        :param thrust: List(time, value). This should a lineal thrust
        :param battery: List(time, value)
        :param parameters: Parameters of the polynomial correction factor
        :param flag: False is to correct the thrust commanded and look if they is similar to the thrust measured.
        :return: Thrust input: List(time, value)
        """
        thrust_input = []
        for (t, thrust_value), (_, voltage) in zip(thrust, battery):
            if len(parameters) == 2:
                y = self.func_1st_order(voltage, *parameters)
            elif len(parameters) == 3:
                y = self.func_2nd_order(voltage, *parameters)
            elif len(parameters) == 4:
                y = self.func_3rd_order(voltage, *parameters)
            if flag:
                thrust_value = thrust_value * y
            else:
                thrust_value = thrust_value / y
            thrust_input.append((t, thrust_value))
        return thrust_input

    def compute_throttle(self, thrust_commanded, battery, parameters, flag_corrected, thrust_map):
        """
        Compute the throttle based on the thrust and voltage using a polynomial correction factor

        :param thrust: List(time, value). This should be the thrust commanded by the controller
        :param battery: List(time, value)
        :param parameters: Parameters of the polynomial correction factor
        :param flag_corrected: If True, the thrust input will be corrected with correction factor
        :param number_motors: Number of motors to change the current thrust map. If -1, it will use the linear aproximation.
        :return: List of throttle (time,value)
        """
        if flag_corrected:
            thrust_input = self.compute_thrust(
                thrust_commanded, battery, parameters, flag_corrected)
        else:
            thrust_input = thrust_commanded
        if thrust_map == None:
            throttle_list = []
            thrust_max = 44
            for (t, thrust_value), (_, voltage_value) in zip(thrust_input, battery):
                value = (thrust_value / thrust_max) * 1000 + 1000  # throttle (1000-2000)
                throttle_list.append((t, value))
                if np.isnan(value):
                    print(f"NaN value at: Thrust {thrust_value}, Voltage {voltage_value}")
            return throttle_list
        else:
            tm_parameters = thrust_map
            throttle_list = []
            for (t, thrust_value), (_, voltage_value) in zip(thrust_input, battery):
                thrust_input = thrust_value / 4
                value = tm_parameters[0] + tm_parameters[1] * thrust_input + tm_parameters[2] * voltage_value + tm_parameters[3] * thrust_input * thrust_input + \
                    tm_parameters[4] * thrust_input * voltage_value + \
                    tm_parameters[5] * voltage_value * voltage_value
                throttle_list.append((t, value))
                if np.isnan(value):
                    print(f"NaN value at: Thrust {thrust_input}, Voltage {voltage_value}")
            return throttle_list

    def compute_error(self, data1, data2):
        """
        Compute the error between two data sets

        :param data1: List of (time, value)
        :param data2: List of (time, value)
        :return: List of (time, error)
        """
        error_list = []
        mean_error = []

        for (t1, v1), (t2, v2) in zip(data1, data2):
            if t1 == t2:
                error = (np.abs(v1 - v2) / 10)
                if np.isnan(error):
                    print(v1, v2)
                error_list.append((t1, error))
                # print(error)
                mean_error.append(error)
        print(f"Error : {np.mean(mean_error)} | {np.std(mean_error)}")
        return error_list
