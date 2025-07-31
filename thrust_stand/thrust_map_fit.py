import pandas as pd
import matplotlib.pyplot as plt
from thrust_map_utils import *
from thrust_map_plot import setup_figure_3D, scatter_plot, surface_plot
from thrust_map_error import compute_error
from scipy.optimize import curve_fit


def fit_curve(data: pd.DataFrame, deg):
    # Fit the curve to the data
    xdata = [data['Thrust (N)'], data['Voltage (V)']]
    ydata = data['ESC signal (µs)']
    print('Fitting curve')
    func = get_polynomial(deg)
    popt, pcov = curve_fit(func, xdata, ydata)
    print('Fitted curve')
    return popt, func


def store_coefficients(popt, output_file='coefficients.txt'):
    # if output_filename is not None:
    #     output_file =
    # else:
    #     output_file = f'results/{output_filename}'
    # Store the coefficients in a file
    order_str = 'The polynomial fitted is '
    if len(popt) == 3:
        order_str += '1st'
    elif len(popt) == 6:
        order_str += '2nd'
    elif len(popt) == 10:
        order_str += '3rd'
    elif len(popt) == 15:
        order_str += '4th'

    order_str += ' order.\n'

    with open(f'results/{output_file}', 'w') as f:
        f.write(order_str)
        f.write('Coefficients: \n')
        for i in range(len(popt)):
            f.write(f'{chr(97+i)}: {popt[i]}\n')


if __name__ == '__main__':
    args = parse_args()

    config = read_config(args.config)

    if args.files:
        data = data_assemble(args.files, config['combined_data_file'])
    elif args.directory:
        data = data_assemble(args.directory, config['combined_data_file'])

    data = filter_data(data, config['data_filter'])

    popt, func = fit_curve(data, config['poly_deg'])

    store_coefficients(popt, config['coefficients_file'])

    if config['compute_error']:
        compute_error(data, popt)

    if config['plot_results']:
        fig, ax = setup_figure_3D()
        surface_plot(data, fig, ax, func, popt, config['plotting']['color'])
        scatter_plot(data, fig, ax, config['plotting']['color'])

        plt.show()
