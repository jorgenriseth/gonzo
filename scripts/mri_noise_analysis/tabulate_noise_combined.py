"""
Predicted concentration vs estimated concentrations
for the Look Locker and Mixed sequences with a given SNR
"""
import click
import numpy as np

from plot_noise_look_locker import generate_look_locker_data
from plot_noise_mixed import generate_mixed_data


def tabulate_estimated_versus_actual(snr, samples, sequence_duration, generate_data_func=generate_mixed_data):
    if sequence_duration is None:
        c, c_est, T1, T1_est, c_values, T1_values, _, _ = generate_data_func(snr, samples)
    else:
        c, c_est, T1, T1_est, c_values, T1_values, _, _ = generate_data_func(snr, samples, sequence_duration)
    c_error = np.abs(c - c_est)

    reference = 0.3 # or c_values
    c_error_5_percentile = np.percentile(c_error, 5, axis=1)/reference*100
    c_error_95_percentile = np.percentile(c_error, 95, axis=1)/reference*100
    c_error_median = np.median(c_error, axis=1)/reference*100
    c_error_mean = np.mean(c_error, axis=1)/reference*100
    c_error_stddev = np.std(c_error, axis=1)/reference*100
    c_error_min = np.min(c_error, axis=1)/reference*100
    c_error_max = np.max(c_error, axis=1)/reference*100

    c_bins = np.array([0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3])
    inds = np.digitize(x=c_values, bins=c_bins)

    def digitize_and_print_statistic(name, data, num_bins, format_str=".3e"):
        line = f"{name} "
        for i in range(num_bins-1):
            line += f"& $\\num{{{np.mean(data[inds==i+1]):{format_str}}}}$ "
        line += "\\\\"
        print(line)

    line = r"$c$ in mmol/l "
    for i in range(len(c_bins)-1):
        line += f"& ${c_bins[i]:.2f}-{c_bins[i+1]:.2f}$"
    line += "\\\\\\midrule"
    print(line)

    stat_names = ["mean(e)", "stddev(e)", "5th(e)", "median(e)", "95th(e)", "min(e)", "max(e)"]
    stats = (c_error_mean, c_error_stddev, c_error_5_percentile, c_error_median, c_error_95_percentile, c_error_min, c_error_max)
    formats = [".2f", ".2f", ".2f", ".2f", ".2f", ".2f", ".2f"]

    for name, stat, fmt in zip(stat_names, stats, formats):
        digitize_and_print_statistic(name, stat, format_str=fmt, num_bins=len(c_bins))
    print(r"\bottomrule")

    reference = 4.0
    t1_error = np.abs(T1 - T1_est)
    t1_error_5_percentile = np.percentile(t1_error, 5, axis=1)/reference*100
    t1_error_95_percentile = np.percentile(t1_error, 95, axis=1)/reference*100
    t1_error_median = np.median(t1_error, axis=1)/reference*100
    t1_error_mean = np.mean(t1_error, axis=1)/reference*100
    t1_error_stddev = np.std(t1_error, axis=1)/reference*100
    t1_error_min = np.min(t1_error, axis=1)/reference*100
    t1_error_max = np.max(t1_error, axis=1)/reference*100

    t1_bins = np.array([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5])
    inds = np.digitize(x=T1_values, bins=t1_bins)

    line = r"$T_1$ in s "
    for i in range(len(t1_bins)-1):
        line += f"& ${t1_bins[i]:.1f}-{t1_bins[i+1]:.1f}$"
    line += "\\\\\\midrule"
    print(line)

    stats = (t1_error_mean, t1_error_stddev, t1_error_5_percentile, t1_error_median, t1_error_95_percentile, t1_error_min, t1_error_max)
    for name, stat, fmt in zip(stat_names, stats, formats):
        digitize_and_print_statistic(name, stat, format_str=fmt, num_bins=len(t1_bins))
    print(r"\bottomrule")


@click.command()
@click.option("--snr", default=25, help="Signal to noise ratio")
@click.option("--samples", default=500, help="Number of samples")
@click.option("--sequence_duration", default=2.6, help="Sequence duration in seconds")
def main(snr, samples, sequence_duration=2.6):
    print("Look-Locker Sequence Results:")
    tabulate_estimated_versus_actual(snr=snr, samples=samples, sequence_duration=sequence_duration, generate_data_func=generate_look_locker_data)
    print("Mixed Sequence Results:")
    tabulate_estimated_versus_actual(snr=snr, samples=samples, sequence_duration=None, generate_data_func=generate_mixed_data)


if __name__ == "__main__":
    main()
