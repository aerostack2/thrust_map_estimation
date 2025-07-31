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

from std_msgs.msg import Header
from pathlib import Path
import pandas as pd
import csv
from collections import defaultdict


def timestamp_to_float(header: Header) -> float:
    """Parse timestamp from header and convert float"""
    return header.stamp.sec + header.stamp.nanosec * 1e-9


class CSVResults:
    def __init__(self):
        pass

    def save_data_to_csv(self,
                         data_list: list[list[tuple]],
                         column_names_list: list[list[str]],
                         filenames: list[str],
                         output_dir: str
                         ):
        """
        Save data

        """
        out_path = Path(output_dir)
        out_path.mkdir(exist_ok=True)

        for series, col_names, filename in zip(data_list, column_names_list, filenames):
            file_path = out_path / filename

            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(col_names)

                for row in series:
                    writer.writerow(row)

    def save_data(self, columns: list[list], column_names: list[str], filename: str, output_dir: str):
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        file_path = out_path / filename
        rows = list(zip(*columns))

        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(column_names)
            writer.writerows(rows)

    def unify_csvs(self, input_dir: str, output_dir: str, filename: str):
        """
        Unify the CSVs of the same type of experiments into one file.
        """
        input_path = Path(input_dir)
        csv_files = list(input_path.glob("*.csv"))

        if not csv_files:
            print(f"[ERROR] No .csv files were found in '{input_dir}'")
            return

        # Crear el directorio de salida si no existe
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        # Ruta completa del archivo de salida
        output_file = out_path / filename

        # Leer y unir los CSVs
        dfs = [pd.read_csv(f) for f in csv_files]
        df_all = pd.concat(dfs, ignore_index=True)
        df_all.to_csv(output_file, index=False)

        print(f"Unify {len(csv_files)} files in {output_file}")

    def read_csv(self, filename: str):
        data = defaultdict(list)

        with open(filename, mode='r', newline='') as file:
            csv_reader = csv.DictReader(file)

            for row in csv_reader:
                for key, value in row.items():
                    if value.strip() == '':
                        continue  # Ignora celdas vacías
                    try:
                        data[key].append(float(value))
                    except ValueError:
                        print(
                            f"WARNING: Could not convert '{value}' to float in column '{key}'"
                        )
                        data[key].append(None)
        ref_key = list(data.keys())[0]
        ref_len = len(data[ref_key])

        for key in data.keys():
            if len(data[key]) != ref_len:
                print(
                    f"ERROR: The key '{key}' has a different length ({len(data[key])}) compared to '{ref_key}' ({ref_len})")

                return None

        return data

    def get_vector_from_csv(self, data1, data2) -> list[tuple[float, float]]:

        vector_list = []
        for d1, d2 in zip(data1, data2):
            vector_list.append((d1, d2))
        return vector_list
    from pathlib import Path

    def files_in_folder(self, folder_name):
        path = Path(folder_name)
        return [str(file) for file in path.iterdir() if file.is_file()]
