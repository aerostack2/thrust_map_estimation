import pandas as pd


def thrustmap(thrust, voltage, popt):
    coeffs = [0.0] * 15
    coeffs[:len(popt)] = popt
    x, y = thrust, voltage
    return coeffs[0] + coeffs[1] * x + coeffs[2] * y + coeffs[3] * x**2 + coeffs[4] * x * y + coeffs[5] * y**2 + coeffs[6] * x**3 + coeffs[7] * x**2 * y + coeffs[8] * x * y**2 + coeffs[9] * y**3 + coeffs[10] * x**4 + coeffs[11] * x**3 * y + coeffs[12] * x**2 * y**2 + coeffs[13] * x * y**3 + coeffs[14] * y**4


def compute_error(data, popt):
    # Compute throttle using the thrustmap function
    data['computed_throttle'] = data.apply(lambda row: thrustmap(
        row['Thrust (N)'], row['Voltage (V)'], popt), axis=1)

    # Compute error
    data['error'] = data['computed_throttle'] - data['ESC signal (µs)']

    # Compute statistics
    mean_abs_error = data['error'].abs().mean()
    std_error = data['error'].std()

    with open('results/fitting_error_report.txt', 'w') as f:
        f.write(f"Mean Error Mutli: {mean_abs_error}\n")
        f.write(f"Standard Deviation of Error Multi: {std_error}\n")
