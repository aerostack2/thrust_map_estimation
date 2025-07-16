import os
import argparse
import glob
import pandas as pd
import yaml
from thrust_map_plot import setup_figure_3D, scatter_plot
import matplotlib.pyplot as plt


def parse_args():
    parser = argparse.ArgumentParser(description='Prepare and plot data before TM computating')
    # pass either a list of data files or directory with all data files
    data = parser.add_mutually_exclusive_group(required=True)
    data.add_argument('-f', '--files', type=str, nargs='+', help='List of paths to data files')
    data.add_argument('-d', '--directory', type=str, help='Path to directory with all data files')
    # config file with data limits to filter
    parser.add_argument('-c', '--config', type=str,
                        default='config/default_config.yaml', help='Path to data config file')
    return parser.parse_args()


def read_config(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def data_assemble(source: str | list[str], output_file: str = None) -> pd.DataFrame:
    # Read the data from csv files and dump it into a common dataframe
    # print(csv_files)
    combined_data = []
    column_names = ['ESC signal (µs)', 'Thrust (N)', 'Current (A)', 'Voltage (V)']

    if isinstance(source, str):
        print(f'Combining all .csv data from directory: {source}\n')
        # Get all CSV files in the folder
        csv_files = glob.glob(os.path.join(source, '*.csv'))
    elif isinstance(source, list):
        print(f'Reading data from input files: {source}\n')
        csv_files = source

    for file in csv_files:
        try:
            df = pd.read_csv(file, usecols=column_names)
            combined_data.append(df)
            print(f"Processed: {file}")
        except Exception as e:
            print(f"Skipping {file} due to error: {e}")

    # Combine and save
    if combined_data:
        combined_df = pd.concat(combined_data, ignore_index=True)
    else:
        print("\nNo data processed. Check your folder or column names.")
    if output_file is not None:
        combined_df.to_csv(output_file, index=False)
        print(f"\nCombined CSV saved to {output_file}")

    return combined_df


# def filter_data(data: pd.DataFrame, max_thrust: float, min_thrust: float, max_volt: float, min_volt: float, max_throttle: float, min_throttle: float) -> pd.DataFrame:
#     # Filter the data and keep only the columns that are required
#     # column_names = ['ESC signal (µs)', 'Thrust (N)', 'Current (A)', 'Voltage (V)']
#     # apply a *(-1) to the Thrust column to make it positive
#     data['Thrust (N)'] = data['Thrust (N)'] * (-1)

#     # filter data
#     data = data[data['Voltage (V)'] > min_volt]
#     data = data[data['Voltage (V)'] < max_volt]
#     data = data[data['ESC signal (µs)'] > min_throttle]
#     data = data[data['ESC signal (µs)'] < max_throttle]
#     data = data[data['Thrust (N)'] > min_thrust]
#     data = data[data['Thrust (N)'] < max_thrust]

#     # print the maximun thrust value
#     print('Max thrust value:', data['Thrust (N)'].max())
#     return data


def filter_data(data: pd.DataFrame, filters: dict[str, float]) -> pd.DataFrame:
    # Filter the data and keep only the columns that are required
    # column_names = ['ESC signal (µs)', 'Thrust (N)', 'Current (A)', 'Voltage (V)']
    # apply a *(-1) to the Thrust column to make it positive
    data['Thrust (N)'] = data['Thrust (N)'] * (-1)

    # filter data
    data = data[data['Voltage (V)'] > filters['min_volt']]
    data = data[data['Voltage (V)'] < filters['max_volt']]
    data = data[data['ESC signal (µs)'] > filters['min_throttle']]
    data = data[data['ESC signal (µs)'] < filters['max_throttle']]
    data = data[data['Thrust (N)'] > filters['min_thrust']]
    data = data[data['Thrust (N)'] < filters['max_thrust']]

    # print the maximun thrust value
    print('Max thrust value:', data['Thrust (N)'].max())
    return data


def func_1st_order(data, a1, a2, a3):
    # Surface fit function with 1st degree polynomial
    x, y = data
    return a1 + a2 * x + a3 * y


def func_2nd_order(data, a1, a2, a3, a4, a5, a6):
    # Surface fit function with 2nd degree polynomial
    x, y = data
    return a1 + a2 * x + a3 * y + a4 * x**2 + a5 * x * y + a6 * y**2


def func_2nd_order_truncated(data, a1, a2, a3, a4):
    x, y = data
    return a1 + a2 * x + a3 * y + a4 * x**2


def func_3rd_order_truncated(data, a1, a2, a3, a4, a5, a6, a7):
    x, y = data
    return a1 + a2 * x + a3 * y + a4 * x**2 + a5 * x * y + a6 * y**2 + a7 * y**3


def func_3rd_order(data, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10):
    # Surface fit function with 3rd degree polynomial
    x, y = data
    return a1 + a2 * x + a3 * y + a4 * x**2 + a5 * x * y + a6 * y**2 + a7 * x**3 + a8 * x**2 * y + a9 * x * y**2 + a10 * y**3


def func_4th_order(data, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15):
    x, y = data
    return a1 + a2 * x + a3 * y + a4 * x**2 + a5 * x * y + a6 * y**2 + a7 * x**3 + a8 * x**2 * y + a9 * x * y**2 + a10 * y**3 + a11 * x**4 + a12 * x**3 * y + a13 * x**2 * y**2 + a14 * x * y**3 + a15 * y**4


def get_polynomial(deg):
    match deg:
        case '1st':
            return func_1st_order
        case '2nd':
            return func_2nd_order
        case '3rd':
            return func_3rd_order
        case '4th':
            return func_4th_order
        case _:
            raise Exception(
                "Invalid polynomial degree. Valid degrees are '1st', '2nd', '3rd', '4th'.")


if __name__ == '__main__':
    args = parse_args()

    config = read_config(args.config)

    if args.files:
        data = data_assemble(args.files, config['output_file'])
    elif args.directory:
        data = data_assemble(args.directory, config['output_file'])

    data = filter_data(data, config['data_filter'])

    fig, ax = setup_figure_3D()
    scatter_plot(data, fig, ax, config['plotting']['color'])

    plt.show()
