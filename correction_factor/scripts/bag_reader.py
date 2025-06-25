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

from typing import Any
from rclpy.serialization import deserialize_message
from rosbag2_py import SequentialReader, StorageOptions, ConverterOptions
from tf2_msgs.msg import TFMessage
from tf2_ros.buffer import Buffer
from as2_msgs.msg import Thrust, PlatformInfo, UInt16MultiArrayStamped
from sensor_msgs.msg import Imu, BatteryState
from geometry_msgs.msg import Vector3Stamped, PoseStamped
from dataclasses import dataclass, field
from pathlib import Path


def read_rosbag(filename: str) -> dict[str, list[Any]]:
    """Read a rosbag"""
    bag_reader = SequentialReader()
    storage_options = StorageOptions(uri=filename, storage_id="sqlite3")
    converter_options = ConverterOptions(
        input_serialization_format="", output_serialization_format="")
    bag_reader.open(storage_options, converter_options)

    topics_dict = {}
    while bag_reader.has_next():
        topic, msg, _ = bag_reader.read_next()
        if topic not in topics_dict:
            topics_dict[topic] = []
        topics_dict[topic].append(msg)
    return topics_dict


def deserialize_tfs(tfs: list[TFMessage], buffer: Buffer) -> Buffer:
    """Deserialize TF messages"""
    for tf in tfs:
        tf_message: TFMessage = deserialize_message(tf, TFMessage)
        for transform in tf_message.transforms:
            buffer.set_transform(transform, 'default_authority')
    return buffer


def deserialize_msgs(msgs: list[Any], msg_type: Any) -> list[Any]:
    """Deserialize messages"""
    deserialized_msgs = []
    for msg in msgs:
        deserialized_msgs.append(deserialize_message(msg, msg_type))
    return deserialized_msgs


def deserialize_rosbag(rosbag: dict[str, list[Any]],
                       msg_types: dict[str, Any]) -> dict[str, list[Any]]:
    """Deserialize messages in rosbags"""
    deserialized_msgs = {}
    for topic, msgs in rosbag.items():
        try:
            deserialized_msgs[topic] = deserialize_msgs(msgs, msg_types[topic])
        except KeyError:
            deserialized_msgs[topic] = []
    return deserialized_msgs


@dataclass
class LogData:
    """Data read from rosbag file"""
    filename: Path
    thrust: list[Thrust] = field(default_factory=list)
    imu: list[Imu] = field(default_factory=list)
    battery: list[BatteryState] = field(default_factory=list)
    armed: list[bool] = field(default_factory=list)
    controller_reference: list[Vector3Stamped] = field(default_factory=list)
    controller_state: list[Vector3Stamped] = field(default_factory=list)
    platform_info: PlatformInfo = field(default_factory=PlatformInfo)
    rc_command: list[UInt16MultiArrayStamped] = field(default_factory=list)
    self_localization: list[PoseStamped] = field(default_factory=list)

    @classmethod
    def from_rosbag(cls, rosbag: Path) -> 'LogData':
        """Read the rosbag"""
        log_data = cls(rosbag)
        rosbag_msgs = read_rosbag(str(rosbag))

        for topic, msgs in rosbag_msgs.items():
            if "actuator_command/thrust" in topic:
                log_data.thrust = deserialize_msgs(msgs, Thrust)
            elif "sensor_measurements/imu" in topic:
                log_data.imu = deserialize_msgs(msgs, Imu)
            elif "sensor_measurements/battery" in topic:
                log_data.battery = deserialize_msgs(msgs, BatteryState)
            elif "debug/controller_reference" in topic:
                log_data.controller_reference = deserialize_msgs(msgs, Vector3Stamped)
            elif "debug/controller_state" in topic:
                log_data.controller_state = deserialize_msgs(msgs, Vector3Stamped)
            elif "debug/rc/command" in topic:
                log_data.rc_command = deserialize_msgs(msgs, UInt16MultiArrayStamped)
            elif "platform/info" in topic:
                log_data.platform_info = deserialize_msgs(msgs, PlatformInfo)
            elif "self_localization/pose" in topic:
                log_data.position = deserialize_msgs(msgs, PoseStamped)
        return log_data


if __name__ == "__main__":

    # info = read_rosbag("rosbags/030625-ThrustMap-Test/hover_subir_1/flight_21")
    # info = deserialize_rosbag(info, {"/drone0/platform/info": PlatformInfo,
    #                                  "/drone0/sensor_measurements/thrust": Thrust})
    # print(info.)
    pass
