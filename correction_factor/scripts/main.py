
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


def process(filename: str, log_file: str, folder_name: str):
    ros = bp.ProcessRosbag(log_file)
    ros.run_preprocesing()
    ros.save_results(filename, folder_name)


def get_results(filename: str, tm_paramerters, cf_parameters, t_max):
    csv = csvr.CSVResults()
    csv.unify_csvs(f"data/{filename}", "data/results", f"{filename}.csv")
    compute_results = results.GetResultsFromCSV(
        f"data/results/{filename}", tm_paramerters, cf_parameters, t_max)
    if t_max:
        compute_results.linear_aproximation()
        print("Linear aproximation")
    elif cf_parameters:
        compute_results.thrustmap_with_correction_factor()
        print("Thrust map for experiments with correction factor")
    else:
        compute_results.thrustmap_without_correction_factor()
        print("Thrust map for experiments without correction factor")
    compute_results.compute_error(f'{filename}')


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
    if not cf_params:
        cf_params_list = None
    else:
        cf_params_list = [cf_params['a2'], cf_params['a1'], cf_params['a0']]
    tm_params = config.get("tm_parameters", {})
    tm_params_list = [tm_params['a'], tm_params['b'], tm_params['c'],
                      tm_params['d'], tm_params['e'], tm_params['f']]
    for filename, path in rosbags.items():
        if not os.path.exists(path):
            print(f"Rosbag file does not exist: {path}")
            exit()
        process(filename, path, folder_experiment)
        print(f"Processed {filename} from {path}")
    get_results(folder_experiment, tm_params_list, cf_params_list, t_max)
