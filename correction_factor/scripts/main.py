
from pathlib import Path
import plot_utils as pl
import csv_utils as csvr
import bag_preparation as bp
import compute_results as cr
import get_results_from_csv as results
import yaml
import os
from bag_reader import LogData
import argparse


def process(filename: str, log_file: str, folder_name: str, mass: float):
    ros = bp.ProcessRosbag(log_file)
    ros.run_preprocesing(mass)
    ros.save_results(filename, folder_name)


def get_results(filename: str, tm_paramerters, cf_parameters, t_max, mass, ref_value, read_only_csv):
    csv = csvr.CSVResults()
    plot = pl.Plotter()
    print(f"[INFO] Reading results from {filename} using the mass {mass} kg")
    if not read_only_csv:
        csv.unify_csvs(f"data/{filename}", "data/results", f"{filename}.csv")
    compute_results = results.GetResultsFromCSV(
        f"data/results/{filename}", tm_paramerters, cf_parameters, t_max, mass)
    if t_max:
        compute_results.linear_aproximation()
        plot.plot_thrust(csv.files_in_folder(f"data/{filename}"))
        print("Linear aproximation")
    elif cf_parameters:
        compute_results.thrustmap_with_correction_factor()
        plot.plot_thrust(csv.files_in_folder(f"data/{filename}"))
        print("Thrust map for experiments with correction factor")
    else:
        compute_results.thrustmap_without_correction_factor()
        print("Thrust map for experiments without correction factor")
        compute_results.computed_thrust_expected(csv.files_in_folder(f"data/{filename}"))
    compute_results.compute_error(f'{filename}')
    # Plot the real z position vs the reference value
    plot.plot_position_z(csv.files_in_folder(f"data/{filename}"), ref_value)
    # Plot the battery voltage vs time for each experiment
    plot.plot_bat_vs_time(csv.files_in_folder(f"data/{filename}"))
    plot.show()


if __name__ == "__main__":
    csv = csvr.CSVResults()

    parser = argparse.ArgumentParser()
    parser.add_argument('--config',
                        type=str,
                        default='correction_factor/config/config_default.yaml',
                        help="Config file path")
    args = parser.parse_args()
    filename_config = args.config

    if not os.path.exists(filename_config):
        raise FileNotFoundError(f"Config file does not exist: {filename_config}")

    with open(filename_config, 'r') as file:
        config = yaml.safe_load(file)
    rosbags = config.get("rosbags", {})
    folder_experiment = config.get("folder_experiment")
    t_max = config.get("t_max")
    cf_params = config.get("cf_parameters", {})
    mass = config.get("mass")
    read_only_csv = config.get("read_only_csv")
    ref_value = config.get("z_ref")
    if not cf_params:
        cf_params_list = None
    else:
        cf_params_list = [cf_params['a2'], cf_params['a1'], cf_params['a0']]
    tm_params = config.get("tm_parameters", {})
    tm_params_list = [tm_params['a'], tm_params['b'], tm_params['c'],
                      tm_params['d'], tm_params['e'], tm_params['f']]
    if not read_only_csv:
        for filename, path in rosbags.items():
            if not os.path.exists(path):
                print(f"Rosbag file does not exist: {path}")
                exit()
            process(filename, path, folder_experiment, mass)
            print(f"Processed {filename} from {path}")
    get_results(folder_experiment, tm_params_list, cf_params_list,
                t_max, mass, ref_value, read_only_csv)
