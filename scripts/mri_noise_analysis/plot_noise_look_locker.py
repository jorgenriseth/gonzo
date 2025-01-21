"""
Predicted concentration vs estimated concentrations
for the Look Locker sequence with a given SNR
"""

import matplotlib.pyplot as plt
import numpy as np
import click
from pathlib import Path
import hashlib

from look_locker import curve_fit_wrapper, OptimizeWarning
from common import compute_T1, compute_c
import multiprocessing as mp


def f(t, x1, x2, x3):
    return np.abs(x1 * (1.0 - (1.1 + x2**2) * np.exp(-(x3**2) * t)))


def curve_fit_(x3, sequence_duration, snr, f, x1, x2, seed, repeats):
    np.random.seed(seed=seed)

    number_images_per_sequence = 14
    t = np.linspace(0, sequence_duration, number_images_per_sequence)

    popt = np.zeros((repeats, 3))
    for j in range(repeats):

        y = f(t, x1, x2, x3)
        max_val = np.max(y)
        re, im = (
            np.random.normal(0, max_val / snr, len(y)),
            np.random.normal(0, max_val / snr, len(y)),
        )
        y = y + np.sqrt(re**2 + im**2)
        try:
            popt[j] = curve_fit_wrapper(f, t, y, (1.0, np.sqrt(0.9), 1.0))
        except (OptimizeWarning, RuntimeError):
            popt[j] = np.nan * np.zeros(3)

    return popt


def generate_look_locker_data(snr, samples, sequence_duration):

    repeats = 50
    c_min, c_max = 0.005, 0.3
    c_values = np.linspace(c_min, c_max, samples)
    c = np.vstack([c_values for _ in range(repeats)]).T
    T1_values = compute_T1(c_values) * 0.001  # convert to seconds
    T1 = np.vstack([T1_values for _ in range(repeats)]).T

    x1 = 1.0
    x2 = np.sqrt(0.5)  # todo: what to choose here? not uniquely defined by T1
    x3 = np.sqrt((0.1 + x2**2) / T1_values)

    # repeat repeats times for each T1 value (noise randomly sampled)
    # check if the values are cached in a file, if yes load from cache, if not compute and store in cache
    m = hashlib.sha256()
    m.update(f"{snr}_{samples}_{sequence_duration}_{c_min}_{c_max}_{repeats}".encode())
    sha = m.hexdigest()
    cache_file = Path(f'looklockercache_{sha}.npy')
    try:
        popt = np.load(cache_file)
        print("Loaded cached popt values.")
    except FileNotFoundError:
        print("Cache file not found. Computing popt values...")
        popt = np.zeros((len(T1_values), repeats, 3))
        with mp.Pool(mp.cpu_count()) as pool:
            results = pool.starmap(curve_fit_, [(x3_, sequence_duration, snr, f, x1, x2, i, repeats) for i, x3_ in enumerate(x3)])
        for i, result in enumerate(results):
            popt[i] = result
        np.save(cache_file, popt)
        print("Computed and cached popt values.")

    # calculate the mean and standard deviation of the estimated T1 values
    def compute_T1_from_x23(x2, x3):
        return (0.1 + x2**2) / (x3**2)

    T1_est = compute_T1_from_x23(x2=popt[:, :, 1], x3=popt[:, :, 2])
    c_est = compute_c(T1_est * 1000)

    c_threshold = 0.1
    T1_threshold = compute_T1(c_threshold) * 0.001

    return c, c_est, T1, T1_est, c_values, T1_values, T1_threshold, c_threshold



def plot_estimated_versus_actual(snr, samples, sequence_duration, ax_c=None, ax_t1=None):

    c, c_est, T1, T1_est, c_values, T1_values, T1_threshold, c_threshold = generate_look_locker_data(snr, samples, sequence_duration)

    fontsize = 12
    if ax_c is not None:
        c_est_mean = np.mean(c_est, axis=1)
        ax_c.scatter(c, c_est, s=1, c="gray", alpha=0.2, label="simulated")
        ax_c.plot(c_values, c_est_mean, "r-", label="mean(sim)")
        ax_c.plot(c_values, c_values, "k--", lw=1, label="identity")
        ax_c.set_xlabel("True c (mmol/l)", fontsize=fontsize)
        ax_c.set_ylabel("Estimated c (mmol/l)", fontsize=fontsize)
        ax_c.annotate(
            f'SNR={snr}',
            xy=(0.04, 0.96), xycoords='axes fraction',
            color='black', fontsize=fontsize,
            ha='left', va='top',
        )
        ax_c.axvline(c_threshold, color="black", linestyle="-.")
        leg = ax_c.legend(loc="lower right", frameon=False, markerscale=5.)
        for lh in leg.legend_handles:
            lh.set_alpha(1)

    if ax_t1 is not None:
        T1_est_mean = np.mean(T1_est, axis=1)
        ax_t1.scatter(T1, T1_est, s=1, c="gray", alpha=0.2, label="simulated")
        ax_t1.plot(T1_values, T1_est_mean, "r-", label="mean(sim)")
        ax_t1.plot(T1_values, T1_values, "k--", lw=1, label="identity")
        ax_t1.set_xlabel("True T1 (s)", fontsize=fontsize)
        ax_t1.set_ylabel("Estimated T1 (s)", fontsize=fontsize)
        ax_t1.annotate(
            f'SNR={snr}',
            xy=(0.04, 0.96), xycoords='axes fraction',
            color='black', fontsize=fontsize,
            ha='left', va='top',
        )
        ax_t1.axvline(T1_threshold, color="black", linestyle="-.")
        ax_t1.invert_xaxis()
        leg = ax_t1.legend(loc="lower left", frameon=False, markerscale=5.)
        for lh in leg.legend_handles:
            lh.set_alpha(1)


@click.command()
@click.option("--snr", default=25, help="Signal to noise ratio")
@click.option("--samples", default=200, help="Number of samples")
@click.option("--sequence_duration", default=2.6, help="Sequence duration in seconds")
def main(snr, samples, sequence_duration=2.6):
    fig, ax = plt.subplots(1, 2, figsize=(8, 3))
    plot_estimated_versus_actual(ax_c=ax[0], ax_t1=ax[1], snr=snr, samples=samples, sequence_duration=sequence_duration)
    fig.suptitle("concentration and T1 from Look-Locker sequence")
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
