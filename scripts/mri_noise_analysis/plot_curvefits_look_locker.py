"""
Curve fitting examples
for the Look Locker sequence with a given SNR
"""

import matplotlib.pyplot as plt
import numpy as np
import click

from look_locker import curve_fit_wrapper


def f(t, x1, x2, x3):
    return np.abs(x1 * (1.0 - (1.1 + x2**2) * np.exp(-(x3**2) * t)))

@click.command()
@click.option('--values', default=5, help='Number of values to test')
@click.option('--num_samples', default=14, help='Number of samples')
@click.option('--sequence_length', default=2.6, help='Sequence length in seconds')
@click.option('--snr', default=45, help='Signal to noise ratio')
def main(values, num_samples, sequence_length, snr):

    # grid figure of individual fits (Look Locker is a sequence of T1 measurements)
    fig, axes = plt.subplots(values, values, figsize=(values * 2, values * 1.5))

    T1 = np.linspace(0.3, 5.0, values**2)
    x1 = 1.0
    x2 = np.sqrt(0.5)  # todo: what to choose here? not unique with x3
    x3 = np.sqrt((0.1 + x2**2) / T1)

    for x3_val, ax in zip(x3, axes.flatten()):

        # generate the data
        t = np.linspace(0.115, sequence_length, num_samples)
        y = f(t, x1, x2, x3_val)

        # add some Rician noise to the data
        max_val = np.max(y)
        a, b = (
            np.random.normal(0, max_val / snr, len(y)),
            np.random.normal(0, max_val / snr, len(y)),
        )
        y = y + np.sqrt(a**2 + b**2)

        # plot noisy data
        ax.plot(t, y, "o")

        # curve fit
        popt = curve_fit_wrapper(f, t, y, p0=(1.0, 2.0, 1.0))

        # plot compute estimated curve
        t = np.linspace(0.115, sequence_length, 1000)
        y_est = f(t, *popt)
        ax.plot(t, y_est)

        ax.set_title(
            f"T1: {(0.1 + popt[1]**2)/(popt[2]**2):.2f} s \n"
            f"Actual T1: {(0.1 + x2**2)/(x3_val**2):.2f} s"
        )

    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
