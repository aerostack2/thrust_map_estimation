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

"""definition."""

__authors__ = 'Carmen De Rojas Pita-Romero'
__copyright__ = 'Copyright (c) 2025 Universidad Politécnica de Madrid'
__license__ = 'BSD-3-Clause'

import numpy as np


class DisturbanceEstimation():
    """
    Disturbance estimation class.
    """

    def __init__(self, real_mass: np.float64):
        """
        Initialize the disturbance estimation.
        """
        self.real_mass_ = real_mass
        self.aceleration_ = np.float64()  # [az]
        self.actuator_thrust_ = np.float64()
        self.measured_thrust_ = np.float64()
        self.estimate_mass_ = np.float64()
        self.correction_factor_mass_ = np.float64()
        self.correction_factor_thrust_ = np.float64()
        self.mass_error_ = np.float64()
        self.thrust_error_ = np.float64()
        self.mass_error_history = []
        self.thrust_error_history = []
        self.rmse = np.float64(0.0)

    def compute_mass(self, thrust: np.float64, aceleration: np.float64) -> np.float64:
        """
        Compute the mass based on thrust and acceleration.

        :param thrust (np.float64): The thrust input.
        :param aceleration (np.float64): The acceleration in z axis.
        :return: The computed mass.
        """
        self.actuator_thrust_ = thrust
        self.aceleration_ = aceleration
        self.estimate_mass_ = self.actuator_thrust_ / self.aceleration_
        return self.estimate_mass_

    def compute_thrust(self, mass: np.float64, aceleration: np.float64) -> np.float64:
        """
        Compute the thrust based on mass and acceleration.

        :param mass (np.float64): The mass input.
        :param aceleration (np.float64): The acceleration in z axis.
        :return: The computed thrust.
        """
        self.real_mass_ = mass
        self.aceleration_ = aceleration
        if self.aceleration_ == 0:
            raise ValueError("Acceleration cannot be zero to compute thrust.")
        else:
            self.measured_thrust_ = self.real_mass_ * self.aceleration_
            return self.measured_thrust_

    def compute_mass_error(self, real_mass: np.float64, estimate_mass: np.float64) -> np.float64:
        """
        Compute the error between the computed mass and the real mass.
        :param real_mass (np.float64): The real mass.
        :param mass_computed (np.float64): The computed mass.
        :return: The error.
        """
        self.real_mass_ = real_mass
        self.estimate_mass_ = estimate_mass
        self.mass_error_ = np.abs(self.estimate_mass_ - self.real_mass_)
        self.mass_error_history.append(self.mass_error_)
        return self.mass_error_

    def compute_thrust_error(self, imu_thrust: np.float64, estimate_thrust: np.float64) -> np.float64:
        """
        Compute the error between the computed thrust and the real thrust.
        :param
        real_thrust (np.float64): The real thrust.
        :param estimate_thrust (np.float64): The computed thrust.
        :return: The error.
        """
        self.actuator_thrust_ = imu_thrust
        self.measured_thrust_ = estimate_thrust
        self.thrust_error_ = np.abs(self.measured_thrust_ - self.real_thrust_)
        self.thrust_error_history.append(self.thrust_error_)
        return self.thrust_error_

    def compute_correction_factor_mass(self, real_mass: np.float64, estimate_mass: np.float64) -> np.float64:
        """
        Compute the correction factor 
        :param real_mass (np.float64): The real mass.
        :param mass_error (np.float64): The error in the mass.
        :return: The correction factor.
        """
        self.real_mass_ = real_mass
        self.estimate_mass_ = estimate_mass
        self.correction_factor_mass_ = self.real_mass_ / self.estimate_mass_
        return self.correction_factor_mass_

    def compute_correction_factor_thrust(self, actuator_thrust: np.float64, measured_thrust: np.float64) -> np.float64:
        """
        Compute the correction factor for thrust.
        :param imu_thrust (np.float64): The IMU thrust.
        :param estimate_thrust (np.float64): The estimated thrust.
        :return: The correction factor.
        """
        self.actuator_thrust_ = actuator_thrust
        self.measured_thrust_ = measured_thrust
        self.correction_factor_thrust_ = self.actuator_thrust_ / self.measured_thrust_  # new
        return self.correction_factor_thrust_

    def compute_RMSE(self):
        """
        Compute the Root Mean Square Error (RMSE) of the mass error.
        :return: The RMSE.
        """
        if len(self.mass_error_history) == 0:
            return np.float64(0.0)
        self.rmse = np.sqrt(np.mean(np.square(self.mass_error_history)))
        return self.rmse
